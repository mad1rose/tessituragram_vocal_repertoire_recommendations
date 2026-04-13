# CADSCOM 2026 — Speaker Script

**Total time: ~12 minutes**
**Presentation:** Content-Based Vocal Repertoire Ranking Framework Using Duration-Weighted Pitch Distributions

---

## Slide 1 — Title Slide (~15 seconds)

Good morning/afternoon, everyone. My name is Madeline Johnson, and I'm here with my co-authors Flint Million and Rajeev Bukralia from Minnesota State University, Mankato. Today I'm going to talk about how we can use data from musical scores to help singers find repertoire that actually fits their voice.

---

## Slide 2 — Hook / Opening Question (~45 seconds)

Let me start with a question. **Have you ever wondered how a singer decides which songs are safe to sing?**

If you're not a singer, that might sound like an odd question. But for singers, choosing the wrong piece isn't just a matter of preference — it can lead to real vocal injury. Research shows that misalignment between a piece's demands and a singer's capabilities raises the risk of strain (Apfelbach, 2022; Phyland et al., 1999).

In practice, singers and voice teachers rely on intuition, trial and error, or vocal classification systems that aren't consistently defined. So **what if we could use data to make this process more objective and safer?**

---

## Slide 3 — The Gap / Why This Matters (~45 seconds)

Here's the gap. Tools already exist that can analyze a song's tessitura — where the voice sits in a piece. For example, a program called Tessa can extract a tessitura profile from a digital score. But these tools only work **after** you've already picked a piece. They help you evaluate a choice you've made — they don't help you **discover** new pieces that are likely to fit.

And here's where my background matters. I was a vocal performance major before pursuing my master's in data science. **I lived this problem as a singer.** I know what it's like to pick a piece that doesn't sit well in your voice. And as a data scientist, I asked: can we build a system that *recommends* songs based on where they actually sit, not just their highest and lowest notes?

---

## Slide 4 — What Is Tessitura? (~60 seconds)

Before we go further, let me explain a music concept that's central to this research: **tessitura**.

If you look at a piece of vocal music, you can see the highest note and the lowest note — that's the **range**. But range alone doesn't tell you where the voice **spends most of its time**. That's tessitura.

A piece might have one very high note at the climax, but if the rest of the piece sits comfortably in the middle of the voice, it's very different from a piece that *lives* up high the entire time.

Duration matters too: holding a high B-flat for eight beats is much more demanding than touching it for a sixteenth note.

For those of you who aren't musicians, think of it like driving. What matters for the wear on your car isn't the farthest you've ever driven — it's your **daily commute**. Tessitura is the voice's daily commute.

---

## Slide 5 — What Is a Tessituragram? (~45 seconds)

So how do we capture tessitura computationally? With something called a **tessituragram**. It's essentially a fingerprint of a song.

On one axis you have every pitch in the vocal line, and on the other you have how much total singing time is spent on that pitch, weighted by note duration. Longer notes count more because sustaining a pitch is more demanding than a passing tone.

We parse digital sheet music — MusicXML files — using a toolkit called music21, and we build one of these profiles for every vocal line in our library.

So the question becomes: **can we use these fingerprints to match songs to singers?**

---

## Slide 6 — The Pipeline (~45 seconds)

Here's the big picture of how the system works. It's a pipeline with five steps.

1. **Singer preferences.** The singer provides three inputs: their comfortable vocal range, their favorite pitches, and pitches they want to avoid.
2. **Range filter.** We remove any song whose written range goes beyond what the singer specified.
3. **Ideal profile construction.** We build a target pitch-duration vector from those preferences — basically a fingerprint of what the perfect song would look like for this singer.
4. **Cosine similarity scoring.** We score every remaining song by how closely its tessituragram matches that ideal, minus a penalty for time spent on avoided pitches.
5. **Ranked song list.** Songs ordered from best match to worst.

The singer tells us three things; we do the rest.

---

## Slide 7 — How Scoring Works (~60 seconds)

So let's look at exactly how the scoring works. The final score for each song is:

> **final_score = cosine_similarity(song, ideal) − α × avoid_penalty**

Let me break that down.

**Cosine similarity** measures how closely a song's pitch-duration fingerprint aligns with what the singer wants. A score of 1.0 would be a perfect match in proportional shape.

**Avoid penalty** is the proportion of the song's total singing duration that falls on notes the singer wants to avoid.

**Alpha** controls the trade-off — at 0.5, we're splitting the weight evenly.

Think of it like a restaurant recommender. It finds dishes that match your taste preferences and then subtracts points for ingredients you don't like. Simple idea, but the question is: **does it actually work?** How do we know this produces good rankings?

---

## Slide 8 — The Dataset (~45 seconds)

To test this, we needed real musical data. We used the **OpenScore Lieder Corpus** — a freely available, openly licensed collection of art songs. These are real scores by composers like Schubert, Clara and Robert Schumann, Debussy, and Fauré.

We ran two experiments:

- **Experiment 1:** A compact library of 101 vocal lines, one per composition.
- **Experiment 2:** A much larger expanded library — 1,655 vocal lines drawn from 1,419 compositions, about 16 times larger. Some compositions have multiple voice parts (like duets), so each vocal line is treated as its own item.

These aren't made-up examples. These are real art songs that singers perform every day around the world.

---

## Slide 9 — How We Tested It: Synthetic Self-Retrieval (~60 seconds)

Now, we didn't have human judges rating songs for us — that's future work. Instead, we used a rigorous method called **synthetic self-retrieval**. Here's how it works:

1. We pick a vocal line from the library.
2. We build a singer profile directly from that line's own tessituragram: the range becomes the singer's range, the four pitches with the most singing time become the favorites, and the two pitches with the least become the avoids.
3. Then we ask the system to rank all the remaining candidates and see where the original line ends up.

If the system is working, it should rank that line very highly — ideally first.

We compared three models: the **full model** with the avoid penalty, **cosine-only** without the penalty, and a **null baseline** that just filters by range and then ranks randomly.

So what did we find?

---

## Slide 10 — Results: Self-Retrieval Accuracy (RQ1) (~60 seconds)

Here are the self-retrieval results. This figure shows **Hit Rate at 1** — how often the target song is ranked first — and **Mean Reciprocal Rank**, which captures how high it ranks on average.

On the **left** is Experiment 1, the compact 101-line library. The full model puts the right song first **76 percent** of the time. Random guessing after the same range filter? About 6 percent.

On the **right** is Experiment 2 with 1,655 lines. The full model still finds the right song first **55 percent** of the time — versus just 2 percent for random. And if we look at the **top 5** instead of just the top 1, the system finds the target song **86 percent** of the time. That's nearly 9 out of 10.

These two experiments use different protocols and different candidate pools, so the drop from 76 to 55 percent is **not** purely a library-size effect. But the key takeaway is clear: the system massively outperforms random ordering in both cases.

---

## Slide 11 — Results: Ranking Stability (RQ2) (~45 seconds)

Next: is the system **stable?** If a singer makes a small change to their preferences — adds one favorite note or removes one avoid note — does the whole ranking fall apart?

We tested this with **580 one-note perturbations** across 20 baseline profiles in the expanded library. We measured **Kendall's tau**, which compares two ranked lists. A tau of 1.0 means identical rankings; 0.0 means completely unrelated. Anything above 0.7 is considered strong agreement.

Our full model achieved a mean tau of **0.84**. The cosine-only model was 0.87, with overlapping confidence intervals. The random baseline was essentially zero, as expected.

This means when a singer tweaks their preferences slightly, the recommendations stay largely the same. **The system is stable and trustworthy.**

---

## Slide 12 — Sensitivity to the Avoid-Penalty Weight (α) (~45 seconds)

We also tested how sensitive the results are to the choice of **alpha** — the parameter that controls how heavily we penalize avoided notes.

We swept alpha from 0 to 1 in both experiments. As you can see, self-retrieval performance — Hit Rate at 1 and MRR — is **largely flat** across the entire range. The system isn't brittle to this choice.

Stability does decrease slightly as alpha increases, which makes sense: a stronger avoid penalty creates more sensitivity to changes in avoid preferences. But even at alpha equals 1, **tau stays above 0.82** — well above the strong agreement threshold.

We report alpha equals 0.5 as a balanced default: it gives singers meaningful control over their avoid preferences without making the rankings jittery.

---

## Slide 13 — Implementation Verification (RQ3) (~30 seconds)

Finally, as an engineering sanity check, we verified that the formula is implemented **exactly as designed**.

- The identity residual — the difference between the computed score and what the formula predicts — is **exactly zero**.
- An OLS regression recovers the exact coefficients: cosine weight = 1.0, avoid weight = −0.5, R² = 1.0.
- All correlations go in the expected directions: higher cosine similarity predicts a higher final score; higher avoid penalty predicts a lower score.

**No hidden bugs. No rounding surprises. The math checks out.**

---

## Slide 14 — What Does This Mean? (~45 seconds)

So what does this all mean?

This is a **proof-of-concept** that shows data science can bring objectivity to a domain where decisions are traditionally subjective — and where bad decisions have real health consequences.

For those of you working in recommendation systems or information retrieval, this demonstrates that familiar techniques — cosine similarity, content-based filtering, offline evaluation metrics — can work in a completely new domain. And it works in a **cold-start setting** with no collaborative filtering data, which is often the hardest case.

I'd love for you to think about this: **how might content-based recommendation techniques from YOUR work apply to creative domains like music, art, or design?** The tools are the same — the application is what makes it novel.

---

## Slide 15 — Limitations & Future Work (~30 seconds)

I want to be upfront about limitations, because honesty strengthens research.

- These are **synthetic profiles**, not real singer preferences. We haven't done a human study yet.
- We only tested on **one corpus** of German and French art song. Opera, musical theatre, and popular song are untested.
- We only model **pitch and duration** — dynamics, tempo, and text setting are not included.

For future work, we want to evaluate with real singers and their actual preferences, expand to more diverse repertoire, add richer musical features, and ultimately build an **interactive tool** that singers and voice teachers can use in practice.

---

## Slide 16 — Closing / Thank You (~15 seconds)

To wrap up: **duration-weighted tessituragrams can rank vocal repertoire by fit — and this is just the beginning.**

Next time a singer asks "What should I sing?" — data might have an answer.

Thank you very much for your time. I'd be happy to take any questions.

---

## Timing Summary

| Slide | Topic | Time |
|-------|-------|------|
| 1 | Title | ~15 sec |
| 2 | Hook / Opening Question | ~45 sec |
| 3 | The Gap | ~45 sec |
| 4 | What Is Tessitura? | ~60 sec |
| 5 | What Is a Tessituragram? | ~45 sec |
| 6 | The Pipeline | ~45 sec |
| 7 | How Scoring Works | ~60 sec |
| 8 | The Dataset | ~45 sec |
| 9 | Synthetic Self-Retrieval | ~60 sec |
| 10 | RQ1: Self-Retrieval Results | ~60 sec |
| 11 | RQ2: Stability | ~45 sec |
| 12 | Alpha Sensitivity | ~45 sec |
| 13 | RQ3: Implementation Check | ~30 sec |
| 14 | What Does This Mean? | ~45 sec |
| 15 | Limitations & Future Work | ~30 sec |
| 16 | Closing / Thank You | ~15 sec |
| **Total** | | **~11 min 30 sec** |

*The ~30 seconds of buffer accommodates natural pauses, audience laughter, or brief elaboration on any slide.*
