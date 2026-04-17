# CADSCOM 2026 — Speaker Script

**Total time: ~12 minutes**
**Presentation:** Content-Based Vocal Repertoire Ranking Framework Using Duration-Weighted Pitch Distributions

---

## Slide 1 — Title Slide (~20 seconds)

Good morning/afternoon, everyone. My name is Madeline Johnson, and I am currently pursuing a master's in data science here at Minnesota State University, Mankato. My undergraduate background is in vocal performance -- I hold a Bachelor of Music from Illinois Wesleyan University -- so this project sits right at the intersection of my two worlds. This work is co-authored with Flint Million and Rajeev Bukralia, and today I want to show you how we can use data from musical scores to help singers find repertoire that actually fits their voice.

---

## Slide 2 — Hook / Opening Question (~45 seconds)

As a trained singer, one of the first things I learned is that choosing the wrong piece is not just an inconvenience -- it can lead to real vocal injury. For example, a singer with a naturally lower voice will usually not feel as comfortable spending long periods in a high range as a singer with a naturally higher voice. Research shows that when a piece's demands do not match a singer's capabilities, the risk of strain goes up significantly (Apfelbach, 2022; Phyland et al., 1999). In practice, singers and voice teachers rely on intuition, trial and error, or vocal classification systems that are not consistently defined. That is what motivated this research: using data to make the process of choosing repertoire more objective and safer.

---

## Slide 3 — The Current Approach (~55 seconds)

Today, singers mainly rely on two approaches.

The first is **filtering by range**. Some databases let you filter by the notes in the vocal line — you set a minimum and maximum pitch. That is useful, but it only tells you the extremes. A piece with one very high note at the climax looks the same as a piece that sits up high the entire time. Range tells you the boundaries, not where the voice actually lives.

The second approach is **Fach** — the system opera uses to categorize voices by range, weight, and color. Lyric soprano, dramatic mezzo, and so on. But Fach labels are not consistently defined across regions or pedagogical traditions (Schloneger et al., 2024), and many voices fall between categories — which makes it hard to assign a single label. Fach gives you a broad category, not a profile tailored to a specific singer's unique voice. Neither approach captures where the voice actually spends its time -- and that distinction matters.

---

## Slide 4 — Tessitura & the Tessituragram (~65 seconds)

There is a concept that does capture where the voice spends its time: **tessitura**. Range tells you the highest and lowest notes, but tessitura tells you where the voice actually *lives* — the pitches where it spends most of its time. A piece might touch its highest note once at the climax, but if it sits in the middle of the range for most of its duration, that is where the real demand is. What matters most is not the extremes — it is where you spend the bulk of your time.

A researcher named Stefan Thurmer formalized a way to represent tessitura visually. In 1988 he introduced the **tessituragram** — a histogram of singing time per pitch. Titze, in 2008, refined this with duration weighting, meaning longer notes count more because sustaining a pitch is more demanding than a passing tone. The result is a **fingerprint** of where the voice spends its time in that piece. This is exactly what range and Fach miss — the internal distribution of vocal demand. That raises a natural follow-up: whether any existing tools already use tessituragrams this way.

---

## Slide 5 — The Gap (~55 seconds)

There are tools that work with tessituragrams, but they are **purely analytic**.

**Tessa**, developed by Apfelbach in 2022, extracts a tessituragram from a digital score and produces summary statistics. The **Kassia Database** — a wonderful resource for art song by women composers — displays a human-assessed tessitura for each entry. Both of these help you evaluate a piece after you have already found it. But neither one lets you use a tessituragram as a query — to search for new pieces whose pitch distribution is likely to fit.

The scale of the problem makes manual discovery impractical. The **LiederNet Archive alone catalogs over 217,000 art-song settings**. No voice teacher, no matter how experienced, can know all of that literature.

Tessituragrams carry detailed information about a song's vocal demand — but to our knowledge, **no existing system uses them on the query side to recommend repertoire**. That is the gap we wanted to explore.

---

## Slide 6 — The Pipeline (~50 seconds)

Let me walk you through the pipeline. First, a quick note on the data. We parse digital sheet music — MusicXML files — using a Python toolkit called **music21**, and for each vocal line we build a tessituragram: every pitch maps to its total duration in quarter-note beats. That is the input to the system.

The pipeline has five steps:

1. **Singer preferences.** The singer provides three inputs: their comfortable vocal range, favorite pitches, and pitches they want to avoid.
2. **Range filter.** We filter out any song whose written range goes beyond what the singer specified.
3. **Ideal profile construction.** We turn those preferences into a target profile the next slide explains in detail.
4. **Cosine similarity scoring.** We score every remaining song by how closely its tessituragram matches that ideal, minus a penalty for time on avoided pitches.
5. **Ranked song list.** Songs ordered from best match to worst.

---

## Slide 7 — How Scoring Works (~70 seconds)

Here is how the scoring works. We create a list of numbers -- one per pitch in the singer's range. Every pitch starts with a small base weight so it is not ignored entirely. Favorite pitches get a large boost on top of that, and avoided pitches are dropped to zero. The result is a profile that peaks at the singer's preferred pitches and has nothing where they want to avoid.

Each song has its own list built the same way -- one number per pitch -- but from the actual score, showing how much singing time falls on each pitch. **Cosine similarity** then compares the pattern of these two lists. If both concentrate time on the same pitches in the same proportions, the score is high -- close to 1.0. It focuses on shape rather than total duration, so a short song and a long song that distribute time across pitches the same way score equally well. It is a standard tool for this kind of comparison in information retrieval, which is why we chose it.

The **avoid penalty** is the proportion of the song's total singing duration that falls on notes the singer wants to avoid. **Alpha** controls the trade-off between rewarding good-fit pitches and penalizing avoided ones -- at 0.5, we split the weight evenly.

The scoring function is straightforward in structure. To find out whether it actually produces good rankings, we ran two experiments on real musical data.

---

## Slide 8 — The Dataset (~35 seconds)

We used the **OpenScore Lieder Corpus** -- a freely available, openly licensed collection of art songs. Conveniently, all of the composers have been dead long enough that copyright is not a concern. We ran two experiments. The first used a compact library of 101 vocal lines, one per composition. The second used a much larger expanded library: 1,655 vocal lines drawn from 1,419 compositions -- about 16 times larger. Some compositions have multiple voice parts, like duets, so each vocal line is treated as its own item.

---

## Slide 9 — How We Tested It: Synthetic Self-Retrieval (~60 seconds)

We did not have human judges rating songs for us — that is future work. Instead, we used a rigorous method called **synthetic self-retrieval**. Here is how it works:

1. We pick a vocal line from the library and build a singer profile directly from that line's own tessituragram: the range becomes the singer's range, the four pitches with the most singing time become the favorites, and the two pitches with the least become the avoids.
2. Then we ask the system to rank all the remaining candidates and see where the original line ends up.

If the system is working, it should rank that line very highly — ideally first.

We compared three models: the **full model** with the avoid penalty, **cosine-only** without the penalty, and a **null baseline** that just filters by range and then ranks randomly. Here is what we found.

---

## Slide 10 — Results: Self-Retrieval Accuracy (RQ1) (~60 seconds)

This figure shows the self-retrieval results. The metric on the left of each panel is **Hit Rate at 1** — how often the target song is ranked first — and **Mean Reciprocal Rank** on the right, which captures how high it ranks on average.

In **Experiment 1**, the compact 101-line library, the full model puts the right song first **76 percent** of the time. Random guessing after the same range filter gets about 6 percent.

In **Experiment 2** with 1,655 lines, the full model still finds the right song first **55 percent** of the time — versus just 2 percent for random. And if we look at the **top 5** instead of just the top 1, the system finds the target song **86 percent** of the time — nearly 9 out of 10.

These two experiments use different protocols and different candidate pools, so the drop from 76 to 55 percent is **not** purely a library-size effect. The key takeaway is clear: the system massively outperforms random ordering in both cases.

---

## Slide 11 — Results: Ranking Stability (RQ2) (~45 seconds)

The next thing we wanted to know was whether the system is **stable** — whether a small change to preferences causes the rankings to shift dramatically.

We tested this with **580 one-note perturbations** across 20 baseline profiles in the expanded library. We measured stability using **Kendall's tau**, a statistic that compares two ranked lists. A tau of 1.0 means identical rankings; 0.0 means completely unrelated. Anything above 0.7 is considered strong agreement.

Our full model achieved a mean tau of **0.84**. The cosine-only model was 0.87, with overlapping confidence intervals. The random baseline was essentially zero, as expected.

When a singer tweaks their preferences slightly, the recommendations stay largely the same. **The system is stable and trustworthy.**

---

## Slide 12 — Sensitivity to the Avoid-Penalty Weight (α) (~45 seconds)

We also tested how sensitive the results are to the choice of **alpha** — the parameter that controls how heavily we penalize avoided notes.

We swept alpha from 0 to 1 in both experiments. As you can see, self-retrieval performance — Hit Rate at 1 and MRR — is **largely flat** across the entire range. The system is not brittle to this choice.

Stability does decrease slightly as alpha increases, which makes sense: a stronger avoid penalty creates more sensitivity to changes in avoid preferences. But even at alpha equals 1, **tau stays above 0.82** — well above the strong agreement threshold.

We report alpha equals 0.5 as a balanced default: it gives singers meaningful control over their avoid preferences without making the rankings jittery.

---

## Slide 13 — Implementation Verification (RQ3) (~30 seconds)

As an engineering sanity check, we verified that the formula is implemented **exactly as designed**.

- The identity residual — the difference between the computed score and what the formula predicts — is **exactly zero**.
- An OLS regression recovers the exact coefficients: cosine weight = 1.0, avoid weight = −0.5, R² = 1.0.
- All correlations go in the expected directions: higher cosine similarity predicts a higher final score, and higher avoid penalty predicts a lower score.

**No hidden bugs. No rounding surprises. The math checks out.**

---

## Slide 14 — What Does This Mean? (~50 seconds)

Let me step back and talk about what this means in practice.

This is a **proof-of-concept** showing that data science can bring objectivity to a domain where decisions are traditionally subjective — and where bad decisions have real health consequences.

Think about the practical impact for a voice teacher. Right now, they recommend pieces from their own training and experience. But a query based on specific pitches — "find me pieces that live on these notes and avoid those" — is far more granular than Fach. It could surface a piece the teacher has never encountered that turns out to be a **perfect fit for their student's unique voice**.

For those of you in CS and data science, this also demonstrates that familiar tools — cosine similarity, content-based filtering, offline evaluation — can work in a completely new domain, and in a **cold-start setting** with no collaborative signal.

I think there is a broader takeaway here for anyone working with content-based recommendation: these familiar techniques can open up entirely new domains, and I would welcome a conversation about where else they might apply.

---

## Slide 15 — Limitations & Future Work (~30 seconds)

I want to be upfront about limitations, because honesty strengthens research.

- These are **synthetic profiles**, not real singer preferences — we have not done a human study yet.
- We only tested on **one corpus** of German and French art song; opera, musical theatre, and popular song are untested.
- We only model **pitch and duration** — we do not account for dynamics, tempo, or text setting.

For future work, we want to evaluate with real singers and their actual preferences, expand to more diverse repertoire, add richer musical features, and ultimately build an **interactive tool** that singers and voice teachers can use in practice.

---

## Slide 16 — Closing / Thank You (~15 seconds)

To wrap up: **duration-weighted tessituragrams can rank vocal repertoire by fit — and this is just the beginning.**

Next time a singer asks "What should I sing?" — data might have an answer.

Thank you very much for your time. I would be happy to take any questions.

---

## Timing Summary

| Slide | Topic | Time |
|-------|-------|------|
| 1 | Title | ~20 sec |
| 2 | Hook / Opening Question | ~45 sec |
| 3 | The Current Approach | ~55 sec |
| 4 | Tessitura & the Tessituragram | ~65 sec |
| 5 | The Gap | ~55 sec |
| 6 | The Pipeline | ~50 sec |
| 7 | How Scoring Works | ~60 sec |
| 8 | The Dataset | ~45 sec |
| 9 | Synthetic Self-Retrieval | ~60 sec |
| 10 | RQ1: Self-Retrieval Results | ~60 sec |
| 11 | RQ2: Stability | ~45 sec |
| 12 | Alpha Sensitivity | ~45 sec |
| 13 | RQ3: Implementation Check | ~30 sec |
| 14 | What Does This Mean? | ~50 sec |
| 15 | Limitations & Future Work | ~30 sec |
| 16 | Closing / Thank You | ~15 sec |
| **Total** | | **~12 min 0 sec** |

---
---

# CONDENSED DECK -- Speaker Script (8 slides)

**Total time: ~9 min 35 sec**
**File:** CADSCOM_2026_Presentation_condensed.pptx

---

## Slide 1 -- Title (~20 seconds)

Good morning/afternoon, everyone. My name is Madeline Johnson, and I am currently pursuing a master's in data science here at Minnesota State University, Mankato. My undergraduate background is in vocal performance -- I hold a Bachelor of Music from Illinois Wesleyan University -- so this project sits right at the intersection of my two worlds. This work is co-authored with Flint Million and Rajeev Bukralia, and today I want to show you how we can use data from musical scores to help singers find repertoire that actually fits their voice.

---

## Slide 2 -- Problem & Motivation (~90 seconds)

As a trained singer, one of the first things I learned is that choosing the wrong piece is not just an inconvenience -- it can lead to real vocal injury. For example, a singer with a naturally lower voice will usually not feel as comfortable spending long periods in a high range as a singer with a naturally higher voice. Research shows that when a piece's demands do not match a singer's capabilities, the risk of strain goes up significantly (Apfelbach, 2022; Phyland et al., 1999). In practice, singers and voice teachers rely on intuition, trial and error, or vocal classification systems that are not consistently defined. That is what motivated this research: using data to make the process of choosing repertoire more objective and safer.

Today, singers mainly rely on two approaches. The first is filtering by range -- you set a minimum and maximum pitch. That is useful, but it only tells you the extremes. A piece with one very high note at the climax looks the same as a piece that sits up high the entire time. The second approach is Fach -- the system opera uses to categorize voices by range, weight, and color. But Fach labels are not consistently defined across regions or pedagogical traditions (Schloneger et al., 2024), and many voices fall between categories. Neither approach captures where the voice actually spends its time -- and that distinction matters.

---

## Slide 3 -- Tessituragrams & the Gap (~90 seconds)

There is a concept that does capture where the voice spends its time: tessitura. Range tells you the highest and lowest notes, but tessitura tells you where the voice actually lives -- the pitches where it spends most of its time. A piece might touch its highest note once at the climax, but if it sits in the middle of the range for most of its duration, that is where the real demand is.

A researcher named Stefan Thurmer formalized a way to represent tessitura visually. In 1988 he introduced the tessituragram -- a histogram of singing time per pitch. Titze, in 2008, refined this with duration weighting, meaning longer notes count more because sustaining a pitch is more demanding than a passing tone. The result is a fingerprint of where the voice spends its time in that piece.

There are tools that work with tessituragrams, but they are purely analytic. Tessa extracts a tessituragram from a digital score. The Kassia Database displays a human-assessed tessitura for each entry. Both help you evaluate a piece after you have already found it. But neither one lets you use a tessituragram as a query -- to search for new pieces whose pitch distribution is likely to fit. The LiederNet Archive alone catalogs over 217,000 art-song settings. To our knowledge, no existing system uses tessituragrams on the query side to recommend repertoire. That is the gap we wanted to explore.

---

## Slide 4 -- Methodology (~100 seconds)

Let me walk you through the methodology. We parse digital sheet music -- MusicXML files -- using a Python toolkit called music21, and for each vocal line we build a tessituragram: every pitch maps to its total duration in quarter-note beats.

The pipeline has five steps. The singer provides three inputs: their comfortable vocal range, favorite pitches, and pitches to avoid. We filter out any song whose written range goes beyond what the singer specified. Then we build an ideal pitch profile from those inputs. We create a list of numbers -- one per pitch in the singer's range. Every pitch starts with a small base weight so it is not ignored entirely. Favorite pitches get a large boost on top of that, and avoided pitches are dropped to zero. The result is a profile that peaks at the singer's preferred pitches and has nothing where they want to avoid.

Each song has its own list built the same way -- but from the actual score, showing how much singing time falls on each pitch. Cosine similarity then compares the pattern of these two lists. If both concentrate time on the same pitches in the same proportions, the score is high -- close to 1.0. It focuses on shape rather than total duration. The avoid penalty is the proportion of the song's total singing duration that falls on notes the singer wants to avoid. Alpha controls the trade-off -- at 0.5, we split the weight evenly. Finally, we return a ranked list from best match to worst.

---

## Slide 5 -- Data & Evaluation Design (~80 seconds)

We used the OpenScore Lieder Corpus -- a freely available, openly licensed collection of art songs. Conveniently, all of the composers have been dead long enough that copyright is not a concern. We ran two experiments. The first used a compact library of 101 vocal lines, one per composition. The second used a much larger expanded library: 1,655 vocal lines drawn from 1,419 compositions -- about 16 times larger. Some compositions have multiple voice parts, like duets, so each vocal line is treated as its own item.

We did not have human judges rating songs for us -- that is future work. Instead, we used a rigorous method called synthetic self-retrieval. We pick a vocal line from the library and build a singer profile directly from that line's own tessituragram: the range becomes the singer's range, the four pitches with the most singing time become the favorites, and the two pitches with the least become the avoids. Then we ask the system to rank all the remaining candidates and see where the original line ends up. If the system is working, it should rank that line very highly -- ideally first. We compared three models: the full model with the avoid penalty, cosine-only without the penalty, and a null baseline that just filters by range and then ranks randomly.

---

## Slide 6 -- Results: Self-Retrieval Accuracy (RQ1) (~60 seconds)

This figure shows the self-retrieval results. The metric on the left of each panel is **Hit Rate at 1** -- how often the target song is ranked first -- and **Mean Reciprocal Rank** on the right, which captures how high it ranks on average.

In **Experiment 1**, the compact 101-line library, the full model puts the right song first **76 percent** of the time. Random guessing after the same range filter gets about 6 percent.

In **Experiment 2** with 1,655 lines, the full model still finds the right song first **55 percent** of the time -- versus just 2 percent for random. And if we look at the **top 5** instead of just the top 1, the system finds the target song **86 percent** of the time -- nearly 9 out of 10.

These two experiments use different protocols and different candidate pools, so the drop from 76 to 55 percent is **not** purely a library-size effect. The key takeaway is clear: the system massively outperforms random ordering in both cases.

---

## Slide 7 -- Robustness: Stability & Alpha Sensitivity (~90 seconds)

So the system can find the right song -- but the next question is: is it **consistent**? If a singer tweaks just one note in their preferences, does the whole list of recommendations shuffle around, or does it mostly stay the same? That matters, because a system that gives you completely different answers every time you make a tiny change would not be very trustworthy.

To test this, we made small, one-note changes to singer profiles and compared the recommendations before and after. We needed a measure that applies when the output is a **ranked list of the same songs twice** -- once before the edit and once after. **Kendall's tau** is a standard rank-correlation statistic for exactly that situation (Kendall, 1948): it looks at every pair of songs and checks whether they still appear in the **same relative order** in both lists. That is why it fits a stability question better than a top-one accuracy number alone -- **Hit Rate at 1** only tells you whether the target song stayed first, whereas tau summarizes how much the **entire ordering** moved.

Tau runs from **1.0** when the two lists are identical in order, down toward **0** when the rankings are unrelated, and can go **negative** if they tend to disagree. In our analysis we treat values **above 0.7** as strong agreement between the two rankings. Our full model averaged about **0.84** -- well above that cutoff. The cosine-only variant was very similar, and the random baseline was near zero, as expected.

The table on the left shows those consistency scores. On the right, the plot shows what happens when we change how much weight we give to the avoid penalty -- the alpha value from the formula earlier. We tried every value from 0 to 1. Self-retrieval accuracy was on the previous slide; here the curves show that ranking stability stays strong across the whole alpha range. We chose **0.5** as the default because it gives singers meaningful control over which notes to avoid without making the recommendations unstable.

---

## Slide 8 -- Takeaways & Limitations (~50 seconds)

This is a **proof-of-concept** showing that data science can bring objectivity to a domain where decisions are traditionally subjective -- and where bad decisions have real health consequences. A query based on specific pitches is far more granular than Fach. It could surface a piece the teacher has never encountered that turns out to be a **perfect fit** for their student's unique voice. For those of you in CS and data science, this also demonstrates that familiar tools -- cosine similarity, content-based filtering, offline evaluation -- can work in a completely new domain and in a cold-start setting.

I want to be upfront about limitations. These are synthetic profiles, not real singer preferences. We only tested on one corpus of German and French art song. And we only model pitch and duration -- dynamics, tempo, and text setting are not included. For future work, we want to evaluate with real singers, expand to more diverse repertoire, add richer features, and ultimately build an interactive tool.

---

## Slide 9 -- Thank You (~15 seconds)

To wrap up: **duration-weighted tessituragrams can rank vocal repertoire by fit -- and this is just the beginning.** Next time a singer asks "What should I sing?" -- data might have an answer. Thank you very much for your time. I would be happy to take any questions.

---

## Condensed Deck -- Timing Summary

| Slide | Topic | Time |
|-------|-------|------|
| 1 | Title | ~20 sec |
| 2 | Problem & Motivation | ~90 sec |
| 3 | Tessituragrams & the Gap | ~90 sec |
| 4 | Methodology | ~100 sec |
| 5 | Data & Evaluation Design | ~80 sec |
| 6 | RQ1: Self-Retrieval Results | ~60 sec |
| 7 | Robustness: Stability & Alpha | ~90 sec |
| 8 | Takeaways & Limitations | ~50 sec |
| 9 | Thank You | ~15 sec |
| **Total** | | **~9 min 55 sec** |
