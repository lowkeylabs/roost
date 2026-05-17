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

```text id="zlfhqb"
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

# Statistical and Scientific Model

ROOST distinguishes between:

* **Decision variables** that define retirement policies and strategies
* **Sampling variables** that control stochastic exploration
* **Execution variables** that control runtime and infrastructure behavior

Examples include:

| Variable Type       | Examples                                                          |
| ------------------- | ----------------------------------------------------------------- |
| Decision variables  | Roth conversion strategy, Social Security timing, spending policy |
| Sampling variables  | random seed, trial count, bootstrap selection                     |
| Execution variables | workers per run, math library threads, solver thread counts       |

This distinction is central to ROOST’s architecture.

Changing a decision variable creates a scientifically different policy evaluation.

Changing a sampling or execution variable may produce a different estimate or execution profile while still evaluating the same underlying policy.

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

```text id="b2cwyt"
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

This allows ROOST to evaluate policies for robustness across many plausible futures rather than optimizing against a single deterministic scenario.

---

# Experiments

An **experiment** defines a structured scientific exploration for a given decision or uncertainty dimension.

Conceptually:

```text id="jlwmr8"
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

Experiments therefore act as scientific overlays that organize and interpret related runs under a common research objective.

Experiments do **not** define filesystem structure.

They define scientific meaning.

---

# Sessions

A **session** represents a specific execution event in which ROOST generates and/or evaluates runs for a case.

Conceptually:

```text id="jlwm7d"
Case × Session → Runs
```

Sessions are operational rather than scientific.

They organize:

* Generated outputs
* Logs and metadata
* Runtime provenance
* Execution history
* Recovery and continuation state

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

# Filesystem vs Scientific Structure

ROOST intentionally separates:

* Operational filesystem organization
  from
* Scientific experiment organization

Filesystem hierarchy primarily reflects execution provenance:

```text id="jlwm6r"
Case → Session → Run → Trial
```

Scientific organization is logical and overlay-based:

```text id="n5a4bz"
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

# Generalization and Cross-Case Studies

Although many retirement studies focus on a single household, ROOST is also designed to support broader comparative analysis across multiple cases.

Experiments may explore questions such as:

* Do retirement strategies generalize across different households?
* Which policies remain robust across varying balance structures?
* How sensitive are outcomes to demographic differences?
* Which optimization strategies scale consistently across cases?

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
* Sampling strategy evaluation
* Statistical estimator comparison
* Experiment overlays and logical grouping systems
* Reproducible scientific experiment management
* Computational complexity and runtime-behavior analysis
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
