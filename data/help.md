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

### Selection Mode

After setting an origin or destination, connected tracts show:

- *Time Change* — Minutes saved (negative = faster)
- *IBX Time* — Travel time with IBX
- *Baseline Time* — Current travel time
- *Transfers* — Number of transfers required

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

....
