-- Staging for the static city reference (the dbt seed).

select
    city,
    country,
    country_name,
    latitude  as city_latitude,
    longitude as city_longitude,
    population,
    timezone
from {{ ref('cities') }}
