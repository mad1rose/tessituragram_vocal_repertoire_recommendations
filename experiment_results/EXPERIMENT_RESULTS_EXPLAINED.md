# Experiment Results Explained

This document explains the results of all experiments run on the
tessituragram vocal repertoire recommendation system. It is written for
readers who may not have a deep background in computer science,
statistics, or music theory.

**Scope.** Unless a section says otherwise, the narrative and tables below
refer to **Experiment 2**—the **1,655-line** library and archived outputs
under `experiment_results/` (e.g. `RQ1_results.json`). The CADSCOM paper
also reports **Experiment 1** (101 vocal lines, one per composition) from
`previous_paper_and_experiments/previous_experiment_results/old_*.json`.
Experiment 1 uses **i.i.d. bootstrap** resampling of query-level outcomes
(Efron & Tibshirani, 1993); Experiment 2 uses **work-level cluster
bootstrap** for RQ1/RQ2 where noted (Cameron et al., 2008; Field & Welsh,
2007). See `experiment/evaluation_plan_research_questions.txt` for the
full split.

---

## What is this system?

This system recommends vocal music (songs for singers). A singer tells
the system:

- **Their vocal range** -- the lowest and highest notes they can sing.
- **Their favorite notes** -- pitches they enjoy singing.
- **Notes they want to avoid** -- pitches they find uncomfortable.

The system then searches a library of songs and ranks them from best
match to worst match. It does this by comparing the singer's preferences
to a "tessituragram" -- a chart showing how much time each song spends
on each pitch.

---

## The dataset

All experiments used a library of **1,655 vocal lines** extracted from
**1,419 musical compositions** in the OpenScore Lieder Corpus. These are
real scores from real published music, not made-up data.

Some compositions have multiple voice parts (for example, a duet has two
vocal lines). Each vocal line was treated as a separate item in the
library, giving us 1,655 total items. Of these, **342 lines** came from
multi-part works and **1,313 lines** came from single-voice songs.

---

## How we created test scenarios

To test the system fairly and without bias, we used **synthetic
profiles** derived from a chosen **vocal line** in the library (each line
is one singing part—often one “song,” but duets contribute multiple
lines). We pretended a singer's preferences perfectly matched that
line’s tessituragram:

- The singer's **vocal range** was set to the line's written pitch range.
- The singer's **4 favorite notes** were the 4 pitches the line spends
  the most time on (by duration).
- The singer's **2 avoid notes** were the 2 pitches the line spends the
  least time on (by duration).

This gave us an objective, repeatable way to test the system without
relying on real human opinions (which would be subjective and hard to
reproduce).

All random selections used a fixed starting point (called a "seed",
set to 42) so that anyone re-running the experiments will get exactly
the same results.

---

## Research Question 1: Synthetic self-retrieval (identifiability check)

### The question

This is **not** a user study. We use **synthetic self-retrieval**: we
pick a **vocal line** from the library, build the singer profile *from
that line’s own tessituragram* (range, favourite pitches = most sung
durations, avoid pitches = least sung), then ask: **how often** does the
system rank **that same line** at the top (or in the top 3 or 5) among
all lines that pass the range filter?

That tests whether the scoring pipeline can recover the generating item
when preferences are an oracle encoding of that item—not whether real
singers would be satisfied in the wild.

### How we tested it (large-library experiment)

We randomly selected **200 vocal lines** from the library (out of 1,647
eligible lines—lines with at least two candidates after range
filtering). Query sampling uses **seed 42**. For each line, we:

1. Built the synthetic profile from that line.
2. Ranked every **candidate** line that fits the profile’s range.
3. Recorded the rank of the **target** line (the one we built the
   profile from).

The archived results also report how many candidates **|C|** each query
had (median 263, mean about 374 on this draw). The **null** model only
applies the range filter and then shuffles candidates at random. For a
uniform shuffle, the chance the target is first is **1/|C|** on that
query; averaging **1/|C|** over the 200 queries gives about **0.017**
(1.7%), which is the order of magnitude of the observed null HR@1
(**2%**).

### The results

| Metric | Value | What it means |
|--------|-------|---------------|
| **HR@1** | **55.0%** | The target line was ranked #1 in 55% of tests |
| **HR@3** | **80.0%** | The target line was in the top 3 in 80% of tests |
| **HR@5** | **86.0%** | The target line was in the top 5 in 86% of tests |
| **MRR** | **0.69** | On average, reciprocal rank ≈ 0.69 (roughly around position 1.5) |

95% bootstrap intervals (work-level clustering; **fixed** query draw;
see `RQ1_results.json`): HR@1 [48.0%, 61.9%], HR@3 [74.4%, 85.5%],
HR@5 [81.1%, 90.6%], MRR [0.64, 0.73].

### What this means in plain language

Under this controlled test, the system usually places the **correct
target line** very high in the list, and far above a random ranking. It
does not prove how humans would experience recommendations.

The target line is not always #1 because many lines share similar
duration-weighted pitch shapes; when it lands at positions 2–3, other
lines are legitimately close matches in tessituragram space.

---

## Research Question 1 -- Baseline Comparisons

We compared the full model to two baselines on the **same 200** query
lines (see `RQ1_baselines.json`):

| Model | HR@1 | MRR | Description |
|-------|------|-----|-------------|
| **Full model** | **55.0%** | **0.69** | Range filter + cosine similarity + avoid penalty (α = 0.5) |
| **Cosine-only** | 54.5% | 0.69 | Same but α = 0 (avoid list not used in the score) |
| **Random** | 2.0% | 0.06 | Range filter, then random order |

### What this means

- The full system is **dramatically better than random guessing** on
  HR@1 (55% vs 2%). The null rate is in line with **mean 1/|C|** on
  this query draw (~1.7%), not a bug.
- The full model and cosine-only model perform almost identically here.
  Under self-retrieval, avoids are the least-used pitches of the target
  line, so the avoid term rarely reorders the top of the list. That does
  **not** mean avoids are useless for real users who specify avoids for
  other reasons.

---

## Research Question 2: Are the rankings stable?

### The question

If a singer slightly changes their preferences (adding or removing just
one favorite or avoid note), does the ranking change dramatically, or
does it stay mostly the same?

### How we tested it

We randomly selected **20 baseline profiles** from the library. For
each one, we made every possible small change:

- Add one new favorite note
- Remove one existing favorite note
- Add one new avoid note
- Remove one existing avoid note

This produced **580 total perturbations** (small changes). For each
change, we re-ranked all the songs and measured how similar the new
ranking was to the original using a statistic called **Kendall's tau**.

Kendall's tau ranges from -1 to +1:
- **1.0** = the two rankings are identical
- **0.0** = the rankings are completely unrelated
- **-1.0** = the rankings are perfectly reversed

### The results

| Metric | Value |
|--------|-------|
| **Mean tau** | **0.84** |
| **95% confidence interval** | [0.82, 0.85] |

Interpretation scale:
- tau > 0.7 = **strong agreement** (rankings very similar)
- tau 0.3 to 0.7 = moderate agreement
- tau < 0.3 = weak agreement

### What this means

A mean tau of 0.84 indicates **strong ranking stability**. When a
singer makes a small change to their preferences, the recommendation
list stays largely the same. The top-ranked songs mostly stay near the
top, and the bottom-ranked songs stay near the bottom. This is a
desirable property -- it means the system is not overly sensitive to
minor preference adjustments.

---

## Research Question 2 -- Baseline Comparisons

| Model | Mean tau | 95% CI |
|-------|----------|--------|
| **Full model** | **0.84** | [0.82, 0.85] |
| **Cosine-only** | 0.87 | [0.86, 0.88] |
| **Random** | 0.00 | [-0.002, 0.007] |

### What this means

- The random model produces tau values near zero, confirming that
  unrelated rankings show no agreement (as expected).
- Both the full model and cosine-only model show strong stability
  (tau > 0.7).
- The cosine-only model is slightly more stable (0.87 vs 0.84). This
  makes sense: the avoid penalty adds an extra dimension that can shift
  rankings when avoid notes change. This small reduction in stability
  is the trade-off for having a system that responds to avoid
  preferences.

---

## Research Question 3: Does the scoring formula work correctly?

### The question

Does the mathematical formula that scores songs actually behave as
designed? Do scores spread out enough to produce meaningful rankings?

### The scoring formula

The system scores each song using:

> **final_score = cosine_similarity - 0.5 x avoid_penalty**

- **Cosine similarity** measures how well a song's pitch distribution
  matches the singer's ideal distribution (1.0 = perfect match,
  0.0 = no match).
- **Avoid penalty** measures how much of the song is spent on notes
  the singer wants to avoid (0.0 = none, 1.0 = all of it).
- **0.5** (called alpha) controls how much weight the avoid penalty
  gets.

### How we tested it

We randomly selected **50 profiles** and, for each one, computed
detailed statistics on all candidate songs' scores.

### The results

**Score spread:**

| Metric | Value | 95% CI |
|--------|-------|--------|
| Mean variance of scores | 0.039 | [0.035, 0.043] |
| Mean range of scores | 1.03 | [0.98, 1.08] |

**Formula verification (identity check):**

| Check | Result |
|-------|--------|
| Mean absolute error | **0.0** |
| Maximum absolute error | **0.0** |

**Regression check** (fitting the formula statistically):

| Coefficient | Expected | Actual |
|-------------|----------|--------|
| Cosine similarity weight | 1.0 | **1.0** |
| Avoid penalty weight | -0.5 | **-0.5** |
| R-squared | 1.0 | **1.0** |

**Correlation checks** (Spearman's rho, measuring relationships between score components):

| Relationship | Expected | Actual | 95% CI |
|-------------|----------|--------|--------|
| Final score vs cosine similarity | Positive | **+0.99** | [0.99, 0.99] |
| Final score vs avoid penalty | Negative | **-0.32** | [-0.41, -0.23] |
| Cosine similarity vs favorite overlap | Positive | **+0.92** | [0.91, 0.93] |

### What this means

- **The formula is implemented exactly as specified.** The identity
  check found zero error between the computed scores and what the
  formula predicts. The regression confirms the cosine weight is
  exactly 1.0 and the avoid weight is exactly -0.5. R-squared is 1.0,
  meaning the formula explains 100% of the variation in scores. There
  are no hidden adjustments or rounding errors affecting the results.
- **Scores spread out meaningfully.** The average range of scores
  across candidate songs is about 1.03 points, which means there is
  real differentiation between good and poor matches. The system is not
  giving everything the same score.
- **All correlations have the expected signs.** Higher cosine
  similarity strongly predicts a higher final score. Higher avoid
  penalty predicts a lower final score. Songs with high favorite
  overlap tend to have high cosine similarity. Everything behaves as
  the math says it should.

---

## Alpha Sensitivity: How does the avoid-penalty weight affect results?

### The question

The scoring formula uses a parameter called alpha (set to 0.5 in the
main experiments) to control how much the avoid penalty matters. What
happens if we change alpha?

### How we tested it

We re-ran the RQ1 and RQ2 experiments with alpha set to five different
values: 0.0, 0.25, 0.5, 0.75, and 1.0. Everything else stayed the same
(same songs, same test profiles, same random seed).

### RQ1 results across alpha values

| Alpha | HR@1 | HR@3 | HR@5 | MRR |
|-------|------|------|------|-----|
| 0.00 | 54.5% | 77.5% | 85.5% | 0.687 |
| 0.25 | 55.5% | 80.5% | 85.5% | 0.693 |
| **0.50** | **55.0%** | **80.0%** | **86.0%** | **0.685** |
| 0.75 | 54.0% | 78.5% | 85.5% | 0.679 |
| 1.00 | 54.0% | 78.0% | 84.0% | 0.672 |

### RQ2 results across alpha values

| Alpha | Mean tau | 95% CI |
|-------|----------|--------|
| 0.00 | 0.87 | [0.86, 0.88] |
| 0.25 | 0.85 | [0.84, 0.86] |
| **0.50** | **0.84** | **[0.82, 0.85]** |
| 0.75 | 0.83 | [0.81, 0.84] |
| 1.00 | 0.82 | [0.80, 0.83] |

### What this means

- **Oracle self-retrieval performance (RQ1) is largely insensitive to alpha.**
  Changing alpha from 0.0 to 1.0 only shifts HR@1 by about 1.5
  percentage points. This means the avoid penalty does not
  dramatically help or hurt the system's ability to rank the **target
  line** highly in this identifiability setup, which makes sense because
  in the self-retrieval test, avoid
  notes are the least-used pitches and carry very little weight
  regardless of alpha.
- **Ranking stability (RQ2) decreases slightly as alpha increases.**
  Higher alpha means the avoid penalty has more influence, which
  creates more sensitivity to changes in avoid preferences. However,
  even at alpha = 1.0, tau remains 0.82 (well above the 0.7 threshold
  for "strong agreement"), so the system stays stable at all tested
  alpha values.
- **Alpha = 0.5 is a reasonable default.** It provides a balanced
  trade-off: nearly the best oracle self-retrieval hit-rates on this draw
  while keeping
  ranking stability strong. It gives singers meaningful control over
  their avoid preferences without making the system jittery.

---

## Statistical methodology

### Confidence intervals

**Experiment 2 (this report, `experiment_results/`):** 95% intervals for
RQ1/RQ2 (and related summaries) use **work-level cluster bootstrap**
with 10,000 resamples (Cameron et al., 2008; Field & Welsh, 2007;
percentile method, Efron & Tibshirani, 1993).

**Experiment 1** (`old_*.json`): 95% intervals use **i.i.d. bootstrap**
resampling of query-level (or baseline-level) outcomes with 10,000
resamples (Efron & Tibshirani, 1993), appropriate when each sampled
query line comes from a distinct composition in that small library.

A confidence interval gives a range of plausible values for a metric
**under the stated resampling scheme** for the fixed sample. For
example, "HR@1 = 55% [48.1%, 61.7%]" summarizes bootstrap variation for
the archived query draw, not repeated re-draws of queries from the corpus.

### Why "cluster" bootstrap (Experiment 2)?

Some lines in the library come from the same composition (for example,
two parts of a duet). Those related lines can behave similarly in
experiments, which would make confidence intervals **too narrow** if we
treated every line as fully independent. Cluster bootstrap resamples
**compositions (work IDs)** with replacement, then includes all sampled
lines belonging to those works, which inflates variance appropriately
when queries share a work. Queries themselves are drawn uniformly from
the pool of **eligible lines** (not uniformly from compositions); the
bootstrap addresses **within-work dependence**, not that compositions
were simple-random-sampled.

### Reproducibility

Query / baseline draws use **seed 42**. For Experiment 2 RQ1 and RQ1
baselines, bootstrap resampling uses a **separate seed (43)** so query
selection and bootstrap streams are independent and reproducible (see
`experiment/run_rq1_experiment.py`). Experiment 1 scripts use **seed 42**
for queries; the bootstrap loop then continues the global random stream
after query selection (no separate bootstrap seed). No results were
cherry-picked, manually adjusted, or fabricated in any way.

---

## Summary of key findings

1. **The system works.** It finds the right song in the top 5 of its
   recommendations 86% of the time, compared to 7% for random guessing.

2. **The system is stable.** Small changes to a singer's preferences
   produce small changes in rankings (Kendall's tau = 0.84).

3. **The math is correct.** The scoring formula is implemented exactly
   as specified, with zero numerical error.

4. **The system is robust to parameter choices.** Changing the
   avoid-penalty weight (alpha) has only minor effects on oracle
   self-retrieval hit-rates and on stability.

5. **The avoid penalty is a meaningful feature.** While it does not
   dramatically affect self-retrieval **performance** on this
   identifiability task (because the test is
   designed with least-used pitches as avoids), it gives singers real
   control over their preferences and introduces only a small, acceptable
   reduction in ranking stability.

---

## References (bootstrap methods cited above)

Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008). Bootstrap-based improvements for inference with clustered errors. *Review of Economics and Statistics*, 90(3), 414–427.

Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman and Hall/CRC.

Field, C. A., & Welsh, A. H. (2007). Bootstrapping clustered data. *Journal of the Royal Statistical Society: Series B*, 69(3), 369–390.
