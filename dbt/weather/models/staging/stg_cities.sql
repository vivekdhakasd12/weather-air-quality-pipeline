select
    city,
    country,
    country_name,
    latitude  as city_latitude,
    longitude as city_longitude,
    population,
    timezone
from {{ ref('cities') }}
