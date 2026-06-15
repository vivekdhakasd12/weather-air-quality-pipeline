# Narration (read this top to bottom)

Natural, spoken style. The slide you should be on is in bold. Pause briefly at each
paragraph break. Total speaking time is about 12 minutes including the demo.

---

**Slide 1, Title.**
Hi, my name is Devendra Singh Dhakad, and this is my final project for Data Management 2.
Over the next few minutes I am going to walk you through a real-time weather and air
quality data pipeline that I built, and at the end I will show you the whole thing
running live. It is built with five main tools: Open-Meteo for the data, Spark for
cleaning, BigQuery as the warehouse, dbt for the transformations, and Airflow to run
everything automatically. So let me start with what I actually set out to build.

**Slide 2, Project goal.**
My goal was to build one complete, automated pipeline, end to end. It collects live
weather and air quality data for ten European cities, cleans it, models it, and serves
clean, analytics-ready tables in BigQuery. What I really wanted to show is the full
data-curation lifecycle: pulling raw data off the internet, cleaning it with a
distributed engine, loading it into a warehouse, transforming it with tested SQL, and
finally scheduling it so it runs on its own. To put numbers on it: two data sources, one
of them real-time, ten cities, a fresh run every five minutes, and it covers all six of
the project requirements. Before we go deeper, here is the big picture.

**Slide 3, Architecture.**
This is the architecture, and it reads left to right. A producer script polls the
Open-Meteo APIs and drops the raw data as JSON. Spark picks that up and cleans it into
Parquet files. A loader pushes that into a raw table in BigQuery. Then dbt models and
tests it, and out come the final tables that are ready for analysis. The important part
is the bar across the bottom: this whole chain is run by Apache Airflow, automatically,
every five minutes, with a simple shell script as a backup. One detail I am happy with
is that Spark and Airflow live in two separate Python environments, so their
dependencies never clash. Now let me start at the very beginning, with the data.

**Slide 4, Data sources.**
The project needs at least two sources, and one of them has to be real-time. My
real-time source is Open-Meteo: two free APIs, no key required, giving me live weather
and live air quality for the ten cities. Because I poll them every five minutes, the
data keeps growing, so it is a genuine live stream, not a one-time snapshot. My second
source is static: a small reference table of the ten cities, with their country,
population, coordinates and timezone. It barely changes, and its job is to enrich every
reading later on. The two sources join together on the city name. So how do I actually
pull that live data in?

**Slide 5, Extract.**
Extraction is handled by a small script called producer. For each city, it calls both
Open-Meteo endpoints and writes the results as one line of JSON per city. A couple of
careful choices here: I request everything in UTC, so the timestamps line up across all
the cities, and I wrap each city in a try and except, so if one city fails, it does not
take down the whole run. You can see on the right that I deliberately keep the data
nested at this stage, because I want Spark to do the real cleaning, not the producer.
And that is the next step.

**Slide 6, Clean with Spark.**
This is the Spark cleaning job, written with Structured Streaming. It does six things: it
flattens that nested structure, it casts every field to the right type, it turns the time
text into a proper timestamp, it drops any rows that are missing key values, it removes
duplicates, and finally it derives a friendly air-quality category from the European AQI
number. The clean result is written out as Parquet, which is a compact, columnar format
that loads quickly. Once the data is clean, it needs a home.

**Slide 7, Load into BigQuery.**
Loading into BigQuery is done by another small script. It reads all the cleaned Parquet
and loads it into a raw table. The key idea here is that it is idempotent: if I run it
twice, I get the exact same table with no duplicates, which means it is safe to retry. And
I do this purely through Google's Python client, with no command-line tools. On the right
you can see the table and its column types. Now the data is in the warehouse, but it is
still raw, so the real modelling happens next.

**Slide 8, Transform with dbt.**
This is the transformation layer, built with dbt, and it follows the ELT pattern. The data
flows from the raw table, into a staging view, into a fact table, and finally into the
aggregate KPI tables. My static city reference joins in right here, to add the country and
the population. The reason I chose ELT over the older ETL is this: Spark only does light
cleaning, and then all the actual business logic runs as SQL inside BigQuery. That gives me
warehouse-scale power, version control on my SQL, automatic lineage, and built-in testing.
And testing is something I really want to highlight.

**Slide 9, Data quality.**
dbt lets me write tests that run automatically, and I have seventeen of them, all passing.
They come in four kinds. Not-null makes sure the key fields are never empty. Unique makes
sure there are no duplicate keys. Accepted-values makes sure the air-quality category is
always one of the valid options. And relationships makes sure that every city in my
readings actually exists in my reference table. The best part is that if any test fails,
the pipeline stops, so bad data never quietly reaches the results. So that is the full
chain, and the last piece is making it all run by itself.

**Slide 10, Automation with Airflow.**
Automation is handled by Apache Airflow. I defined a DAG that runs the six steps in order,
on a five-minute schedule. And I did not just build it, I verified it: the whole DAG ran
end to end through Airflow, and every single task came back successful. The seed loaded the
cities, the run built five models, and the tests all passed against BigQuery. There is also
a plain shell script that runs the same chain, which I can schedule with cron as a fallback.
Let me show you some of the actual results.

**Slide 11, Sample results.**
These are real numbers from the mart tables. On the left is the average air quality by
country, where a lower score is better. You can see that Italy had the worst air quality in
this sample, and Poland the best. On the right, a few highlights: Madrid was the hottest
city, and Warsaw the coolest. And because new data arrives every five minutes, these
averages just keep getting richer over time. Finally, let me tie everything back to the
requirements.

**Slide 12, Requirement mapping.**
This table connects each requirement to where I implemented it. Two sources with one
real-time: Open-Meteo plus the city reference. Extract, clean, and load to BigQuery: my
three scripts. Transformation with dbt. Spark, as the cleaning engine. Runs automatically,
with Airflow. And the presentation, which is this video. So all six requirements are
covered.

---

**Now switch to VS Code for the live demo.**

Alright, that is the design. Now let me actually show you the whole pipeline running live.

So I am in my project here. I will run the entire pipeline with a single command.

(Run it: `source config/settings.env && ./scripts/run_pipeline.sh`)

And there it goes. Step one, the producer is fetching live data for all ten cities. Step
two, Spark is cleaning it. Step three, it is loading into BigQuery. And steps four, five
and six are dbt: it seeds the cities, builds the models, and runs all seventeen tests. And
there we are, pipeline complete, everything green.

(Optional, switch to the BigQuery console in the browser.)

And if I jump over to BigQuery, here are the tables that dbt built. Let me run a quick query
on the air quality by country. And there are the results, straight from the warehouse.

---

**Closing.**

So that is the full project: real-time ingestion, Spark cleaning, BigQuery loading, dbt
modelling with tests, and automatic scheduling with Airflow, all running end to end. Thanks
very much for watching.
