# ROOST Catalog Architecture

The `catalog/` subsystem provides the provenance, introspection, lineage, and semantic navigation infrastructure for ROOST.

The catalog is intentionally designed as a metadata and relationship layer built on top of the existing ontology and execution architecture documented in the top-level `README.md`.

This document complements the main architecture document and focuses specifically on:

* Semantic ownership
* Variable lineage
* Projection tracing
* Provenance indexing
* Cross-registry navigation
* Runtime realization tracing
* Analytical introspection workflows

The catalog is intended to make the internal architecture of ROOST observable, queryable, explainable, and operationally navigable.

---

# Architectural Context

ROOST distinguishes between multiple semantic ontology layers:

| Registry            | Responsibility                                  |
| ------------------- | ------------------------------------------------ |
| `schema/`           | Executable configuration ontology                |
| `metrics/`          | Observable output ontology                       |
| `display/`          | Analytical projection ontology                   |

These registries intentionally remain separate.

The catalog subsystem does NOT replace these registries.

Instead, the catalog provides:

```text
cross-registry provenance and introspection infrastructure
```

layered on top of them.

---

# Primary Responsibilities

The catalog subsystem is responsible for:

* Variable ownership tracing
* Source-file discovery
* Projection lineage
* Override lineage
* Runtime materialization tracing
* Aggregation lineage
* Report and view usage discovery
* Provenance indexing
* Explainability support
* Architectural introspection
* Developer navigation workflows

The catalog acts as the semantic navigation and provenance graph layer of ROOST.

---

# Conceptual Role

Conceptually:

```text
semantic ontology
    ↓
projection layers
    ↓
runtime realization
    ↓
aggregation
    ↓
analytical overlays
    ↓
reporting
```

The catalog indexes and traces relationships across this entire pipeline.

---

# Architectural Invariants

The following concepts are foundational to the catalog architecture and SHOULD remain stable unless intentionally redesigned.

---

## Registries Remain Layered

The catalog MUST NOT collapse or replace the existing ontology registries.

The following architectural layering is intentional:

| Layer      | Role                               |
| ---------- | ---------------------------------- |
| `schema/`  | Executable ontology                |
| `metrics/` | Observable ontology                |
| `display/` | Analytical ontology                |
| `catalog/` | Provenance and introspection graph |

The catalog exists to connect and explain these layers rather than merge them.

---

## Schema Registry Owns Executable Semantics

The schema registry remains authoritative for:

* Executable input semantics
* Hydra sweep generation
* Runtime configuration ontology
* Runtime materialization semantics

The catalog MUST treat the schema registry as the canonical executable ontology source.

The catalog MUST NOT weaken or partially replicate schema coverage.

---

## Metrics Registry Owns Observable Semantics

The metrics registry remains authoritative for:

* Runtime observations
* Aggregation semantics
* Statistical outputs
* Metric interpretation

The catalog MAY trace metric lineage and aggregation provenance but MUST NOT redefine metric semantics independently.

---

## Display Registry Owns Analytical Projection

The display registry remains renderer-facing and analytical.

Display fields MAY:

* Override labels
* Define formatting
* Define grouping semantics
* Synthesize analytical overlays

but SHOULD NOT become canonical semantic authorities.

The catalog MUST preserve distinction between:

* Canonical semantic ownership
  and
* Analytical presentation overlays

---

## Operational Realization Remains Separate

ROOST intentionally separates semantic definitions from operational runtime realization.

Canonical runtime dataset structures currently distinguish between:

| Runtime Component | Meaning                                     |
| ----------------- | ------------------------------------------- |
| `_inputs`         | Materialized executable configuration       |
| `_metrics`        | Runtime observations and aggregation        |
| `_meta`           | Operational metadata and transient identity |
| `_paths`          | Filesystem provenance                       |

The catalog MUST preserve this distinction.

The catalog indexes runtime realization.

It does NOT replace runtime realization.

---

## Filesystem Paths Remain Canonical Provenance Identifiers

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

## Semantic Projection and Hierarchical Projection Are Distinct

ROOST distinguishes between:

| Projection Type         | Meaning                                       |
| ----------------------- | --------------------------------------------- |
| Semantic projection     | Registry-to-display analytical projection     |
| Hierarchical projection | Trial/run/session/case aggregation projection |

These are separate architectural concepts.

The catalog SHOULD preserve this distinction explicitly.

---

## Provenance Is First-Class

The catalog treats provenance as a foundational architectural concern.

Provenance includes both:

* Operational provenance
* Semantic provenance

Examples include:

* Variable origin registry
* Runtime storage location
* Source-file ownership
* Aggregation lineage
* Display override lineage
* Runtime discovery lineage
* Hydra generation provenance
* Report and view usage
* Runtime realization paths

The catalog exists primarily to preserve and expose these relationships.

---

# Catalog Responsibilities

The catalog subsystem is expected to evolve toward support for:

| Capability            | Description                             |
| --------------------- | --------------------------------------- |
| Ownership tracing     | Which registry owns a variable          |
| Source tracing        | Which file or plugin defines a variable |
| Projection tracing    | How variables flow across layers        |
| Override tracing      | Which overlays modify behavior          |
| Aggregation lineage   | How metrics are synthesized             |
| Runtime lineage       | How variables materialize operationally |
| Usage tracing         | Which views/reports reference variables |
| Explainability        | Human-readable provenance explanations  |
| Introspection         | Developer navigation and debugging      |
| Structural comparison | Variable-aware equivalence tracing      |

---

# Catalog Philosophy

The catalog is intentionally metadata-oriented rather than execution-oriented.

It SHOULD:

* Explain architecture
* Expose relationships
* Preserve provenance
* Improve discoverability
* Support explainability
* Support reporting workflows
* Support study-generation workflows
* Support developer navigation

The catalog SHOULD NOT:

* Become a replacement runtime datastore
* Become the canonical semantic authority
* Collapse ontology layers
* Duplicate registry semantics unnecessarily
* Replace runtime execution metadata
* Replace filesystem provenance

---

# Catalog and Explainability

The catalog is expected to become the foundation of future explainability systems.

Conceptually:

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

The catalog SHOULD support tracing across this entire chain.

This explainability architecture is foundational to:

* Reporting
* QA/QC validation
* Study generation
* Reproducibility
* Provenance analysis
* Runtime debugging
* Merge compatibility analysis
* Structural comparison workflows

---

# Catalog and Developer Tooling

The catalog is expected to support future developer and CLI workflows such as:

```text
roost vars show <variable>
roost vars where <variable>
roost vars lineage <variable>
roost vars views <variable>
roost vars reports <variable>
roost vars overrides <variable>
roost vars trace <variable>
```

These workflows are intended to provide:

* Jump-to-definition navigation
* Provenance inspection
* Projection tracing
* Report introspection
* Aggregation explainability
* Runtime realization tracing

---

# Metadata-Enriched Architecture

ROOST is evolving toward a metadata-rich analytical architecture in which:

* Semantic ontologies remain explicitly layered
* Runtime realization remains operationally reproducible
* Analytical overlays remain logically separated
* Provenance remains queryable across all layers
* Study workflows become increasingly automated
* Reporting becomes increasingly introspectable

The catalog subsystem is expected to become the central provenance and introspection layer enabling these workflows.

---

# Long-Term Direction

The catalog architecture is expected to evolve toward:

* Provenance graph indexing
* Cross-study introspection
* Automated explainability generation
* Variable-aware reporting systems
* Projection-aware lineage tracing
* Structural equivalence analysis
* Merge-compatibility analysis
* Study-template introspection
* Runtime execution introspection
* Publication-oriented provenance reporting

The catalog therefore serves as:

```text
the semantic navigation and provenance graph layer of ROOST
```

rather than merely a metadata utility subsystem.
