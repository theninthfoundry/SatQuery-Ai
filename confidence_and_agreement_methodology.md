# Confidence Calibration & Cross-Modal Agreement — Methodology Check

## Part 1: Why "GSD-weighted confidence" isn't yet a probability

A number like `confidence = 0.91` is only meaningful if it satisfies a
**calibration property**:

> Among all predictions the system assigns confidence ≈ p, the fraction
> that are actually correct should be ≈ p.

That property has to be *measured*, not asserted. Right now the pipeline
likely computes something like:

```
confidence = f(model_score, GSD_suitability)
```

which is a **heuristic score**, not a calibrated probability, until you
run the experiment below. Two things can be true at once: the heuristic
might correlate usefully with correctness, and it might still be
wildly miscalibrated (e.g., everything reported as 0.85-0.95 regardless
of true accuracy). You can't tell which without measuring.

### 1.1 Formalize the score first

Don't let GSD "become" a probability by itself. Decompose it into named,
separately-justified components, e.g.:

```
raw_score = w1 * model_confidence        (softmax / logit margin from GeoChat or ChangeNet)
          + w2 * gsd_suitability(GSD)    (task-dependent: is this GSD fine enough
                                           to resolve the claimed feature?)
          + w3 * registration_quality    (bi-temporal / optical-SAR: alignment error)
          + w4 * cross_modal_agreement   (see Part 2)
```

`gsd_suitability` should be a documented function, not a magic constant —
e.g. a step or sigmoid centered on the minimum resolvable size of the
feature class (a 10m-GSD pixel cannot resolve a car; it can resolve a
building footprint). State that function explicitly in your docs so a
judge asking "what does 0.87 mean" has an answer.

### 1.2 Calibrate `raw_score` → probability

`raw_score` is not yet a probability just because it's bounded [0,1].
Fit a calibration map on held-out labeled data:

- **Platt scaling** (logistic): `p = sigmoid(a * raw_score + b)`, fit `a, b`
  by logistic regression against binary correctness labels.
- **Isotonic regression**: non-parametric monotonic map, more flexible,
  needs more data (~hundreds of labeled points minimum) to avoid overfitting.

Either way you need a labeled validation set: (prediction, raw_score,
was_it_actually_correct?) tuples — e.g. from your RSVQA-HR / VRSBench /
CDVQA benchmark splits, or manually adjudicated change-detection polygons.

### 1.3 Measure calibration quality

**Reliability diagram**: bin predictions by predicted confidence into
`M` bins (commonly M=10), and for each bin compute:

```
acc(bin_m)  = (# correct predictions in bin_m) / (# predictions in bin_m)
conf(bin_m) = mean predicted confidence in bin_m
```

Plot `acc(bin_m)` vs `conf(bin_m)` against the y=x diagonal. Points above
the diagonal mean under-confidence; below means over-confidence.

**Expected Calibration Error (ECE)** — the standard scalar summary:

```
ECE = Σ_m ( |B_m| / n ) * | acc(B_m) − conf(B_m) |
```

where `B_m` is the set of predictions in bin `m`, `n` is the total count.
Lower is better; report this number in your Phase 1 report rather than a
bare confidence percentage. There's also **Maximum Calibration Error**
(the max over bins instead of the weighted average) if you want the
worst-case figure for a judge who pushes on edge cases.

**Brier score** (proper scoring rule, no binning needed):

```
Brier = (1/n) * Σ_i (p_i − y_i)^2
```

where `p_i` is predicted probability and `y_i ∈ {0,1}` is the ground-truth
correctness indicator. Lower is better; it rewards both calibration and
sharpness (confident-and-correct beats vague-and-correct).

### 1.4 What to actually report

Instead of "Evidence Engine computes verifiable confidence scores
weighted by GSD," something defensible under questioning is:

> "Confidence is a logistic-calibrated combination of model score, GSD
> suitability for the claimed feature class, and (where applicable)
> cross-modal agreement, calibrated on N held-out labeled examples with
> ECE = X.XX and Brier score = Y.YY."

If you haven't run that calibration yet, label the number explicitly as
a **heuristic priority score**, not a confidence probability, until it is.

---

## Part 2: Cross-modal (optical–SAR) agreement — what "agreement" can mean

"Honest cross-modal agreement score" needs one specific, stated
definition. Three genuinely different things could be meant, and they
have different math and different failure modes:

### 2.1 Feature-level agreement (embedding similarity)

If DOFA produces a shared embedding space for optical and SAR patches:

```
agreement = cosine_similarity(embed_optical, embed_sar)
          = (embed_optical · embed_sar) / (||embed_optical|| ||embed_sar||)
```

**Caveat**: cosine similarity between embeddings from *different sensing
modalities* is only meaningful if the encoder was actually trained/
fine-tuned to align optical and SAR representations of the same location
(contrastive objective, e.g. CLIP-style). If DOFA's wavelength-conditioned
encoder wasn't trained with such an alignment objective, raw cosine
similarity between optical and SAR embeddings has no guaranteed
interpretation — it could be near-constant regardless of true agreement.
**Check this before using it as a score.**

### 2.2 Prediction-level (decision) agreement

If both modalities independently produce a segmentation/classification
(e.g. "built-up" mask from optical, "built-up" mask from SAR backscatter
thresholding), agreement is well-defined as spatial overlap:

```
IoU = |mask_optical ∩ mask_sar| / |mask_optical ∪ mask_sar|
```

or **Cohen's kappa** for chance-corrected agreement on categorical
per-pixel or per-region labels:

```
κ = (p_o − p_e) / (1 − p_e)
```

where `p_o` = observed agreement rate, `p_e` = expected agreement rate
under independence. This is the most defensible option for a judge —
it's a standard, named statistic with a known interpretation (κ > 0.6 is
"substantial agreement" per Landis & Koch), not a bespoke score.

### 2.3 Signal-level correlation

For a continuous claim like "SAR backscatter corroborates optical
brightness change," use **Pearson correlation** between paired,
co-registered pixel/patch values:

```
r = Σ(x_i − x̄)(y_i − ȳ) / sqrt(Σ(x_i − x̄)² Σ(y_i − ȳ)²)
```

x = optical reflectance/NDVI change, y = SAR σ⁰ change, over co-registered
patches. Report r and its p-value (or a confidence interval) — a single
correlation coefficient without a significance check is easy for a judge
to poke a hole in ("is that just noise?").

### 2.4 Recommended fix to your framing

Rename the field from "honest cross-modal agreement score" to something
that states the actual computation, e.g. **"cross-modal decision
concordance (IoU)"** or **"cross-modal signal correlation (Pearson r,
p<0.05)"**. Then in the evidence trace, show the actual numeric agreement
metric with its definition inline — that turns a vague number into a
statistic a judge can independently sanity-check.

### 2.5 Validating that agreement predicts correctness

The strongest version of this feature: show empirically that high
agreement correlates with the fusion output actually being right. Take
your labeled validation set, bucket by agreement score, and compute the
correctness rate per bucket — the same reliability-diagram approach as
Part 1.3. If high agreement doesn't track higher accuracy, the metric
isn't earning its place in the confidence formula, and the honest
result to report is "no predictive value found yet" rather than dropping
it silently.

---

## Part 3: Minimal validation experiment to run before the demo

If time is short, this is the smallest experiment that makes both
claims (calibrated confidence, meaningful agreement) defensible:

1. Take ~50-100 labeled examples across VQA / grounding / change / fusion
   tasks (can reuse benchmark harness splits).
2. For each, record: predicted answer, raw_score components, final
   confidence, cross-modal agreement (if fusion task), and whether the
   prediction was actually correct (human-adjudicated or benchmark
   ground truth).
3. Compute ECE and Brier score on the confidence values.
4. Compute correctness-rate-by-agreement-bucket for fusion tasks.
5. Report both numbers plainly, even if unflattering — "ECE = 0.18,
   under-validated on N=60 examples" is a stronger position in front of
   judges than an unqualified "92% confidence."
