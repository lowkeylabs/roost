# ROOST Catalog Architecture

The `catalog/` subsystem provides the semantic metadata, provenance, lineage, introspection, and analytical navigation infrastructure for ROOST.

The catalog is intentionally designed as a metadata-oriented layer built on top of the existing ontology and execution architecture documented in the top-level `README.md`.

This document complements the main architecture document and focuses specifically on:

* Semantic metadata
* Variable ownership
* Variable lineage
* Projection tracing
* Provenance indexing
* Runtime realization tracing
* Cross-registry introspection
* Explainability infrastructure
* Analytical navigation workflows

The catalog is intended to make the internal architecture of ROOST:

```text
observable
queryable
explainable
traceable
navigable
```

---

# Architectural Context

ROOST distinguishes between multiple ontology layers:

| Registry   | Responsibility                                   |
| ---------- | ------------------------------------------------ |
| `schema/`  | Executable configuration ontology                |
| `metrics/` | Observable runtime ontology                      |
| `display/` | presentation and rendering overlays              |
| `catalog/` | Metadata, provenance, and introspection ontology |

These registries intentionally remain separate.

The catalog subsystem does NOT replace these registries.

Instead, the catalog provides:

```text
cross-registry semantic metadata and provenance infrastructure
```

## Canonical Variable Identity

ROOST intentionally treats a semantic variable as a single canonical entity that evolves through layered realization, projection, aggregation, and provenance refinement.

Conceptually:

```text
canonical semantic variable
    +
ontology layers
    +
runtime realization
    +
aggregation lineage
    +
projection overlays
    +
presentation refinement
```

The catalog therefore maintains:

```text
one semantic variable identity
```

rather than creating independent catalog rows for:

* schema definitions
* metrics realizations
* display overlays
* formatting refinements
* aggregation derivatives

Examples:

```text
financial.spending.total.today
```

remains a single semantic variable even as it acquires:

* runtime realizations (`_metrics`)
* aggregation derivatives (`__median`)
* display formatting
* analytical projections
* provenance overlays

These enrichments SHOULD contribute provenance and metadata layers rather than creating competing semantic identities.

The catalog therefore acts as:

```text
a layered semantic identity graph
```

rather than merely a flattened registry index.

# Architectural Invariant

ROOST maintains:

```
one canonical semantic identity per variable
```

across the entire analytical lifecycle.

Registries MAY:

* enrich
* refine
* aggregate
* project
* format
* materialize
* annotate

a variable.

Registries SHOULD NOT:

* create competing semantic identities
* duplicate canonical ontology
* redefine ownership
* fork provenance lineage

The catalog therefore acts as:

```
the canonical semantic identity graph
```

for all ROOST analytical infrastructure.

---

# Conceptual Role

Conceptually:

```text
semantic ontology
    ↓
runtime realization
    ↓
aggregation
    ↓
analytical projection
    ↓
reporting
```

The catalog indexes and traces relationships across this entire pipeline.

The catalog is therefore evolving toward:

```text
a semantic analytical metadata system
```

rather than merely a provenance helper.

---

# Architectural Philosophy

The catalog is intentionally:

* metadata-oriented
* introspection-oriented
* provenance-aware
* explainability-oriented
* projection-aware
* workflow-aware

The catalog SHOULD:

* Explain architecture
* Expose relationships
* Preserve provenance
* Improve discoverability
* Support explainability
* Support QA/QC workflows
* Support developer navigation
* Support reporting workflows
* Support study-generation workflows

The catalog SHOULD NOT:

* Become a replacement runtime datastore
* Become the canonical semantic authority
* Collapse ontology layers
* Duplicate registry semantics unnecessarily
* Replace runtime execution metadata
* Replace filesystem provenance

---

# Semantic Metadata Dimensions

The catalog is evolving toward a set of orthogonal metadata dimensions that describe:

```text
what a variable means,
who owns it,
how it is produced,
how it is analytically realized,
and how it evolved through the system.
```

These dimensions are intentionally independent.

---

# Owner

The `owner` dimension identifies conceptual ontology ownership.

Current taxonomy:

| Owner   | Meaning                                                      |
| ------- | ------------------------------------------------------------ |
| `OWL`   | Retirement/planning engine ontology                          |
| `ROOST` | Orchestration, analytics, runtime, display, catalog ontology |

Examples:

| Variable                       | Owner |
| ------------------------------ | ----- |
| `solver_options.bequest`       | OWL   |
| `rates_selection.method`       | OWL   |
| `roost_settings.trials_per_run` | ROOST |
| `compact_id`                   | ROOST |

Ownership is stable and SHOULD NOT change because of:

* Display overlays
* Formatting overrides
* Aggregation derivations
* Runtime realization
* Provenance events

---

# Semantic Domain

The `semantic_domain` dimension identifies the role a variable plays in the scientific and analytical workflow.

Current taxonomy:

| Domain      | Meaning                                          |
| ----------- | ------------------------------------------------ |
| `decision`  | Retirement strategy and planning assumptions     |
| `design`    | Experimental and scenario-generation methodology |
| `execution` | Computational and runtime orchestration          |

---

## Decision Variables

Decision variables define:

* Retirement policy
* Financial assumptions
* Optimization objectives
* Planning strategy

Examples:

| Variable                            |
| ----------------------------------- |
| `solver_options.bequest`            |
| `optimization_parameters.objective` |
| `asset_allocation.*`                |
| `fixed_income.*`                    |

---

## Design Variables

Design variables define:

* How evidence is generated
* Scenario methodology
* Trial structure
* Historical/stochastic methodology
* Robustness methodology

Examples:

| Variable                 |
| ------------------------ |
| `rates_selection.method` |
| `trials_per_run`         |
| `historical.from`        |
| `historical.to`          |
| `longevity.method`       |

These are:

```text
study design variables
```

rather than merely “sampling variables”.

---

## Execution Variables

Execution variables define:

* Runtime orchestration
* Computational realization
* Concurrency
* Performance configuration

Examples:

| Variable                |
| ----------------------- |
| `workers_per_run`       |
| `OMP_NUM_THREADS`       |
| `worker_timeout`        |
| `roost_environment.*` |

Execution variables SHOULD ideally NOT change:

* Scientific meaning
* Evidence quality
* Retirement interpretation

They SHOULD affect only runtime behavior.

---

# Value Origin

The `value_origin` dimension identifies where a value fundamentally comes from.

Current taxonomy:

| Value Origin     | Meaning                                           |
| ---------------- | ------------------------------------------------- |
| `user-specified` | Configured/prescribed by humans                   |
| `owl-computed`   | Generated by OWL execution                        |
| `roost-computed` | Generated analytically/orchestrationally by ROOST |

---

## User-Specified Values

Examples:

| Variable                 |
| ------------------------ |
| `solver_options.bequest` |
| `rates_selection.method` |
| `trials_per_run`         |

These represent:

```text
model assumptions and study configuration
```

---

## OWL-Computed Values

Examples:

| Variable                         |
| -------------------------------- |
| `financial.spending.total.today` |
| `financial.bequest.total.today`  |
| `success_rate`                   |

These represent:

```text
simulation and planning outcomes
```

---

## ROOST-Computed Values

Examples:

| Variable               |
| ---------------------- |
| `compact_id`           |
| `compact_threads`      |
| `display.total_assets` |

These represent:

```text
analytical or orchestration projections
```

generated by ROOST infrastructure.

---

# Projection Kind

The `projection_kind` dimension identifies how a variable analytically exists.

Current taxonomy:

| Projection Kind | Meaning                               |
| --------------- | ------------------------------------- |
| `canonical`     | Original semantic variable            |
| `aggregate`     | Statistical reduction over trials     |
| `composed`      | Combination of multiple variables     |
| `synthetic`     | Derived analytical helper/computation |
| `formatted`     | Presentation-only refinement          |
| `alias`         | Alternate naming/projection           |

---

## Canonical Variables

Examples:

| Variable                         |
| -------------------------------- |
| `solver_options.bequest`         |
| `financial.spending.total.today` |

These are first-class semantic variables.

---

## Aggregate Variables

Examples:

| Variable   |
| ---------- |
| `__mean`   |
| `__median` |
| `__p90`    |

These are:

```text
statistical analytical projections
```

derived from trial-level distributions.

---

## Composed Variables

Examples:

| Variable          |
| ----------------- |
| `compact_id`      |
| `compact_threads` |

These combine multiple semantic variables into a single analytical projection.

---

## Synthetic Variables

Examples:

| Variable               |
| ---------------------- |
| `display.total_assets` |
| `display.net_worth`    |

These are analytical helper computations.

---

## Formatted Variables

Presentation-only refinements.

Examples include:

* Compact display formatting
* Presentation labels
* Renderer-oriented overlays

---

## Alias Variables

Alternate naming or projection forms.

Examples include:

* `mxSpd`
* Short-form display labels

---


# Analytical Kind

The `analytic_kind` dimension identifies the type of analytical meaning represented by a variable.

This dimension is intentionally distinct from:

* provenance
* projection mechanics
* runtime materialization
* storage hierarchy

Instead, `analytic_kind` describes how a variable participates in analytical reasoning and interpretation workflows.

Current taxonomy:

| Analytic Kind    | Meaning                                  |
| ---------------- | ---------------------------------------- |
| `observed`       | Direct runtime observation               |
| `synthetic`      | Row-local analytical synthesis           |
| `comparative`    | Cross-row analytical comparison          |
| `distributional` | Distribution-aware analytical comparison |
| `inferential`    | Statistical or probabilistic inference   |
| `aggregate`      | Statistical reduction over populations   |

These analytical categories are expected to influence:

* automatic table generation
* report generation
* visualization selection
* explainability workflows
* validation rules
* compatibility analysis
* analytical pipeline routing

---

## Observed Variables

Observed variables represent direct runtime measurements or outcomes.

Examples:

| Variable                         |
| -------------------------------- |
| `timing.elapsed_seconds`         |
| `financial.spending.total.today` |
| `success_rate`                   |

These are typically materialized directly from:

```text
metrics.json
```

or equivalent runtime execution outputs.

---

## Synthetic Variables

Synthetic variables are computed analytically from a single row or runtime realization.

Examples:

| Variable                          |
| --------------------------------- |
| `run_execution.trials_per_second` |
| `display.total_assets`            |
| `display.net_worth`               |

These variables are analytical helper projections derived from existing semantic variables.

---

## Comparative Variables

Comparative variables describe similarities, differences, or structural relationships between multiple rows.

These variables remain:

```text
row-level analytical observations
```

even though their computation may require neighboring rows, multirun context, or session-wide comparison structure.

Examples:

| Variable                            |
| ----------------------------------- |
| `comparison.common_overrides`       |
| `comparison.run_specific_overrides` |
| `comparison.spending_delta`         |
| `comparison.percent_change`         |

Comparative variables are especially important within:

```text
Hydra multirun sessions
```

where neighboring runs differ along one or more sweep dimensions.

These variables support:

* sweep interpretation
* sensitivity analysis
* automated comparison reports
* structural equivalence analysis
* comparative explainability

---

## Distributional Variables

Distributional variables compare or characterize entire trial-level distributions rather than single-point summary statistics.

Examples include:

| Variable                                  |
| ----------------------------------------- |
| `comparison.spending.ks_distance`         |
| `comparison.failure_distribution_overlap` |
| `comparison.bequest_wasserstein_distance` |

These variables help distinguish:

```text
true distributional differences
```

from:

```text
superficial point-estimate differences
```

and are expected to become increasingly important for:

* Monte Carlo analysis
* robustness evaluation
* tail-risk analysis
* probabilistic comparison workflows

---

## Inferential Variables

Inferential variables represent statistical or probabilistic conclusions derived from analytical evidence.

Examples include:

| Variable                                 |
| ---------------------------------------- |
| `comparison.spending.p_value`            |
| `comparison.mean_difference_significant` |
| `comparison.superiority_probability`     |

These variables support:

* statistical significance analysis
* uncertainty-aware reporting
* probabilistic decision support
* automated interpretation workflows

---

## Aggregate Variables

Aggregate variables represent statistical reductions across populations, trials, sessions, or analytical cohorts.

Examples:

| Variable   |
| ---------- |
| `__mean`   |
| `__median` |
| `__p90`    |

Aggregate variables remain analytical projections layered on top of canonical semantic variables.

---

# Materialization Level

The `materialization_level` dimension identifies the operational granularity where a value exists.

Expected taxonomy:

| Level     | Meaning       |
| --------- | ------------- |
| `case`    | Case-level    |
| `session` | Session-level |
| `run`     | Run-level     |
| `trial`   | Trial-level   |

Examples:

| Variable                                 | Level |
| ---------------------------------------- | ----- |
| `solver_options.bequest`                 | run   |
| `financial.spending.total.today`         | trial |
| `financial.spending.total.today__median` | run   |
| `compact_id`                             | run   |

This becomes especially important for:

* Aggregates
* Explainability
* Reporting
* Lineage tracing
* Provenance analysis

---

# Provenance Chain

The catalog treats provenance as a first-class architectural concern.

The `provenance_chain` dimension captures how variables evolve through the system.

Conceptually:

```python
@dataclass
class ProvenanceEvent:
    stage: str
    operation: str
    file: str
    detail: dict = field(default_factory=dict)
```

Expected operations include:

| Operation           | Meaning                         |
| ------------------- | ------------------------------- |
| `REGISTERED`        | Initial ontology registration   |
| `OVERRIDDEN`        | Projection/display refinement   |
| `AGGREGATE_DERIVED` | Statistical derivative creation |
| `COMPOSED`          | Combined projection creation    |
| `FORMATTED`         | Presentation refinement         |
| `MATERIALIZED`      | Runtime realization             |

Examples:

```text
schema/plugins/owl.py
    REGISTERED

display/fields/planning.py
    LABEL_OVERRIDE

metrics/aggregation/aggregate_metrics.py
    AGGREGATE_DERIVED
```

The catalog exists primarily to preserve and expose these relationships.

---

# Runtime Realization

ROOST intentionally separates semantic definitions from runtime realization.

Canonical runtime dataset structures currently distinguish between:

| Runtime Component | Meaning                                     |
| ----------------- | ------------------------------------------- |
| `_inputs`         | Materialized executable configuration       |
| `_metrics`        | Runtime observations and aggregation        |
| `_meta`           | Operational metadata and transient identity |
| `_paths`          | Filesystem provenance                       |

The catalog indexes runtime realization but does NOT replace it.


Analytical metrics materialized into:

```text
_metrics
```

may include:

* direct observations
* synthetic analytical projections
* comparative analytical projections
* distributional analysis outputs
* inferential statistical outputs
* aggregate analytical reductions

Once materialized, these analytical variables behave as first-class semantic runtime observations throughout:

* reporting
* explainability
* aggregation
* display
* study-generation workflows

---

# Filesystem Provenance

Filesystem paths remain the canonical operational provenance identifiers throughout ROOST.

Examples include:

* Session paths
* Run paths
* Trial paths
* Materialized outputs
* Runtime artifacts

Transient operational IDs remain convenience handles rather than canonical provenance identifiers.

The catalog MUST preserve this invariant.

---

# Explainability

The catalog is expected to become the foundation of future explainability systems.

Conceptually:

```text
semantic variable
    ↓
runtime materialization
    ↓
aggregation
    ↓
projection overlays
    ↓
report usage
```

The catalog SHOULD support tracing across this entire chain.

This explainability infrastructure is foundational to:

* Reporting
* QA/QC validation
* Study generation
* Reproducibility
* Provenance analysis
* Runtime debugging
* Structural comparison workflows

---

# Developer Tooling

The catalog is expected to support future CLI workflows such as:

```text
roost vars show <variable>
roost vars lineage <variable>
roost vars where <variable>
roost vars views <variable>
roost vars reports <variable>
roost vars overrides <variable>
roost vars trace <variable>
```

These workflows are intended to provide:

* Jump-to-definition navigation
* Provenance inspection
* Projection tracing
* Runtime realization tracing
* Aggregation explainability
* Report introspection

---

# Long-Term Direction

The catalog architecture is expected to evolve toward:

* Provenance graph indexing
* Projection-aware lineage tracing
* Automated explainability generation
* Variable-aware reporting systems
* Cross-study introspection
* Structural equivalence analysis
* Merge-compatibility analysis
* Runtime execution introspection
* Publication-oriented provenance reporting
* Study-template introspection

The catalog therefore serves as:

```text
the semantic metadata, provenance,
and analytical navigation layer of ROOST
```

rather than merely a metadata utility subsystem.
