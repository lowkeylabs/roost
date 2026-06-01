# Display Subsystem Architecture

The `display/` subsystem provides the renderer-facing presentation layer for ROOST.

This document complements:

* Top-level `README.md`
* `catalog/README.md`

and focuses specifically on:

* Display architecture
* Presentation overlays
* View construction
* Analytical presentation
* Renderer-facing metadata
* Relationships to schema, metrics, and catalog

This document intentionally avoids repeating broader ontology and catalog architecture documented elsewhere.

---

# Purpose

The display subsystem transforms canonical semantic entities into human-oriented analytical presentations suitable for:

* CLI tables
* Pivot views
* Comparative reports
* Quarto workflows
* QA/QC inspection
* Study reporting
* Publication-oriented outputs

Conceptually:

```text
schema ontology
metrics ontology
catalog identity graph
        ↓
display overlays
        ↓
tables and reports
```

Display exists to help humans consume analytical information.

Display is not the authoritative source of semantic meaning.

---

# Architectural Role

Display occupies the final analytical layer before rendering.

Conceptually:

```text
schema
    ↓
metrics
    ↓
catalog
    ↓
display
    ↓
renderer
```

Responsibilities are intentionally separated.

| Subsystem    | Responsibility                             |
| ------------ | ------------------------------------------ |
| `schema/`    | executable input ontology                  |
| `metrics/`   | observable output ontology                 |
| `catalog/`   | semantic identity, lineage, and provenance |
| `display/`   | presentation overlays and analytical views |
| `renderers/` | final rendering implementation             |

Display therefore operates as:

```text
a presentation layer
```

rather than a semantic authority.

---

# Display Responsibilities

Display owns:

* Labels
* Formatting
* Alignment
* Visibility
* Grouping
* View composition
* Renderer-facing metadata
* Presentation behavior

Examples include:

* Currency formatting
* Percent formatting
* Human-readable labels
* Column ordering
* Group membership
* View definitions
* Pivot presentation rules

These concerns are intentionally renderer-facing.

---

# Display Does Not Own

Display SHOULD NOT become the canonical source for:

* Semantic ownership
* Ontology definitions
* Runtime ontology
* Metric ontology
* Provenance authority
* Aggregation semantics
* Dependency graphs
* Lineage graphs
* Runtime materialization

Those concerns belong elsewhere.

Display may enrich semantic variables but SHOULD NOT redefine their meaning.

---

# Display Fields

Display fields represent renderer-facing overlays attached to semantic variables.

Display fields define:

* labels
* formatting
* alignment
* visibility
* grouping
* presentation behavior

Conceptually:

```text
Semantic Entity
       ↓
DisplayField
```

Display fields should remain lightweight whenever possible.

---

# Semantic Entities

Display consumes semantic entities produced elsewhere.

Examples include:

```text
solver_options.bequest
rates_selection.method
timing.elapsed_seconds
timing.elapsed_seconds__median
```

The semantic identity originates from:

* schema
* metrics
* catalog

Display merely overlays presentation metadata.

Conceptually:

```text
FieldSpec
MetricSpec
CatalogSpec
        ↓
DisplayField
```

---

# Synthetic Semantic Variables

Some displayed variables do not originate directly from schema inputs or runtime metrics.

Examples include:

```text
display.net_worth
display.total_assets
display.fixed_income
display.current_ages
completion_ratio
compact_id
compact_threads
```

These variables possess:

* semantic identity
* lineage
* provenance
* explainability

and therefore belong conceptually to the catalog layer rather than the display layer.

Examples:

```text
display.net_worth
    ← display.total_savings
    ← display.net_hfp_assets

display.total_savings
    ← display.taxable_savings
    ← display.tax_deferred_savings
    ← display.tax_free_savings

compact_id
    ← case_id
    ← session_id
    ← run_id
    ← trial_id
```

Display may contain the implementation of these computations, but semantic ownership belongs to catalog.

Conceptually:

```text
semantic computation
         ↓
     CatalogSpec
         ↓
     DisplayField
```

Every displayed variable SHOULD ultimately trace back to a semantic entity.

---

# Registration Philosophy

Display registration should remain simple.

Field authors should work from a single declaration whenever possible.

The registration layer may:

* attach an existing ontology entity
* attach an existing catalog entity
* synthesize a catalog entity
* create a display overlay

depending on the variable being registered.

Field authors should not need to reason about the underlying registration path.

The preferred authoring experience is:

```python
DisplayField(...)
```

while the registration layer handles ontology integration automatically.

---

# Views

Views organize display fields into reusable analytical presentations.

Examples include:

* balances
* runtime
* methodology
* provenance
* catalog

Views define:

* included fields
* ordering
* grouping
* default presentation

Views SHOULD remain declarative.

Views SHOULD NOT contain business logic.

---

# Groups

Groups provide logical analytical organization independent of specific views.

Examples include:

```text
identity
balances
methodology
runtime
provenance
catalog
```

Groups improve:

* navigation
* discoverability
* reporting workflows
* explainability

Groups SHOULD remain presentation-oriented.

---

# Relationship to Catalog

Display and catalog are complementary.

Catalog answers:

```text
What is this variable?
Where did it come from?
How was it derived?
What depends on it?
```

Display answers:

```text
How should this variable appear?
```

Catalog remains the canonical semantic identity graph.

Display consumes catalog metadata but does not replace it.

---

# Relationship to Schema

Schema defines executable input variables.

Display projects those variables into analytical views.

Examples:

```text
solver_options.bequest
rates_selection.method
asset_allocation.*
```

Display SHOULD NOT redefine schema semantics.

---

# Relationship to Metrics

Metrics define observable runtime outputs.

Display projects metrics into analytical reports.

Examples:

```text
timing.elapsed_seconds
trial.completed
trial.pending
success_rate
```

Display SHOULD NOT redefine metric semantics.

Aggregated metrics remain metric entities and are merely projected by display.

---

# Relationship to Synthetic Variables

Synthetic variables occupy an intermediate position within the architecture.

They are:

* not raw schema inputs
* not raw runtime metrics

but they are also not merely presentation concerns.

Synthetic variables participate fully in:

* catalog lineage
* provenance
* explainability
* reporting
* study workflows
* comparative analysis

Semantic ownership therefore belongs to catalog even when implementation resides inside `display/fields/`.

---

# Architectural Invariants

The following concepts SHOULD remain stable.

## Every displayed variable has semantic identity

Every displayed variable SHOULD ultimately trace back to:

* FieldSpec
* MetricSpec
* CatalogSpec

Display SHOULD NOT create anonymous analytical variables.

## Display remains presentation-oriented

Display owns presentation semantics.

Display SHOULD NOT become a semantic authority.

## Catalog remains authoritative

Catalog remains the canonical source for:

* semantic identity
* lineage
* provenance
* dependency relationships

Display consumes catalog metadata but does not replace it.

## Views remain declarative

Views organize analytical presentation.

Views SHOULD NOT contain business logic.

## Display overlays remain lightweight

Display fields SHOULD enrich semantic variables rather than duplicate ontology.

## Semantic identity is unique

ROOST maintains:

```text
one canonical semantic identity
per variable
```

Display overlays should attach to that identity rather than redefine it.

---

# Design Philosophy

Display exists to help humans understand analytical information.

The subsystem should optimize for:

* Readability
* Explainability
* Discoverability
* Reusability
* Consistency

while preserving the separation between:

```text
semantic meaning
        and
analytical presentation
```

that underlies the broader ROOST architecture.

As the system evolves, semantic ownership should continue moving toward catalog while display remains focused on presentation, organization, and rendering support.
