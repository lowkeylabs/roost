# OWL-ROOST

**Retirement Options and Outcomes Studies Tool**

**ROOST** (Retirement Options and Outcomes Studies Tool) evaluates **retirement decision policies**—not just static plans—by comparing how **agent-controlled actions** perform under **uncertainty** when those decisions are revisited annually.

ROOST is designed to answer questions like:

> *“Given the uncertainty I face, how flexible are my retirement decisions—and which decision policies are most robust?”*

It does this by organizing retirement analysis around a small number of clear, orthogonal concepts spanning:

* Scientific experimentation
* Stochastic simulation
* Policy comparison
* Execution provenance
* Statistical evaluation under uncertainty
* Reproducible operational execution

ROOST builds on OWL while extending retirement analysis into a broader scientific experimentation framework for studying retirement policies under uncertainty.

---

# Core Concepts

ROOST introduces eight key concepts in extending the work of OWL.

* **Decision options** define *what question is being asked*
* **Choice templates** define *policy alternatives*
* **Cases** define *initial conditions and constraints*
* **Experiments** define *scientific groupings and research objectives*
* **Sessions** define *execution provenance and generated outputs*
* **Runs** define *policy evaluations under uncertainty*
* **Trials** define *individual stochastic realizations*
* **Results** provide *evidence for comparison and insight*

Cases and runs are shared between OWL and ROOST. They are represented by exactly the same files and outputs.

---

# Conceptual Relationships

The following relationships define the conceptual structure of ROOST.

```text
Case × Session → Runs
Experiment → Scientifically Related Runs
Run → Statistical Summary of Trials
Trial → Primitive Stochastic Observation
```

These concepts are intentionally asymmetric.

* Trials and runs contain scientific and statistical evidence.
* Sessions preserve operational provenance and execution history.
* Experiments organize scientific interpretation and comparison.

---

# Canonical Operational Structure

ROOST distinguishes between:

* Operational execution structure
* Scientific interpretation structure

The canonical operational provenance hierarchy is:

```text
Case → Session → Run → Trial
```

This hierarchy defines:

* Filesystem organization
* Runtime provenance
* Recovery and continuation state
* Execution metadata
* Trial execution outputs
* Aggregated statistical results

All operational discovery, cleanup, reporting, and execution management are rooted in this hierarchy.

Scientific interpretation operates as a logical overlay on top of this operational structure.

---

# Statistical and Scientific Model

ROOST distinguishes between:

* **Decision variables** that define retirement policies and strategies
* **Sampling variables** that control stochastic exploration
* **Execution variables** that control runtime and infrastructure behavior

Examples include:

| Variable Type       | Examples                                                                |
| ------------------- | ----------------------------------------------------------------------- |
| Decision variables  | Roth conversion strategy, Social Security timing, spending policy       |
| Sampling variables  | random seed, trial count, bootstrap selection                           |
| Execution variables | workers per run, resolved solver, thread counts, runtime execution mode |

This distinction is central to ROOST’s architecture.

Changing a decision variable creates a scientifically different policy evaluation.

Changing a sampling or execution variable may produce:

* Different statistical estimates
* Different convergence behavior
* Different runtime characteristics
* Different operational execution profiles

while still evaluating the same underlying policy.

---

# Trials and Runs

A **trial** represents a single stochastic realization of uncertainty.

Examples of stochastic variation include:

* Market returns
* Historical sequence selection
* Bootstrap sampling
* Inflation trajectories
* Longevity realizations

Trials are the primitive observations of the ROOST system.

A **run** represents a statistical evaluation of a fixed policy configuration across one or more trials.

Conceptually:

```text
Policy + Uncertainty Sampling → Run
```

Runs are the primary scientific comparison unit in ROOST.

When a run contains:

* A single trial, run-level metrics are identical to trial metrics
* Multiple trials, run-level metrics become statistical summaries over uncertainty

Examples include:

* Mean spending
* Median bequest
* P90/P95 outcomes
* Success rates
* Runtime distributions
* Sampling stability measurements

This allows ROOST to evaluate policies for robustness across many plausible futures rather than optimizing against a single deterministic scenario.

---

# Structural Run Identity

ROOST distinguishes between:

* Structural run identity
* Session provenance
* Observed runtime behavior

Two runs may be considered structurally equivalent when they share:

* Decision variables
* Sampling variables
* Resolved execution configuration

while differing only in:

* Session provenance
* Execution timestamps
* Runtime observations
* Execution durations
* Throughput metrics

This distinction supports workflows such as:

* Operational deduplication
* Structural comparison
* Merge compatibility analysis
* Reproducible experiment organization
* Runtime performance analysis

Filesystem paths preserve immutable execution provenance, while structural comparison operates over resolved run configuration.

---

# Run Materialization and Execution

ROOST distinguishes between:

* Declarative configuration intent
* Resolved executable runtime configuration
* Observed runtime outcomes

Conceptually:

```text
Case Configuration
    ↓
Decision / Sampling Expansion
    ↓
Runtime Resolution
    ↓
Materialized Run Configuration
    ↓
Trial Execution
    ↓
Metrics and Aggregation
```

Examples of runtime resolution include:

* Solver auto-selection
* Worker auto-selection
* Thread allocation
* Runtime execution mode selection

The persisted `run.toml` file therefore represents:

```text
a frozen executable run contract
```

rather than merely a partially specified execution template.

A fully materialized run configuration supports:

* Reproducibility
* Stable structural comparison
* Deterministic replay behavior
* Operational provenance integrity
* Consistent purge and cleanup semantics
* Stable experiment organization

---

# Experiments

An **experiment** defines a structured scientific exploration for a given decision or uncertainty dimension.

Conceptually:

```text
Experiment → Scientifically Related Runs
```

An experiment answers the question:

> *“What scientific question or policy dimension are we exploring?”*

Experiments may:

* Systematically vary a decision parameter (e.g., Social Security claiming age)
* Sweep across a family of choice templates
* Explore Roth conversion strategies
* Compare spending policies
* Enumerate historical market regimes
* Compare optimization or simulation approaches
* Study execution and sampling strategies
* Test whether conclusions generalize across households

Experiments are:

* Logical rather than physical
* Scientific rather than operational
* Potentially cross-case and cross-session

A single experiment may include runs from:

* Multiple sessions
* Multiple dates
* Multiple cases/households
* Multiple execution environments

Experiments are logical scientific overlays over structurally related runs.

Experiments therefore organize and interpret related runs under a common research objective.

Experiments do **not** define filesystem structure.

They define scientific meaning.

---

# Sessions

A **session** represents a specific execution event in which ROOST generates and/or evaluates runs for a case.

Conceptually:

```text
Case × Session → Runs
```

Sessions are operational rather than scientific.

They organize:

* Generated outputs
* Logs and metadata
* Runtime provenance
* Execution history
* Recovery and continuation state
* Incremental execution work

A session answers the question:

> *“What execution work was performed during this event?”*

Sessions provide:

* Immutable execution provenance
* Timestamp-oriented organization of outputs
* Incremental extension of larger experiments
* Separation of execution management from scientific interpretation
* Repeatable and reproducible execution history

For example, a worker-scaling experiment might be executed across multiple sessions:

* Session A: `workers_per_run=2..5`
* Session B: `workers_per_run=6..10`

Scientifically, these sessions may belong to the same experiment even though they were executed separately.

Sessions are associated with individual cases and execution events, while experiments may span multiple sessions and multiple cases.

This distinction allows ROOST to separate:

* **Scientific organization** (*experiments*)
  from
* **Execution and storage organization** (*sessions*)

while preserving a stable hierarchy of runs and trials.

---

# Execution Provenance

Execution provenance refers to the complete operational context in which runs and trials were generated.

Examples include:

* Runtime configuration
* Solver selection
* Parallelism configuration
* Thread allocation
* Sampling strategy
* Session organization
* Execution timestamps
* Recovery and continuation state
* Execution environment details

ROOST treats provenance as operational metadata distinct from scientific interpretation.

Filesystem paths serve as the canonical provenance identifiers for generated execution artifacts.

---

# Operational IDs and Selection Handles

ROOST may assign transient operational IDs to sessions, runs, and trials for:

* Interactive selection
* CLI workflows
* Filtering and display
* Operational management
* Cleanup and maintenance workflows

These IDs are:

* Ephemeral
* Context-dependent
* Operational rather than scientific
* Intended for CLI convenience

Filesystem paths remain the canonical provenance identifiers.

Experiments and persistent scientific overlays SHOULD reference canonical paths or structurally equivalent run definitions rather than transient operational IDs.

---

# Filesystem vs Scientific Structure

ROOST intentionally separates:

* Operational filesystem organization
  from
* Scientific experiment organization

Filesystem hierarchy reflects operational execution provenance:

```text
Case → Session → Run → Trial
```

Scientific organization is logical and overlay-based:

```text
Experiment → Related Runs
```

Experiments may span:

* Sessions
* Dates
* Execution environments
* Multiple cases/households

Experiments are therefore not tied directly to filesystem structure.

---

# Scientific and Operational Architecture

ROOST distinguishes between four major entity types:

| Entity     | Primary Role                               |
| ---------- | ------------------------------------------ |
| Trial      | Primitive stochastic observation           |
| Run        | Statistical policy evaluation              |
| Session    | Execution provenance container             |
| Experiment | Scientific organization and interpretation |

These entities are intentionally asymmetric.

Trials and runs contain numerical observations and statistical evidence.

Sessions and experiments primarily organize, contextualize, and interpret those results.

---

# Variable Ontology and Provenance Architecture

ROOST distinguishes between multiple semantic and operational variable domains.

This separation is intentional and foundational to the architecture.

The system is designed to support:

* Exhaustive OWL input coverage
* Hydra sweep generation
* Runtime materialization
* Statistical aggregation
* Scientific reporting
* Provenance tracing
* Reproducible analytical workflows
* Human-oriented analytical overlays

These concerns operate at different semantic layers and therefore use distinct ontology and registry systems.

---

# Registry Layering

ROOST currently distinguishes between three major semantic registry domains:

| Registry            | Primary Responsibility                                  |
| ------------------- | ------------------------------------------------------- |
| `schema/`           | Executable input and runtime ontology                   |
| `metrics/`          | Observable output and aggregation ontology              |
| `display/`          | Analytical projection and presentation ontology         |

These registries intentionally represent different semantic domains rather than duplicated metadata systems.

---

# Schema Registry

The schema registry defines the authoritative executable configuration ontology for ROOST and OWL integration.

Responsibilities include:

* OWL input variable discovery
* Runtime configuration semantics
* Runtime-default discovery
* Hydra configuration generation
* Hydra sweepability
* Runtime materialization support
* Compatibility and helper fields
* Executable configuration validation

The schema registry is intentionally exhaustive across the executable OWL input domain.

This is a critical architectural requirement.

Complete schema coverage ensures that:

* Hydra sweep generation remains complete
* All executable configuration variables remain discoverable
* Study templates can enumerate valid parameter spaces
* Runtime materialization remains reproducible
* Users are not forced to rely on ad hoc Hydra `+variable=value` syntax

The schema registry therefore functions as:

```text
the executable configuration ontology of ROOST
```

rather than merely a documentation or validation system.

Schema fields may originate from:

* OWL Pydantic models
* OWL runtime-discovered defaults
* ROOST runtime extensions
* Compatibility overlays
* Helper and derived runtime variables

---

# Metrics Registry

The metrics registry defines the authoritative ontology for observable runtime outputs and statistical aggregation semantics.

Responsibilities include:

* Canonical output metric definitions
* Statistical aggregation semantics
* Metric typing and interpretation
* Aggregation-level compatibility
* Output-level provenance semantics
* Runtime observation interpretation

Metrics represent observable evidence generated by runs and trials.

Examples include:

* Spending outcomes
* Bequest distributions
* Success probabilities
* Runtime durations
* Convergence metrics
* Computational complexity metrics
* Sampling stability measurements

The metrics registry defines:

```text
the observable output ontology of ROOST
```

rather than runtime execution behavior or analytical presentation.

---

# Display Registry

The display registry defines the analytical projection and presentation layer used by reporting, CLI rendering, views, tables, and comparative analysis workflows.

The display registry is intentionally renderer-facing.

It owns:

* Labels
* Formatting
* Alignment
* Visibility
* Grouping
* View composition
* Aggregate display synthesis
* Analytical overlays

The display registry does NOT own canonical semantic meaning.

Canonical semantic ownership remains with:

* `schema_registry`
* `metrics_registry`

The display layer instead projects semantic variables into:

```text
human-oriented analytical representations
```

suitable for:

* CLI tables
* Pivot displays
* Comparative reporting
* Quarto workflows
* Publication-oriented outputs
* QA/QC inspection workflows

Display fields may therefore:

* Wrap canonical semantic variables
* Override analytical labels
* Introduce analytical grouping semantics
* Synthesize aggregate display variables
* Define report-oriented presentation behavior

without becoming the authoritative semantic source for the underlying variable.

---

# Operational Realization Layer

ROOST separates semantic variable definition from runtime operational realization.

Operational realization occurs during dataset loading and execution discovery.

Canonical runtime dataset rows currently distinguish between:

| Dataset Component | Responsibility                              |
| ----------------- | ------------------------------------------- |
| `_inputs`         | Materialized executable configuration       |
| `_metrics`        | Runtime observations and aggregations       |
| `_meta`           | Operational metadata and transient identity |
| `_paths`          | Filesystem provenance and execution lineage |

This distinction allows ROOST to preserve separation between:

* Semantic ontologies
* Runtime execution state
* Observed runtime evidence
* Filesystem provenance
* Analytical overlays

Filesystem paths remain the canonical operational provenance identifiers throughout the system.

---

# Semantic Projection vs Hierarchical Projection

ROOST currently distinguishes between two different forms of projection.

## Semantic Projection

Semantic projection maps canonical semantic registries into analytical display overlays.

Conceptually:

```text
schema ontology
metrics ontology
        ↓
display ontology
```

This projection stage synthesizes renderer-facing analytical representations while preserving canonical semantic ownership in the underlying registries.

## Hierarchical Projection

Hierarchical projection maps runtime entities across operational aggregation levels.

Examples include:

```text
trial → run
run → session
session → case
```

These projections aggregate operational observations and statistical evidence across the canonical execution hierarchy defined elsewhere in this document.

The distinction between semantic projection and hierarchical projection is intentional and architecturally important.

---

# Provenance and Introspection

ROOST treats provenance as a first-class architectural concern.

Provenance includes both:

* Operational execution provenance
  and
* Semantic variable provenance

Examples include:

* Variable origin registry
* Runtime storage location
* Materialized execution paths
* Aggregation lineage
* Display override lineage
* Hydra generation provenance
* Runtime discovery provenance
* Report and view usage

ROOST is evolving toward a dedicated catalog and introspection architecture capable of tracing:

```text
semantic variable
    ↓
runtime materialization
    ↓
aggregation
    ↓
display projection
    ↓
report usage
```

across the entire analytical pipeline.

This provenance architecture is foundational to:

* Explainability
* Reproducibility
* Study generation
* QA/QC validation
* Structural comparison
* Merge compatibility analysis
* Runtime debugging
* Reporting and publication workflows

---

# Architectural Direction

ROOST is evolving toward a metadata-rich analytical architecture in which:

* Semantic ontologies remain explicitly layered
* Runtime realization remains operationally reproducible
* Analytical overlays remain logically separated from canonical semantics
* Provenance remains traceable across all execution and reporting layers
* Study workflows become increasingly automated and introspectable

The current ontology layering is therefore intentional and SHOULD remain conceptually stable unless explicitly redesigned.


---

# Generalization and Cross-Case Studies

Although many retirement studies focus on a single household, ROOST is also designed to support broader comparative analysis across multiple cases.

Experiments may explore questions such as:

* Do retirement strategies generalize across different households?
* Which policies remain robust across varying balance structures?
* How sensitive are outcomes to demographic differences?
* Which optimization strategies scale consistently across cases?
* Which execution strategies scale consistently across environments?

This allows ROOST to support both:

* Detailed household-specific retirement analysis
  and
* Cross-household scientific generalization studies

within the same conceptual framework.

---

# Sampling and Estimation

ROOST treats uncertainty sampling as a first-class scientific concern.

Multiple runs may evaluate the same underlying policy while differing only in:

* Random seeds
* Sampling methods
* Trial counts
* Execution configuration

This supports workflows such as:

* Combining compatible runs to increase sample sizes
* Comparing sampling strategies
* Studying estimator stability
* Evaluating convergence behavior under uncertainty
* Comparing execution strategies
* Studying runtime scaling behavior

For example:

* Two independent runs of 100 trials each may be compared against
* One run containing 200 trials

to study differences in sampling behavior and estimator quality.

Scientifically compatible runs may therefore be merged or compared even when generated in different sessions.

---

# Architectural Invariants

The following concepts are foundational to ROOST and SHOULD remain stable unless intentionally redesigned.

## Runs are the primary scientific comparison unit

Runs represent statistical evaluations of fixed policy configurations under uncertainty.

Most scientific comparison, reporting, and analysis in ROOST occurs at the run level.

## Trials are primitive stochastic observations

Trials represent individual realizations of uncertainty and are aggregated into run-level statistical summaries.

## Sessions are operational rather than scientific

Sessions preserve execution provenance, filesystem organization, runtime metadata, and execution history.

Sessions SHOULD NOT become primary scientific result entities.

## Experiments are logical scientific overlays

Experiments organize scientifically related runs and MAY span:

* Multiple sessions
* Multiple cases
* Multiple dates
* Multiple execution environments

Experiments SHOULD remain logically decoupled from filesystem hierarchy.

## Run configurations are fully materialized before execution

Persisted run configurations SHOULD represent resolved executable runtime contracts rather than partially specified execution templates.

Runtime auto-resolution SHOULD occur before execution begins.

## Filesystem paths are canonical provenance identifiers

Filesystem paths preserve immutable operational provenance.

Transient operational IDs SHOULD remain convenience handles rather than canonical scientific identifiers.

## Decision, sampling, and execution variables are distinct

Decision variables alter policy meaning.

Sampling variables alter statistical estimation.

Execution variables alter runtime behavior.

These variable classes SHOULD remain conceptually distinct throughout the ROOST architecture.

---

# Design Non-Goals

ROOST is NOT intended to:

* Treat sessions as primary scientific result entities
* Collapse experiments directly into filesystem structure
* Conflate execution provenance with scientific interpretation
* Optimize only for deterministic single-plan analysis
* Treat all hierarchy levels as semantically identical
* Restrict experiments to single-case analysis
* Treat transient operational IDs as stable scientific identifiers
* Conflate runtime observations with structural run identity

---

# Design Philosophy

ROOST treats retirement planning as a **sequential decision problem**:

* Decisions are agent-controlled
* They are revisited annually
* Outcomes unfold under uncertainty
* Policies are evaluated across many plausible futures for robustness, not just optimality
* Runs statistically evaluate policy behavior across stochastic realizations
* Experiments organize scientific comparison and interpretation
* Sessions preserve execution provenance and support incremental exploration over time

Rather than asking:

> *“What is the single optimal plan?”*

ROOST instead helps answer:

> *“Which decision policies perform well across many plausible futures—and how much flexibility do I really have?”*

---

# Future Directions

ROOST is evolving toward support for:

* Cross-household generalization studies
* Merge-compatible run analysis
* Structural equivalence analysis
* Sampling strategy evaluation
* Statistical estimator comparison
* Experiment overlays and logical grouping systems
* Reproducible scientific experiment management
* Computational complexity and runtime-behavior analysis
* Operational deduplication and cleanup workflows
* Advanced reporting and comparative visualization workflows

---

# Relationship to OWL

* **OWL** computes optimal strategies for a given case
* **ROOST** evaluates, compares, and studies retirement decision policies under uncertainty

ROOST builds on OWL’s optimization engine by providing the conceptual structure, stochastic simulation framework, scientific organization model, and tooling needed to explore retirement decisions as they are actually faced:

* Sequentially
* Under uncertainty
* Across many plausible futures
* With multiple competing policy alternatives under consideration
* With reproducible scientific experimentation and statistical evaluation

## Studies and Study Templates

ROOST is evolving toward a **methodology-oriented analytical architecture** in which studies represent reusable analytical frameworks layered on top of the canonical operational execution hierarchy.

Conceptually:

```text
Study Template
    ↓
Study Instantiation
    ↓
Session Materialization
    ↓
Run and Trial Execution
    ↓
Statistical Aggregation
    ↓
Scientific Interpretation and Reporting
```

Studies are intended to organize and operationalize structured analytical methodologies rather than merely group related runs.

This direction extends ROOST beyond simple parameter sweeps into a broader framework for:

* Retirement decision analysis
* Uncertainty and sampling analysis
* Runtime and execution-behavior analysis
* Cross-household comparative studies
* Scientific methodology evaluation
* Statistical convergence and estimator analysis

---

# Studies

A **study** defines a structured analytical investigation over one or more related dimensions of variation.

Studies organize:

* Scientific intent
* Variable exploration strategies
* Comparison methodologies
* Aggregation semantics
* Reporting structure
* Interpretation workflows

Conceptually:

```text
Study → Structured Interpretation of Related Runs
```

A study answers questions such as:

> *“What analytical methodology or scientific question are we exploring?”*

Examples include:

* Social Security timing analysis
* Spending flexibility analysis
* Roth conversion strategy comparison
* Historical vs bootstrap sampling analysis
* Worker scaling and runtime efficiency analysis
* Cross-household generalization analysis
* Statistical convergence analysis

Studies are:

* Logical rather than operational
* Methodological rather than provenance-oriented
* Potentially cross-session and cross-case
* Defined independently from filesystem hierarchy

Studies operate as analytical overlays on top of sessions, runs, and trials.

---

# Study Templates

A **study template** defines a reusable analytical methodology capable of generating studies and their associated execution sessions automatically.

Study templates may define:

* Decision variable sweeps
* Sampling variable sweeps
* Execution variable sweeps
* Comparison structures
* Aggregation methodologies
* Reporting templates
* Visualization workflows
* Runtime execution requirements

Conceptually:

```text
Study Template → Reusable Analytical Methodology
```

A study template may therefore operationalize an analytical workflow such as:

```text
Explore retirement age sensitivity
    across:
        retirement ages
        market sampling methods
        uncertainty realizations
```

or:

```text
Evaluate runtime scaling behavior
    across:
        workers_per_run
        thread allocation
        solver configurations
```

Study templates are intended to support automated workflows in which ROOST can:

* Instantiate studies from reusable methodologies
* Automatically generate sessions
* Materialize runs and trials
* Infer comparison dimensions
* Generate reports and dashboards
* Organize scientific interpretation

For example:

```text
roost study create retirement-age \
    --cases case_alex.toml
```

may eventually:

* Instantiate a retirement-age study
* Generate required sessions automatically
* Expand decision and sampling sweeps
* Produce Quarto reporting structure
* Generate comparison and summary reports

---

# Relationship to Variable Classes

Study semantics are strongly informed by the classes of variables being explored.

ROOST distinguishes between:

| Variable Class      | Analytical Meaning                    |
| ------------------- | ------------------------------------- |
| Decision variables  | Retirement policy exploration         |
| Sampling variables  | Uncertainty and estimator exploration |
| Execution variables | Runtime and computational exploration |

This distinction allows ROOST to support multiple categories of studies within a unified framework.

Examples include:

| Study Type             | Primary Variable Classes |
| ---------------------- | ------------------------ |
| Retirement policy      | Decision variables       |
| Sampling analysis      | Sampling variables       |
| Runtime scaling        | Execution variables      |
| Methodology comparison | Mixed variable classes   |

ROOST may eventually use variable-class distinctions to automatically infer:

* Study categories
* Comparison methodologies
* Aggregation semantics
* Visualization strategies
* Reporting structures
* Suggested analytical workflows

---

# Relationship to Sessions

Studies and sessions serve fundamentally different purposes.

| Concept | Primary Role                             |
| ------- | ---------------------------------------- |
| Session | Operational execution provenance         |
| Study   | Scientific and analytical interpretation |

Sessions preserve:

* Execution history
* Runtime provenance
* Recovery and continuation state
* Materialized execution outputs

Studies organize:

* Analytical intent
* Scientifically related runs
* Comparative methodologies
* Aggregated interpretation

A single study may span:

* Multiple sessions
* Multiple dates
* Multiple execution environments
* Multiple cases/households

while a single session may contribute evidence to multiple studies.

Studies therefore operate as logical analytical overlays on top of the canonical operational hierarchy:

```text
Case → Session → Run → Trial
```

without altering filesystem provenance structure.

---

# Future Direction

ROOST is likely to evolve toward a study-centered analytical workflow in which:

* Study templates become reusable analytical methodologies
* Studies become the primary scientific organization layer
* Sessions remain operational execution containers
* Runs remain the primary scientific comparison unit
* Trials remain primitive stochastic observations

This direction supports both:

* Household-specific retirement analysis
  and
* Cross-household scientific generalization

while also supporting:

* Operational runtime studies
* Computational scaling analysis
* Sampling and convergence evaluation
* Statistical methodology exploration

within a unified conceptual architecture.

## Reproducible Study Workflows

ROOST is evolving toward a workflow-oriented analytical architecture in which studies and study templates operationalize reproducible analytical methodologies layered on top of the canonical execution hierarchy.

Conceptually:

```text
Study Template
    ↓
Study Instantiation
    ↓
Session Materialization
    ↓
Run and Trial Execution
    ↓
QA/QC Validation
    ↓
Scientific Interpretation and Reporting
```

Study templates are intended to define reusable analytical workflows rather than merely reusable reports.

A study template may define:

* Decision, sampling, and execution sweeps
* Session generation strategies
* Runtime execution defaults
* QA/QC validation requirements
* Comparison methodologies
* Aggregation semantics
* Starter visualizations and reports
* Publication-oriented reporting scaffolds

A study instantiation may therefore generate:

* One or more execution sessions
* Session orchestration notebooks (`study-run.qmd`)
* QA/QC validation notebooks (`study-qaqc.qmd`)
* Starter analytical reports (`study-start.qmd`)
* Derived dashboards, figures, and publication artifacts

This architecture intentionally separates:

| Layer              | Purpose                                     |
| ------------------ | ------------------------------------------- |
| `results/`         | Immutable operational execution evidence    |
| `studies/`         | Curated analytical interpretation workflows |
| `templates/study/` | Reusable analytical methodologies           |

Studies are expected to support workflows ranging from:

* Household-specific retirement guidance
  to
* Cross-household scientific generalization
  to
* Runtime and computational scaling analysis

within a unified reproducible analytical framework.

Long-term architectural direction is expected to shift scientific organization from experiment-oriented overlays toward study-oriented analytical methodologies layered over operational execution provenance.
