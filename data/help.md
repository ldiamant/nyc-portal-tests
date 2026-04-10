# NYC Transit Viewer

This interactive map visualises the potential impact of the **Interborough Express (IBX)** on travel times across NYC.

---

## Getting Started

### How to Explore

- **Hover** over any tract to see its statistics in the panel below
- **Click** a tract to select it
- Use **Set as Origin** or **Set as Destination** to explore connections

### Two Main Views

- **Census Tracts** — Analyse travel time impacts by neighbourhood
- **Transit** — See how existing routes would be affected by IBX

---

## Census Tracts Mode

### Overview Mode

Choose how tracts are coloured:

- **As Origin** — Shows time savings *from* each location
- **As Destination** — Shows time savings *to* each location

Available metrics:

- *Avg Time Change* — Average minutes saved per trip
- *Total Time Saved* — Cumulative hours saved
- *Total Trips* — Number of trips affected
- *Vulnerability (SVI)* — CDC Social Vulnerability Index score
- *Vulnerability + Benefit* — Bivariate equity map (see below)

### Selection Mode

After setting an origin or destination, connected tracts show:

- *Time Change* — Minutes saved (negative = faster)
- *IBX Time* — Travel time with IBX
- *Baseline Time* — Current travel time
- *Transfers* — Number of transfers required

### Equity Analysis

Two special metrics help assess whether IBX benefits reach vulnerable communities:

**Vulnerability (SVI)** — Shows the CDC/ATSDR Social Vulnerability Index for each tract. SVI measures a community's vulnerability to stressors like disease outbreaks or natural disasters, based on:

- Socioeconomic status (poverty, unemployment, education)
- Household composition (elderly, children, disabled, single parents)
- Minority status and language barriers
- Housing type and transportation access

Scores range from 0 (low vulnerability) to 1 (high vulnerability). Darker purple = higher vulnerability.

**Vulnerability + Benefit (Equity Map)** — A bivariate choropleth showing two dimensions simultaneously:

- **Vulnerability** (vertical axis) — SVI score
- **Benefit** (horizontal axis) — Time savings from IBX

Tracts are coloured using a 3×3 matrix:

- **Purple** = High vulnerability, low benefit (equity gap)
- **Teal** = Low vulnerability, high benefit
- **Dark blue** = High vulnerability, high benefit (equitable outcome)

Click the **?** button to open the Equity Map Guide with a detailed explanation and scatter plot showing tract distribution across quadrants.

---

## Transit Mode

Switch to Transit mode using the **Transit** button at the top of the sidebar.

### Overview

Shows all transit routes in their natural colours. Hover over any route to see its name.

### Route Impact

See how IBX affects ridership on existing routes:

- **% Change** — Percentage change in passengers
- **Passenger Change** — Absolute change in riders
- **Baseline Passengers** — Current ridership
- **New Passengers** — Projected ridership with IBX

Routes are coloured by impact:

- **Green** = gains passengers
- **Red** = loses passengers
- **Grey** = minimal or no change

Use the threshold slider to filter routes.

### Station Impact

Visualise IBX station activity:

- **Total Passengers** — Combined boardings, alightings, and transfers
- **Change** — Difference from baseline
- **Transfers/Boardings/Alightings** — Individual metrics

Station circles are sized by the selected metric. Click stations to pin them for comparison.

---

## Map Controls

### Layer Toggles

- **IBX route & stations** — Show/hide the proposed line
- **Transit lines** — Show existing subway and rail
- **Census tract boundaries** — Show/hide outlines

### Tools

- **Measure Distance** — Click points to measure
- **Export GeoJSON** — Download data for GIS software

---

## Quick Tips

- **Green** = time savings (faster with IBX)
- **Red** = time increase (rare)
- **Grey** = no data or unaffected
- Press **Escape** or click outside to close this help
- Click **Back to Overview** to exit selection mode

---

## About the Data

### Travel Time Analysis

-----

### Census Data

Demographic data is sourced from the **American Community Survey (ACS) 5-Year Estimates** at the census tract level, including:

- Population by age, race, and ethnicity
- Median household income and poverty rates
- Commute patterns and travel times
- Vehicle ownership and transit usage

### Social Vulnerability Index (SVI)

SVI data comes from the **CDC/ATSDR Social Vulnerability Index 2022**, which ranks census tracts on 16 social factors grouped into four themes:

1. **Socioeconomic Status** — Below poverty, unemployment, housing cost burden, no health insurance, no high school diploma
2. **Household Characteristics** — Aged 65+, aged 17 and younger, civilian with disability, single-parent households, English language proficiency
3. **Racial & Ethnic Minority Status** — Minority populations, limited English speakers
4. **Housing Type & Transportation** — Multi-unit structures, mobile homes, crowding, no vehicle, group quarters

Higher SVI scores (closer to 1) indicate greater vulnerability.

### Data Sources

- **MTA** — Transit network and ridership data
- **US Census Bureau** — American Community Survey 5-Year Estimates
- **CDC/ATSDR** — Social Vulnerability Index 2022
- **NYC Open Data** — Geographic boundaries and infrastructure
