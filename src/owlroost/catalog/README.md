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
| `metrics/` | Modeled and analytical runtime ontology          |
| `display/` | presentation and rendering overlays              |
| `catalog/` | Metadata, provenance, and introspection ontology |

These registries intentionally remain separate.

The catalog subsystem does NOT replace these registries.

Instead, the catalog provides:

```text
cross-registry semantic metadata and provenance infrastructure
```
The catalog does not own semantic
definitions.

Schema, metrics, display, and future
registries remain authoritative sources
for their respective domains.

The catalog owns integration,
navigation, and relationship metadata
across those registries.

## Semantic Identity

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
presentation metadata references
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

## Cross-Registry Introspection

Catalog inspection workflows MAY expose
display metadata for diagnostic and
navigation purposes.

Examples include:

* labels
* display profiles
* view participation
* dashboard participation

This does not imply ownership.

Display remains the authoritative owner
of presentation metadata.

Catalog merely queries and presents
that information as part of cross-
registry introspection workflows.

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

The catalog owns identity integration,
not semantic definition.

Semantic definitions remain owned by
their originating registries.

The catalog provides a unified view of
those definitions and their
relationships.

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
who owns its semantics,
where its value originated,
how it is realized,
what analytical role it plays,
where it exists operationally,
and how it relates to other semantic entities.
```

Ontology dimensions intentionally answer
different questions.

owner
    Who owns the semantic meaning?

semantic_domain
    Which scientific workflow domain
    does it belong to?

value_origin
    Where did the value originate?

projection_kind
    How is the variable realized?

analytic_kind
    What analytical role does it play?

materialization_level
    At what operational scope does it
    exist?

node_type
    What kind of catalog entity is it?

## Ontology Design Principle

ROOST intentionally separates:

    provenance
        (value_origin)

    realization
        (projection_kind)

    interpretation
        (analytic_kind)

These concepts frequently overlap in
practice but answer different
questions.

Maintaining this separation reduces
ontology ambiguity and allows new
analytical capabilities to be added
without redefining existing semantic
entities.

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

The term "design" is intentionally
broader than statistical sampling.

It encompasses all aspects of
experimental design and evidence
generation, including:

    trial generation
    historical period selection
    uncertainty methodology
    robustness methodology
    scenario construction


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

The `value_origin` dimension identifies where the value fundamentally comes from.

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

ProjectionKind answers:

    "How is this variable realized?"

Projection semantics describe the
structural realization of a variable.

Projection semantics do NOT describe:

    provenance
    analytical meaning
    statistical interpretation

Those concerns are handled by:

    value_origin
    analytic_kind

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
| `financial.spending.total.today__mean`   |
| `financial.spending.total.today__median` |
| `financial.spending.total.today__p90`    |

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

Synthetic variables exist primarily to
support workflow integration,
preprocessing, orchestration,
comparison, or reporting.

Examples:

    roost_sweeps.ss_age_pair
    comparison.common_overrides
    comparison.run_specific_overrides

Synthetic variables frequently exist
to bridge:

    user-facing workflows

and

    canonical semantic variables

Most synthetic variables never become
model inputs, simulation outputs, or
published report fields.

They nevertheless participate in the
catalog because their relationships are
important for explainability and
workflow navigation.

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

Most variables in ROOST are expected to
be primary.

The remaining categories exist because
analytical workflows frequently require
variables that are:

    comparative
    aggregate
    distributional
    inferential

even though those variables may share
the same provenance and projection
semantics as primary variables.

This dimension is intentionally distinct from:

* provenance
* projection mechanics
* runtime materialization
* storage hierarchy

Instead, `analytic_kind` describes how a variable participates in analytical reasoning and interpretation workflows.

Current taxonomy:

    primary
    comparative
    aggregate
    distributional
    inferential

AnalyticKind answers:

    "What analytical role does this
     variable play?"

This dimension is intentionally
independent from:

    value_origin

        where the value originated

    projection_kind

        how the variable is realized

These analytical categories are expected to influence:

* automatic table generation
* report generation
* visualization selection
* explainability workflows
* validation rules
* compatibility analysis
* analytical pipeline routing

---

## Primary Variables

Primary variables represent first-class
semantic entities within ROOST.

A primary variable may be:

    user-specified
    owl-computed
    roost-computed

because provenance and analytical role
are separate concerns.

Examples:

    bequest
    spending
    taxes
    net_worth
    success_probability
    elapsed_seconds

---

## Comparative Variables

Comparative variables describe similarities, differences, or structural relationships between multiple rows.

These variables remain:

```text
row-level analytical variables
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

The `materialization_level` dimension identifies the operational granularity where the value exists.

Materialization level identifies the
native operational scope of an entity.

Additional projections or aggregations
may materialize the same semantic
variable at other scopes.

Expected taxonomy:

| Level     | Meaning       |
| --------- | ------------- |
| `case`    | Case-level    |
| `session` | Session-level |
| `run`     | Run-level     |
| `trial`   | Trial-level   |
| `catalog` | Catalog-level metadata entity |
| `display` | Display-layer projection |
| `row`     | Report or table row context |

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

# Semantic Relationships

The ontology records semantic
relationships between variables.

These relationships are distinct from:

* runtime provenance
* execution history
* materialized datasets

Current relationship types include:

    derived_from
    expands_to
    materializes_to

## derived_from

Documents computational
dependencies.

Examples:

    net_worth

        <- total_assets
        <- total_liabilities

These relationships describe how a
variable is computed.

## expands_to

Documents preprocessor relationships for command line arguments that don't live in the catalog.

for example:

    ss_age_pair
        expands_to
            ss_age_person0
            ss_age_person1

and then:

    ss_age_person0
    ss_age_person1
        materialize_to
            fixed_income.social_security_ages

## materializes_to

materializes_to documents workflow
expansion or realization relationships.

It is most commonly used by synthetic
helper variables that expand into
canonical variables before execution.


Examples:

    roost_sweeps.ss_age_pair

        ->
        fixed_income
            .social_security_ages

These relationships commonly occur in
synthetic helper variables that bridge
user-facing configuration and canonical
model inputs.

Unlike derived_from, materializes_to
does not imply computation.

Instead it documents semantic
transformation.

---

# Provenance Chain

The catalog distinguishes:

    semantic relationships

from

    operational provenance

Semantic relationships are captured by:

    derived_from
    materializes_to

Operational evolution is captured by:

    provenance_chain

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

The catalog exists to preserve and
expose semantic relationships,
operational provenance, and analytical
identity across the ROOST architecture.

---

# Runtime Variables

Variables materialized into:

    _metrics

may include:

    primary modeled variables
    aggregate variables
    comparative variables
    distributional variables
    inferential variables
    synthetic analytical projections

Examples:

    financial.spending.total.today

    financial.spending.total.today__median

    comparison.spending_delta

    comparison.spending.ks_distance

    comparison.superiority_probability

Once materialized, these variables
behave as first-class runtime entities
throughout:

    reporting
    explainability
    aggregation
    visualization
    comparison workflows
    study-generation workflows

The catalog preserves the semantic
identity of these variables while
allowing runtime systems to materialize
them in different operational contexts.

# Filesystem Provenance

ROOST treats filesystem locations as
canonical operational provenance.

Examples include:

    session directories
    run directories
    trial directories
    generated reports
    exported datasets
    execution artifacts

Filesystem provenance identifies where
analytical evidence originated and how
it was produced.

Transient identifiers such as compact
IDs remain convenience handles rather
than authoritative provenance records.

The catalog MUST preserve this
distinction.

Conceptually:

    semantic identity
        +
    filesystem provenance
        +
    runtime realization

provides reproducible analytical
traceability.

# Explainability

The catalog is intended to become the
foundation of ROOST explainability.

Conceptually:

    semantic variable
        ↓
    runtime realization
        ↓
    aggregation
        ↓
    analytical projection
        ↓
    report usage

The catalog records metadata and
relationships that allow future tooling
to trace this chain.

Examples of explainability questions
the catalog should support:

    What does this variable mean?

    Where did it originate?

    How was it computed?

    What variables contribute to it?

    What aggregates were derived from it?

    Where is it used?

    How is it displayed?

This infrastructure supports:

    reporting
    QA/QC validation
    reproducibility
    provenance analysis
    runtime debugging
    comparison workflows
    study generation
    developer navigation


# Developer Tooling

The catalog is intended to support
future variable-centric workflows.

Examples:

    roost vars show <variable>

    roost vars lineage <variable>

    roost vars relationships <variable>

    roost vars where <variable>

    roost vars reports <variable>

    roost vars explain <variable>

    roost vars trace <variable>

These workflows are expected to provide:

    semantic inspection
    ontology inspection
    provenance inspection
    relationship inspection
    runtime realization tracing
    aggregate tracing
    projection tracing
    report introspection
    explainability support

The long-term goal is to make semantic
entities directly navigable throughout
the ROOST architecture.

# Long-Term Direction

The catalog is evolving toward a
semantic navigation and explainability
layer for ROOST.

Expected future capabilities include:

    provenance graph indexing
    relationship-aware lineage tracing
    projection-aware explainability
    variable-aware reporting
    cross-study introspection
    structural comparison analysis
    compatibility analysis
    execution introspection
    publication-oriented provenance
    automated documentation generation
    study-template introspection

The catalog therefore serves as:

    the semantic metadata,
    relationship,
    provenance,
    and analytical navigation layer
    of ROOST

rather than merely a metadata utility
subsystem.
