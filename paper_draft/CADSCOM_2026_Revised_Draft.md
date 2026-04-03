<!-- CADSCOM 2026 Formatting Notes for Transfer to Word/LaTeX:
     - Font: Georgia 10pt body, 13pt bold H1, 11pt bold-italic H2, 10pt bold H3
     - Layout: Single column, single-spaced, US Letter, 1-inch margins all around
     - Section headings: NOT numbered, left-justified
     - Table/figure captions: Georgia 10pt bold, centered, beneath the element
     - Running header: abbreviated title (max 8 words), e.g. "Tessituragram Vocal Repertoire Ranking Framework"
     - No author info on cover page for blind review submission
     - References: New MIS Quarterly style
-->

<!-- ============================== COVER PAGE (not counted toward 6-page limit) ============================== -->

# Content-Based Vocal Repertoire Ranking Framework Using Duration-Weighted Pitch Distributions

## Abstract

Choosing vocal repertoire that fits a singer's voice is important for vocal health, yet to the author's knowledge, current tools based on tessituragrams help assess a piece only after it has been selected—they do not recommend new pieces likely to suit the singer. A key factor in vocal fit is tessitura: the pitches on which the voice spends the most time in a given piece, weighted by how long each pitch is sustained. This paper presents a content-based ranking framework that uses duration-weighted tessituragrams—pitch-by-duration profiles extracted from machine-readable musical scores—to rank songs by how well they match a singer's stated preferences. The singer specifies a comfortable vocal range, favorite pitches, and pitches to avoid; the system filters songs by range, constructs an ideal pitch profile from these preferences, and scores each candidate using cosine similarity minus a penalty for time spent on pitches the singer wants to avoid. The framework is validated through two offline experiments using automatically generated user profiles and standard ranking metrics. The first experiment uses a library of 101 nineteenth-century art songs; the second scales the evaluation to 1,655 vocal lines from 1,419 compositions in the same corpus, addressing a prior limitation of small library size. In the initial experiment, the system correctly identifies the source song as its top-ranked result in 84% of test cases (HR@1), outperforming a random baseline (6%). In the expanded experiment with a 16-fold larger library, HR@1 is 55%—expected given increased competition among similar songs—while the system still places the correct song in the top 5 in 86% of cases, compared to 7% for random. Rankings remain stable under small perturbations of user preferences in both experiments (Kendall's τ = 0.85 and 0.84, respectively). The avoid-penalty component does not improve over similarity alone in either experiment under synthetic self-retrieval conditions. These results demonstrate internal consistency, scalability, and feasibility of the ranking framework across library sizes, while evaluation with real singers and more diverse repertoires remains future work.

**Keywords:** tessitura, tessituragrams, vocal repertoire recommendation, content-based recommendation, cosine similarity, music information retrieval, MusicXML

<!-- ============================== PAGE 1 — INTRODUCTION ============================== -->

## Introduction

Choosing repertoire that matches a singer's vocal characteristics is important for vocal health: misalignment between a piece's demands and a singer's capabilities can increase the risk of strain or injury (Apfelbach, 2022; Phyland et al., 1999). A central factor in those demands is tessitura—where in the vocal range the line sits most of the time, i.e. the pitches on which the voice spends the most time (Apfelbach, 2022; Schloneger et al., 2024; Thurmer, 1988). In practice, singers and teachers often filter by a piece's written range (the highest and lowest notes in the score) or by vocal classification such as Fach—the system used in opera to categorize voices by range, weight, and color. A piece's written range alone, however, does not show how much time the voice spends in different parts of that span, and Fach labels are not consistently defined across pedagogical contexts (Schloneger et al., 2024).

Tessituragrams—introduced by Thurmer in 1988—address the first limitation by showing how much time the voice spends on each pitch (Thurmer, 1988). Later work weighted pitches by rhythmic duration, so sustained notes count more than short ones (Titze, 2008). Tools such as Tessa extract tessitura from MusicXML (a machine-readable score format) and produce pitch histograms and statistics for a given piece (Apfelbach, 2022). Such tools are analytic: they help assess a piece after it is chosen, not find pieces whose tessitura is likely to fit the singer.

This paper explores whether tessituragrams can support content-based ranking of repertoire candidates based on singer preferences. We build a tessituragram-based framework that filters songs by the user's range, constructs an ideal pitch profile from favorite pitches and pitches to avoid, and ranks candidates by cosine similarity to that profile minus a penalty for time spent on avoid pitches. The framework is validated through two offline experiments with automatically generated user profiles. The first experiment, using a library of 101 art songs, establishes the framework's internal consistency. The second experiment scales the evaluation to 1,655 vocal lines from 1,419 compositions in the same corpus—a 16-fold increase in library size—to test whether the framework's properties generalize to a larger and more diverse library, directly addressing a limitation identified in the initial evaluation.

The contributions of this research are as follows:

1. A content-based ranking pipeline combining duration-weighted tessituragrams with user-specified favorite pitches and pitches to avoid, scored using cosine similarity minus an avoid-penalty.
2. A two-experiment offline evaluation demonstrating internal consistency, ranking stability, and scalability of the ranking method across library sizes—with comparison to null and cosine-only baselines—using a library of 101 songs and a larger library of 1,655 vocal lines.

<!-- ============================== PAGES 1–2 — RELATED WORK ============================== -->

## Related Work

### *Tessituragram Analysis and Repertoire Selection*

Thurmer (1988) formalized the tessituragram as the distribution of pitch occurrence in the vocal line; Titze (2008) added duration weighting. Recent work uses duration-based and dose-based summaries to characterize demand across works or cycles (Schloneger et al., 2024; Patinka, 2024). On the applied side, Nix (2014) evaluates objective methods—including voice range profiles, tessituragrams, and dosimetry—for matching pieces to singers in pedagogy; Apfelbach's Tessa (2022) automates tessitura extraction from MusicXML. These contributions support evaluating suitability of a chosen piece, but not recommending pieces whose tessitura is likely to fit.

### *Music Information Retrieval*

MIR addresses content-based search and retrieval of music, including symbolic (score-based) methods (Casey et al., 2008; Gurjar and Moon, 2018). For symbolic music, pitch histograms and duration distributions are common features (Corrêa and Rodrigues, 2016). Cosine similarity suits such pitch-indexed vectors because it measures proportional alignment (Müller, 2015). For the voice, octave matters: unlike transposition-invariant melodic similarity (Mongeau and Sankoff, 1990), tessitura modelling must keep pitch in specific octaves to reflect register and demand. Our system is related to the query-by-example paradigm in MIR, though the user supplies pitch preferences rather than an example song (Casey et al., 2008; Müller, 2015).

### *Recommender Evaluation*

Offline evaluation is standard when human relevance judgments are unavailable (Herlocker et al. 2004; Urbano et al. 2013). In music recommendation, Gruson et al. (2019) showed that offline metrics can align with A/B outcomes. Shared implementations of evaluation metrics improve comparability in MIR (Raffel et al. 2014). Common ranking metrics include hit rate at k and mean reciprocal rank; Kendall's τ is standard for comparing two ranked lists (Kendall, 1948). Uncertainty is often quantified with bootstrap confidence intervals (Efron and Tibshirani, 1993). When observations are not independent—for example, when multiple vocal lines are drawn from the same composition—the cluster bootstrap provides correctly calibrated confidence intervals by resampling at the cluster level rather than the observation level (Cameron et al., 2008; Field and Welsh, 2007). We are not aware of prior evaluation of tessitura-based vocal recommenders with these metrics and explicit baselines.

<!-- ============================== PAGES 2–3 — METHOD ============================== -->

## Method

### *Data and Song Library*

All MusicXML source files come from the OpenScore Lieder Corpus, an openly licensed (CC0) collection of art songs with structured metadata for MIR research (Gotham and Jonas, 2022). The corpus is predominantly Lieder (German art song) and French mélodies; tessitura and vocal fit are central concerns in both traditions. We parse MusicXML with music21 (Cuthbert and Ariza 2010), extract the vocal line, and build a tessituragram per vocal line: a mapping from each MIDI pitch (e.g. 60 = middle C) to total duration in quarter-note beats. Duration weighting reflects that sustaining a pitch is more demanding than a brief note (Titze 2008). Table 1 lists features extracted or derived per vocal line.

Two libraries are used. The first (Experiment 1) contains 101 art songs (e.g. Schubert, Clara and Robert Schumann, Debussy, Fauré). The second (Experiment 2) contains 1,655 vocal lines from 1,419 compositions. Because some compositions contain multiple voice parts (e.g. duets), each vocal line is treated separately. Of the 1,655 lines, 342 come from multi-part works and 1,313 from single-voice songs. The expanded library spans a wider range of composers and styles. No human relevance judgments were collected.

| Feature | Source | Description |
|---|---|---|
| Pitch, duration (per note) | MusicXML | Converted to MIDI number; duration in quarter beats, summed per pitch for tessituragram. |
| Part/voice | MusicXML | Vocal line only. |
| Tessituragram | Derived | MIDI pitch → total duration (duration-weighted). |
| min\_midi, max\_midi | Derived | Written pitch range of the vocal part. |
| Composer, title, filename | MusicXML/corpus | Work and file identification. |

**Table 1. Features Extracted from MusicXML and Stored per Vocal Line**

### *Ranking Framework and Scoring*

The system takes three inputs: (1) the singer's vocal range (lowest and highest comfortable MIDI pitch); (2) favorite notes; (3) notes to avoid. It proceeds in three steps.

**Range filter.** Songs whose written range extends beyond the singer's range are excluded (candidate set C).

**Ideal vector construction.** A dense vector over [min\_midi, …, max\_midi] is initialized to a base weight of 0.2, with +1.0 at favorites and −1.0 at avoids. Negative entries are clamped to 0 and the vector is L2-normalized so similarity depends only on direction (Müller, 2015).

**Song scoring and ranking.** Each song's tessituragram is converted to a dense vector and L1-normalised (proportions of total vocal duration per pitch). The final score is:

> final\_score = cosine\_similarity(song, ideal) − α × avoid\_penalty

where α controls the weight of the avoid penalty (α = 0.5 in the main experiments). The avoid penalty is the proportion of the song's vocal duration spent on notes to avoid. Scores are rounded to four decimal places; ties are broken by filename.

### *Synthetic User Profiles and Statistical Methods*

With no human relevance labels, we follow standard offline evaluation practice (Herlocker et al., 2004; Urbano et al., 2013). For a chosen "profile song" we set the user's range to that song's written range, take the top 4 pitches by duration as favorites and the bottom 2 as notes to avoid (disjoint). That song is then treated as the designated correct match. All experiments use random seed 42. Bootstrap 95% confidence intervals use 10,000 resamples (Efron and Tibshirani, 1993).

In Experiment 1, confidence intervals are computed via a standard bootstrap over the unit of analysis (queries or baseline means). In Experiment 2, because multi-part works introduce statistical dependence among vocal lines from the same composition, confidence intervals are computed via a cluster bootstrap that resamples at the work level rather than the individual-line level (Cameron et al., 2008; Field and Welsh, 2007). This produces correctly calibrated intervals that account for within-composition correlation. Where correlations are aggregated across profiles (RQ3), Fisher's z-transformation is used (Fisher, 1915).

<!-- ============================== PAGES 3–5 — RESULTS ============================== -->

## Results

### *Research Question 1 (RQ1): Self-Retrieval Accuracy*

**Question:** When the profile is derived from one vocal line, does the system rank that line first (or in the top 3 or 5)?

**Experiment 1 procedure:** The valid query pool consists of all songs for which at least two candidates remain after range filtering (95 qualified out of 101). We draw 50 queries at random. For each, we build the synthetic profile and run the recommender (α = 0.5), record the rank of the query song, and compute HR@1, HR@3, HR@5, and MRR. We compare the full model (α = 0.5), cosine-only (α = 0), and a null baseline (range filter + random ranking).

**Experiment 2 procedure:** The same methodology is applied to the expanded library (1,655 vocal lines, 1,647 qualified). We draw 200 queries at random (192 from distinct compositions). All other parameters are identical. Confidence intervals use the cluster bootstrap.

Table 2 presents results. In Experiment 1, the full model achieves HR@1 = 0.84 and MRR = 0.91. In Experiment 2, HR@1 = 0.55 and MRR = 0.69. The decline is expected: a 16-fold larger library contains more songs with similar pitch distributions competing for the top rank. Critically, HR@5 remains 0.86 in Experiment 2 (vs. 1.00 in Experiment 1), indicating the correct song nearly always appears among the top recommendations. Both experiments strongly outperform the null baseline (HR@1 = 0.06 and 0.02). The cosine-only model performs comparably to the full model in both experiments, with overlapping CIs. The 45% of Experiment 2 queries not ranked first occur when other songs have sufficiently similar pitch distributions—desirable behavior for a recommendation system.

| Model | | Experiment 1 (101 songs, 50 queries) | | | | Experiment 2 (1,655 lines, 200 queries) | | | |
|---|---|---|---|---|---|---|---|---|---|
| | HR@1 | HR@3 | HR@5 | MRR | HR@1 | HR@3 | HR@5 | MRR |
| Null (random) | 0.06 [0.00, 0.12] | 0.14 [0.06, 0.24] | 0.26 [0.14, 0.38] | 0.18 [0.12, 0.25] | 0.02 [0.00, 0.04] | 0.06 [0.03, 0.09] | 0.07 [0.04, 0.11] | 0.06 [0.04, 0.09] |
| Cosine-only (α = 0) | 0.88 [0.78, 0.96] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.93 [0.87, 0.98] | 0.55 [0.48, 0.61] | 0.78 [0.71, 0.83] | 0.86 [0.80, 0.90] | 0.69 [0.64, 0.73] |
| Full (α = 0.5) | 0.84 [0.72, 0.94] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.91 [0.84, 0.96] | 0.55 [0.48, 0.62] | 0.80 [0.74, 0.85] | 0.86 [0.81, 0.91] | 0.69 [0.63, 0.74] |

**Table 2. Self-Retrieval Accuracy and Baseline Comparison (95% CI from Bootstrap)**

### *Research Question 2 (RQ2): Ranking Stability*

**Question:** When we add or remove one favorite note or note to avoid, how similar is the new ranking to the original?

**Procedure:** In Experiment 1, we use 5 baseline profiles (candidate set ≥ 10 songs each, 130 total perturbations). In Experiment 2, we use 20 baseline profiles (candidate set ≥ 10, 580 total perturbations, all 20 from distinct compositions). For each baseline, we obtain the reference ranking and generate all one-note perturbations (add or remove one favorite or avoid note). For each perturbation we compute Kendall's τ (Kendall, 1948). τ ranges from −1 to 1; values above 0.7 indicate strong agreement. Table 3 gives mean τ per baseline with 95% CI.

Both experiments show strong stability (τ > 0.7). Mean τ for the full model is 0.85 (Experiment 1) and 0.84 (Experiment 2)—near-identical despite the 16-fold increase in library size and 4-fold increase in the number of baseline profiles. Cosine-only is slightly higher in both cases (0.87), with overlapping CIs. The null baseline hovers near τ ≈ 0 as expected.

| Model | Experiment 1 (5 baselines, 130 perturbations) | Experiment 2 (20 baselines, 580 perturbations) |
|---|---|---|
| | Mean τ (95% CI) | Mean τ (95% CI) |
| Null (random) | −0.04 [−0.05, −0.02] | 0.00 [−0.00, 0.01] |
| Cosine-only (α = 0) | 0.87 [0.84, 0.91] | 0.87 [0.86, 0.88] |
| Full (α = 0.5) | 0.85 [0.81, 0.88] | 0.84 [0.82, 0.85] |

**Table 3. Ranking Stability: Mean τ per Baseline (95% CI)**

### *Implementation Verification (RQ3)*

As a verification step, we check three properties of the scoring pipeline in both experiments: (a) Do scores spread out meaningfully? (b) Does final\_score = cos − α × avoid hold numerically? (c) Do components correlate in the directions the formula predicts?

In Experiment 1, we use 25 synthetic profiles (≥ 10 candidates each). In Experiment 2, we use 50 profiles (≥ 10 candidates each, 49 from distinct compositions). In both experiments, the identity residual |final − (cos − α × avoid)| is exactly 0 (mean and max), and regression recovers coefficients of 1.0 (cosine) and −0.5 (avoid) with R² = 1.0, confirming that the scoring formula is implemented exactly as specified. Scores spread meaningfully: the mean range of final\_score is 0.76 in Experiment 1 and 1.03 in Experiment 2—the wider spread in the larger library reflects greater diversity in pitch distributions. All sanity-check correlations (Spearman's ρ; Spearman, 1904) have the expected signs: ρ(final, cos) = 0.987 and 0.989; ρ(final, avoid) = −0.35 and −0.32; ρ(cos, favorite\_overlap) = 0.935 and 0.921.

### *Sensitivity to α*

To assess how sensitive the results are to the avoid-penalty weight, we repeated the self-retrieval and stability experiments for α ∈ {0.0, 0.25, 0.5, 0.75, 1.0} on the same queries and baselines in both experiments. Table 4 shows HR@1, MRR (self-retrieval), and mean τ per baseline (stability) for all five values.

| α | | Experiment 1 (101 songs) | | | Experiment 2 (1,655 lines) | | |
|---|---|---|---|---|---|---|---|
| | HR@1 (95% CI) | MRR (95% CI) | Mean τ (95% CI) | HR@1 (95% CI) | MRR (95% CI) | Mean τ (95% CI) |
| 0.0 | 0.88 [0.78, 0.96] | 0.93 [0.87, 0.98] | 0.87 [0.84, 0.91] | 0.55 [0.48, 0.61] | 0.69 [0.64, 0.74] | 0.87 [0.86, 0.88] |
| 0.25 | 0.86 [0.76, 0.94] | 0.92 [0.86, 0.97] | 0.86 [0.83, 0.88] | 0.56 [0.49, 0.62] | 0.69 [0.64, 0.74] | 0.85 [0.84, 0.86] |
| 0.5 | 0.84 [0.74, 0.94] | 0.91 [0.84, 0.96] | 0.85 [0.81, 0.88] | 0.55 [0.48, 0.62] | 0.69 [0.64, 0.73] | 0.84 [0.82, 0.85] |
| 0.75 | 0.84 [0.74, 0.94] | 0.91 [0.84, 0.96] | 0.83 [0.80, 0.87] | 0.54 [0.47, 0.61] | 0.68 [0.63, 0.73] | 0.83 [0.81, 0.84] |
| 1.0 | 0.84 [0.74, 0.94] | 0.91 [0.84, 0.96] | 0.83 [0.78, 0.86] | 0.54 [0.47, 0.61] | 0.67 [0.62, 0.72] | 0.82 [0.80, 0.83] |

**Table 4. Alpha Sensitivity: Self-Retrieval and Stability across α Values (95% CI)**

In both experiments, metrics remain high across all α values and vary smoothly, confirming that the system is not brittle at any single operating point. In Experiment 1, HR@1 varies by only 4 percentage points across the full α range; in Experiment 2, by only 2 percentage points. Stability (mean τ) decreases monotonically as α increases in both experiments but remains at or above 0.82 at α = 1.0—well within the range of strong agreement. The pattern is consistent across library sizes: the avoid penalty does not improve self-retrieval accuracy, but it does not substantially degrade performance either, and α = 0.5 provides a balanced trade-off between responsiveness to avoid preferences and ranking stability.

<!-- ============================== PAGES 5–6 — DISCUSSION, LIMITATIONS, CONCLUSION ============================== -->

## Discussion and Limitations

The results across both experiments confirm that range filtering combined with cosine similarity over duration-weighted pitch profiles captures meaningful differences between songs and produces stable rankings that generalize across library sizes. The second experiment directly addresses a key limitation of the initial evaluation—small library size—by scaling to 1,655 vocal lines from 1,419 compositions. Key findings replicate: ranking stability is nearly identical (τ = 0.85 vs. 0.84), the scoring formula is verified as exactly correct, and both models strongly outperform the null baseline.

The decline in HR@1 from 0.84 to 0.55 is an expected consequence of the larger library: more items with similar pitch distributions compete for the top rank. The high HR@5 of 0.86 in Experiment 2 indicates the system reliably surfaces the correct song near the top—for a recommendation system, surfacing several well-matching songs may better reflect practical utility than HR@1 alone.

In both experiments, the cosine-only model performs comparably to the full model. The avoid penalty is conceptually motivated but in synthetic self-retrieval—where avoids are the two least-used pitches—it contributes little discriminative signal. Its value may require real user preferences or a more heterogeneous library to manifest. The second experiment also introduced the cluster bootstrap for confidence intervals, correctly accounting for non-independent vocal lines from multi-part works (Cameron et al., 2008).

Several limitations qualify these findings:

- **No human judgments.** Both experiments use synthetic profiles; results indicate internal consistency and robustness, not user satisfaction.
- **Self-retrieval circularity.** The synthetic profile is derived from the same representation used for scoring, so the task tests internal consistency rather than external validity.
- **Single corpus.** Both libraries are drawn from the OpenScore Lieder Corpus, spanning primarily nineteenth- and early-twentieth-century European art song. The expanded library is more stylistically diverse but still limited to this tradition. Generalization to opera, musical theatre, popular song, or other traditions remains untested.
- **Pitch and duration only.** Other factors that affect vocal suitability—dynamics, tempo, text setting, accompaniment difficulty—are not modelled.
- **Avoid penalty does not outperform cosine-only.** In both experiments, the full model does not improve on cosine-only for any metric. The avoid term's value may depend on richer preference data or a more heterogeneous library.

## Conclusion

We presented a content-based ranking framework that uses duration-weighted tessituragrams to rank vocal repertoire by pitch-preference match. Validated across two experiments—101 songs and 1,655 vocal lines from 1,419 compositions—both the full model and cosine-only baseline strongly outperform a null baseline. Rankings are stable under small preference perturbations (τ ≥ 0.82 across all conditions), and implementation verification confirms exact formula alignment in both experiments. The framework scales from 101 to 1,655 items without degradation in stability, and HR@5 remains 0.86 in the larger library. The avoid penalty does not improve over cosine-only in synthetic self-retrieval, likely due to limited discriminative signal from synthetically derived avoids. Future work should evaluate with real user preferences and human relevance judgments, expand to more diverse repertoire (e.g. opera, musical theatre, popular song), and incorporate additional factors such as dynamics, tempo, and text setting.

<!-- ============================== REFERENCES (not counted toward 6-page limit) ============================== -->

## References

Apfelbach, C. S. 2022. "Tessa: A Novel MATLAB Program for Automated Tessitura Analysis," *Journal of Voice* (36:5), pp. 599–607. (https://doi.org/10.1016/j.jvoice.2020.07.039).

Cameron, A. C., Gelbach, J. B., and Miller, D. L. 2008. "Bootstrap-Based Improvements for Inference with Clustered Errors," *Review of Economics and Statistics* (90:3), pp. 414–427. (https://doi.org/10.1162/rest.90.3.414).

Casey, M. A., Veltkamp, R., Goto, M., Leman, M., Rhodes, C., and Slaney, M. 2008. "Content-Based Music Information Retrieval: Current Directions and Future Challenges," *Proceedings of the IEEE* (96:4), pp. 668–696. (https://doi.org/10.1109/JPROC.2008.916370).

Corrêa, D. C., and Rodrigues, F. A. 2016. "A Survey on Symbolic Data-Based Music Genre Classification," *Expert Systems with Applications* (60), pp. 190–210. (https://doi.org/10.1016/j.eswa.2016.04.008).

Cuthbert, M. S., and Ariza, C. 2010. "music21: A Toolkit for Computer-Aided Musicology and Symbolic Music Data," in *Proceedings of the 11th International Society for Music Information Retrieval Conference*, pp. 637–642. (https://ismir2010.ismir.net/proceedings/ismir2010-108.pdf).

Efron, B., and Tibshirani, R. J. 1993. *An Introduction to the Bootstrap*, New York, NY: Chapman and Hall/CRC. (https://doi.org/10.1201/9780429246593).

Field, C. A., and Welsh, A. H. 2007. "Bootstrapping Clustered Data," *Journal of the Royal Statistical Society: Series B* (69:3), pp. 369–390. (https://doi.org/10.1111/j.1467-9868.2007.00593.x).

Fisher, R. A. 1915. "Frequency Distribution of the Values of the Correlation Coefficient in Samples from an Indefinitely Large Population," *Biometrika* (10:4), pp. 507–521. (https://doi.org/10.1093/biomet/10.4.507).

Gotham, M. R. H., and Jonas, P. 2022. "The OpenScore Lieder Corpus," in *Music Encoding Conference Proceedings 2021*, S. Münnich and D. Rizo (eds.), Humanities Commons, pp. 131–136. (https://doi.org/10.17613/1my2-dm23).

Gruson, A., Chandar, P., Charbuillet, C., McInerney, J., Hansen, S., Tardieu, D., and Carterette, B. 2019. "Offline Evaluation to Make Decisions about Playlist Recommendation Algorithms," in *Proceedings of the 12th ACM International Conference on Web Search and Data Mining*, New York, NY: ACM, pp. 420–428. (https://doi.org/10.1145/3289600.3291027).

Gurjar, K., and Moon, Y. S. 2018. "A Comparative Analysis of Music Similarity Measures in Music Information Retrieval Systems," *Journal of Information Processing Systems* (14:1), pp. 32–55. (https://jips-k.org/digital-library/2018/14/1/32).

Herlocker, J. L., Konstan, J. A., Terveen, L. G., and Riedl, J. T. 2004. "Evaluating Collaborative Filtering Recommender Systems," *ACM Transactions on Information Systems* (22:1), pp. 5–53. (https://doi.org/10.1145/963770.963772).

Kendall, M. G. 1948. *Rank Correlation Methods*, London, UK: Charles Griffin. (https://search.worldcat.org/title/3641982).

Mongeau, M., and Sankoff, D. 1990. "Comparison of Musical Sequences," *Computers and the Humanities* (24:3), pp. 161–175. (https://doi.org/10.1007/BF00117340).

Müller, M. 2015. *Fundamentals of Music Processing: Audio, Analysis, Algorithms, Applications*, Cham, Switzerland: Springer. (https://doi.org/10.1007/978-3-319-21945-5).

Nix, J. 2014. "Measuring Mozart: A Pilot Study Testing the Accuracy of Objective Methods for Matching a Song to a Singer," *Journal of Singing* (70:5), pp. 561–572.

Patinka, P. M. 2024. "Quantitative Analysis of Tessitura and Density in Franz Schubert's Die schöne Müllerin," *Journal of Voice*, Advance online publication. (https://doi.org/10.1016/j.jvoice.2024.09.035).

Phyland, D. J., Oates, J. M., and Greenwood, K. M. 1999. "Self-Reported Voice Problems among Three Groups of Professional Singers," *Journal of Voice* (13:4), pp. 602–611. (https://doi.org/10.1016/S0892-1997(99)80014-9).

Raffel, C., McFee, B., Humphrey, E. J., Salamon, J., Nieto, O., Liang, D., and Ellis, D. P. W. 2014. "mir_eval: A Transparent Implementation of Common MIR Metrics," in *Proceedings of the 15th International Society for Music Information Retrieval Conference*, pp. 367–372. (https://archives.ismir.net/ismir2014/poster/000039.pdf).

Schloneger, M., Hunter, E. J., and Maxfield, L. 2024. "Quantifying Vocal Repertoire Tessituras through Real-Time Measures," *Journal of Voice* (38:1), pp. 247.e11–247.e25. (https://doi.org/10.1016/j.jvoice.2021.06.019).

Spearman, C. 1904. "The Proof and Measurement of Association between Two Things," *American Journal of Psychology* (15:1), pp. 72–101. (https://doi.org/10.2307/1412159).

Thurmer, S. 1988. "The Tessiturogram," *Journal of Voice* (2:4), pp. 327–329. (https://doi.org/10.1016/S0892-1997(88)80025-0).

Titze, I. R. 2008. "Quantifying Tessitura in a Song," *Journal of Singing* (65:1), pp. 59–61. (https://vocology.utah.edu/_resources/documents/quantifying_tessitura_titze.pdf).

Urbano, J., Schedl, M., and Serra, X. 2013. "Evaluation in Music Information Retrieval," *Journal of Intelligent Information Systems* (41:2), pp. 345–369. (https://doi.org/10.1007/s10844-013-0249-4).
