# Contributing to ROOST

Thank you for your interest in contributing to ROOST.

ROOST (Retirement Options and Outcomes Studies Tool) is an open-source platform for retirement policy analysis, stochastic simulation, reproducible studies, and comparative evaluation of retirement decision strategies under uncertainty.

ROOST builds upon OWL while extending retirement analysis into a broader framework for:

* Retirement policy evaluation
* Stochastic simulation and uncertainty analysis
* Reproducible scientific workflows
* Comparative study design
* Statistical aggregation and reporting
* Execution provenance and introspection
* Cross-household and cross-policy research

We welcome contributions that improve the software, documentation, testing, study methodologies, reporting capabilities, and overall research ecosystem.

---

# Project Philosophy

ROOST is designed around several long-term principles:

* Reproducibility over convenience
* Explicit provenance over hidden state
* Scientific transparency over black-box behavior
* Open research and collaboration
* Clear separation of operational and analytical concerns
* Respect for backwards compatibility whenever practical

Contributors are encouraged to preserve these principles when proposing changes.

---

# Development Setup

Create a development environment:

```bash
uv sync --extra dev
```

Install repository hooks:

```bash
uv run pre-commit install
```

Run all configured checks:

```bash
uv run pre-commit run --all-files
```

---

# Running Tests

Run the full test suite:

```bash
uv run pytest
```

Run a specific test module:

```bash
uv run pytest tests/path/to/test_file.py
```

Contributors are encouraged to add tests for new functionality whenever practical.

---

# Code Style

ROOST uses automated tooling to maintain consistency.

Before submitting changes, run:

```bash
uv run pre-commit run --all-files
```

This may automatically:

* format source files
* normalize whitespace
* validate repository structure
* run linting and static checks

---

# Documentation

Documentation is considered a first-class part of the project.

Contributions are welcome in:

* README improvements
* User documentation
* Architecture documentation
* Study methodology documentation
* Tutorials and examples
* API documentation

Substantial new functionality should generally include corresponding documentation updates.

---

# Research and Study Contributions

ROOST is evolving toward a study-oriented analytical workflow.

Contributions may include:

* Study templates
* Reporting workflows
* Statistical methodologies
* Visualization improvements
* Comparative analysis tooling
* Reproducibility enhancements

When contributing analytical methodologies, please describe:

* the scientific question being addressed
* assumptions and limitations
* expected outputs
* validation approaches

---

# Issues and Feature Requests

Bug reports and feature requests are welcome.

When reporting issues, please include:

* ROOST version
* operating system
* reproduction steps
* expected behavior
* observed behavior

If possible, include a minimal reproducible example.

---

# Licensing

ROOST is licensed under the GNU General Public License version 3 or later (GPL-3.0-or-later).

By submitting a contribution, you certify that:

1. You have the legal right to submit the contribution.
2. The contribution may be distributed under the project's GPL-3.0-or-later license.
3. You understand that your contribution may become part of future ROOST releases.

Contributors retain copyright ownership of their contributions.

---

# Attribution

All contributors are appreciated and acknowledged.

Contributions may include:

* source code
* documentation
* testing
* study methodologies
* bug reports
* design discussions
* examples and tutorials

Thoughtful feedback is a valuable contribution.

---

# Questions

If something is unclear:

* open an issue
* start a discussion
* ask in a pull request

Research software grows through collaboration, curiosity, and careful review.

Thank you for helping improve ROOST.
