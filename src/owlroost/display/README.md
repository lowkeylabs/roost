# ROOST Display Architecture

The `display/` subsystem provides the analytical projection, dataset transformation, view composition, table materialization, and rendering infrastructure for ROOST.

The display subsystem is intentionally designed as a presentation-oriented layer built on top of the ontology, runtime realization, and metadata architecture documented in:

* Top-level `README.md`
* `catalog/README.md`

This document complements those architecture documents and focuses specifically on:

* Dataset construction
* Runtime realization loading
* Hierarchical analytical projection
* Semantic display projection
* View composition
* Table materialization
* Rendering
* Analytical presentation workflows

The display subsystem is intended to transform ROOST runtime realizations into:

```text
observable
navigable
comparable
reportable
explainable
human-oriented
```

analytical representations.

---

# Architectural Context

ROOST intentionally separates several orthogonal responsibilities:

| Subsystem  | Responsibility                                   |
| ---------- | ------------------------------------------------ |
| `schema/`  | Executable configuration ontology                |
| `metrics/` | Observable runtime ontology                      |
| `catalog/` | Metadata, provenance, and introspection ontology |
| `display/` | Analytical projection and presentation ontology  |

These subsystems intentionally remain separate.

The display subsystem does NOT replace:

* schema ontology
* metrics ontology
* catalog metadata
* runtime execution

Instead, display provides:

```text
analytical projection,
presentation composition,
and reporting infrastructure
```

built on top of those systems.

---

# Architectural Invariant

Display does NOT own canonical semantic meaning.

Canonical semantic meaning is defined by:

* schema ontology
* metrics ontology
* catalog semantic identity

Display owns only:

```text
presentation semantics
analytical projection semantics
view composition semantics
rendering semantics
```

Display MAY:

* project
* aggregate
* compose
* format
* alias
* materialize
* render

variables.

Display SHOULD NOT:

* redefine ownership
* redefine ontology
* duplicate canonical semantics
* create competing semantic identities

The catalog remains the canonical semantic identity graph.

Display remains a projection layer built on top of that graph.

---

# Conceptual Role

Conceptually:

```text
semantic ontology
        ↓
runtime realization
        ↓
dataset construction
        ↓
hierarchical projection
        ↓
semantic projection
        ↓
view composition
        ↓
table materialization
        ↓
rendering
```

The display subsystem operates across this pipeline.

Display therefore acts as:

```text
an analytical presentation engine
```

rather than merely a rendering system.

---

# Dataset-Centric Architecture

The foundational abstraction of the display subsystem is:

```text
Dataset
```

rather than:

```text
DisplayField
ViewSpec
Renderer
```

Datasets provide a common operational representation for:

* Cases
* Sessions
* Runs
* Trials
* Catalog entities

A dataset consists of rows that typically contain:

```text
_inputs
_metrics
_meta
_paths
```

These structures correspond to the runtime realization architecture defined elsewhere in ROOST.

Datasets provide a uniform interface for:

* filtering
* sorting
* projection
* view generation
* reporting

This allows the same analytical workflow to operate across all ROOST data sources.

---

# Runtime Realization Loading

Display is responsible for constructing analytical datasets from runtime realizations.

Examples include:

```text
case.toml
run.toml
trial.toml
metrics.json
catalog entities
```

Display loaders transform these heterogeneous sources into a common dataset abstraction.

Display therefore consumes runtime realizations but does not define them.

---

# Hierarchical Projection

Display owns hierarchical analytical projection.

Hierarchical projection transforms evidence across operational levels.

Examples include:

```text
trial
    ↓
run

run
    ↓
session

session
    ↓
case
```

Hierarchical projection is responsible for:

* aggregation
* summarization
* evidence consolidation
* reporting-level reductions

This projection is operational and analytical.

It is distinct from semantic ontology.

---

# Semantic Projection

Display also owns semantic projection.

Semantic projection transforms canonical semantic variables into presentation-oriented representations.

Examples include:

```text
display labels

group membership

column ordering

presentation aliases

renderer-specific formatting

analytical display overlays
```

Semantic projection is implemented through:

```text
DisplayField
DisplayGroup
ViewSpec
DisplayRegistry
```

These overlays enrich presentation without modifying canonical semantic identity.

---

# View Composition

Display views define reusable analytical representations of datasets.

Views describe:

* which variables are shown
* grouping structure
* ordering
* visibility
* presentation intent

Views intentionally remain independent from:

* filesystem structure
* execution structure
* renderer implementation

A view may be rendered through multiple output systems without modification.

---

# Materialization

Display materialization converts projected datasets and views into renderer-independent table structures.

Conceptually:

```text
Dataset
    +
DisplayRegistry
        ↓
RoostTable
```

Materialization intentionally separates:

```text
analytical structure
```

from:

```text
renderer implementation
```

This enables consistent behavior across reporting targets.

---

# Rendering

Rendering converts materialized analytical tables into output formats.

Current targets include:

```text
Rich
Markdown
HTML
LaTeX
```

Future renderers may include:

```text
Web UI
API responses
interactive dashboards
publication workflows
```

Renderers should remain thin.

Most analytical behavior should occur before rendering.

---

# Display Registry

The display registry provides presentation-oriented overlays layered on top of canonical ontology.

The display registry owns:

* labels
* formatting
* alignment
* visibility
* grouping
* view composition
* renderer-oriented metadata

The display registry does NOT own:

* ownership semantics
* analytical ownership
* provenance ownership
* canonical ontology

These remain defined elsewhere.

---

# Relationship to the Catalog

The catalog and display subsystems intentionally complement one another.

Conceptually:

```text
catalog
    = semantic identity graph

display
    = analytical presentation graph
```

The catalog answers:

```text
What is this variable?
Where did it come from?
Who owns it?
How did it evolve?
```

Display answers:

```text
How should this variable be viewed?
Grouped?
Compared?
Rendered?
Reported?
```

The catalog therefore provides semantic context.

Display provides analytical presentation.

---

# Explainability

Display is expected to become a major consumer of catalog explainability infrastructure.

Future workflows may include:

```text
view explainability

column lineage

aggregation tracing

projection tracing

report introspection

analytical compatibility validation
```

Display should consume catalog metadata rather than duplicate it.

---

# Consumers

The display subsystem is intentionally consumer-independent.

Current consumers include:

```text
CLI
Quarto
Markdown reports
HTML reports
LaTeX reports
```

Future consumers may include:

```text
Web applications
REST APIs
Interactive dashboards
Study-generation workflows
```

Consumers should use display infrastructure rather than implementing their own presentation logic.

---

# Long-Term Direction

The display subsystem is expected to evolve toward:

* ontology-aware view generation
* automatic report generation
* analytical compatibility validation
* projection-aware explainability
* catalog-driven reporting
* variable-aware visualization selection
* publication-oriented reporting workflows
* study-template reporting systems

The display subsystem therefore serves as:

```text
the analytical projection,
presentation,
and reporting layer
of ROOST
```

rather than merely a collection of renderers or table utilities.

