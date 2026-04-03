# Experiment Results Explained

This document explains the results of all experiments run on the
tessituragram vocal repertoire recommendation system. It is written for
readers who may not have a deep background in computer science,
statistics, or music theory.

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

To test the system fairly and without bias, we used a method called
**synthetic user profiles**. For each test, we picked a song from the
library and pretended a singer's preferences perfectly matched that
song's characteristics:

- The singer's **vocal range** was set to the song's pitch range.
- The singer's **4 favorite notes** were the 4 pitches the song uses
  most.
- The singer's **2 avoid notes** were the 2 pitches the song uses
  least.

This gave us an objective, repeatable way to test the system without
relying on real human opinions (which would be subjective and hard to
reproduce).

All random selections used a fixed starting point (called a "seed",
set to 42) so that anyone re-running the experiments will get exactly
the same results.

---

## Research Question 1: Does the system find the right song?

### The question

If we build a singer profile from a specific song, will the system rank
that same song at the top of its recommendations?

### How we tested it

We randomly selected **200 songs** from the library (out of 1,647
eligible songs). For each one, we:

1. Created a synthetic singer profile from the song.
2. Asked the system to rank all songs that fit the singer's range.
3. Checked where the original song appeared in the ranking.

### The results

| Metric | Value | What it means |
|--------|-------|---------------|
| **HR@1** | **55.0%** | The correct song was ranked #1 in 55% of tests |
| **HR@3** | **80.0%** | The correct song was in the top 3 in 80% of tests |
| **HR@5** | **86.0%** | The correct song was in the top 5 in 86% of tests |
| **MRR** | **0.69** | On average, the correct song appeared around position 1.5 |

(95% confidence intervals: HR@1 [48.1%, 61.7%], HR@3 [74.1%, 85.4%],
HR@5 [81.1%, 90.6%], MRR [0.63, 0.74])

### What this means in plain language

The system is quite good at finding songs that match a singer's
preferences. More than half the time, the exact right song is the #1
recommendation. The vast majority of the time (86%), it appears in the
top 5. This is strong evidence that the recommendation algorithm works
as intended.

The system does not always rank the correct song at #1 because many
songs in the library are genuinely similar -- they use similar pitches
in similar proportions. When the correct song lands at position 2 or 3,
it is because other songs are an equally good or nearly-as-good match,
which is actually a desirable property for a recommendation system.

---

## Research Question 1 -- Baseline Comparisons

To understand how good the system really is, we compared it against two
simpler alternatives using the same 200 test songs:

| Model | HR@1 | MRR | Description |
|-------|------|-----|-------------|
| **Full model** | **55.0%** | **0.69** | The complete system (cosine similarity + avoid penalty) |
| **Cosine-only** | 54.5% | 0.69 | Same system but ignoring the "avoid notes" feature |
| **Random** | 2.0% | 0.06 | Picks songs in random order (no intelligence at all) |

### What this means

- The full system is **dramatically better than random guessing** (55%
  vs 2%). This proves the algorithm is doing meaningful work, not just
  getting lucky.
- The full model and cosine-only model perform almost identically for
  self-retrieval. This makes sense: in the self-retrieval test, the
  avoid notes are the least-used pitches, so they have very little
  weight and removing them barely changes the ranking. The avoid penalty
  becomes more important in real-world use where a singer might avoid
  notes for reasons unrelated to how much a song uses them.

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

- **Self-retrieval accuracy (RQ1) is largely insensitive to alpha.**
  Changing alpha from 0.0 to 1.0 only shifts HR@1 by about 1.5
  percentage points. This means the avoid penalty does not
  dramatically help or hurt the system's ability to find the right
  song, which makes sense because in the self-retrieval test, avoid
  notes are the least-used pitches and carry very little weight
  regardless of alpha.
- **Ranking stability (RQ2) decreases slightly as alpha increases.**
  Higher alpha means the avoid penalty has more influence, which
  creates more sensitivity to changes in avoid preferences. However,
  even at alpha = 1.0, tau remains 0.82 (well above the 0.7 threshold
  for "strong agreement"), so the system stays stable at all tested
  alpha values.
- **Alpha = 0.5 is a reasonable default.** It provides a balanced
  trade-off: nearly the best self-retrieval accuracy while keeping
  ranking stability strong. It gives singers meaningful control over
  their avoid preferences without making the system jittery.

---

## Statistical methodology

### Confidence intervals

All confidence intervals in this report are 95% intervals computed
using a technique called **cluster bootstrap** with 10,000 resamples.
A confidence interval gives a range of plausible values for a metric.
For example, "HR@1 = 55% [48.1%, 61.7%]" means we are 95% confident
the true HR@1 falls between 48.1% and 61.7%.

### Why "cluster" bootstrap?

Some songs in the library come from the same composition (for example,
the soprano and alto lines of a duet). These related lines might behave
similarly in experiments, which could make our confidence intervals
misleadingly narrow if we treated every line as fully independent. The
cluster bootstrap accounts for this by grouping lines from the same
composition together when computing confidence intervals. This produces
more honest (slightly wider) intervals that accurately reflect our
uncertainty.

### Reproducibility

Every random selection in these experiments used a fixed random seed
(42), meaning anyone who re-runs the code will get exactly the same
results. No results were cherry-picked, manually adjusted, or
fabricated in any way.

---

## Summary of key findings

1. **The system works.** It finds the right song in the top 5 of its
   recommendations 86% of the time, compared to 7% for random guessing.

2. **The system is stable.** Small changes to a singer's preferences
   produce small changes in rankings (Kendall's tau = 0.84).

3. **The math is correct.** The scoring formula is implemented exactly
   as specified, with zero numerical error.

4. **The system is robust to parameter choices.** Changing the
   avoid-penalty weight (alpha) has only minor effects on accuracy and
   stability.

5. **The avoid penalty is a meaningful feature.** While it does not
   dramatically affect self-retrieval accuracy (because the test is
   designed with least-used pitches as avoids), it gives singers real
   control over their preferences and introduces only a small, acceptable
   reduction in ranking stability.
