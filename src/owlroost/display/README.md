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

### Important

DisplayField declarations may include metadata that ultimately belongs to catalog or ontology.

This does **not** imply that Display owns those concepts.

The registration layer may consume declaration metadata and synthesize:

* CatalogSpec entities
* ontology relationships
* provenance relationships
* display overlays

as appropriate.

Ownership remains with the catalog subsystem even when metadata is authored through DisplayField.field.

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
DisplayField.field(...)
```

while the registration layer handles ontology integration automatically.

## DisplayField.field as an Authoring Helper

`DisplayField.field(...)` is primarily an authoring convenience API.

Its purpose is to simplify registration of analytical fields without requiring authors to manually construct catalog entities and display overlays separately.

Conceptually:

```text
Author
    ↓
DisplayField.field(...)
    ↓
Registration Layer
    ↓
CatalogSpec
    +
DisplayField
```

Field authors should think in terms of:

```text
I want this analytical field to exist.
```

rather than:

```text
I need to construct catalog metadata,
ontology metadata, and display metadata
separately.
```

The registration layer is responsible for routing metadata to the appropriate subsystem.

DisplayField.field therefore acts as a declaration DSL rather than a semantic authority.

```text
Ontology metadata supplied through
DisplayField.field SHOULD be treated as
declaration metadata and transferred to
CatalogSpec ownership during registration.
```

## Catalog Declaration Lifecycle

`DisplayField.field(...)` serves as an authoring convenience API.

Field authors may declare both:

* presentation metadata
* ontology metadata

through a single declaration.

Conceptually:

```text
Author
    ↓
DisplayField.field(...)
    ↓
DisplayField
    +
CatalogSpec declaration
    ↓
Catalog synthesis
    ↓
Canonical CatalogSpec
```

The helper may construct a temporary CatalogSpec declaration describing the intended semantic entity.

This declaration is not itself authoritative.

Authoritative semantic ownership is established only during catalog synthesis, where declarations from:

* schema
* metrics
* display

are merged into a unified catalog.

This distinction is important.

`DisplayField.field(...)` may accept ontology metadata for authoring convenience, but it does not perform:

* catalog lookups
* catalog merges
* provenance updates
* ontology reconciliation

Those responsibilities belong to the catalog subsystem.

The display subsystem therefore remains independent from catalog construction while still providing a simple authoring experience.

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

The current README is very good on **Catalog vs Display ownership**, but it does not yet lock in the newer concepts we've been discussing:

1. **Display Modes** (`table`, `pivot`)
2. **Display Profiles**
3. **Mode-aware view/group entries**
4. The distinction between:

   * View composition
   * Mode participation
   * Profile selection

Without documenting these, a future LLM (or future John) will almost certainly drift back toward:

```text
Views are column lists.
Pivot is a table transformation.
Profiles are optional formatting helpers.
```

when the architecture is actually becoming:

```text
Views
    define analytical presentations

Modes
    define user workflows

Profiles
    define renderer behavior
```

---

# Recommended New Section

I would insert a new section immediately after:

```text
# Views
```

and before:

```text
# Groups
```

because modes and profiles are really part of view composition.

---

# New Section: Display Modes

````markdown
# Display Modes

Display views support multiple display modes.

A display mode represents a user workflow rather than a rendering layout.

Current modes include:

* `table`
* `pivot`

## Table Mode

Table mode is optimized for:

* discovery
* filtering
* navigation
* object selection

Characteristics:

* many rows
* few fields
* compact presentation

Examples:

```text
roost vars
roost results
````

Table mode helps users locate rows of interest.

## Pivot Mode

Pivot mode is optimized for:

* inspection
* comparison
* explainability

Characteristics:

* few rows
* many fields
* detailed presentation

Examples:

```text
roost vars 10 --pivot
roost vars 10,11,12 --pivot

roost results 5 --pivot
```

Pivot mode helps users understand and compare selected entities.

## Important

Display modes are not merely rendering layouts.

Conceptually:

```text
table
    = selection workflow

pivot
    = inspection workflow
```

The renderer may implement pivot mode through row/column transposition, but that implementation detail does not define the mode.

````

---

# New Section: Display Profiles

Immediately after the new Display Modes section.

```markdown
# Display Profiles

Display profiles provide renderer-facing presentation customization.

Profiles may define:

* labels
* widths
* alignment
* formatting
* precision
* visibility behavior

Examples:

```text
Owner
Semantic Domain
Projection Kind
````

vs

```text
Owner
Domain
Projection
```

depending on the active profile.

## Architectural Role

Display profiles do not determine whether a field participates in a view.

Profiles determine how a participating field appears.

Conceptually:

```text
DisplayField
    ↓
DisplayProfile
    ↓
Renderer
```

## Profile Selection

Every DisplayField MUST have at least one profile.

When rendering:

1. Explicitly requested profile wins.
2. Otherwise a profile matching the active display mode is used.
3. Otherwise the sole available profile is used.

This guarantees deterministic presentation behavior.

---

# View Entries

Views and groups contain ordered entries.

Entries define:

* participation
* ordering
* mode visibility

Entries do not define semantic identity.

Examples:

```python
entries=[
    "field_name",
    (
        "description",
        {
            "modes": ["pivot"],
        },
    ),
]
````

Conceptually:

```text
DisplayField
        +
View Entry Metadata
        ↓
Participating View Field
```

## Entry Metadata

Entry metadata belongs to the owning view or group.

It does not belong to the DisplayField itself.

For example:

```python
(
    "description",
    {
        "modes": ["pivot"],
    },
)
```

means:

```text
show description only in pivot mode
```

This does not modify the DisplayField definition.

## Architectural Invariant

DisplayField objects remain reusable across many views.

Mode participation is owned by:

* DisplayView
* DisplayGroup

rather than DisplayField.

```

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

Ontology metadata SHOULD have a single canonical owner.

DisplayField.field may accept ontology-related declaration metadata for authoring convenience, but the registration layer SHOULD transfer semantic ownership to catalog entities rather than storing duplicate ontology state inside DisplayField objects.

Architectural Invariant

```text
Catalog
    owns meaning

Display
    owns presentation
```

while preserving a simple authoring experience for field contributors.

## Semantic identity is unique

ROOST maintains:

```text
one canonical semantic identity
per variable
```

Display overlays should attach to that identity rather than redefine it.

## Views and modes are independent

Views define:

* analytical scope
* included fields
* field ordering
* analytical organization

Modes define:

* user workflow
* presentation behavior

Conceptually:

```text
View
    answers:
        What information is relevant?

Mode
    answers:
        How is the information being consumed?
```

Switching between:

```text
table
pivot
```

SHOULD NOT normally require switching views.

A single view may define both:

* table presentation
* pivot presentation

through mode-aware entries.

## Modes own workflow behavior

Display modes define user workflows.

```text
table
    → selection

pivot
    → inspection
```

Table mode is optimized for:

* discovery
* filtering
* navigation
* object selection

Pivot mode is optimized for:

* inspection
* comparison
* explainability

Views may present different subsets of fields depending on the active mode.

Mode participation belongs to views and groups rather than DisplayField declarations.

## Analytical workflows follow selection → inspection

ROOST analytical workflows generally follow:

```text
discover
    ↓
filter
    ↓
select
    ↓
inspect
```

Typical examples include:

```text
roost vars
roost vars 10
roost vars 10 --pivot

roost results
roost results 15
roost results 15 --pivot
```

Table mode supports discovery and selection.

Pivot mode supports inspection and comparison.

## Participation is owned by views and groups

DisplayField objects remain reusable.

DisplayField definitions SHOULD NOT contain:

* mode participation
* view participation
* group participation

Those concerns belong to:

* DisplayView
* DisplayGroup

through entry metadata.

Conceptually:

```text
DisplayField
        +
View Entry Metadata
        ↓
Participating View Field
```

## Entry metadata determines participation

Entry metadata determines:

* whether a field appears
* where a field appears
* which modes include a field

Entry metadata does NOT determine:

* labels
* formatting
* widths
* alignment

Conceptually:

```text
Entry Metadata
    answers:
        Should this field appear?

DisplayProfile
    answers:
        How should this field appear?
```

## Profiles own presentation behavior

Display profiles determine how fields appear.

Profiles may alter:

* labels
* formatting
* widths
* alignment
* precision

without altering:

* semantic identity
* ontology
* catalog ownership
* mode participation

## Every field has at least one profile

Every DisplayField MUST possess at least one DisplayProfile.

Fields registered without explicit profiles SHOULD receive a synthesized default profile.

This guarantees deterministic rendering behavior.

## Profile selection is deterministic

Profile resolution MUST follow:

```text
1. Explicit profile request

2. Profile matching the active mode

3. Sole available profile
```

This guarantees stable presentation behavior regardless of rendering context.

## Views define analytical presentations

Views are not merely column lists.

Views define:

* analytical scope
* field ordering
* mode-aware participation
* default analytical presentations

Conceptually:

```text
View
    =
        analytical presentation

Mode
    =
        analytical workflow
```

A view may present different subsets of fields in different modes while remaining a single analytical presentation.

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
