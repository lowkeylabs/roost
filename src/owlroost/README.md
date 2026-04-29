src/owlroost/README.md

# OWL-ROOST Architecture

This directory contains the current implementation of OWL-ROOST.

The roost system is a **clean, schema-driven, test-first design** with the goal of:

- eliminating unnecessary module couplings
- unifying inputs and outputs under a single schema model
- simplifying reasoning about experiments, runs, and trials
- enabling transparent analytics and reporting


# Core Principles

## 1. Schema is the foundation

Everything in the system—inputs, outputs, derived values—is represented as **schema fields**.

There is no distinction between:

- "input fields"
- "metrics"
- "computed values"

All are:

> **Fields defined in a unified schema registry**


## 2. Pure data pipeline

The system is a pipeline:

```text
Case → Experiment → Run → Trial → Outputs → Aggregation → Reporting
````

Each stage:

* consumes structured data
* produces structured data
* does not depend on presentation


## 3. Functional core, thin orchestration

* Core logic is **pure and testable**
* Side effects (filesystem, CLI, Hydra) are isolated


## 4. Test-driven development (TDD)

All features are introduced via tests:

* behavior first
* implementation second

Legacy tests (`tests_legacy/`) are used as reference only.


# Top-Level Modules

```text
owlroost/
  schema/        ← unified schema system (foundation)
  planner/       ← experiment/run/trial construction (Hydra-facing)
  trial/         ← execution layer (OWL integration)
  analytics/     ← metrics + aggregation
  reporting/     ← tables, views, QMD generation
  cli/           ← command-line interface (thin wrapper)
  io/            ← filesystem + serialization utilities
```


# Module Responsibilities

## schema/

> The most important module in roost.

Defines the **SchemaRegistry**, which unifies:

* TOML input fields
* OWL output fields
* derived/computed fields

### Responsibilities

* register fields
* define types and metadata
* support:

  * compute functions
  * aggregation behavior
  * display semantics

### Key concept

```text
Field = {name, type, source, compute_fn, aggregates, display}
```


## planner/

> Responsible for constructing experiments.

Transforms:

```text
case.toml + overrides → runs → trials
```

### Responsibilities

* interpret override space
* expand experiments into runs
* generate trial configurations
* write `_effective.toml`

### Notes

* replaces Hydra-dependent logic with a clean abstraction
* Hydra may still be used internally, but is not the model


## trial/

> Executes a single trial.

### Responsibilities

* run OWL planner
* capture outputs
* normalize results into schema-aligned structure
* handle failures consistently

### Output

```text
trial_result = {
  inputs: {...},
  outputs: {...},
  metadata: {...}
}
```


## analytics/

> Computes values across trials and runs.

### Responsibilities

* apply schema `compute_fn`
* aggregate trial results:

  * mean
  * median
  * percentiles
  * counts
* enforce invariants

### Output

```text
run_summary = {
  field_name: aggregated_value
}
```



## reporting/

> Converts structured data into human-readable outputs.

### Responsibilities

* table generation
* pivoting
* view definitions
* QMD generation

### Key idea

Reporting is:

> **a projection of schema fields—not custom logic**


## cli/

> Thin wrapper over the system.

### Responsibilities

* parse commands
* call into planner / analytics / reporting
* no business logic


## 💾 io/

> Handles filesystem and serialization.

### Responsibilities

* read/write TOML
* load/save JSON artifacts
* manage results directory structure


# 🔄 Data Flow

```text
case.toml
   ↓
planner
   ↓
runs / trials
   ↓
trial execution
   ↓
trial outputs (JSON + effective TOML)
   ↓
analytics
   ↓
aggregated run data
   ↓
reporting
   ↓
tables / reports / QMD
```


# Testing Strategy

## New tests (active)

Located in:

```text
tests/
```

Focus on:

* schema behavior
* planner correctness
* aggregation correctness
* end-to-end golden tests

## Legacy tests

Located in:

```text
tests_legacy/
```

Used for:

* behavioral reference only
* not executed in CI


# Legacy Code

The v1 implementation is located in:

```text
src/owlroost_v1/
```

Rules:

* do not import from it
* do not modify it
* use only for reference during migration

This directory will be removed after stabilization.

# Development Workflow

1. Write a failing test
2. Implement minimal code
3. Make test pass
4. Refactor
5. Repeat

# 🎯 End State

* single clean codebase (`owlroost/`)
* unified schema-driven model
* minimal coupling between layers
* reproducible, testable results pipeline


```

# Why this works

This README:

- locks in your **architecture direction**
- prevents drifting back into v1 patterns
- aligns perfectly with your goals (schema + metrics unification)
- is actionable for every next module you build
