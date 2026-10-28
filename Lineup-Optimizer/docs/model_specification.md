# Model Specification

## Production Data Scope

The simulator represents the 2025 version of each player.

Player-specific inputs remain 2025-only:

- hitter event probabilities: BB, HBP, 1B, 2B, 3B, HR, K, batted-out mix
- hitter-specific single direction tendencies
- hitter-specific flyout direction/depth tendencies
- Sprint Speed
- Home-to-First
- player identity/effects used by contextual walk and stolen-base components

League-level BIP structural relationships now use 2021-2025 equal-weight pooled data reconstructed from structured MLB StatsAPI runner movements joined to Statcast BIP classification/detail:

- BIP empirical whole-play transition rows
- BIP advancement attempt model coefficients
- BIP safe/out conditional distributions inside empirical transition rows
- single LF/CF/RF advancement behavior
- flyout direction/depth advancement behavior, subject to minimum-sample fallback

Legacy inferred next-PA transition artifacts are retained only for regression comparison and are no longer production defaults.

## BIP Advancement Attempt Model

Runtime uses the hitter/runner's 2025 Sprint Speed with a 2021-2025 equal-weight league logistic attempt model.

Production default:

- `data/processed/speed_attempt_models_2021_2025_direct_movement.json`

The neutral Sprint Speed reference remains 27.35 ft/s.

For speed-sensitive contexts, the simulator computes:

- `p_actual`: attempt probability at the runner's 2025 Sprint Speed
- `p_neutral`: attempt probability at 27.35 ft/s

Then empirical whole-play transition rows are reweighted:

- attempt rows: `weight *= p_actual / p_neutral`
- no-attempt rows: `weight *= (1 - p_actual) / (1 - p_neutral)`

The conditional safe/out split among attempted advances is not modeled parametrically. It comes from the pooled empirical transition rows.

The direct-movement invalid-record audit found 0 invalid records and 0 repaired records inside the six speed-sensitive model-fitting contexts:

- single 1B -> 3B
- single 2B -> Home
- double 1B -> Home
- flyout 1B -> 2B
- flyout 2B -> 3B
- flyout 3B -> Home

## Empirical Transition Tables

Production default:

- `data/processed/transition_models_2021_2025_direct_movement.json`

The transition table uses 2021-2025 equal-weight pooled league observations built from direct MLB StatsAPI runner-movement records joined to Statcast BIP classification/detail whenever available. It preserves the existing whole-play architecture: a sampled row jointly determines batter destination, runner destinations, outs added, and runs scored.

The rebuilt direct-transition dataset contains 537,054 rows. No direct rows are discarded after cleanup. Inning-ending force plays with omitted trailing-runner movement are repaired by clearing residual safe base occupants after the third out is established. Outs, runs scored, and the actual recorded outs are preserved; post-play base occupancy is irrelevant because the inning is over.

Lookup hierarchy remains:

1. event + outs + base state + exact detail
2. event + outs + base state + no detail
3. event + base state
4. event-level fallback

The minimum exact-detail sample threshold remains 25.

## Batted-Ball Detail

The hitter's chance of producing each detail remains 2025-specific.

Examples:

- a 2025 hitter's LF/CF/RF single distribution is sampled from his 2025 profile
- once a detail is chosen, the transition outcome is sampled from 2021-2025 league data for that detail
- flyout direction/depth works the same way, with minimum-sample fallback when exact buckets are sparse

## Stolen Bases

Production default:

- `data/processed/contextual_stolen_base_rates_2025.csv`

The production stolen-base artifact is the revised beta-binomial behavioral 2025 model. It estimates demonstrated 2025 stolen-base behavior/effectiveness after shrinkage and simple base/out context adjustment. It is retrospective for the 2025 simulator; it is not a pure speed-talent estimate, future projection, true-talent baserunning model, or counterfactual model against different pitcher attention.

Attempt model:

- steal 2B uses clean steal-2B opportunities with beta-binomial player tendency shrinkage, `k=2.0`
- clean steal 3B uses clean `-2-` steal-third opportunities with beta-binomial player tendency shrinkage, `k=2.0`
- 2B probabilities share one underlying player tendency across contexts, then apply league base-state and outs adjustments
- 3B probabilities share one underlying player tendency across outs contexts, then apply league outs adjustment
- no independent player-by-cell estimation is used

Success model:

- the current behavioral success model from the NEW candidate is retained
- success uses demonstrated SB/CS outcomes with shrinkage
- 2B success is stored separately for `1--` and `1-3`
- 3B success is stored for clean `-2-`

Allowed pre-PA steal contexts are:

- steal 2B from `1--`, outs 0/1/2
- steal 2B from `1-3`, outs 0/1/2
- steal 3B from `-2-`, outs 0/1/2

Steal 3B from `12-` is disabled. Double steals, steals of home, defensive indifference, and ambiguous CS/pickoff opportunities remain excluded. The simulator permits at most one steal action before a PA, and a caught stealing that creates the third out ends the inning before the PA.

Excluded production features:

- Sprint Speed
- lead distance gained
- pitcher identity
- catcher identity
- disengagement state
- pickoff history
- exposure number / opportunity length
- pitch count or pitch type
- score or inning
- jump timing proxies

Those fields may remain in research artifacts, diagnostic reports, or player-pool metadata, but they do not affect the production stolen-base probabilities.

Runtime lookup order is:

1. exact contextual player probability for target base + base state + outs
2. custom-player raw SB/CS shrinkage fallback, if the profile supplies SB, CS, and PA
3. neutral league contextual probability for the exact state, derived from the promoted behavioral artifact
4. legacy flat 2B/3B fields only when no contextual state lookup applies

Promotion report:

- `reports/stolen_base_beta_binomial_promotion_2025/beta_binomial_stolen_base_promotion_report.md`

Legacy rollback artifact:

- `data/processed/contextual_stolen_base_rates_2025_legacy_complex.csv`

## GDP

The fitted Home-to-First GDP model remains unchanged.


## One-Run Probability Mode

One-Run Probability - Version A: Descriptive Behavior is a separate evaluation mode that estimates `P(score >= 1 run before 3 outs)` for clone lineups or any selected nine-hitter order in the app.

Each trial is one fresh inning:

- bases empty
- 0 outs
- batting-order slot 1
- score differential fixed at 0
- late-inning context supplied as inning 7

The trial stops immediately after the first run scores, or stops as a failure after the third out if no run has scored. It does not enter a second inning.

The mode reuses the production plan engine for hitter PA outcomes, contextual non-IBB walks, empirical BIP transitions, Sprint Speed advancement, GDP, beta-binomial behavioral stolen bases, and normal base/out accounting. It does not optimize sacrifice bunts, steals, or runner advancement. The contextual walk model receives clone ThreatGap = 0 when all nine slots are the same hitter because the current hitter and on-deck hitter are identical.

Leaderboard script:

- `scripts/run_one_run_clone_leaderboard.py`

Default high-precision setting:

- `100,000` trials per hitter
