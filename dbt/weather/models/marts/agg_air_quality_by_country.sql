-- KPI mart: air quality summary per country across all observations.

select
    country,
    country_name,
    count(*)                       as reading_count,
    round(avg(pm2_5), 2)           as avg_pm2_5,
    round(avg(pm10), 2)            as avg_pm10,
    round(avg(european_aqi), 1)    as avg_european_aqi,
    round(avg(ozone), 1)           as avg_ozone,
    max(observed_at)               as latest_observed_at
from {{ ref('fct_weather_readings') }}
group by country, country_name
order by avg_european_aqi desc
