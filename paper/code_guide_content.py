"""Every code file in the project, explained in plain-language bullets."""

ENTRIES = [
    # ---------------------------------------------------------------- core
    ("Core model", "Support", "ciscarl2/paths.py",
     "A small locator for the data file.",
     "Checks the ACTG175_PATH variable, then data/ACTG175.csv, then the root copy, and returns one path.",
     "Resolves to data/ACTG175.csv. The root and data-folder copies have the same SHA-256 checksum."),
    ("Core model", "Support", "ciscarl2/__init__.py",
     "The package marker for ciscarl2.",
     "Tells Python that the folder is a package and records the project name.",
     "No output. It exists so every other module can be imported as ciscarl2.*."),
    ("Core model", "Final evidence", "ciscarl2/audit.py",
     "A small self-test suite for the rule code and the estimator.",
     "Checks that rule conditions match patient masks, that tree leaves do not overlap, that the "
     "influence-function contrast equals the direct formula, and that purity, capture and Jaccard "
     "match hand counts.",
     "All checks pass. AIPW bias is +0.0031 (SD 0.0130) and the arm means are within 0.002."),
    ("Core model", "Final evidence", "ciscarl2/audit_commit.py",
     "A check that the commitment decision is not scored on the same patients used to make it.",
     "Compares deciding on all test patients with deciding on one half and scoring on the other.",
     "Benefit per treated patient is 0.1975 full-sample and 0.1978 honest-split; efficiency is "
     "0.987 vs 0.989."),
    ("Core model", "Final evidence", "ciscarl2/dgp.py",
     "The simulation data generator.",
     "Resamples the real ACTG175 covariate matrix, randomises treatment 50/50, generates survival "
     "and censoring times, and adds a known effect in one or two regions.",
     "Prevalence 25.5%, event rate 20.0%, censoring 10.1%, true ATE +0.050, true regional effect "
     "+0.195 and 0 outside."),
    ("Core model", "Final evidence", "ciscarl2/diagnostics.py",
     "The nuisance diagnostic report for the real data.",
     "Runs proportional-hazards tests, tie handling checks, survival calibration, and weight-cap "
     "sensitivity, then writes diagnostics.md and three CSV files.",
     "Global PH p = 0.235 / 0.368; cd40 p = 0.021 / 0.023; calibration ECE 0.032; cap 1.2 binds "
     "9.9% of weights and caps of 1.5 or more never bind."),
    ("Core model", "Final pipeline", "ciscarl2/estimators.py",
     "The production estimator.",
     "Fits a survival model for each arm and a censoring model, cross-fits over five folds, builds "
     "the AIPW pseudo-outcome, and caps extreme weights.",
     "Used by every gate. Audit bias +0.0031; cap is min(99th percentile, 20); effective sample "
     "size on discovery is 372 of 527."),
    ("Core model", "Final pipeline", "ciscarl2/rules.py",
     "The rule representation and cleanup code.",
     "Turns each tree leaf into a readable if-then rule, removes duplicate conditions, prunes broad "
     "rules, and assigns patients to the most specific match.",
     "Audit shows conditions equal their patient masks exactly, and leaves partition the data."),
    ("Core model", "Final evidence", "ciscarl2/nested_tune.py",
     "Hyperparameter tuning with honest nested refitting.",
     "Tunes depth, leaf size and split criterion by cross-validation while refitting the nuisance "
     "models inside every fold.",
     "Best nested MAE: depth 4 / leaf 60 / squared 0.8633; frozen depth 3 is 0.8638; absolute error "
     "is 0.8711. The earlier 0.824 was leakage and was withdrawn."),
    ("Core model", "Final evidence", "ciscarl2/policy_eval.py",
     "Policy value and net-benefit comparison.",
     "Compares treat-none, C200, SCRE and treat-all, including a cost per treated patient and "
     "influence-function coverage.",
     "Policy value: none 0.7659; C200 0.7870 single / 0.7855 two; SCRE 0.7926 / 0.8044; treat-all "
     "0.8145 / 0.8345. C200 leads net benefit from a cost of 0.05–0.10; IF coverage 92.5%."),
    ("Core model", "Final evidence", "ciscarl2/scre_vs_ciscarl.py",
     "The real-data rule table and SCRE comparison.",
     "Lists every CART leaf with support, validation and assessment effects, and compares C200 with "
     "SCRE on the same patients.",
     "Selected rule cd40≤407.5 & wtkg>71.0 & homo≤0.5; support 61; validation +0.116 (LCB −0.250); "
     "assessment +0.401 on 38 patients; decision INSUFFICIENT."),

    # ---------------------------------------------------------------- gates 1-4
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate1.py",
     "The first estimator validation.",
     "Tests AIPW under four censoring mechanisms and three censoring levels, with 200 replications "
     "per cell and a known effect.",
     "Bias is small at 10–25% censoring but −0.0302 at 50% covariate censoring; event-dependent "
     "censoring bias grows from −0.0152 to −0.0806."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate1_verify.py",
     "A check that the weight cap still works under the full cross-fitting pipeline.",
     "Compares the single cross-fit used in Gate 1b with the outer five-fold production pipeline.",
     "Confirms the cap behaves as intended once the production folds are used."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate1b.py",
     "The weight-stabilisation experiment.",
     "Compares no cap, fixed caps at 50/20/10, the 99th and 95th percentiles, and an oracle cap.",
     "Uncapped maximum weight 1,000 and RMSE 0.2942; a cap at 20 gives RMSE 0.1172; the 99th "
     "percentile gives 0.0983. The project adopted min(99th percentile, 20)."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate1c.py",
     "A check of the Cox comparator under non-proportional hazards.",
     "Runs a crossing-hazards design and compares a pooled Cox model with the separate-arm model.",
     "The pooled Cox proxy is biased by 16–45% under crossing hazards, so every comparison uses the "
     "separate-arm production model."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate2.py",
     "Rule-level inference, abstention and stability.",
     "Measures interval coverage, the fraction of runs with no rule, and TREAT sign accuracy.",
     "Coverage 88.3% over 103 rules in the first run; 15–30% of replications returned no rule. The "
     "coverage result was later rechecked with more replications in Gate 2b."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate2_funnel.py",
     "A discovery funnel for the no-rule cases.",
     "Records where candidate rules are lost: raw leaves, after pruning, after support, and after "
     "stability.",
     "Identifies the stage that removes candidates. The result is saved in results/gate2_funnel*.csv."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate2b.py",
     "A higher-precision check of subgroup intervals.",
     "Repeats the interval study with 100 replications and compares the plain influence-function "
     "interval with an EIF-corrected version.",
     "Coverage is 93.1% over 333 rules; the nuisance correction changes variance by only 1–2%. The "
     "earlier 88.3% was mostly small-sample noise."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate2c.py",
     "A sweep of the stability-selection threshold.",
     "Runs nested stability thresholds and measures discovery quality versus calibration.",
     "The project chose the 0.50 threshold; the sweep is recorded in results/gate2c_summary.csv."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate2d.py",
     "An application-matched sample-size test.",
     "Repeats the pipeline at n = 589, which is the real discovery size, with the same effect scale "
     "and censoring as ACTG175.",
     "Shows how little power the real sample gives; this is the reason accuracy claims are made in "
     "simulation, not on ACTG175."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate2e.py",
     "A diagnosis of the decision layer at the real sample size.",
     "Measures false commitment among rules whose true effect is near zero and sweeps the "
     "commitment threshold.",
     "Near-zero rules are committed 6.5–8.3% of the time against a nominal 5%; no threshold gives "
     "90% precision and at least 50% commitment."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate3.py",
     "The delta sensitivity analysis under a known missing-not-at-random mechanism.",
     "Checks the delta = 0 identity and tests whether tilting the outcome model recovers the truth.",
     "Delta = 0 reproduces the baseline to 1.7e-16. The adjustment slope is about 0.002 per unit "
     "delta, far too small to correct a bias of 0.01–0.02."),
    ("Gates 1–4", "Historical evidence", "ciscarl2/gate4.py",
     "The first comparison with the real SCRE implementation.",
     "Matches data, split, horizon and evaluation patients, and fits both methods on the same seeds.",
     "Fixes a degenerate SCRE alpha choice and sets the comparison protocol used later. The final "
     "head-to-head is reported in Gate 28."),

    # ---------------------------------------------------------------- gates 5-15
    ("Gates 5–15", "Historical evidence", "ciscarl2/gate5.py",
     "Subgroup-level missing-not-at-random sensitivity.",
     "Tilts the censoring weights over δ ∈ [−2, 2] and records where a TREAT verdict changes.",
     "All three TREAT verdicts survive the whole range, moving by about ±0.02. The production cap "
     "of 1.31 absorbs the tilt, which is reported as a limitation."),
    ("Gates 5–15", "Historical evidence", "ciscarl2/gate6.py",
     "A test of whether the problem is the pseudo-outcome or the rule extraction.",
     "Runs the same extraction and selection on a true-effect target and on the estimated target.",
     "With a clean target the rule machinery recovers the region, so extraction is not the main "
     "bottleneck; the target is."),
    ("Gates 5–15", "Historical evidence", "ciscarl2/gate7.py",
     "A minimum-support sweep at n = 2000.",
     "Varies the support floor and compares the rule model with the constant baseline.",
     "The sweep is stored in results/gate7_summary.csv and informed the 200-patient floor."),
    ("Gates 5–15", "Tested and rejected", "ciscarl2/gate8.py",
     "A test of the RMST estimand.",
     "Rebuilds every step for restricted mean survival time and compares it with the constant.",
     "RMST is worse than its own constant by 3.495 days (+10.8% MAE, CI above zero). It was not "
     "adopted."),
    ("Gates 5–15", "Tested and rejected", "ciscarl2/gate9.py",
     "A test of a smoother plug-in discovery target.",
     "Compares the AIPW target with Cox and RSF plug-in targets while keeping the final evaluation "
     "on held-out AIPW.",
     "The plug-in target is 10–14 times less noisy and lifts Jaccard from 0.107 to about 0.61, but "
     "final MAE is worse than the constant (+0.0047 / +0.0094). It was not adopted."),
    ("Gates 5–15", "Historical evidence", "ciscarl2/gate10.py",
     "Conservative rule extraction on the cross-fitted plug-in target.",
     "Builds candidate rules from a tree on the plug-in target and measures their support and "
     "stability.",
     "The result is saved in results/gate10_*.csv and was an early step before the AIPW target was "
     "adopted."),
    ("Gates 5–15", "Historical evidence", "ciscarl2/gate11.py",
     "The first sample-size result for the depth-2 rule model.",
     "Compares the rule model with the constant at 4,000, 8,000 and 12,000 patients, 40 seeds per "
     "cell.",
     "Gain is +9.2% at 4,000, +19.6% at 8,000 and +20.6% at 12,000. The model is adopted at 8,000 "
     "and 12,000 but not at 4,000."),
    ("Gates 5–15", "Historical evidence", "ciscarl2/gate12.py",
     "The confirmation of the depth-3 rule model on fresh seeds.",
     "Repeats the depth-3 comparison at 8,000 and 12,000 patients with new seeds.",
     "Gain is +26.0% at 8,000 and +33.7% at 12,000, with purity 0.87–0.95. Depth 3 is adopted."),
    ("Gates 5–15", "Historical evidence", "ciscarl2/gate13.py",
     "A delta-tilt sensitivity on the adopted rule set.",
     "Discovers the rule once at delta = 0, then re-estimates it under several censoring tilts.",
     "The estimates move only slightly across the tilt range; the details are in "
     "results/gate13_tilt.csv."),
    ("Gates 5–15", "Historical evidence", "ciscarl2/gate14.py",
     "A test of the rule model under a misspecified Cox outcome model.",
     "Runs the pipeline with a correct, mild and severe outcome-model violation.",
     "Gain is +30.1% at κ=0 and +23.8% at κ=1, but −4.1% at κ=3. The method is not robust to severe "
     "outcome-model misspecification."),
    ("Gates 5–15", "Tested and rejected", "ciscarl2/gate15.py",
     "A test of blending the plug-in target with AIPW.",
     "Standardises both targets and mixes them at several weights under a severe violation.",
     "The blend fails (MAE +0.0022, 48% of replications better); AIPW alone is better and more "
     "robust."),

    # ---------------------------------------------------------------- gates 16-30
    ("Gates 16–30", "Historical evidence", "ciscarl2/gate16.py",
     "The confirmation of the AIPW target.",
     "Compares AIPW with the plug-in target at 8,000 and 12,000 patients, with correct and wrong "
     "outcome models.",
     "AIPW gains 37.8%/48.0% at κ=0 and 32.7%/53.4% at κ=3; the plug-in falls to −4.0%/+6.5% at "
     "κ=3. AIPW is adopted."),
    ("Gates 16–30", "Historical evidence", "ciscarl2/gate17.py",
     "The lower sample-size boundary of the final design.",
     "Compares the AIPW rule model, its constant and an oracle at 2,000, 4,000 and 6,000 patients.",
     "At 2,000 it is worse (−22.8%); at 4,000 it is +8.1% and at 6,000 +23.0%. The gap to the oracle "
     "is 40–61 points."),
    ("Gates 16–30", "Historical evidence", "ciscarl2/gate18.py",
     "A joint outcome-and-censoring misspecification test.",
     "Crosses a correct or wrong outcome model with a conditional or marginal censoring model.",
     "Prediction still gains about 30%, but subgroup purity falls from 0.823 to 0.659 in the worst "
     "cell: average prediction survives, subgroup reliability does not."),
    ("Gates 16–30", "Final evidence", "ciscarl2/gate19.py",
     "The commitment-versus-shrinkage experiment.",
     "Compares no commitment, hard commitment at a positive lower bound, and shrinkage only.",
     "Hard commitment removes null-benefit treatment (10–12% to 0%), raises benefit per treated "
     "patient to +0.176/+0.183, and abstains in 30–45% of runs."),
    ("Gates 16–30", "Final evidence", "ciscarl2/gate20.py",
     "The honest commitment test with disjoint roles.",
     "Uses 4,000 discovery, 2,000 validation and 2,000 assessment patients, and repeats with only "
     "1,000 validation patients.",
     "Full validation gives 50% commitment, 0% null treatment and MAE −0.0131 vs constant; half "
     "validation gives MAE +0.0083. Validation size matters."),
    ("Gates 16–30", "Final evidence", "ciscarl2/gate21.py",
     "The selection-rule comparison.",
     "Compares max mean, lower confidence bound, support at least 200 and stability-weighted "
     "selection.",
     "Support 200 captures 0.548 vs 0.356, raises purity 0.69→0.81, Jaccard 0.33→0.51, and removes "
     "null-benefit leaves (5%→0%). It is adopted."),
    ("Gates 16–30", "Historical evidence", "ciscarl2/gate22.py",
     "A valid stability measurement.",
     "Refits each configuration with its own selection procedure on 20 disjoint discovery "
     "half-samples.",
     "C200 has Jaccard 0.318/0.334 and capture 0.623; every configuration produces many different "
     "rules across splits."),
    ("Gates 16–30", "Final evidence", "ciscarl2/gate23.py",
     "The two-region confirmation of the support floor.",
     "Compares max mean, support 100/200/400 and a stability rule on a two-region effect.",
     "C200 captures 0.364 vs 0.148 (+0.216), recovers Jaccard 0.295 vs 0.127, keeps purity 0.82 vs "
     "0.77, and commits 70% vs 45%."),
    ("Gates 16–30", "Historical evidence", "ciscarl2/gate24.py",
     "A joint nuisance stress test on the two-region design.",
     "Adds control-arm non-proportional hazards and censoring misspecification to the two-region "
     "effect.",
     "Prediction holds, but subgroup recovery degrades; the numbers are in "
     "results/gate24_summary.csv."),
    ("Gates 16–30", "Tested and rejected", "ciscarl2/gate25.py",
     "The two-leaf rule-list experiment.",
     "Compares the single C200 leaf with a two-leaf list from the same tree.",
     "The list captures more (+0.169) but purity falls by 0.166 and per-treated benefit by 0.009. It "
     "was rejected; one leaf is kept."),
    ("Gates 16–30", "Tested and rejected", "ciscarl2/gate26.py",
     "The flexible DR-learner with rule distillation.",
     "Learns a more complex effect surface and distils a simple rule from it.",
     "It is purer (+0.068/+0.058) but captures less (−0.094/−0.073) and has slightly worse MAE. It "
     "was not adopted."),
    ("Gates 16–30", "Final evidence", "ciscarl2/gate28.py",
     "The head-to-head with SCRE on identical splits.",
     "Fits both methods on the same discovery, validation and assessment patients and the same "
     "horizon.",
     "C200 MAE is worse by 0.0043 (p=0.046) in one region and 0.0031 (p=0.112) in two; purity is "
     "0.86/0.87 vs 0.43/0.58; capture is 0.59/0.33 vs 0.95/0.80."),
    ("Gates 16–30", "Final evidence", "ciscarl2/gate30.py",
     "The C200 knob sweep and confirmation.",
     "Tests shrinkage, two commitment thresholds, two leaf sizes and depth 4 on 40 tuning and 40 "
     "fresh seeds.",
     "Shrinkage lowers MAE by 0.0054/0.0025; depth 4 is worse (+0.0092/+0.0073); leaf size and "
     "threshold do almost nothing. Shrinkage becomes C200-S."),

    # ---------------------------------------------------------------- gates 31-44
    ("Gates 31–44", "Final evidence", "ciscarl2/gate31.py",
     "The outcome-nuisance comparison.",
     "Compares per-arm Cox, random survival forest, gradient boosting and equal-weight stacking.",
     "Cox has the best Brier (0.0028/0.0033). Stacking lowers MAE by 0.0043/0.0075 but loses 0.030 "
     "purity and costs 136–260 s. Cox is retained."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate32.py",
     "The rule-learner comparison.",
     "Compares CART, pruned CART, PRIM, a classification tree and boosting distillation.",
     "Pruned CART purity falls to 0.741/0.637, PRIM to 0.328/0.473, classification to 0.671/0.701, "
     "boosting to 0.883/0.761. CART (0.889/0.811) is retained."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate33.py",
     "The calibration and interval comparison.",
     "Compares no calibration, shrinkage and isotonic; and influence-function, bootstrap, selection "
     "bootstrap and conformal intervals.",
     "Isotonic lowers MAE by 0.0053/0.0065 on fresh seeds and is adopted for prediction (C200-I). "
     "The selection bootstrap fails (85%) and conformal is 2.33× wider; IF is retained."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate34.py",
     "The fold-count comparison.",
     "Compares 3, 5 and 10 cross-fitting folds with everything else fixed.",
     "Ten folds gains 0.0005 MAE at 2.1–2.3× cost; three folds is worse by 0.0010–0.0011. Five "
     "folds are retained."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate35.py",
     "The fairness, SHAP and transport analysis.",
     "Describes rule effects by race and gender, measures calibration and SHAP, and transports a "
     "white-group rule to the non-white group.",
     "Every group has <30 rule patients: white +0.444 (24), non-white +0.328 (14), male +0.514 (25), "
     "female +0.184 (13); female ECE 0.058; transport support 74, effect +0.223."),
    ("Gates 31–44", "Tested and rejected", "ciscarl2/gate36.py",
     "The fixed-horizon IPCW-TMLE comparison.",
     "Implements TMLE with the same folds and nuisances and compares it with AIPW.",
     "TMLE MAE is 0.1408/0.1374 vs AIPW 0.0516/0.0578, Brier is 0.0177/0.0172 vs 0.0026/0.0031, "
     "and bias is larger. AIPW is retained."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate37.py",
     "The five-horizon screen.",
     "Compares 365, 548, 730, 912 and 1,095 days on events, at-risk share, support and precision.",
     "No horizon meets every criterion. 730 has 99 events and 71% at risk; 365/548 have too few "
     "events; 1,095 has 51% censoring. 730 is kept as a compromise."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate38.py",
     "The feature-selection comparison.",
     "Compares 12 covariates, 16 candidates, lasso and RFE, all fitted on discovery only.",
     "The 12- and 16-feature rules are identical; lasso keeps all 12; RFE keeps 11 and selects "
     "cd80>805 & race>0.5 with support 79. The 12 covariates are kept."),
    ("Gates 31–44", "Tested and rejected", "ciscarl2/gate39.py",
     "The learned-stacking comparison.",
     "Fits positive weights on Cox, RSF and GBM out-of-fold predictions and compares them with Cox "
     "and equal weights.",
     "Learned weights are about 0.77 Cox / 0.14 RSF / 0.09 GBM and the result is indistinguishable "
     "from Cox (+0.0007/+0.0001). Learned stacking is rejected."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate40.py",
     "The SCRE alpha-path sensitivity.",
     "Fits SCRE once per replication and evaluates every alpha on the path on the same patients.",
     "The chosen alpha is within 0.0010–0.0017 MAE of the best; the direction (SCRE more accurate, "
     "C200 purer) is unchanged."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate41.py",
     "The selection-aware interval comparison.",
     "Compares the influence-function interval with Bonferroni and sample-splitting.",
     "IF covers 95–100% at width 0.297–0.298; Bonferroni covers 100% at 1.38–1.39× width; "
     "sample-splitting covers 100% at the same width but uses a different rule. IF is retained."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate42.py",
     "The dense horizon grid.",
     "Searches every 30 days from 365 to 1,085 and ranks by validation lower bound with event and "
     "support guards.",
     "The single-split optimum is 965 days (LCB 0.000, effect +0.427, support 61, assessment "
     "+0.200)."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate43.py",
     "The discovery-only horizon selection.",
     "Uses five-fold inner cross-validation inside discovery, never validation or assessment.",
     "The optimum is 845 days (inner LCB +0.014 vs −0.118 for 730); validation +0.114, assessment "
     "+0.498."),
    ("Gates 31–44", "Final evidence", "ciscarl2/gate44.py",
     "The horizon stability test.",
     "Repeats 730, 845 and 965 on 20 different random splits and records validation and assessment.",
     "730: mean LCB −0.142, SD 0.114; 845: −0.167, SD 0.185; 965: −0.206, SD 0.191. 730 is retained "
     "on stability."),

    # ---------------------------------------------------------------- variants
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4c.py",
     "The crossing-hazards comparison with real SCRE.",
     "Runs a crossing-hazards design against SCRE with matched splits and reconciles the earlier "
     "marginal and paired calculations.",
     "The sign convention and paired subset are fixed; the comparison is internally consistent."),
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4d.py",
     "The piecewise-constant DGP comparison with SCRE.",
     "Compares CISCaRL and SCRE on a rule-shaped effect at 589 and 2,000 patients.",
     "The rule-shaped advantage is not supported: sensitivity is 0.11 at 589 and 0.28 at 2,000, and "
     "the false-positive rate is 0.321 at 2,000."),
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4d_cart.py",
     "A three-way recoverability test.",
     "Compares a tree fitted to the true effect, a tree fitted to the pseudo-outcome, and the full "
     "search.",
     "Shows whether the true rule is in the candidate pool and whether the selection step can find "
     "it."),
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4d_diagnose.py",
     "A failure-location diagnostic.",
     "Separates failure in the estimate, the interval and the decision for each discovered rule.",
     "Records conditions, test support, in-region fraction and effect error, so the failure can be "
     "attributed rather than guessed."),
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4d_discovery.py",
     "A discovery-funnel diagnostic.",
     "Records where the true region is lost: representable, generated, or filtered by support or "
     "stability.",
     "The output is in results/gate4d_discovery*.csv and explains the zero-rule cases."),
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4d_stability_check.py",
     "A stability-selection diagnostic.",
     "Checks whether a good rule was found but then rejected by the stability filter.",
     "Separates discovery failure from stability-filter failure."),
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4e.py",
     "A variance-normalised splitting criterion.",
     "Tests whether normalising the split criterion makes the true region more reproducible.",
     "The result is recorded in results/gate4e_summary.csv and informs the later n-sweep."),
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4f.py",
     "A larger-n recoverability test.",
     "Repeats the half-sample stability test at 589, 2,000, 4,000 and 8,000 patients.",
     "At 8,000 the region is recovered (Jaccard 0.88, precision 0.94, recall 0.93) but stability is "
     "only 46–47.5% against a 50% target."),
    ("Diagnostics and variants", "Historical evidence", "ciscarl2/gate4g.py",
     "The final recoverability validation.",
     "Compares the production random forest, an oracle CART and a CART on the pseudo-outcome at "
     "8,000 and 12,000 patients.",
     "Production RF has Jaccard 0.86 and stability 37.6%, below the oracle's 61.4%; the gap is "
     "discovery, not representability."),

    # ---------------------------------------------------------------- gates 45-47
    ("Gates 45–48", "Tested and rejected", "ciscarl2/gate45.py",
     "The broad CART tuning experiment.",
     "Runs 540 configurations over depth, leaf size, split criterion and pruning, with the "
     "nuisance models refitted inside every outer fold.",
     "Best nested MAE is 0.85982 for depth 5 / leaf 30 / squared error, against 0.86379 for the "
     "frozen depth 3 / leaf 60 (rank 54 of 540). It was not adopted on prediction error alone."),
    ("Gates 45–48", "Tested and rejected", "ciscarl2/gate46.py",
     "The ensemble-versus-CART comparison.",
     "Distils random forest, extra trees, gradient boosting, histogram boosting and a ridge stack "
     "into a depth-3 rule, then applies the same support and commitment protocol.",
     "No ensemble gains capture with a 95% interval above zero; costs are 4.8–65.9 s against 0.07 s "
     "for CART. CART is retained."),
    ("Gates 45–48", "Tested and rejected", "ciscarl2/gate47.py",
     "CART tuning on simulated subgroup performance.",
     "Evaluates 48 CART configurations on the same 20 splits × 2 DGPs, selecting on validation LCB "
     "with purity, capture and interpretability guardrails.",
     "Depth 2 / absolute error is best in simulation (LCB +0.0605/+0.0731), but on ACTG175 it "
     "selects 122 patients, LCB −0.210 and abstains. The frozen tree remains."),
    ("Gates 45–48", "Final evidence", "ciscarl2/gate48.py",
     "The SHAP and LIME explainability audit.",
     "Runs exact TreeSHAP on the final CART, LIME on 40 rule-in/rule-out patients with five seeds, "
     "and compares top features, stability and group-wise SHAP.",
     "SHAP: cd40 0.128, homo 0.093, cd80 0.057, wtkg 0.035; all other features zero. "
     "SHAP–LIME overlap 0.767/0.700; LIME stability 0.703/0.712. No model change."),

    # ---------------------------------------------------------------- external and builders
    ("External and build", "External dependency", "ciscarl2/external/scre.py",
     "The SCRE comparator implementation.",
     "Fits a survival causal rule ensemble with a Coxnet path and rule-interaction terms; used by "
     "Gates 4, 28 and 40.",
     "It is the baseline only. The final CISCaRL model does not depend on it."),
    ("External and build", "Support", "ciscarl2/external/__init__.py",
     "The package marker for ciscarl2.external.",
     "Allows SCRE to be imported as a normal subpackage.",
     "No output."),
    ("External and build", "Build tool", "run_all.py",
     "The one-command reproducibility runner.",
     "Runs the notebook, Gates 23–44, the figure builder and optionally the paper; backs up results "
     "before a full run and uses a sandbox for --quick.",
     "The quick sandbox ran all 16 gate groups in 12.5 minutes; Gate 37 re-ran byte-for-byte."),
    ("External and build", "Build tool", "paper/make_paper_figures.py",
     "The paper figure generator.",
     "Reads the saved result CSVs and draws all paper figures.",
     "Writes 15 PNG/PDF figure pairs into paper/figs."),
    ("External and build", "Build tool", "paper/build_ieee_detailed.py",
     "The detailed IEEE paper builder.",
     "Builds the two-column paper from the result numbers and figures.",
     "Writes an 8-page paper with 15 figures and 10 tables."),
    ("External and build", "Build tool", "paper/build_model_creation_detailed.py",
     "The detailed 31-step report builder.",
     "Builds the 42-page report, inserting the exact output images and saved figures.",
     "Writes the detailed model-creation report; 31 steps and 52 exhibits."),
    ("External and build", "Build tool", "paper/report_content.py",
     "The text content of the 31-step report.",
     "Stores each step's title, code, explanation, result, meaning and decision, plus the figure "
     "mapping.",
     "No standalone output; imported by the detailed report builder."),
    ("External and build", "Build tool", "paper/make_step_exhibits.py",
     "The exact-output image generator.",
     "Reads the executed notebook, captures each step's printed output, and renders it as a "
     "console-style PNG.",
     "Writes 38 console images and 4 notebook plots into paper/exhibits."),
    ("External and build", "Build tool", "paper/build_code_guide.py",
     "The builder for this complete code and file guide.",
     "Reads the entry list, writes the grouped explanations, the 80-file coverage checklist and the "
     "glossary, then saves the Word document.",
     "Writes this guide. Its checklist is the proof that every code file is covered."),
    ("External and build", "Support", "paper/code_guide_content.py",
     "The content store for this guide.",
     "Holds one entry per code file: path, status, what it is, what it does, and what it produced.",
     "No standalone output; imported by the guide builder."),
]
