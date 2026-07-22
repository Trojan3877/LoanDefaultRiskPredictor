# Model Card — Loan Default Risk Candidate

## Intended use

Research and engineering evaluation of default-risk ranking. Output is a review recommendation, not an autonomous approval/decline decision.

## Model and inputs

LightGBM binary classifier over validated loan attributes after fitted target/one-hot/binning transformations. `loan_id` and offline governance attributes are excluded from predictive features.

## Evaluation

The trainer compares an untouched candidate holdout with logistic regression and reports discrimination, probability, calibration, operating-point, confusion, and bootstrap interval evidence. Dated data uses an out-of-time test cohort. No repository result establishes real-world quality.

## Limitations and prohibited use

- No representative or external lending cohort is bundled.
- Group fairness, calibration, and threshold acceptance require dataset-specific review.
- Deterministic reason codes are placeholders until model-faithfulness and adverse-action approval.
- Do not use for lending, pricing, limits, collections, or eligibility without independent approval.

## Required reviewers

Model risk, fair lending, legal/compliance, privacy, security, product policy, and operational owner.
