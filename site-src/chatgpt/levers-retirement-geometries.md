---
title: levers
---


You’ve already separated:

* **Exogenous case structure** (what the household looks like)
* **Experiments** (how we generate runs)
* **Policies** (what decisions are taken)
* **Trials** (uncertainty realizations)

Now you’re asking:

> Given the exogenous variables in a case, how do we design **decision surface screens** that suggest where decision leverage exists?

That’s powerful.

This moves ROOST from:

> “Run experiments”

to:

> “Here’s where your decision surface is wide, narrow, fragile, or flat.”

---

# 1️⃣ First Principle: Screens Must Be Case-Driven

A decision screen should only appear if the **case structure implies a meaningful decision dimension**.

This is consistent with your structural threshold logic:

ROOST is only meaningful when there is:

* Multiple account types
* Timing optionality
* Withdrawal exposure
* Tax interaction

So the UI logic becomes:

```
Case structure → Detect decision dimensions → Offer screens
```

---

# 2️⃣ What Exogenous Variables Actually Matter?

From OWL case inputs, the relevant structural levers are:

### Timing Levers

* retirement_age
* social_security_ages
* longevity assumptions
* pension start

### Tax Structure

* pre_tax balances
* roth balances
* taxable balances
* marginal tax rates
* heirs_rate_on_tax_deferred_estate

### Spending Structure

* baseline spending
* discretionary flexibility
* minimum spending floor

### Portfolio Structure

* asset allocation
* return model selection
* withdrawal dependency

---

# 3️⃣ The Decision Surface Screen Concept

A decision surface screen should:

1. Identify a decision dimension
2. Sweep it
3. Measure:

   * Feasible width
   * Spending elasticity
   * Failure gradient
4. Present geometry summary

Each screen is essentially:

```
Case × Single Lever Sweep × Uncertainty → Surface Geometry
```

---

# 4️⃣ Core Decision Surface Screens

These are not experiments for exploration.
They are diagnostic instruments.

---

## 🔹 Screen 1: Retirement Timing Surface

Only show if:

* retirement_age is flexible
* wages > 0
* assets > threshold

Sweep:

* retirement_age from earliest feasible to latest feasible

Metrics:

* Sustainable spending vs retirement age
* Failure probability vs retirement age
* Gradient magnitude
* Feasible band width

Interpretation:

* Wide flat region → high flexibility
* Sharp drop-off → fragile
* Infeasible outside narrow band → constrained

Decision Support Direction:

> “Retirement timing is / is not a high-leverage decision for this case.”

---

## 🔹 Screen 2: Social Security Claiming Surface

Only show if:

* SS not already fixed
* Assets > threshold

Sweep:

* SS claiming age 62–70

Measure:

* Spending impact
* Failure probability shift
* Survivorship effects (if couple)

Decision Support Direction:

> “Claiming timing modestly affects robustness” or
> “Claiming age materially changes downside risk.”

---

## 🔹 Screen 3: Roth Conversion Elasticity Surface

Only show if:

* Pre-tax + Roth both present
* Taxable or wage flexibility exists

Sweep:

* Annual conversion target from 0 to threshold

Measure:

* Lifetime tax paid
* Failure probability
* Late-life net wealth
* IRMAA sensitivity

Decision Support Direction:

> “Conversion strategy meaningfully widens your robustness band” or
> “Tax strategy has marginal impact.”

---

## 🔹 Screen 4: Spending Robustness Surface

Sweep:

* Spending from floor to optimistic

Measure:

* Failure probability curve
* CVaR
* 10th percentile wealth

Compute:

* Spending buffer ratio
* Failure gradient

Decision Support Direction:

> “Your spending has 18% slack before risk rises sharply.”

---

## 🔹 Screen 5: Allocation Sensitivity Surface

Only show if:

* Portfolio funds spending
* Allocation is user-controlled

Sweep:

* Equity allocation from 30–90%

Measure:

* Early failure probability
* Worst 10% drawdown impact
* Terminal dispersion

Decision Support Direction:

> “Allocation risk dominates timing decisions” or
> “Allocation changes produce small robustness differences.”

---

# 5️⃣ Structural Detection Logic

Before offering screens, ROOST could compute a simple **Decision Surface Eligibility Map**.

Example:

| Condition                            | Enable Screen     |
| ------------------------------------ | ----------------- |
| Wage > 0 & retirement_age flexible   | Retirement screen |
| SS flexible                          | SS screen         |
| Pre-tax + Roth                       | Conversion screen |
| Portfolio withdrawals > 40% spending | Allocation screen |
| Spending adjustable                  | Spending screen   |

This keeps ROOST targeted and clean.

---

# 6️⃣ Geometry Summary Output

Each screen should summarize:

* Feasible Width
* Sensitivity Gradient
* Failure Gradient
* Downside Dispersion

Not just raw sweeps.

You’re not building sliders.
You’re building diagnostic geometry.

---

# 7️⃣ How This Fits Philosophically

You are not answering:

> “What should I do?”

You are answering:

> “Where are my decisions constrained vs flexible?”

That is second-order insight.

Most tools optimize.
Very few quantify constraint geometry.

---

# 8️⃣ Example Case Walkthrough

Imagine:

* Age 58
* $1.4M pre-tax
* $300k Roth
* $200k taxable
* Flexible retirement 60–65
* Flexible SS 62–70

Decision surface screens might reveal:

* Retirement age: wide flat region
* SS timing: modest slope
* Conversion strategy: strong improvement in late-life robustness
* Spending: narrow margin
* Allocation: moderate early fragility

Now the user knows where to focus cognitive effort.

---

# 9️⃣ Architectural Implication for cmd_cases

Your current `cases` command shows:

* Exogenous structure

You could add:

```
roost surfaces Case_1
```

Which:

1. Detects enabled screens
2. Runs diagnostic sweeps
3. Prints geometry summaries

Not charts initially.
Just numeric geometry.

---

# 1️⃣0️⃣ Avoid the Trap

Do not:

* Combine screens prematurely
* Create composite flexibility score yet
* Over-simulate dynamic re-optimization

Start simple:

1. Sweep
2. Measure slope
3. Measure feasible band
4. Report curvature intuition

---

# 1️⃣1️⃣ The Big Conceptual Move

ROOST becomes:

> A decision geometry engine.

Not a retirement calculator.

That’s defensible.
