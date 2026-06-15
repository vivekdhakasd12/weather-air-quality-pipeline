with source as (
    select * from {{ source('raw', 'weather_readings') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by city, observed_at
            order by ingested_at desc
        ) as row_rank
    from source
)

select
    city,
    country,
    latitude,
    longitude,
    observed_at,
    temperature_2m       as temperature_c,
    relative_humidity_2m as humidity_pct,
    wind_speed_10m       as wind_speed_kmh,
    weather_code,
    pm10,
    pm2_5,
    european_aqi,
    ozone,
    aqi_category,
    ingested_at
from ranked
where row_rank = 1
