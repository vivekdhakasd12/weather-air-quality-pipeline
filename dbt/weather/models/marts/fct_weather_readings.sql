with weather as (
    select * from {{ ref('stg_weather') }}
),

cities as (
    select * from {{ ref('stg_cities') }}
)

select

    to_hex(md5(concat(weather.city, '|', cast(weather.observed_at as string)))) as reading_id,

    weather.city,
    weather.country,
    cities.country_name,
    cities.population,
    cities.timezone,

    weather.observed_at,
    weather.temperature_c,
    weather.humidity_pct,
    weather.wind_speed_kmh,
    weather.weather_code,

    weather.pm10,
    weather.pm2_5,
    weather.european_aqi,
    weather.ozone,
    weather.aqi_category,

    case
        when weather.temperature_c < 0  then 'Freezing'
        when weather.temperature_c < 10 then 'Cold'
        when weather.temperature_c < 20 then 'Mild'
        when weather.temperature_c < 30 then 'Warm'
        else 'Hot'
    end as temperature_band,

    weather.ingested_at
from weather
left join cities
    on weather.city = cities.city
    and weather.country = cities.country
