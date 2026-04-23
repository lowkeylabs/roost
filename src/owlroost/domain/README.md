

Here is a **concise design contract** for ROOST. This is the canonical reference to keep the architecture stable over time.

---

# 🧭 ROOST Reporting & Analysis Contract

## 🔷 Core Philosophy

* **Single source of truth:** `final_rows`
* **Views define *what*** (metrics, groups, layout)
* **Materialization computes *values***
* **Renderers/plots define *how* results are presented**
* **CLI and reports must share identical computation paths**

---

# 🔁 End-to-End Pipeline

```text
experiments
  ↓
build_run_rows / build_trial_rows
  ↓
filter / sort / top
  ↓
final_rows   ← canonical dataset (list[dict])
  ↓
materialize_view(view, layout)
  ↓
RoostTable   ← rectangular, structured data
  ↓
┌───────────────────────┬────────────────────────┐
│ CLI (inspect)         │ QMD / reports          │
│ render_table (rich)   │ pandas / plots         │
└───────────────────────┴────────────────────────┘
```

---

# 📦 `final_rows` (Input Contract)

* Type: `list[dict]`
* Each row represents:

  * **run** (default) OR
  * **trial** (`--trials`)
* Each row contains:

  * identity/context (`case`, `run_label`, etc.)
  * computed metrics (flattened)
  * nested raw data (e.g. `financial`, `timing`)
* Rows are:

  * filtered
  * sorted
  * ready for analysis
* ❗ Not a DataFrame, not flat, not display-ready

---

# 🧠 `materialize_view(...)` (Core Engine)

## Purpose

Convert:

```text
final_rows + view → structured table
```

## Responsibilities

* Apply `show_if` filtering (`is_table`, `is_pivot`)
* Deduplicate metrics for single-row views
* Resolve each metric via:

  * `MetricSpec`
  * aggregation (`median`, `p10`, etc.)
  * compute functions
* Produce rectangular output (rows × columns)

## Output

Returns a `RoostTable`

---

# 📊 `RoostTable` (Core Data Model)

## Location

```text
domain/models/table.py
```

## Structure

```python
class RoostTable:
    columns: list[str]
    rows: list[list[Any]]
    layout: "table" | "pivot"
    meta: dict
```

## Semantics

### Layout = "table"

* rows = runs/trials
* columns = metrics

### Layout = "pivot"

* rows = metrics
* columns = runs/trials

---

## Required Methods

```python
to_dataframe()        # → pandas DataFrame
series(col)           # → pandas Series
numeric_series(col)   # → numeric-safe Series
```

---

## Meta (recommended)

```python
meta = {
    "metrics": [...],       # resolved metric specs
    "layout": "table",
    "level": "run"|"trial"
}
```

---

# 🖥️ Rendering Layer (CLI)

## Entry Point

```python
render_table(..., engine="rich")
```

## Behavior

* Calls `materialize_view(...)`
* Delegates to renderer

## Engines (initial)

| Engine   | Purpose                |
| -------- | ---------------------- |
| `rich`   | CLI display            |
| `pandas` | debug / export         |
| `none`   | programmatic use (QMD) |

## Rule

> Renderers consume `RoostTable` only (no metric logic)

---

# 📈 Plotting Layer

## Location

```text
domain/services/plots/
```

## Principle

> Plots consume `RoostTable` (via DataFrame)

---

## Supported Plot Types

### 1. Distribution

* histogram
* boxplot
* violin (future)

### 2. Risk / Probability

* CDF (preferred over histogram)
* tail analysis (p10, p5)

### 3. Comparison

* grouped by `run_label`

### 4. Frontier (advanced)

* spending vs shortfall probability
* derived from trial distributions

---

## Required Inputs

* Must operate on:

```python
table.to_dataframe()
```

* Must support grouping:

```python
by="run_label"
```

---

# 🧩 Views / Groups / Metrics (Unchanged)

* **MetricSpec** → defines computation + aggregation
* **Groups** → reusable metric bundles
* **Views** → ordered layout + structure
* Views drive:

  * table columns
  * pivot structure
  * plot inputs

---

# 🔁 CLI vs QMD (Unified)

| Feature     | CLI (`inspect`)    | QMD (`report`)     |
| ----------- | ------------------ | ------------------ |
| data source | `final_rows`       | `final_rows`       |
| computation | `materialize_view` | `materialize_view` |
| output      | rich table         | pandas + plots     |

---

# ⚠️ Non-Goals

* ❌ No duplicate aggregation logic in pandas
* ❌ No direct plotting from raw JSON
* ❌ No mixing rendering into metric computation
* ❌ No format-specific engines (HTML/LaTeX) at this layer

---

# 🚀 Minimal API (Target Usage)

```python
ctx = ReportContext.from_metadata("metadata.yaml")

run_table = ctx.view("run", "default")
trial_table = ctx.view("trial", "default")

df = trial_table.to_dataframe()

plot_cdf(trial_table, "Worst Year / Acceptable", by="run_label")
```

---

# 🏁 Final Contract Summary

* `final_rows` = canonical dataset
* `materialize_view` = computation engine
* `RoostTable` = universal table abstraction
* renderers = presentation only
* plots = consumers of `RoostTable`
