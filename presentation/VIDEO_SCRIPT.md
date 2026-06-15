# Presentation video: record-from-this script

Deadline: 15 June, 23:59. Max 15 minutes. Max 100 MB. Voice required. Demo required.

Plan: about 8 minutes of narrated slides, then about 4 minutes of live demo, then a
short close. That lands near 12 to 13 minutes, safely under 15.

---

## 1. How to record (macOS, one continuous take is easiest)

1. Open `DM2_Weather_Pipeline.pptx` in PowerPoint or Keynote. Start the slideshow in
   full screen.
2. Press `Cmd + Shift + 5` to open the screen-recording toolbar.
3. Click `Options` and under `Microphone` choose your mic (this is what records your
   voice). Tip: keep the mic on the whole time.
4. Choose `Record Entire Screen`, then click `Record`.
5. Narrate the slides using section 3 below. When you reach the demo, leave the
   slideshow, switch to Terminal and the browser, and follow section 4.
6. When finished, click the stop icon in the menu bar. The video saves to your Desktop
   as a `.mov`.

Speak slowly and clearly. It is fine to pause; you can cut later if needed. If your
English feels rushed, read each line, breathe, then move on.

---

## 2. Timing guide (keep this next to you)

| Part | Target |
|------|--------|
| Slides 1 to 12 | about 8:00 |
| Live demo | about 4:00 |
| Close | about 0:20 |
| Total | about 12:30 |

---

## 3. Narration, slide by slide (read it aloud)

**Slide 1, Title (about 25 sec)**
Hello, my name is Devendra Singh Dhakad, matriculation number one zero zero zero zero
four six eight four. This is my final project for Data Management 2, supervised by
Professor Binh Vu. The project is a real-time weather and air quality data pipeline,
built with Open-Meteo, Spark, BigQuery, dbt, and Airflow. I will explain the data
sources, the cleaning, and the transformation, and then I will show a live demo.

**Slide 2, Project goal (about 40 sec)**
The goal is to build a complete, automated data pipeline. It collects live weather and
air quality data for ten European cities, cleans and models it, and serves
analytics-ready tables in BigQuery. It covers the full data-curation lifecycle:
real-time extraction, distributed cleaning, warehouse loading, SQL transformation with
tests, and automatic scheduling. In numbers: two data sources, one of them real-time,
ten cities polled live, a five-minute run interval, and all six exam requirements met.

**Slide 3, Architecture (about 45 sec)**
Here is the data flow. The producer polls the Open-Meteo APIs and writes raw JSON.
Spark cleans that data into Parquet. The load script loads it into the BigQuery raw
table. dbt then models and tests it, producing the final mart tables. Apache Airflow
runs every step automatically, every five minutes, and there is also a shell script as
a cron fallback. To avoid dependency conflicts, the project uses two separate Python
3.11 environments: one for Spark, dbt and BigQuery, and one for Airflow.

**Slide 4, Data sources (about 40 sec)**
There are two data sources. The first is Open-Meteo, the real-time source: two free
REST APIs, no key needed, giving weather and air quality for the ten cities. Because
they are polled every five minutes, the landing zone becomes a live, growing stream of
observations. The second source is a static city reference: a curated CSV with country,
population, coordinates and timezone, loaded as a dbt seed. It enriches every reading
and anchors a data-quality test. The two sources join on the city name.

**Slide 5, Extract (about 35 sec)**
Extraction is done by producer dot p-y. For each city it calls both Open-Meteo
endpoints and writes one JSON line per city into the landing zone. It requests UTC time
so the timestamps are comparable, and it uses a try-and-except per city, so one failed
city does not stop the whole run. The nesting you see in the JSON is deliberate, because
Spark does the real flattening in the next step.

**Slide 6, Clean with Spark (about 40 sec)**
Spark does the cleaning, using Structured Streaming. The six steps are: flatten the
nested blocks, cast every field to its proper type, parse the time string into a real
timestamp, drop rows with missing key values, deduplicate by city and observation time,
and derive the air quality category from the European AQI bands. The result is written
as clean Parquet.

**Slide 7, Load into BigQuery (about 35 sec)**
The cleaned Parquet is loaded into BigQuery, into the raw weather_readings table, using
write-truncate. This makes the load idempotent: running it twice gives the same table
with no duplicates, so Airflow can safely retry. It uses the Google Cloud BigQuery
Python client only, with no gcloud command line. In my run, thirty rows were loaded.

**Slide 8, Transform with dbt (about 45 sec)**
Transformation is done with dbt, following the ELT pattern. The lineage goes from the
raw table, to a staging view, to the fact table, to the aggregate KPI tables. The
static seed joins into the fact table to add country name and population. The key idea
is ELT, not ETL: Spark does only light cleaning, and all the business logic runs as SQL
inside BigQuery. This gives warehouse scale, version-controlled SQL, lineage, and
built-in tests. Five models are built.

**Slide 9, Data quality (about 35 sec)**
Data quality is enforced with seventeen dbt tests, and they all pass. There are four
kinds: not-null on the key fields, unique on the keys, accepted-values so the AQI
category is always valid, and relationships, which checks that every city in the
readings exists in the reference table. If any test fails, the Airflow task fails, so
bad data is caught automatically.

**Slide 10, Automation with Airflow (about 40 sec)**
Automation is handled by Apache Airflow. The DAG runs six tasks in order: ingest, spark
clean, load BigQuery, dbt seed, dbt run, and dbt test, on a five-minute schedule. I
verified it: the DAG ran end to end through Airflow, the run state was success, and all
six tasks returned success. dbt seed loaded the cities, dbt run built five models, and
dbt test passed all seventeen checks. A shell script runs the same chain for cron.

**Slide 11, Sample results (about 35 sec)**
These are sample results from the marts. The table shows the average air quality by
country, where a lower European AQI is better. Italy had the worst air quality, and
Poland the best. For weather, Madrid was the hottest city and Warsaw the coolest. These
numbers come straight from the dbt aggregate tables, and they grow richer over time as
new observations arrive every five minutes.

**Slide 12, Requirement mapping (about 30 sec)**
Finally, this table maps each exam requirement to where it is implemented. Two sources
with one real-time: Open-Meteo plus the city seed. Extract, clean and load to BigQuery:
the three scripts. Transformation with dbt. Spark included as the cleaning job. Runs
automatically with Airflow. And the presentation, which is this video. All six
requirements are met. Now let me show a live demo.

---

## 4. Live demo runbook (about 4 minutes)

Switch from the slideshow to a Terminal window (keep the mic recording).

**Step A: run the whole pipeline with one command.** Say: "I will run the entire
pipeline with a single command." Paste and run:

    cd "/Users/dev/Agentic Workflows /dm2-weather-pipeline"
    source config/settings.env
    ./scripts/run_pipeline.sh

While it runs (about 70 seconds), narrate each step as it appears on screen: "Step one,
the producer fetched live data for the ten cities. Step two, Spark cleaned it. Step
three, it loaded into BigQuery. Steps four to six, dbt seeded the cities, built the
models, and ran the tests, all passing."

**Step B: show the cleaned data.** Say: "Here is the cleaned data." Run:

    ./.venv-pipeline/bin/python -c "import pandas as pd, glob; df=pd.concat([pd.read_parquet(f) for f in glob.glob('data/processed/*.parquet')]); print(len(df),'rows'); print(df[['city','observed_at','temperature_2m','aqi_category']].head())"

**Step C: show the data in BigQuery.** Switch to the browser, open
console.cloud.google.com, go to BigQuery, project `data-engineering-2-481619`. Open the
`weather` dataset and click `agg_air_quality_by_country`, then `Preview`. Then click
`Query` and run this, and say "These are the KPI tables that dbt built":

    SELECT country_name, avg_pm2_5, avg_european_aqi
    FROM `data-engineering-2-481619.weather.agg_air_quality_by_country`
    ORDER BY avg_european_aqi DESC;

**Step D (optional): show the Airflow run was green.** Back in Terminal:

    export AIRFLOW_HOME="/Users/dev/Agentic Workflows /dm2-weather-pipeline/airflow"
    ./airflow/.venv-airflow/bin/airflow dags list-runs -d weather_pipeline

Say: "This confirms the Airflow DAG ran with state success." Then switch back to the
last slide.

**Close (about 20 sec):** "That is the full pipeline: real-time ingestion, Spark
cleaning, BigQuery loading, dbt modelling with tests, and automatic scheduling with
Airflow. Thank you for watching."

Stop the recording.

---

## 5. Get the file under 100 MB

First check the size: right-click the `.mov` on your Desktop and choose `Get Info`.

If it is over 100 MB, pick one:

**Option A, no install (QuickTime).** Open the `.mov` in QuickTime Player. Menu `File`,
`Export As`, choose `720p`. This re-encodes to a smaller `.mov`. Check the size; if
still over, export `480p`.

**Option B, precise (ffmpeg).** Install once with `brew install ffmpeg`, then run:

    ffmpeg -i ~/Desktop/yourvideo.mov -vf "scale=-2:720" -r 24 -c:v libx264 -crf 30 -preset medium -pix_fmt yuv420p -c:a aac -b:a 96k ~/Desktop/presentation.mp4

Check the result. Slides and terminal compress very well, so this usually lands far
below 100 MB. If by any chance it is still too big, change `-crf 30` to `-crf 32`.

---

## 6. Final checklist before you submit

- [ ] Your voice is audible the whole way through
- [ ] The demo is included (the pipeline running and BigQuery)
- [ ] Length is under 15 minutes
- [ ] File size is under 100 MB
- [ ] File is an `.mp4` or `.mov`
