# Dashboard Subsystem Architecture

The `display/dashboards/` subsystem provides reusable analytical dashboard layouts for ROOST.

This document complements:

* `display/README.md`
* `catalog/README.md`

and focuses specifically on:

* dashboard architecture
* dashboard layouts
* dashboard panels
* dashboard rendering
* dashboard registration

---

# Purpose

Dashboards provide higher-level analytical presentations built from reusable panels.

Unlike views, which typically materialize a single table, dashboards organize multiple analytical components into a coordinated inspection experience.

Examples include:

* ontology inspection
* catalog QA/QC
* display validation
* registry auditing
* executive summaries
* study reporting

Conceptually:

```text
catalog
    ↓
display
    ↓
dashboard
    ↓
renderer
```

Dashboards exist to help users understand collections of related analytical information.

---

# Architectural Role

The dashboard subsystem is a first-class component of the display architecture.

Conceptually:

```text
DisplayField
DisplayGroup
DisplayView
DisplayDashboard
```

All four participate in the DisplayRegistry.

Responsibilities remain distinct.

| Artifact         | Responsibility                       |
| ---------------- | ------------------------------------ |
| DisplayField     | Presentation metadata                |
| DisplayGroup     | Reusable field collections           |
| DisplayView      | Single-table analytical presentation |
| DisplayDashboard | Multi-panel analytical presentation  |

---

# Dashboard Structure

A dashboard is composed of rows.

Each row contains panels.

Conceptually:

```text
Dashboard
 ├── Row
 │    ├── Panel
 │    ├── Panel
 │    └── Panel
 │
 ├── Row
 │    └── Panel
 │
 └── Row
      ├── Panel
      └── Panel
```

This hierarchy intentionally mirrors common dashboard systems such as Quarto dashboards.

---

# Dashboard Layouts

Dashboard definitions live in:

```text
display/dashboards/layouts/
```

Each module registers one or more dashboard layouts.

Example:

```python
DisplayDashboard(
    name="ontology",
    rows=[
        ...
    ],
)
```

Dashboard layouts should remain declarative.

Layouts SHOULD NOT contain rendering logic.

Layouts SHOULD NOT contain business logic.

Layouts define:

* panel placement
* panel ordering
* dashboard organization

only.

---

# Dashboard Rows

Rows provide layout structure.

A row is an ordered collection of panels.

Conceptually:

```text
DashboardRow
    panels=[
        panel_a,
        panel_b,
        panel_c,
    ]
```

Rows do not perform computation.

Rows exist solely to describe layout.

Renderer implementations determine how rows are displayed.

Examples:

* side-by-side panels
* stacked cards
* responsive layouts
* Quarto rows

---

# Dashboard Panels

Panels are the fundamental analytical building blocks of a dashboard.

Panels encapsulate a specific analytical presentation.

Examples include:

* CrosstabPanel
* CountPanel
* SummaryPanel
* TablePanel

Additional panel types may be introduced without changing dashboard architecture.

Conceptually:

```text
Dashboard
    ↓
Row
    ↓
Panel
    ↓
Materialization
    ↓
Renderer
```

---

# Crosstab Panels

The initial dashboard implementation centers on CrosstabPanel.

Conceptually:

```python
CrosstabPanel(
    title="Projection × Owner",
    row_field="projection_kind",
    column_field="owner",
)
```

A CrosstabPanel describes:

* row dimension
* column dimension
* title

The panel specification remains independent from rendering.

Materialization logic is responsible for constructing the resulting table.

---

# Materialization

Dashboard panels should materialize into renderer-neutral structures whenever possible.

Preferred outputs include:

```text
RoostTable
```

or other renderer-independent artifacts.

Dashboard specifications SHOULD NOT construct Rich objects directly.

This preserves:

* renderer independence
* testability
* future Quarto export support

---

# Rendering

Rendering is owned by:

```text
display/renderers/
```

Dashboard rendering should eventually be implemented by:

```text
rich_dashboard.py
```

Conceptually:

```text
DisplayDashboard
    ↓
Dashboard Materialization
    ↓
Rich Renderer
```

The renderer owns:

* spacing
* alignment
* layout decisions
* visual presentation

The dashboard specification does not.

---

# Registration

Dashboards are registered through the DisplayRegistry.

Conceptually:

```text
DisplayField
DisplayGroup
DisplayView
DisplayDashboard
```

Dashboard discovery should mirror existing discovery systems used by:

* fields
* groups
* views
* explain facets

Adding a new dashboard should require only:

```text
display/dashboards/layouts/<dashboard>.py
```

with no modifications elsewhere.

---

# Architectural Invariants

The following concepts SHOULD remain stable.

## Dashboards Are Presentation Artifacts

Dashboards do not own semantic meaning.

Dashboards consume semantic information.

Semantic ownership remains with:

* schema
* metrics
* catalog

---

## Dashboards Are Declarative

Dashboard definitions describe:

* organization
* layout
* analytical presentation

Dashboard definitions SHOULD NOT contain:

* rendering logic
* business logic
* semantic computation

---

## Rows Own Layout

Dashboard rows describe layout structure.

Rows do not perform computation.

Rows do not perform rendering.

---

## Panels Own Analytical Presentation

Panels define what information should appear.

Renderers define how that information appears.

---

## Materialization Precedes Rendering

Panels should materialize into renderer-neutral artifacts before rendering.

This preserves portability and testability.

---

## Dashboards Complement Views

Views and dashboards serve different purposes.

Views answer:

```text
What fields should appear in a table?
```

Dashboards answer:

```text
What analytical panels should appear together?
```

Views remain optimized for:

* selection
* inspection
* comparison

Dashboards remain optimized for:

* exploration
* QA/QC
* executive reporting
* analytical summaries

---

# Design Philosophy

The dashboard subsystem should remain:

* declarative
* composable
* renderer-neutral
* easy to extend

Dashboard authors should focus on:

```text
What analytical information should appear?
```

rather than:

```text
How should it be rendered?
```

Renderer implementations are responsible for presentation.

Dashboard specifications are responsible for analytical organization.
