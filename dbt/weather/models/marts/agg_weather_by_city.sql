select
    city,
    country,
    count(*)                          as reading_count,
    round(avg(temperature_c), 2)      as avg_temperature_c,
    round(min(temperature_c), 2)      as min_temperature_c,
    round(max(temperature_c), 2)      as max_temperature_c,
    round(avg(humidity_pct), 1)       as avg_humidity_pct,
    round(max(wind_speed_kmh), 1)     as max_wind_speed_kmh,
    max(observed_at)                  as latest_observed_at
from {{ ref('fct_weather_readings') }}
group by city, country
order by city
