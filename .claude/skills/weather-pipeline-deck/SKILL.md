---
name: weather-pipeline-deck
description: Build or edit the project presentation (PPTX) for the DM2 weather pipeline, keeping the SRH Mobile University branding. Use when the user wants to update slides, change the deck, add the name/matriculation, drop in the logo, or rebuild the presentation.
---

# Weather pipeline presentation

The deck is generated from code: `presentation/build_pptx.py` ->
`presentation/DM2_Weather_Pipeline.pptx` (14 slides). Edit the script, never the
.pptx directly, so the deck stays reproducible.

## Build

```bash
cd "/Users/dev/Agentic Workflows /dm2-weather-pipeline"
uv run --with python-pptx python presentation/build_pptx.py
```

## Brand rules (must match SRH Mobile University)

Reference: https://www.mobile-university.de/ . Corporate minimalist.

- `ORANGE = #F39200` is the single dominant accent (defined at the top of the
  script; `TEAL` and `AMBER` are aliases that remap to orange shades).
- White / light-grey backgrounds (`LIGHT`), white cards, charcoal text (`INK`),
  near-black headings (`PRIMARY`), charcoal title/closing slides (`DARK`).
- Font is Arial (`HEAD_FONT` / `BODY_FONT`), code in Courier New.
- Wordmark "SRH FERNHOCHSCHULE | THE MOBILE UNIVERSITY" on title and closing.
- If the user provides a sample file or official brand guide, match that exactly.

## No em dashes

Never use em dashes in any slide text. Use commas, colons, or parentheses.

## Open placeholders to fill when the user provides the info

- Slide 1 and 14: `[YOUR NAME]` and `[MATRICULATION NUMBER]`
  (`PLACEHOLDER_NAME` / `PLACEHOLDER_MATRIC` constants).
- Slide 10: a box to paste the Airflow DAG screenshot.
- Logo is currently a styled text wordmark. If a PNG/SVG logo is provided, add it
  with `slide.shapes.add_picture(...)` on the title and closing slides.

## Always QA visually after editing

Render to images and inspect before declaring done (the first render is rarely
perfect: look for card text overflowing its border, labels clipped by rounded
corners, low contrast).

```bash
cd presentation
soffice --headless --convert-to pdf DM2_Weather_Pipeline.pptx
rm -f slide-*.jpg && pdftoppm -jpeg -r 110 DM2_Weather_Pipeline.pdf slide
# view slide-*.jpg, fix issues in build_pptx.py, rebuild, re-render
rm -f slide-*.jpg DM2_Weather_Pipeline.pdf   # clean up artifacts when done
```

Content QA (should return nothing):

```bash
uv run --with "markitdown[pptx]" python -m markitdown DM2_Weather_Pipeline.pptx | grep "—"
```

## Slide map (14 slides)

1 title, 2 goal, 3 architecture, 4 data sources, 5 extract, 6 Spark cleaning,
7 BigQuery load, 8 dbt transform (ELT vs ETL + lineage), 9 data quality tests,
10 Airflow automation, 11 sample KPIs, 12 requirement mapping, 13 challenges +
future work, 14 closing.
