# OWL-ROOST

**Retirement Options and Outcomes Studies Tool**

**ROOST** (Retirement Options and Outcomes Studies Tool) evaluates **retirement decision policies**—not just static plans—by comparing how **agent-controlled actions** perform under **uncertainty** when those decisions are revisited annually.

ROOST is designed to answer questions like:

> *“Given the uncertainty I face, how flexible are my retirement decisions—and which decision policies are most robust?”*

It does this by organizing retirement analysis around a small number of clear, orthogonal concepts.

## Core Concepts

ROOST introduces seven key concepts in extending the work of OWL.

* **Decision options** define *what question is being asked*
* **Choice templates** define *policy alternatives*
* **Cases** define *initial conditions and constraints*
* **Experiments** define *how runs are generated and organized*
* **Runs** define *a fixed decision policy applied to a case*
* **Trials** define *individual realizations of uncertainty*
* **Results** provide *evidence for comparison and insight*

Cases and runs are shared between OWL and ROOST. They are represented by exactly the same files and outputs.

### Experiments

An **experiment** defines a structured method for generating and organizing runs for a given case.

Conceptually:

```
Case × Experiment → Many Runs
```

An experiment answers the question:

> *“How are we exploring this decision or uncertainty dimension?”*

Experiments may:

* Systematically vary a decision parameter (e.g., Social Security claiming age)
* Sweep across a family of choice templates
* Enumerate historical market regimes (e.g., roll/reverse of historical slices)
* Explore timing variations such as retirement age
* Stress-test exogenous assumptions

Experiments do **not** change what a run is.
They define how multiple runs are constructed and grouped under a single research objective.

## Design Philosophy

ROOST treats retirement planning as a **sequential decision problem**:

* Decisions are agent-controlled
* They are revisited annually
* Outcomes unfold under uncertainty
* Policies are evaluated across many plausible futures for robustness, not just optimality
* Experiments systematically generate structured sets of runs for comparison

Rather than asking *“What is the single optimal plan?”*, ROOST helps answer:

> *“Which decision policies perform well across many plausible futures—and how much flexibility do I really have?”*

## Relationship to OWL

* **OWL** computes optimal strategies for a given case
* **ROOST** compares decision policies across cases and uncertainty to understand trade-offs, robustness, and flexibility

ROOST builds on OWL’s optimization engine by providing the conceptual structure and tooling needed to explore retirement decisions as they are actually faced: sequentially, under uncertainty, and with multiple plausible decision policies under consideration.
