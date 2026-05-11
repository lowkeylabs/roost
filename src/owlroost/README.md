
# OWL-ROOST Architecture

This directory contains the current implementation of OWL-ROOST.

The roost system is a **clean, schema-driven, layered, test-first design** with the goals of:

- eliminating unnecessary module couplings
- unifying inputs, outputs, and derived values under a single semantic model
- separating semantic meaning from presentation
- simplifying reasoning about experiments, runs, and trials
- enabling transparent analytics, display, and reporting
- supporting reproducible and testable experiment pipelines


# Core Principles

## 1. Schema is the semantic foundation

Everything in the system—inputs, outputs, derived values, runtime values—is represented as **schema fields**.

There is no distinction between:

- "input fields"
- "metrics"
- "computed values"
- "runtime outputs"

All are:

> **Fields defined in a unified schema registry**

The schema registry defines:

- field identity
- types
- provenance
- extraction paths
- compute functions
- defaults
- semantic metadata

The schema layer does **not** own rendering or presentation behavior.


## 2. Display is layered on top of schema

Display behavior is intentionally separated from schema semantics.

The display subsystem:

- references schema fields
- adds presentation metadata
- organizes fields into reusable groups and views
- materializes tables/pivots
- renders output for CLI and reports

This separation prevents:

- coupling semantic meaning to rendering
- renderer-specific logic leaking into schema
- duplication of schema metadata

Architecture:

```text
SchemaRegistry
    ↓
DisplayRegistry
    ↓
Groups / Views
    ↓
Materialization
    ↓
RoostTable
    ↓
Renderers
````

## 3. Layer-aware data model

Roost operates across multiple semantic layers:

```text
Case
  ↓
Experiment
  ↓
Run
  ↓
Trial
```

Each layer represents a different dataset abstraction:

| Layer      | Row Represents            |
| ---------- | ------------------------- |
| case       | one TOML case file        |
| experiment | one experiment directory  |
| run        | one parameterized run     |
| trial      | one stochastic simulation |

Views are registered against a specific layer.

## 4. Pure data pipeline

The system is a pipeline:

```text
Case → Experiment → Run → Trial → Outputs → Aggregation → Display → Reporting
```

Each stage:

* consumes structured data
* produces structured data
* does not depend on presentation concerns

## 5. Functional core, thin orchestration

* Core logic is pure and testable
* Side effects (filesystem, CLI, Hydra, rendering) are isolated
* CLI commands are orchestration layers only

## 6. Test-driven development (TDD)

All features are introduced via tests:

1. write failing test
2. implement minimal code
3. make test pass
4. refactor
5. repeat

Legacy tests are used as behavioral references only.

# Top-Level Modules

```text
owlroost/
  schema/        ← semantic field system (foundation)
  display/       ← views, groups, materialization, rendering
  hydra/         ← Hydra-facing experiment generation
  core/          ← execution + metrics extraction
  cli/           ← command-line interface (thin wrappers)
  tools/         ← validation and developer tooling
```

Additional modules may emerge as the v2 architecture stabilizes.

# Semantic vs Presentation Layers

## Semantic Layer (`schema/`)

Defines:

```text
FieldSpec
```

A schema field represents semantic meaning only.

Responsibilities:

* identity
* typing
* extraction
* defaults
* provenance
* compute functions

## Presentation Layer (`display/`)

Defines:

```text
DisplayField
DisplayProfile
DisplayGroup
ViewSpec
```

Presentation is layered on top of schema fields.

Responsibilities:

* labels
* formatting
* alignment
* explanations
* visibility
* aggregation presentation
* table/pivot behavior

# Module Responsibilities

## schema/

> The semantic foundation of roost.

Defines the `SchemaRegistry`.

### Responsibilities

* register fields
* define semantic metadata
* unify:

  * TOML inputs
  * runtime values
  * OWL outputs
  * derived/computed values
* support:

  * compute functions
  * runtime defaults
  * provenance tracking

### Key concepts

```text
FieldSpec
    semantic definition of a field
```

Example:

```text
FieldSpec = {
  name,
  dtype,
  source,
  path,
  compute_fn,
  default,
}
```

## display/

> Presentation and dataset exploration system.

Defines the `DisplayRegistry`.

### Responsibilities

* define display fields
* define reusable display groups
* define layer-aware views
* support:

  * table mode
  * pivot mode
* materialize:

  * RoostTable
* render:

  * rich
  * markdown
  * latex
  * html (future)

### Key concepts

```text
DisplayField
    presentation configuration for a schema field

DisplayProfile
    mode-specific presentation behavior

DisplayGroup
    reusable bundle of display fields

ViewSpec
    ordered composition of groups + fields
```

### Display modes

Current display modes:

* `table`
* `pivot`

Important:

> "pivot" refers only to row/column orientation,
> not OLAP/database pivot semantics.

### Display profiles

A field may render differently depending on mode.

Example:

| Mode  | Label                     |
| ----- | ------------------------- |
| table | `P90`                     |
| pivot | `90th Percentile Runtime` |

Profiles may define:

* labels
* formatting
* alignment
* wrapping
* explanations
* visibility

## hydra/

> Experiment/run/trial generation.

Transforms:

```text
case.toml + overrides → experiments → runs → trials
```

### Responsibilities

* interpret override space
* expand experiments into runs
* generate trial configurations
* manage Hydra integration
* write effective configuration artifacts

### Notes

Hydra is an implementation tool—not the core architecture model.

## core/

> Trial execution and metrics extraction.

### Responsibilities

* execute OWL planner
* normalize outputs
* capture metrics
* enforce consistent failure handling
* produce structured outputs

### Output

```text
trial_result = {
  inputs: {...},
  outputs: {...},
  metadata: {...}
}
```

## cli/

> Thin orchestration layer.

### Responsibilities

* parse commands/options
* select datasets
* select views
* invoke display/materialization
* invoke execution pipeline

### No business logic

CLI commands should contain minimal logic.

# Display Architecture

## Views

Views are:

> ordered compositions of fields and groups

Views are registered against a specific layer:

```text
trial
run
experiment
case
```

Examples:

```text
run/default
run/timing
trial/audit
case/build
```

## Groups

Groups are reusable display bundles.

A group may define:

* fields
* aggregates
* display hints
* visibility rules

Groups support different behavior in:

* table mode
* pivot mode

## Materialization

Materialization transforms:

```text
dataset + view + mode
```

into:

```text
RoostTable
```

This layer handles:

* aggregate expansion
* field resolution
* pivot orientation
* profile selection
* visibility filtering

## Renderers

Renderers are intentionally dumb.

Responsibilities:

* render `RoostTable`
* no schema logic
* no aggregation logic
* no dataset logic

Current renderers:

* rich
* markdown
* latex

Future:

* html
* dashboard
* API serializers

# Data Flow

```text
case.toml
   ↓
hydra/planner
   ↓
experiments / runs / trials
   ↓
trial execution
   ↓
trial outputs + metrics
   ↓
aggregation
   ↓
display materialization
   ↓
RoostTable
   ↓
renderers / reports / CLI
```

# Command Model

Commands naturally operate at different dataset layers.

| Command       | Primary Layer            |
| ------------- | ------------------------ |
| `cmd_build`   | case                     |
| `cmd_run`     | run                      |
| `cmd_results` | run / trial / experiment |
| `cmd_report`  | any                      |

Each command defines default views appropriate for its layer.

# Testing Strategy

## Active tests

Located in:

```text
tests/
```

Focus on:

* schema correctness
* display materialization
* aggregation correctness
* renderer behavior
* experiment generation
* execution correctness
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
* use only as migration reference

The directory will be removed after stabilization.

# Development Workflow

1. write failing test
2. implement minimal code
3. make test pass
4. refactor
5. repeat

# End State

* single clean codebase (`owlroost/`)
* unified semantic field model
* layered display architecture
* reusable views/groups/profiles
* minimal coupling between layers
* reproducible and testable experiment pipeline
* shared display engine for:

  * CLI
  * reports
  * future APIs
