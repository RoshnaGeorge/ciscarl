"""Content for the detailed 31-step report."""
from pathlib import Path

ROOT = Path(r"C:\Users\roshn\OneDrive\Desktop\Amrita\SEM 5\ML\Project")
FIG = ROOT / "paper" / "figs"
EXH = ROOT / "paper" / "exhibits"

STEPS = [
    {
        "title": "Environment and reproducibility",
        "code": "ciscarl2/audit.py, requirements.txt",
        "what": ("Before touching the data, the project fixes the Python version and every package, "
                 "loads the data path, and runs an audit. The audit checks small, hand-verifiable "
                 "things: a rule's conditions must match the patients it selects, tree leaves must "
                 "not overlap, the influence-function contrast must equal the direct formula, and "
                 "the purity, capture and Jaccard definitions must match hand counts. It also "
                 "simulates a tiny dataset with a known answer to check the AIPW estimator."),
        "result": ("All checks pass. AIPW bias is +0.0031 with a standard deviation of 0.0130, and "
                   "the two arm means are within 0.002 of the truth."),
        "meaning": ("The building blocks are correct before any result is quoted. If this audit "
                    "failed, the pipeline would stop here; because it passes, the environment and "
                    "seeds can be frozen for the rest of the study."),
    },
    {
        "title": "Study the dataset",
        "code": "notebook Step 2 (pandas profiling)",
        "what": ("The raw file has 27 columns. Each column gets a role: identifier, outcome, "
                 "treatment, post-baseline, design, or baseline covariate. The project then checks "
                 "missingness, variance, redundancy, sparsity and implausible values, so the "
                 "covariate set is chosen from evidence rather than from habit."),
        "result": ("Fifteen of the 27 columns are not baseline covariates. Of the 16 baseline "
                   "candidates, four are removed: zprior is constant in arms 0/1, z30 agrees with "
                   "str2 in 94.8% of patients, oprior is present in only 2.4%, and preanti is a "
                   "redundant prior-treatment duration. cd496 is missing for 797 of 2,139 patients "
                   "and is post-baseline. Three patients have cd40 = 0, 199 fall outside the trial's "
                   "200–500 range, and 13 are minors."),
        "meaning": ("This step produces the 12 baseline covariates used everywhere later. Each "
                    "exclusion has a reason, so the model is not silently dropping difficult "
                    "patients or keeping a duplicate variable."),
    },
    {
        "title": "Cohort and outcome definition",
        "code": "notebook Step 3 (cohort and endpoint construction)",
        "what": ("The analysis sample, time origin, composite event and horizon are fixed. The "
                 "composite event is a CD4 decline of at least 50, AIDS progression, or death. The "
                 "project then checks that the horizon is inside the observed follow-up and that "
                 "enough patients are still being followed at that point."),
        "result": ("1,054 of 2,139 patients remain (522 treated and 532 control). There are 284 "
                   "composite events (26.9%), 103 patients are censored before day 730 (9.8%), and "
                   "750 (71.2%) are still at risk at the horizon. Median observed time is 989 days, "
                   "maximum 1,231."),
        "meaning": ("The horizon is observable rather than extrapolated. Censoring before 730 days "
                    "is modest but real, so the estimator must adjust for it. The 284 events are the "
                    "binding limit on subgroup precision, which is why accuracy is measured in "
                    "simulation."),
    },
    {
        "title": "Split the data",
        "code": "notebook Step 4 (train_test_split; seeds 2024/2025)",
        "what": ("The cohort is divided into discovery, validation and assessment, stratified by "
                 "treatment and event together. The row indices are frozen, so the same patients "
                 "stay in the same role for the whole project."),
        "result": ("The split is 527 / 263 / 264, with event rates 27.1% / 26.6% / 26.9% — a spread "
                   "of 0.5 points, compared with 2.8 points when stratifying on treatment alone. A "
                   "separate ratio study found 50/25/25 gave the highest capture (0.479) at purity "
                   "0.941 with 80% commitment. Every ratio produced 20 distinct rules from 20 "
                   "splits."),
        "meaning": ("Validation and assessment are small, so an uneven event rate would add noise "
                    "to every later comparison; joint stratification removes that noise. The "
                    "50/25/25 ratio is kept because it balances discovery size and validation "
                    "precision. The rule instability is recorded now, not hidden."),
    },
    {
        "title": "Choose the horizon",
        "code": "ciscarl2/estimators.py, notebook Step 5",
        "what": ("Several candidate horizons are evaluated under pre-declared constraints: at least "
                 "150 events, at least 60% of patients still at risk, and at most 15% censoring. "
                 "The horizon is not chosen by picking the largest estimated effect."),
        "result": ("The minimum standard error is at 365 days, the maximum signal-to-noise ratio is "
                   "around 900 days, and 730 days sits between them with 71% of the cohort at risk "
                   "and under 10% censored. The constraints admit roughly 550–900 days, and 730 is "
                   "fixed inside that range as the two-year window. A sensitivity analysis covers "
                   "365 and 1,095 days."),
        "meaning": ("Choosing the horizon where the effect looks largest would be selection on the "
                    "outcome. 730 days is a defensible compromise inside a range that satisfies "
                    "precision constraints, and the sensitivity analysis shows how much the answer "
                    "moves at the edges."),
    },
    {
        "title": "Preprocessing fitted on discovery",
        "code": "ciscarl2/estimators.py, notebook Step 6",
        "what": ("The scaler is fitted on the discovery partition only. The step then checks whether "
                 "standardisation is actually required by the Cox prediction formula, and tests "
                 "common transforms such as logarithms and winsorising."),
        "result": ("Discovery means differ from full-cohort means (cd80 1,019.5 vs 995.7; drugs 0.112 "
                   "vs 0.129), which proves the scaler never saw validation or assessment. With raw "
                   "covariates the predicted control survival at 730 days is 0.909; with "
                   "standardised covariates it is 0.732, a maximum per-patient difference of 0.43. "
                   "Log transformation and winsorising change nothing once the model is fitted."),
        "meaning": ("Standardisation is a correctness requirement, not a convenience. The prediction "
                    "formula assumes centred covariates, and the nuisance model is weakly penalised, "
                    "so scale affects the fit. Fitting the scaler on discovery only keeps the "
                    "validation and assessment partitions untouched."),
    },
    {
        "title": "Leakage checklist",
        "code": "notebook Step 7 (mechanical leakage checks)",
        "what": ("This step proves mechanically that no validation or assessment information entered "
                 "any fitted quantity. It checks the covariate list, the scaler means and the "
                 "partition membership."),
        "result": ("No post-baseline or outcome column is in X. The scaler means equal the discovery "
                   "means and differ from the full-cohort means. The three partitions share no "
                   "patient and have the intended sizes."),
        "meaning": ("The mechanical leakage channels are closed. The remaining risk is analyst-side: "
                    "looking at assessment before the analysis is frozen. That is controlled by the "
                    "order of the notebook, not by code, which is why the notebook separates "
                    "discovery, validation and assessment so strictly."),
    },
    {
        "title": "Nuisance estimation",
        "code": "ciscarl2/estimators.py (crossfit_nuisances)",
        "what": ("Two nuisance models are fitted on discovery: a survival model for each treatment "
                 "arm and a conditional censoring model. Both use five-fold cross-fitting, so a "
                 "patient's own outcome never helps predict that patient. Censoring weights are then "
                 "capped to stop a few extreme values from dominating."),
        "result": ("Fold sizes are 106/106/105/105/105. Weight caps range from 1.23 to 1.35. Of 527 "
                   "patients, 373 carry a positive weight; the maximum weight is 1.335 and the 99th "
                   "percentile is 1.31. Effective sample size is 372 (71% of discovery), and 10.4% "
                   "of discovery patients are censored before day 730."),
        "meaning": ("The weights barely bind, so the estimate rests on observed follow-up rather "
                    "than on extrapolation. Cross-fitting is still required because the nuisances "
                    "are fitted on the same patients they later score. An effective sample size of "
                    "372 is the honest denominator for precision claims."),
    },
    {
        "title": "Target construction (AIPW)",
        "code": "ciscarl2/estimators.py, ciscarl2/gate2.py (pseudo_outcome)",
        "what": ("The two nuisance models are combined into one pseudo-outcome per patient. This "
                 "number is the AIPW estimate of that patient's treatment effect: it uses the "
                 "outcome model but also corrects it with the observed outcome, so it stays "
                 "consistent if one of the models is wrong."),
        "result": ("The pseudo-outcome is centred at +0.180 with a standard deviation of 0.997. The "
                   "audit showed AIPW bias +0.0031 (SD 0.0130) and arm means within 0.002. The "
                   "global proportional-hazards test does not reject (p = 0.235 and 0.368), but cd40 "
                   "violates in both arms (p = 0.021, 0.023). Efron and Breslow tie handling differ "
                   "by at most 0.0014. Calibration at 730 days has a weighted mean absolute gap of "
                   "0.032."),
        "meaning": ("The pseudo-outcome is the target the tree needs: one number per patient whose "
                    "average is the treatment effect, already adjusted for censoring. Its spread "
                    "near 1 is the heterogeneity signal; if it were tightly concentrated, no rule "
                    "could beat the constant. The cd40 violation is a limitation, not a reason to "
                    "abandon the model, because the global test holds."),
    },
    {
        "title": "Rule discovery (decision tree)",
        "code": "ciscarl2/rules.py, ciscarl2/gate11.py (_cart)",
        "what": ("A small regression tree is fitted to the pseudo-outcome. Each root-to-leaf path "
                 "becomes a candidate rule, such as 'cd40 ≤ 407.5 AND wtkg > 71.0'. Depth is capped "
                 "at three so a rule has at most three conditions and can be read aloud."),
        "result": ("The tree produces six leaves with supports from 60 to 173 patients and mean "
                   "pseudo-outcomes from −0.184 to +0.556. Two leaves are negative and one is "
                   "strongly positive."),
        "meaning": ("The tree separates a high-benefit subgroup from a negative one — exactly the "
                    "heterogeneity the method exists to find. Two of six leaves being negative also "
                    "shows that 'treat the best leaf' is not the same as 'treat everyone above "
                    "average'. Depth 3 is fixed for interpretability; leaf size is tuned later."),
    },
    {
        "title": "Selection and commitment",
        "code": "ciscarl2/estimators.py, notebook Step 11",
        "what": ("The support floor is applied: a leaf must contain at least 200 discovery patients "
                 "to be selected. The chosen rule is then re-estimated on validation, and treatment "
                 "is recommended only if the one-sided 95% lower confidence bound is above zero."),
        "result": ("No leaf reaches 200 patients (the largest has 173), so the fallback is used and "
                   "leaf 2 is selected: cd40 ≤ 407.5 & wtkg > 71.0 & homo ≤ 0.5, with 61 discovery "
                   "patients. On validation (n = 31) the effect is +0.116 (SE 0.222), giving a lower "
                   "bound of −0.250 and the decision INSUFFICIENT. On assessment the rule shows "
                   "+0.401 [+0.033, +0.770] on 38 patients, but that is descriptive only."),
        "meaning": ("The support floor cannot bind at 527 discovery patients, and the validation "
                    "partition is too small to certify a 61-patient leaf. The model therefore "
                    "refuses to recommend treatment. That is the commitment layer doing its job, not "
                    "a bug."),
    },
    {
        "title": "Simulation harness",
        "code": "ciscarl2/dgp.py",
        "what": ("Real data cannot tell us whether a subgroup is correct. The project therefore "
                 "builds semi-synthetic trials from the real ACTG175 covariate matrix, generates "
                 "survival and censoring times, and adds a known treatment effect in one or two "
                 "regions. Because the effect is generated, every patient's true benefit is known."),
        "result": ("The harness gives 25.5% prevalence, a 20.0% event rate, 10.1% censoring, a true "
                   "average effect of +0.050, and a true effect of +0.195 inside the region and 0 "
                   "outside."),
        "meaning": ("The truth is analytic, so accuracy, purity and capture can be computed honestly. "
                    "The marginal effect is only +0.05 because most patients do not benefit; that "
                    "dilution is why a model predicting the average everywhere cannot win, and why "
                    "capture and purity are the informative metrics."),
    },
    {
        "title": "First result: the constant baseline",
        "code": "ciscarl2/gate17.py, results/gate17_summary.csv",
        "what": ("The rule model is compared with the simplest possible policy: give everyone the "
                 "same marginal effect. The comparison is repeated at 2,000, 4,000 and 6,000 "
                 "patients, with 40 seeds per cell. An oracle model that knows the true effect is "
                 "included as an upper bound."),
        "result": ("At n = 2,000 the rule model is worse than the constant (−26.4%, only 17.5% of "
                   "replications better). At 4,000 it is marginal (+4.5%, 55% better). At 6,000 it "
                   "is clearly better (+21.7%, 85% better). The oracle sits 40–60 points higher "
                   "throughout."),
        "meaning": ("The method has a measured operating range, not a universal advantage. Below "
                    "roughly 5,000 patients it should not be used. The gap to the oracle is a "
                    "discovery gap, not an information gap: the signal exists, but a depth-3 tree "
                    "cannot recover it at small sample sizes."),
    },
    {
        "title": "Support floor",
        "code": "ciscarl2/gate21.py, gate23.py, gate30.py",
        "what": ("The minimum subgroup size is swept to measure the trade-off between purity (how "
                 "many treated patients truly benefit) and capture (how much of the total benefit "
                 "the rule finds). The sweep includes no floor, 100, 200 and 400 patients, and a "
                 "proportional floor at small sample sizes."),
        "result": ("In the two-region design, no floor gives capture 0.149 and purity 0.774; a floor "
                   "of 100 gives 0.246/0.847; 200 gives 0.364/0.820; 400 gives 0.441/0.778. In the "
                   "single-region design, no floor gives 0.228/0.626 and a floor of 200 gives "
                   "0.514/0.821. At n = 2,000 the absolute floor gives purity 0.47 and commitment "
                   "17.5%, while a 5% proportional floor gives 0.73 and 30%."),
        "meaning": ("The floor roughly triples capture at a purity cost of about 0.02 in the "
                    "two-region design, and improves purity in the single-region design. A floor of "
                    "400 buys more capture but gives purity back, so 200 is the better operating "
                    "point. At small n the absolute floor is disproportionate, which is a documented "
                    "limitation."),
    },
    {
        "title": "Calibration",
        "code": "ciscarl2/gate30.py (shrinkage variants)",
        "what": ("Leaf effects are noisy because each leaf contains only a few dozen patients. "
                 "Calibration pulls those noisy effects toward the overall average. The project "
                 "compares no calibration with empirical-Bayes shrinkage, using 80 paired "
                 "replications across two designs."),
        "result": ("Shrinkage lowers MAE by 0.0051 [−0.0077, −0.0025] in the single-region design "
                   "and 0.0026 [−0.0048, −0.0005] in the two-region design. Purity, capture, "
                   "commitment and rank correlation are unchanged. The head-to-head with SCRE moves "
                   "from a significant deficit to a tie."),
        "meaning": ("The pattern is pure variance reduction: the leaf means are noisy, and pulling "
                    "them toward the average improves prediction without changing who is treated. "
                    "Because this was chosen after the SCRE comparison, it is reported as a post-hoc "
                    "calibration (C200-S), confirmed on fresh seeds, not merged into the frozen "
                    "configuration."),
    },
    {
        "title": "Nuisance and estimator comparison",
        "code": "ciscarl2/gate31.py, gate36.py, gate39.py",
        "what": ("Three alternatives are tested against the frozen choices: flexible outcome models "
                 "(random survival forest, gradient boosting, equal-weight stacking), a fixed-"
                 "horizon TMLE estimator, and learned stacking of Cox, RSF and GBM. Everything else "
                 "is held fixed."),
        "result": ("Cox has the best Brier score (0.0028 single, 0.0033 two). Stacking lowers "
                   "patient-level MAE (0.0475/0.0504 vs 0.0517/0.0579) but loses 0.030 purity in the "
                   "two-region design and costs 136–260 s per replication vs 0.002 s. GBM loses "
                   "0.036 purity. TMLE is purer (+0.064/+0.068) but its MAE is 0.089/0.080 worse and "
                   "Brier is 0.015/0.014 worse. The learned stack puts about 0.77 weight on Cox and "
                   "is indistinguishable from Cox (+0.0007/+0.0001 MAE)."),
        "meaning": ("Cox and AIPW are retained. A flexible model buys a small MAE gain and pays with "
                    "purity, calibration and a very large cost. TMLE is not a patient-level "
                    "improvement. The result is a tested negative result for complexity, not an "
                    "unexamined preference for the incumbent."),
    },
    {
        "title": "Rule learners",
        "code": "ciscarl2/gate32.py",
        "what": ("Five learners are compared on the same pseudo-outcome and the same selection "
                 "protocol: regression CART, cost-complexity-pruned CART, PRIM peeling boxes, a "
                 "classification tree on the sign of the effect, and boosting distillation."),
        "result": ("Pruned CART gains capture in the two-region design (+0.261) but loses 0.173 "
                   "purity, nearly nine times the allowed loss of 0.02. The classification tree "
                   "loses 0.219/0.110 purity. PRIM loses both capture and purity and needs 4.6–4.8 "
                   "conditions. Boosting is the only learner with a better two-region MAE (−0.0029) "
                   "but loses capture (−0.092) and purity (−0.050) and costs 25–105 s per "
                   "replication."),
        "meaning": ("No alternative meets the pre-registered guardrails. Regression CART is kept. "
                    "Higher capture is not worth a rule that treats many people who do not benefit."),
    },
    {
        "title": "Hyperparameter tuning",
        "code": "ciscarl2/nested_tune.py",
        "what": ("Depth, leaf size and the splitting criterion are tuned by five-fold cross-"
                 "validation inside discovery. The important detail is that the nuisance models are "
                 "refitted inside every inner fold, so the inner validation rows do not influence "
                 "the pseudo-outcome used to tune the tree."),
        "result": ("Under nested refitting the best configuration is depth 4 / leaf 60 / squared "
                   "error at 0.8633; the frozen depth 3 / leaf 60 / squared error is 0.8638, a "
                   "difference of 0.0005 against a fold SD of about 0.02. The earlier grid, which "
                   "tuned on a pseudo-outcome computed once, reported 0.824 for absolute error "
                   "versus 0.871 for squared error."),
        "meaning": ("The earlier gap was optimism from nuisance leakage, not a real gain. With "
                    "honest nested refitting, no configuration beats the frozen one. The false claim "
                    "was withdrawn, and depth 3 was kept."),
    },
    {
        "title": "Freeze the configuration",
        "code": "notebook Step 19, results/CANONICAL_RESULTS.md",
        "what": ("Every modelling decision is written into one record, with the evidence and the "
                 "number that produced it. The record separates design decisions (fixed by the "
                 "protocol) from experimental decisions (kept only after a comparison) and "
                 "post-hoc calibration."),
        "result": ("Sixteen decisions are recorded with their evidence. The two choices changed "
                   "after seeing results — the commitment criterion and the shrinkage — are labelled "
                   "as post-hoc."),
        "meaning": ("Every value in the final model is traceable. A reader can tell the frozen "
                    "design from the calibration, which is what stops the final model from becoming "
                    "a pile of post-hoc choices."),
    },
    {
        "title": "Confirmation on fresh seeds",
        "code": "ciscarl2/gate30.py (confirmation block, 320100–320139)",
        "what": ("The frozen configuration is re-run on seeds it has never seen, with the previous "
                 "configuration kept as the control. This is the step that turns a tuning result "
                 "into a confirmed result."),
        "result": ("Shrinkage reproduces its direction: single-region ΔMAE −0.0047 (p = 0.022), "
                   "two-region −0.0027 (p = 0.078), pooled −0.0051 and −0.0026."),
        "meaning": ("A gain on tuning seeds is only a proposal. The single-region effect survives "
                    "confirmation; the two-region effect is directionally consistent but not "
                    "individually significant. That qualification is carried into the paper instead "
                    "of being rounded away."),
    },
    {
        "title": "Assessment evaluation",
        "code": "results/sweep1000_two_summary.csv, sweep1000_stress_summary.csv",
        "what": ("The frozen model is scored once on the untouched assessment partition, using 1,000 "
                 "replications per scenario. The metrics cover purity, capture, coverage, benefit "
                 "per treated patient, commitment, null treatment and MAE."),
        "result": ("In the two-region design, purity is 0.856 (SD 0.166), median 0.925, 10th "
                   "percentile 0.603, and 68.7% of committed runs are above 0.80. Coverage is 0.135, "
                   "capture 0.304, benefit per treated patient 0.164, commitment 72.5%, null rate "
                   "0%, and MAE 0.0701. The joint stress cell gives 0.844, 0.915, 0.579, 65.5%, "
                   "0.136, 0.294, 0.159, 68.2%, 0% and 0.0701."),
        "meaning": ("The policy treats about one patient in seven and, in two thirds of runs, finds "
                    "a leaf that is at least 80% pure. The mean hides a bimodal distribution: the "
                    "median is 0.925 but the bottom decile is 0.60. Capture 0.30 is the direct cost "
                    "of treating only 13% of patients, and the 0% null rate shows the gate never "
                    "recommends a harmful leaf."),
    },
    {
        "title": "Baseline comparison (SCRE)",
        "code": "ciscarl2/gate28.py, gate40.py, policy_eval.py",
        "what": ("CISCaRL is compared with SCRE, a survival causal rule ensemble, on identical "
                 "splits, the same 730-day horizon and the same patients. The comparison covers "
                 "accuracy, purity, capture, benefit per treated patient and policy value. SCRE's "
                 "regularisation path is also checked so the conclusion does not depend on one "
                 "tuning value."),
        "result": ("The frozen model is worse on MAE in both designs (+0.0062, p < 0.001; +0.0031, "
                   "p = 0.044). After shrinkage the difference is +0.0011 (p = 0.48) and +0.0004 "
                   "(p = 0.76), a tie. Purity is 0.890 vs 0.437, benefit per treated patient 0.174 "
                   "vs 0.085, and coverage 0.133 vs 0.548. At zero treatment cost, treat-all has the "
                   "highest policy value; at a cost of 0.05–0.10, C200 has the highest net benefit. "
                   "The validation interval covers the true rule effect in 92.5% of replications. "
                   "The chosen SCRE alpha is within 0.0010–0.0017 MAE of the best path alpha."),
        "meaning": ("SCRE wins on accuracy and coverage; CISCaRL wins on purity and benefit per "
                    "treated patient, and it can abstain. Neither dominates. The honest claim is "
                    "two-sided: comparable accuracy after calibration, higher precision, an "
                    "abstention layer, and a large coverage cost."),
    },
    {
        "title": "Real-data run (ACTG175)",
        "code": "ciscarl2/gate13.py, ciscarl2/scre_vs_ciscarl.py",
        "what": ("The frozen pipeline is applied to the real trial. The step reports both what the "
                 "model estimates and what it refuses to claim. A Kaplan–Meier check and a "
                 "censoring-weight sensitivity analysis are included, because the real data have no "
                 "individual treatment-effect truth."),
        "result": ("Overall τ(730) = +0.124 [−0.002, +0.250]. The selected rule has 61 discovery "
                   "patients; validation is +0.116 (SE 0.222, lower bound −0.250) and is not "
                   "committed. Assessment gives +0.401 [+0.033, +0.770] on 38 patients. The "
                   "unadjusted Kaplan–Meier difference for the rule is +0.341 [+0.194, +0.494], and "
                   "the marginal Kaplan–Meier difference is +0.133, matching the AIPW estimate."),
        "meaning": ("Two honest statements follow. The overall verdict is not robust to the "
                    "partition: the treatment-only split gave +0.143 [0.025, 0.262] while the "
                    "balanced split gives +0.124 [−0.002, 0.250]. The point estimate is stable near "
                    "0.13, but its significance is not. The subgroup cannot be certified with 31 "
                    "validation patients and a lower bound of −0.250, so the model abstains."),
    },
    {
        "title": "Ablations",
        "code": "ciscarl2/gate37.py, gate38.py, gate42.py, gate43.py, gate44.py",
        "what": ("The choices a reader could challenge are tested: the covariate set, the horizon, "
                 "and robustness to missingness. A dense horizon grid and two independent horizon "
                 "selection rules are used, followed by a 20-split stability test."),
        "result": ("Adding the four excluded baseline history columns leaves the rule unchanged. The "
                   "horizon does change the rule: 365 days gives 7 leaves and +0.062; 730 gives 6 "
                   "leaves and +0.180; 1,095 gives 5 leaves and +0.162. Five per cent missingness in "
                   "cd40 changes the leaf to a cd80/race split. No horizon meets every criterion. A "
                   "single split prefers 965 days, discovery-only cross-validation prefers 845, and "
                   "across 20 splits 730 has the best mean lower bound (−0.142, SD 0.114) against "
                   "−0.167 (SD 0.185) for 845 and −0.206 (SD 0.191) for 965. RFE drops to support "
                   "79, and lasso keeps all 12 features."),
        "meaning": ("The rule is stable to the covariate set but sensitive to the horizon and to "
                    "missingness, matching the simulation instability (Jaccard about 0.34). No "
                    "alternative is adopted: 12 covariates are kept, and 730 days is retained on "
                    "20-split stability rather than on convention."),
    },
    {
        "title": "From the frozen pipeline to the post-freeze evidence",
        "code": "notebook Step 25 (checklist)",
        "what": ("Before adding more experiments, the project separates what Steps 1–24 settled from "
                 "what they did not. This prevents the extension from testing things that are "
                 "already known, or from adding methods just to look thorough."),
        "result": ("Settled: the estimand and endpoint, the cohort and 12 covariates, the split, "
                   "discovery-fitted preprocessing, Cox/AIPW construction, depth-3 CART, the support "
                   "floor, the commitment rule, shrinkage calibration, the SCRE comparison and the "
                   "ACTG175 assessment. Open: the nuisance model, the rule learner, calibration "
                   "choice, interval choice, fold count, fairness, and the horizon."),
        "meaning": ("The later gates test real gaps. This is why the post-freeze work changed the "
                    "calibration and the evidence record, but not the rule or the decision."),
    },
    {
        "title": "Calibration and intervals",
        "code": "ciscarl2/gate33.py, gate41.py",
        "what": ("Two questions are tested after the freeze. How should noisy leaf effects be "
                 "calibrated: none, shrinkage, or out-of-fold isotonic regression? And how should "
                 "uncertainty be reported after the rule has been selected: influence function, "
                 "validation bootstrap, selection bootstrap, or split-conformal?"),
        "result": ("Isotonic beats no calibration by −0.0076 MAE in the main single-region run and "
                   "−0.0034 in the two-region run, with the policy unchanged. On fresh seeds it "
                   "replicates: −0.0053 [−0.0104, −0.0001] and −0.0065 [−0.0099, −0.0032]. "
                   "Shrinkage is not significant in confirmation. The influence-function interval "
                   "covers 90% in the main run and 95% in confirmation. The selection bootstrap "
                   "covers 85% (single) and 95% (two) in confirmation; it fails in the single-"
                   "region design and is rejected. Split-conformal covers 100% but is 2.33 times "
                   "wider than IF and is rejected. In the selection-aware comparison, IF covers "
                   "95–100% at width 0.297–0.298; Bonferroni covers 100% at 1.38–1.39 times the "
                   "width; sample-splitting covers 100% at the same width but uses a different rule."),
        "meaning": ("Isotonic calibration is adopted for prediction only, giving C200-I; the rule and "
                    "the commitment decision are unchanged. The influence-function interval is "
                    "retained because it is the narrowest valid option. Its coverage still depends "
                    "on the selected rule, and that limitation is quantified rather than removed."),
    },
    {
        "title": "Number of cross-fitting folds",
        "code": "ciscarl2/gate34.py",
        "what": ("Three, five and ten folds are compared with the nuisances, target, partitions and "
                 "seeds fixed. Only the fold count changes. The criterion is a MAE improvement of at "
                 "least 0.002 with a paired confidence interval below zero."),
        "result": ("Ten folds improves MAE by 0.0005 — real but one quarter of the threshold — at "
                   "2.1–2.3 times the cost. Three folds is worse by 0.0010–0.0011. Coverage is 95% "
                   "in every cell."),
        "meaning": ("Five folds are kept. The fold count is a tested compromise, not an unexamined "
                    "default. The cost of ten folds is too high for a gain that is practically "
                    "negligible."),
    },
    {
        "title": "Fairness, SHAP and internal transport",
        "code": "ciscarl2/gate35.py",
        "what": ("The frozen rule is described by race and gender, calibration is measured by group, "
                 "SHAP is computed on a surrogate for the pseudo-outcome, and a rule learned on the "
                 "white group is transported to the non-white group. The real data have no "
                 "individual truth, so this is descriptive only."),
        "result": ("Every group has fewer than 30 rule patients: white +0.444 [+0.081, +0.807] "
                   "(n=24), non-white +0.328 [−0.191, +0.847] (n=14), male +0.514 [+0.147, +0.881] "
                   "(n=25), female +0.184 [−0.318, +0.686] (n=13). Female calibration has the worst "
                   "ECE at 0.058. SHAP ranks wtkg, cd40, cd80, str2 and homo. The white-to-non-white "
                   "transported rule has support 74 (<200) and effect +0.223 [+0.071, +0.375]."),
        "meaning": ("Fairness is not established, and the transported rule is below the support "
                    "floor. Both are reported as descriptions and feasibility signals. The analysis "
                    "is underpowered by design, with 38 rule patients in assessment, and external "
                    "validation on PBC is out of scope."),
    },
    {
        "title": "Evidence summary: tested, adopted, rejected and proposed",
        "code": "results/EVIDENCE_EXTENSION.md, CLAIMS_v1.17.md",
        "what": ("Every important decision is placed on one status table. The table distinguishes "
                 "what was experimentally settled, what was adopted provisionally, what was tested "
                 "and rejected, and what remains outside the project's scope."),
        "result": ("Four decisions are experimentally settled: CART over four learners, 5 folds "
                   "over 3 and 10, Cox over three flexible nuisances, and the split/feature/estimand "
                   "design. Isotonic calibration is adopted for prediction. The selection bootstrap "
                   "and split-conformal intervals are rejected. Fixed-horizon IPCW-TMLE is tested and "
                   "rejected. External validation on PBC is out of scope."),
        "meaning": ("A method is not called rejected because it looks worse. It is rejected only "
                    "after being implemented, run on the same data and criteria, and failing those "
                    "criteria. That distinction is what the report must preserve."),
    },
    {
        "title": "Decision register and final claims",
        "code": "results/CLAIMS_v1.17.md, CANONICAL_RESULTS.md",
        "what": ("The frozen decision register is extended with the post-freeze decisions, and the "
                 "project states exactly what it can and cannot claim."),
        "result": ("The register now has 32 decisions. The rule is still C200: Cox nuisances, AIPW, "
                   "depth-3 CART, leaf 60, support 200 and the lower-bound commitment. Prediction "
                   "calibration is isotonic (C200-I); the influence-function interval is retained. "
                   "The post-freeze gates did not change the rule or the decision."),
        "meaning": ("The project can claim that CART, five folds, Cox and AIPW were retained after "
                    "direct comparison, and that isotonic calibration was adopted. It cannot claim "
                    "that CISCaRL is more accurate than SCRE, that fairness is established, or that "
                    "the ACTG175 subgroup is certified. The final rule is "
                    "cd40 ≤ 407.5 & wtkg > 71.0 & homo ≤ 0.5, and the model abstains."),
    },
    {
        "title": "Packaging",
        "code": "run_all.py, notebooks/CISCaRL_31_steps.ipynb, paper/build_ieee_detailed.py",
        "what": ("The final step checks that every artifact is present and reproducible: the code, "
                 "the executed notebook, the saved results, the figures, the report and the paper. "
                 "One command re-runs the evidence, with a sandboxed quick mode for a safe smoke "
                 "test."),
        "result": ("All artifacts resolve. The audit passes. The notebook runs end to end with zero "
                   "error cells: 136 cells, 52 of them code. Gates 31–35 are full runs, and Gate 33 "
                   "includes a 20-seed confirmation. The quick mode ran all 16 gate groups in 12.5 "
                   "minutes."),
        "meaning": ("The deliverable is checkable in one command rather than argued in prose. The "
                    "only open items are external validation on PBC and longitudinal TMLE; both are "
                    "stated rather than hidden."),
    },
]

WHY = {1: 'Every later number depends on the estimator and the rule code being correct. The audit makes that assumption testable instead of assumed, and it is cheap to run.', 2: 'A subgroup model fails quietly when an input is constant, duplicated, measured after treatment, or missing for most patients. This step decides the 12 inputs and records why each other column was excluded.', 3: "The endpoint and time origin define what 'benefit' means. A different endpoint or a different start time would answer a different clinical question.", 4: 'If the same patient appears in discovery and validation, every later comparison is optimistic. The split is the structural defence against that.', 5: 'A horizon chosen because the estimated effect is largest is selected on the outcome. The horizon must be fixed by follow-up constraints before the effect is read.', 6: 'Scaling on all patients leaks information, and the Cox prediction formula assumes centred covariates. Fitting the scaler on discovery only is both a leakage control and a correctness requirement.', 7: 'Leakage is the most common reason a model looks good in development and fails in use. A mechanical checklist is stronger than an intention to be careful.', 8: 'The effect estimate needs a good outcome model and honest censoring weights. Cross-fitting stops a patient from helping predict their own outcome.', 9: 'The tree needs one number per patient. The choice of target determines what the tree can find, and a noisy target makes discovery fail even when a real subgroup exists.', 10: 'The rule must be simple enough to read and specific enough to matter. Depth is an interpretability constraint, not a tuning knob.', 11: 'The best leaf in discovery is often a small lucky leaf. The support floor and the validation bound decide whether that leaf should be trusted.', 12: 'Real data have no individual treatment-effect truth, so accuracy cannot be measured without simulation. The simulator supplies the missing answer.', 13: 'A subgroup model is only useful if it beats the simple policy of treating everyone at the average effect. Without this baseline, a gain can be imaginary.', 14: "Small leaves win by luck. The support floor is the main defence against the winner's curse, and its cost in purity must be measured.", 15: 'Leaf effects are noisy because each leaf contains only a few dozen patients. Calibration changes reported effects without changing who is treated.', 16: 'A flexible outcome model may fit survival better but produce worse treatment effects. The comparison must be on the effect, not on the survival fit alone.', 17: 'Different learners produce different rules. The simplest learner has to be tested against the alternatives rather than assumed to be best.', 18: 'Tuning on a pseudo-outcome computed once on the whole discovery set leaks information and inflates performance. Nested refitting is the honest version.', 19: 'A model assembled from undocumented choices cannot be reproduced or defended. Freezing the configuration with its evidence prevents silent drift.', 20: 'A result on tuning seeds may be selection rather than signal. Fresh seeds are the test that turns a proposal into a result.', 21: 'Assessment must be read once, after the model is frozen. Reading it earlier turns the evaluation into another tuning set.', 22: 'A model must be compared with a real alternative, not only with a constant. The comparison also has to use identical splits and the same target.', 23: 'The real trial is the intended use case, even though the truth is unknown. The output has to include what the model refuses to claim.', 24: 'Readers will challenge the covariate set, the horizon and the handling of missing data. Each challenge needs a measured answer, not an assurance.', 25: 'Without a gap analysis, extension work repeats settled questions or adds methods for their own sake. This step decides what is actually open.', 26: 'Calibration and interval choice affect the reported effect and its uncertainty, so both must be tested after the rule is frozen.', 27: 'The fold count affects variance and cost. Five is a common default, but it still has to be tested against three and ten.', 28: 'A model used across groups must be checked, but small groups cannot support strong claims. The analysis has to be labelled descriptive from the start.', 29: 'A status table prevents tested negative results from disappearing. It separates what was settled from what was adopted, rejected, or left out of scope.', 30: 'Claims must match evidence. The register is the contract with the reader about what the project can and cannot say.', 31: 'A result that cannot be rebuilt is not a deliverable. The final check makes the whole chain reproducible from data and code.'}

DECISION = {1: 'Freeze the environment and seeds, and proceed only because the audit passes.', 2: 'Keep the 12 baseline covariates; exclude the other 15 columns with recorded reasons.', 3: 'Use the composite progression-free event and the 730-day horizon, with censoring adjustment.', 4: 'Fix the 527/263/264 split, stratified by treatment and event together.', 5: 'Fix 730 days inside the feasible range; report 365 and 1,095 days as sensitivity analyses.', 6: 'Fit the scaler on discovery only and standardise every covariate.', 7: 'Pass the leakage checklist and keep validation and assessment untouched.', 8: 'Use per-arm Cox plus a conditional censoring Cox, five folds, and cap weights at min(Q0.99, 20).', 9: 'Use the AIPW pseudo-outcome as the discovery target; record the cd40 proportional-hazards violation.', 10: 'Use depth 3 and treat every root-to-leaf path as a candidate rule.', 11: 'Apply support 200 and the validation lower-bound rule; abstain when the bound is below zero.', 12: 'Use the semi-synthetic ACTG175-based simulator for every accuracy claim.', 13: 'Record the operating range; do not present the model as universally better than the constant.', 14: 'Adopt the 200-patient floor; keep 400 as a sensitivity.', 15: 'Adopt empirical-Bayes shrinkage as a post-hoc prediction calibration (C200-S) and confirm it on fresh seeds.', 16: 'Keep Cox and AIPW; reject RSF, GBM, equal-weight stacking, learned stacking and fixed-horizon TMLE.', 17: 'Keep regression CART; reject pruned CART, PRIM, the classification tree and boosting distillation.', 18: 'Use nested tuning, keep depth 3 / leaf 60 / squared error, and withdraw the leakage-driven gain.', 19: 'Freeze 16 decisions with their evidence and label the two post-hoc choices.', 20: 'Accept the shrinkage direction; carry the two-region qualification into the paper.', 21: 'Report the full assessment metric set and make no model change afterwards.', 22: 'Keep C200; claim comparable accuracy after calibration, higher purity, and abstention, not overall superiority.', 23: 'Report the overall effect and the abstention on the subgroup; do not treat the assessment result as evidence.', 24: 'Keep 12 covariates and 730 days; report the horizon and missingness sensitivity as limitations.', 25: 'Test only the open layers in the extension.', 26: 'Adopt isotonic calibration for prediction (C200-I) and retain the influence-function interval.', 27: 'Keep five folds.', 28: 'Report fairness and transport as descriptive only; make no fairness claim.', 29: 'Record four settled decisions, the adopted calibration, the rejected intervals and TMLE, and the out-of-scope external validation.', 30: 'Freeze the 32-decision register and state the exact claim boundary.', 31: 'Ship the code, data, notebook, results and paper with a one-command rerun.'}

FIGS = {2: [('EXH', 'nbimg_02_1.png', 'Missing values by column and observed follow-up time by arm. Only cd496 has missing values; the dashed line marks 730 days.')], 3: [('EXH', 'nbimg_03_1.png', 'Kaplan–Meier curves for the two treatment arms on ACTG175, with 730 days marked.')], 9: [('EXH', 'nbimg_09_1.png', 'Distribution of the AIPW pseudo-outcome on the discovery partition. The spread is the heterogeneity signal the tree uses.')], 13: [('FIG', 'fig1_operating_range.png', 'Operating range: rule model versus the constant baseline, with the oracle bound.')], 14: [('FIG', 'fig2_frontier.png', 'Purity–capture frontier for the support floor.')], 16: [('FIG', 'fig_gate31_nuisance.png', 'Gate 31: Cox versus random survival forest, gradient boosting and equal-weight stacking.'), ('FIG', 'fig_gate36_tmle.png', 'Gate 36: AIPW versus fixed-horizon IPCW-TMLE.')], 17: [('FIG', 'fig_gate32_learners.png', 'Gate 32: purity–capture positions of the five rule learners.')], 22: [('FIG', 'fig_gate40_scre_path.png', 'Gate 40: SCRE full regularisation path; the chosen alpha is close to the best-MAE point.')], 23: [('FIG', 'fig3_actg175_tilt.png', 'ACTG175 censoring-weight tilt for the selected rule.')], 24: [('FIG', 'fig_gate37_44_horizon.png', 'Horizon stability across 20 splits (Gates 37 and 42–44).'), ('FIG', 'fig_gate38_features.png', 'Gate 38: feature-selection alternatives.')], 26: [('FIG', 'fig_gate33_calibration_intervals.png', 'Gate 33: calibration and interval coverage and width.'), ('FIG', 'fig_gate41_intervals.png', 'Gate 41: selection-aware intervals.')], 27: [('FIG', 'fig_gate34_folds.png', 'Gate 34: three, five and ten cross-fitting folds.')], 28: [('FIG', 'fig_gate35_fairness.png', 'Gate 35: group rule effects; every group has fewer than 30 rule patients.')], 31: [('FIG', 'fig_pipeline.png', 'End-to-end pipeline: discovery, validation and assessment are disjoint.')]}

for _i, _step in enumerate(STEPS, 1):
    _step['why'] = WHY[_i]
    _step['decision'] = DECISION[_i]
    _step['figures'] = [
        (str((FIG if kind == 'FIG' else EXH) / name), caption)
        for kind, name, caption in FIGS.get(_i, [])
    ]
