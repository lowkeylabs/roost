# Display Explain Subsystem

## Purpose

The explain subsystem provides row-level interpretation for
ROOST pivot tables.

Explain exists to help users understand:

* what a variable means
* where values came from
* how values relate to one another
* how a result was produced

The explain subsystem intentionally serves both:

* analysts interpreting results
* developers inspecting architecture

while keeping these concerns separate.

---

# Model Architecture

```text
Schema
    owns executable ontology

Metrics
    owns runtime metric ontology

Catalog
    owns canonical semantic identity

Display
    owns presentation identity

Explain
    interprets pivot-table rows
```

Explain does not own semantic metadata.

Explain consumes metadata already
materialized into:

* CatalogSpec
* DisplayField

and renders user-facing explanations.

---

# Architectural Invariant

Explain is table-oriented rather than
catalog-oriented.

A user interacting with:

```
roost results --pivot
```

is looking at a table rather than a
catalog entry.

Explain therefore operates on pivot rows.

A pivot row represents:

```
one variable
one or more values
```

Explanation facets describe the row
currently visible to the user.

This distinction is important.

Explain is not primarily a field
inspection system.

Explain is a pivot-table interpretation
system.

---

# Responsibilities

Explain owns:

* explanation facet rendering
* row-level interpretation
* explanation composition
* analyst-facing explanations
* developer-facing explanations

Explain does NOT own:

* ontology synthesis
* catalog construction
* schema discovery
* metric discovery
* display registration
* provenance generation

Those responsibilities belong to:

* schema subsystem
* metrics subsystem
* catalog subsystem
* display subsystem

---

# Explanation Categories

Explain supports two classes of
explanations.

## Analyst Explanations

These explanations help users understand
the data currently displayed in the pivot
table.

### variables

Explains what the variable means.

Typically rendered from:

* description
* notes
* user-facing metadata

Example:

```text
Net worth at end of planning horizon.
```

### values

Explains the meaning of the values
currently visible in the row.

Current implementation displays the
materialized values associated with
the row.

Future implementations may provide:

* comparisons
* ratios
* trends
* distributions
* anomaly detection
* significance interpretation

across the visible values.

Example:

```text
Run B is 8.3% higher than Run A.
```

### sources

Explains where values originated.

Typically rendered from:

* value_origin
* source

Example:

```text
owl-computed / metric
```

or:

```text
user-specified / input
```

These explanations answer:

```text
What am I looking at?
What do these values mean?
Where did they come from?
```

---

## Architectural Explanations

These explanations expose internal
ROOST metadata.

### ontology

Displays semantic classification.

Examples:

* owner
* semantic_domain
* value_origin
* projection_kind
* analytic_kind
* materialization_level
* node_type

### relationships

Displays semantic relationships.

Examples:

* derived_from
* materializes_to

These relationships describe how
semantic entities connect within
the catalog graph.

### provenance

Displays semantic evolution history.

Examples:

* origin_file
* defined_in
* provenance_depth
* provenance_chain

### display

Displays presentation metadata.

Examples:

* profiles
* labels
* formatting
* display configuration

### debug

Displays complete internal structures.

Intended primarily for subsystem
development and debugging.

---

# Explain Facets

Current and planned explanation facets:

```text
variables
values
sources

ontology
relationships
provenance
display

debug
```

---

# Explain Composition

Multiple explanation facets may be
requested simultaneously.

Example:

```bash
roost results 0 \
    --pivot \
    --explain=variables,sources
```

Each facet contributes an explanation
column to the rendered table.

Explain therefore behaves as a table
augmentation system rather than a
standalone reporting system.

---

# Catalog Integration

Explain receives catalog metadata from
the caller.

Typical flow:

```text
catalog subsystem
    builds catalog_index

materializer
    receives catalog_index

explain subsystem
    receives catalog_row

explanation rendered
```

Explain intentionally does not perform:

* catalog lookups
* registry traversal
* schema introspection

All required metadata should already be
attached to the catalog row or display
field before explanation rendering begins.

---

# Future Direction

The explain subsystem is expected to
evolve from static metadata rendering
toward analytical interpretation.

Particular focus areas include:

* value comparison
* run comparison
* session comparison
* scenario comparison
* aggregate interpretation
* distribution explanation

The long-term goal is not merely to
display metadata, but to help users
understand the significance of the
results appearing in each pivot row.
