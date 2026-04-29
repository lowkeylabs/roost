# Metrics Domain Pattern (ROOST)

This folder defines the **metrics + views system** used throughout ROOST.

It is designed to be:

- Declarative (definitions, not logic)
- Registry-driven (single source of truth)
- Extensible (easy to add metrics and views)
- Reusable (pattern can be replicated in other domains)

---

# 🧠 Core Concept

This system separates **what data exists** from **how it is displayed**.

```text
MetricSpec → defines a single measurable value
Registry   → stores all metrics
Views      → select subsets of metrics for display
````

---

# 📁 Folder Structure

```text
metrics/
├── metrics_spec.py         # MetricSpec class (schema + extraction)
├── metrics_registry.py     # METRIC_REGISTRY (store + get/register)
├── metrics_definitions.py  # All metric definitions (register_metric calls)
├── view_registry.py        # METRIC_VIEW_REGISTRY (store + get/register)
├── view_definitions.py     # All view definitions (register_view calls)
├── __init__.py             # Imports definitions → triggers registration
```

---

# 🔁 Execution Flow

When this module is imported:

```python
import owlroost.domain.metrics
```

the following happens:

1. `metrics_definitions.py` runs → registers all metrics
2. `view_definitions.py` runs → registers all views

This populates:

```python
METRIC_REGISTRY
METRIC_VIEW_REGISTRY
```

---

# 🧩 MetricSpec (metrics_spec.py)

A `MetricSpec` defines:

* `key` → unique identifier
* `path` → where to extract data from `_metrics.json`
* `label` → display name
* `fmt` → formatting
* `dtype` → type (float, int, str, bool)
* `aggregates` → list of aggregations (mean, median, p10, etc.)

Example:

```python
MetricSpec(
    key="bequest",
    path="financial.bequest.total.today",
    label="Bequest",
    fmt="currency",
    aggregates=["mean", "median"],
)
```

---

# 📦 Metric Registry (metrics_registry.py)

Stores all metrics:

```python
METRIC_REGISTRY: dict[str, MetricSpec]
```

Access:

```python
get_metric("bequest")
```

Register:

```python
register_metric(spec)
```

---

# 🧾 Metric Definitions (metrics_definitions.py)

This file contains **only declarations**.

Example:

```python
register_metric(
    MetricSpec(
        key="elapsed",
        path="timing.elapsed_seconds",
        label="Time (s)",
        fmt="float2",
        aggregates=["mean"],
    )
)
```

👉 No logic should live here — only definitions.

---

# 👁️ View Registry (view_registry.py)

Stores views:

```python
METRIC_VIEW_REGISTRY = {
    "trials": {},
    "runs": {},
    "experiments": {},
}
```

Register:

```python
register_view(level, name, metric_keys)
```

Retrieve:

```python
get_view("trials", "default")
```

---

# 🧾 View Definitions (view_definitions.py)

Defines how metrics are grouped for display.

Example:

```python
register_view(
    "trials",
    "default",
    [
        "status",
        "elapsed",
        "bequest",
        "spending",
        "risk",
    ],
)
```

---

# ⚠️ Rules & Constraints

## 1. Metric keys must be unique

```python
key="bequest"  # unique across all metrics
```

---

## 2. Views can only reference registered metrics

If a view includes a missing key:

```text
KeyError: unknown metrics
```

---

## 3. Definitions must be imported

`__init__.py` must include:

```python
from . import metrics_definitions
from . import view_definitions
```

---

## 4. Extraction uses dot-paths

```python
"path": "risk.outcome.classification.risk_level"
```

Must match structure of `_metrics.json`.

---

## 5. Aggregates are opt-in

Only metrics with:

```python
aggregates=["mean", "median"]
```

will produce:

```text
bequest_mean
bequest_median
```

---

# ➕ Adding a New Metric

### Step 1 — Add to `metrics_definitions.py`

```python
register_metric(
    MetricSpec(
        key="new_metric",
        path="some.path.to.value",
        label="New Metric",
        fmt="float2",
        aggregates=["mean"],
    )
)
```

---

### Step 2 — Add to a view

```python
register_view(
    "trials",
    "debug",
    [
        "status",
        "new_metric",
    ],
)
```

---

# ➕ Adding a New View

```python
register_view(
    "trials",
    "diagnostics",
    [
        "status",
        "failure_reason",
        "min_cushion",
        "worst_drawdown",
    ],
)
```

---

# 🔍 Design Principles

## Separation of Concerns

| Layer       | Responsibility  |
| ----------- | --------------- |
| MetricSpec  | data definition |
| Registry    | storage         |
| Definitions | configuration   |
| Views       | presentation    |

---

## Declarative > Imperative

All metrics and views are declared — not computed inline.

---

## Registry = Source of Truth

* All metrics must exist in `METRIC_REGISTRY`
* Views reference keys only

---

## Views are Projections

Views do not define logic — they select metrics.

---

# 🔁 Reusing This Pattern in Other Domains

This pattern can be replicated for:

* decision levers
* scenario inputs
* model parameters
* experiment metadata

---

## Example: `domain/levers`

```text
levers/
├── lever_spec.py
├── levers_registry.py
├── levers_definitions.py
├── view_registry.py
├── view_definitions.py
```

---

## Key Rule

👉 Keep domain meaning:

* `MetricSpec` (not `ValueSpec`)
* `LeverSpec` (not generic names)

---

# 🚀 Future Extensions

This system supports:

* dynamic views (`--view`)
* filtering and sorting
* aggregation across trials
* diagnostics for failures
* category-based views (financial, risk, timing)

---

# 🏁 Summary

This folder implements a **schema-driven analytics system**:

```text
MetricSpec → Registry → Views → CLI
```

It is:

* scalable
* extensible
* consistent
* reusable across domains


# 💬 For AI Assistants

When extending this system:

1. NEVER hardcode metrics in CLI
2. ALWAYS register new metrics in `metrics_definitions.py`
3. ALWAYS reference metrics by key in views
4. DO NOT bypass the registry
5. KEEP logic out of definitions files
