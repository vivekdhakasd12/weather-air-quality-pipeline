from __future__ import annotations

import os
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LANDING_DIR = os.environ.get("LANDING_DIR", str(PROJECT_ROOT / "data" / "landing"))
PROCESSED_DIR = os.environ.get("PROCESSED_DIR", str(PROJECT_ROOT / "data" / "processed"))
CHECKPOINT_DIR = os.environ.get(
    "CHECKPOINT_DIR", str(PROJECT_ROOT / "data" / "checkpoints" / "spark")
)

CURRENT_WEATHER = StructType(
    [
        StructField("time", StringType()),
        StructField("temperature_2m", DoubleType()),
        StructField("relative_humidity_2m", LongType()),
        StructField("wind_speed_10m", DoubleType()),
        StructField("weather_code", LongType()),
    ]
)
CURRENT_AIR_QUALITY = StructType(
    [
        StructField("time", StringType()),
        StructField("pm10", DoubleType()),
        StructField("pm2_5", DoubleType()),
        StructField("european_aqi", LongType()),
        StructField("ozone", DoubleType()),
    ]
)
LANDING_SCHEMA = StructType(
    [
        StructField("city", StringType()),
        StructField("country", StringType()),
        StructField("latitude", DoubleType()),
        StructField("longitude", DoubleType()),
        StructField("weather", CURRENT_WEATHER),
        StructField("air_quality", CURRENT_AIR_QUALITY),
        StructField("ingested_at", StringType()),
    ]
)

def clean_batch(batch_df: DataFrame, _epoch_id: int) -> None:

    cleaned = (
        batch_df.select(
            F.col("city"),
            F.col("country"),
            F.col("latitude"),
            F.col("longitude"),

            F.to_timestamp(F.col("weather.time"), "yyyy-MM-dd'T'HH:mm").alias("observed_at"),
            F.col("weather.temperature_2m").alias("temperature_2m"),
            F.col("weather.relative_humidity_2m").cast("int").alias("relative_humidity_2m"),
            F.col("weather.wind_speed_10m").alias("wind_speed_10m"),
            F.col("weather.weather_code").cast("int").alias("weather_code"),
            F.col("air_quality.pm10").alias("pm10"),
            F.col("air_quality.pm2_5").alias("pm2_5"),
            F.col("air_quality.european_aqi").cast("int").alias("european_aqi"),
            F.col("air_quality.ozone").alias("ozone"),
            F.to_timestamp(F.col("ingested_at"), "yyyy-MM-dd'T'HH:mm:ss'Z'").alias("ingested_at"),
        )

        .where(
            F.col("city").isNotNull()
            & F.col("observed_at").isNotNull()
            & F.col("temperature_2m").isNotNull()
        )

        .dropDuplicates(["city", "observed_at"])
    )

    enriched = cleaned.withColumn(
        "aqi_category",
        F.when(F.col("european_aqi").isNull(), F.lit("Unknown"))
        .when(F.col("european_aqi") <= 20, F.lit("Good"))
        .when(F.col("european_aqi") <= 40, F.lit("Fair"))
        .when(F.col("european_aqi") <= 60, F.lit("Moderate"))
        .when(F.col("european_aqi") <= 80, F.lit("Poor"))
        .when(F.col("european_aqi") <= 100, F.lit("Very poor"))
        .otherwise(F.lit("Extremely poor")),
    )

    count = enriched.count()
    if count == 0:
        print("[spark] batch had no valid rows, nothing written")
        return

    enriched.write.mode("append").parquet(PROCESSED_DIR)
    print(f"[spark] wrote {count} cleaned rows to {PROCESSED_DIR}")

def main() -> int:

    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)

    spark = (
        SparkSession.builder.appName("weather_clean")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")

        .config("spark.hadoop.fs.defaultFS", "file:///")

        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

    stream = spark.readStream.schema(LANDING_SCHEMA).json(LANDING_DIR)
    query = (
        stream.writeStream.foreachBatch(clean_batch)
        .option("checkpointLocation", CHECKPOINT_DIR)
        .trigger(availableNow=True)
        .start()
    )
    query.awaitTermination()
    spark.stop()
    print("[spark] done")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
