# ROOST Retirement Reporting and Decision-Support Notes

This document supplements the main ROOST alignment document and focuses specifically on retirement reporting, progress tracking, and household decision support.

## Core Observation

ROOST is not intended to become an accounting system.

The goal is not transaction tracking, budgeting, reconciliation, or personal bookkeeping.

Instead, ROOST should help retirees:

* Understand their current financial position.
* Measure long-term retirement progress.
* Evaluate future decisions.
* Build confidence in retirement spending.

The preferred model is periodic balance-sheet snapshots rather than transaction history.

---

## Historical Snapshot Concept

A lightweight historical snapshot may be collected for:

* Current year
* 5 years ago
* 10 years ago

Preferred date:

* January 1

Minimum data:

* taxable_savings_balances
* tax_deferred_savings_balances
* tax_free_savings_balances

Optional:

* hsa_savings_balances
* total_fixed_assets
* total_liabilities

The objective is to reconstruct household balance sheets, not historical accounting records.

---

## Annual Retirement Management Workflow

### Beginning of Year

Gather current balances and assets.

Generate:

* Balance sheet
* Retirement outlook
* Decision recommendations

Examples:

* Roth conversion strategy
* Asset allocation changes
* Cash reserve targets
* Spending targets

### Mid-Year / Fall Review

Refresh balances.

Re-run OWL.

Evaluate:

* Year-end Roth conversions
* Tax opportunities
* Spending adjustments
* Updated outlook

### Repeat Annually

ROOST operates on periodic snapshots rather than detailed financial transactions.

---

## Five-Year and Ten-Year Decision Horizons

Future decision support should emphasize:

* 5-year projections
* 10-year projections

rather than relying exclusively on end-of-life metrics.

Rationale:

* Easier for retirees to understand.
* More actionable.
* Less sensitive to longevity assumptions.
* Better suited for comparing alternatives.

End-of-life outcomes remain useful but should not be the primary user-facing decision framework.

---

## P10 / P50 / P90 Thinking

Future projections should generally be expressed as distributions rather than point estimates.

Important views:

* P10
* P50
* P90

This aligns naturally with ROOST's stochastic architecture.

Potential scenario dimensions include:

* Bootstrap samples
* Historical windows
* Inflation regimes
* Market regimes

The goal is to evaluate decision robustness rather than predict a single future.

---

## Historical + Future Timeline Concept

A useful report structure combines:

* Historical observations
* Current state
* Future projections

Example:

| Date         |       P10 |   Central |       P90 |
| ------------ | --------: | --------: | --------: |
| 10 years ago |           |  observed |           |
| 5 years ago  |           |  observed |           |
| Today        |           |  observed |           |
| +5 years     | projected | projected | projected |
| +10 years    | projected | projected | projected |

Historical rows contain facts.

Future rows contain uncertainty ranges.

This creates a unified timeline spanning past, present, and future.

---

## Net Worth Caveat

Net worth is useful because:

* Users understand it.
* It can be verified from statements.
* It supports balance-sheet reporting.

However, net worth is not the retirement objective.

A declining net worth may represent successful retirement execution.

Care should be taken not to imply that preserving or maximizing net worth is the primary retirement goal.

---

## Essential vs Lifestyle Spending

Future retirement reporting may distinguish between:

### Essential Spending

Minimum spending required to maintain the household.

Examples:

* Housing
* Utilities
* Insurance
* Healthcare
* Taxes
* Food
* Transportation

### Lifestyle Spending

Desired spending level that supports the retiree's preferred lifestyle.

Examples:

* Travel
* Dining
* Hobbies
* Gifting
* Entertainment

This separation may provide a more meaningful measure of retirement success than net worth alone.

---

## Candidate Decision-Support Metrics

Potentially more meaningful than net worth:

* Spending capacity
* Essential spending coverage
* Lifestyle spending coverage
* Funding ratio
* Retirement surplus

These metrics align more closely with retirement objectives and may reduce anxiety caused by declining portfolio balances.

---

## Reporting Philosophy

Balance sheets remain important because they provide a verifiable representation of household state.

The primary purpose of reporting should be:

* Understanding progress.
* Evaluating decisions.
* Measuring robustness.
* Supporting confident spending.

The long-term objective is not maximizing wealth.

The objective is helping retirees convert accumulated wealth into a secure and enjoyable retirement.
