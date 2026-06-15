# Narration (short version, read top to bottom)

Spoken style. The bold line is the slide to be on. About 5 to 6 minutes with the demo.

---

**Slide 1, Title.**
Hi, I am Devendra Singh Dhakad, and this is my Data Management 2 final project: a
real-time weather and air quality data pipeline, built with Open-Meteo, Spark, BigQuery,
dbt, and Airflow. I will explain it, then show it running live.

**Slide 2, Project goal.**
The goal was one automated pipeline that collects live weather and air quality for ten
European cities, cleans it, and serves analytics-ready tables in BigQuery. Two sources,
one of them real-time, a fresh run every five minutes, and all six requirements met.

**Slide 3, Architecture.**
Here is the flow: a producer pulls from Open-Meteo, Spark cleans the data, it loads into
BigQuery, and dbt models and tests it into the final tables. Airflow runs the whole chain
automatically, every five minutes.

**Slide 4, Data sources.**
Two sources. Open-Meteo is the real-time one: free APIs giving live weather and air
quality, polled every five minutes. The second is a static city reference table that
enriches every reading. They join on the city name.

**Slide 5, Extract.**
The producer script calls both Open-Meteo endpoints for each city and writes JSON. It
uses UTC timestamps, and it skips any city that fails, so one error never stops the run.

**Slide 6, Clean with Spark.**
Spark cleans the data with Structured Streaming: it flattens it, casts the types, parses
the timestamps, drops bad rows, removes duplicates, and derives the air-quality category.
The result is saved as Parquet.

**Slide 7, Load into BigQuery.**
A loader script pushes the clean Parquet into a raw BigQuery table. It is idempotent, so
it is safe to retry, and it uses only Google's Python client.

**Slide 8, Transform with dbt.**
dbt handles the transformation, ELT style. The data goes from raw, to staging, to a fact
table, to the KPI tables, with the city reference joining in. All the business logic is
tested SQL, running inside BigQuery.

**Slide 9, Data quality.**
I have seventeen dbt tests, all passing: not-null, unique, accepted-values, and
relationships. If any test fails, the pipeline stops, so bad data never reaches the
results.

**Slide 10, Automation with Airflow.**
Airflow runs the six steps on a five-minute schedule. I verified it end to end: the DAG
ran with every task successful. A shell script does the same chain as a cron fallback.

**Slide 11, Sample results.**
These are real numbers from the marts. Italy had the worst air quality, Poland the best.
Madrid was the hottest city, Warsaw the coolest. The averages get richer as new data
arrives every five minutes.

**Slide 12, Requirement mapping.**
And this table maps all six requirements to where I implemented them. Everything is
covered.

---

**Switch to VS Code for the live demo.**

Now let me show it running live. I will run the whole pipeline with one command.

(Run `source config/settings.env && ./scripts/run_pipeline.sh`.)

The producer fetches live data, Spark cleans it, it loads into BigQuery, and dbt seeds the
cities, builds the models, and runs all seventeen tests. Pipeline complete, all green.

(Optional: switch to BigQuery and show the tables, or run a quick query.)

**Closing.**
So that is the full project, running end to end: ingestion, Spark cleaning, BigQuery, dbt
with tests, and Airflow. Thanks for watching.
