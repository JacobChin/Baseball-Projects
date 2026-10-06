# Calculated Metrics Dictionary

This file lists the metrics calculated by the OBP swing-time pipeline. It does
not list every Driveline-provided POI or HitTrax column carried into
`model_dataset.csv`; those source columns are preserved as inputs.

## Swing Manifest / QC

Source tables: metadata CSV, POI CSV, HitTrax CSV, landmarks full-signal table,
force-plate full-signal table.

| Metric | Units | Source | Meaning / Calculation |
| --- | --- | --- | --- |
| `first_time` | seconds | `landmarks.time` | First recorded landmark timestamp for the swing. |
| `last_time` | seconds | `landmarks.time` | Last recorded landmark timestamp for the swing. |
| `frames` | count | `landmarks.time` | Number of landmark rows for the swing. |
| `has_poi` | boolean | `poi_metrics.csv` | `True` if the swing ID exists in POI metrics. |
| `has_hittrax` | boolean | `hittrax.csv` | `True` if the swing ID exists in HitTrax. |
| `has_force` | boolean | `force_plate.zip` | `True` if the swing ID exists in force-plate full signal. |
| `has_all_events` | boolean | landmarks event columns | `True` if `fp_10_time`, `fp_100_time`, and `contact_time` are all present. |
| `event_order_valid` | boolean | landmarks event columns | `True` if `fp_10_time <= fp_100_time <= contact_time`. |
| `contact_in_window` | boolean | `contact_time`, `first_time`, `last_time` | `True` if contact occurs within the recorded landmark window. |
| `analysis_event_valid` | boolean | `contact_time`, `contact_in_window` | `True` if contact exists and is inside the recorded window. |
| `fp10_to_contact_ms` | milliseconds | `fp_10_time`, `contact_time` | `(contact_time - fp_10_time) * 1000`. |
| `recorded_duration_s` | seconds | `first_time`, `last_time` | `last_time - first_time`. |

## Segment Onsets and Swing Time

Source tables: `joint_velos.zip`, `landmarks.zip`, metadata hitter side.

Primary onset settings:

- contact-anchored search window: final 0.50 seconds before contact
- light Savitzky-Golay smoothing
- segment onsets use 3D resultant angular velocity magnitude from OBP
  `joint_velos`
- the detector smooths angular velocity magnitude and finds that segment's
  pre-contact angular-velocity peak
- from the start of the search window through that velocity peak, the detector
  fits a continuous two-piece linear model
- the fitted change point defines the beginning of the segment's velocity-ramp
  window
- pelvis onset is selected from local positive signed angular-acceleration
  peaks at or above 25% of the largest pelvis burst after that piecewise change
  point and before the pelvis velocity peak; if multiple peaks qualify, the
  selected pelvis onset is the one closest to 191.7 ms before contact
- torso and lead-hand onsets are the largest positive signed
  angular-acceleration burst after that piecewise change point and before each
  segment's velocity peak
- pelvis, torso, and lead hand are the primary initiation-clock segments
- lead arm is still calculated for visual/QC and sequencing context, but it is
  not included in `composite_swing_time_ms` or `initiation_spread_ms`
- for every segment, the selected reference timestamp is the final onset
  timestamp; there is no extra movement-confirmation shift
- barrel onset is not included in event timing or the composite clock
- the QC viewer still keeps the barrel tracer and derived bat angular-velocity
  readout for visual reference

| Metric | Units | Source | Meaning / Calculation |
| --- | --- | --- | --- |
| `pelvis_onset_time` | seconds | pelvis angular velocity x/y/z | Local positive signed angular-acceleration peak at or above 25% of the largest pelvis burst after the pelvis piecewise change point and before the pelvis angular-velocity peak; if multiple peaks qualify, choose the one closest to 191.7 ms before contact. |
| `pelvis_to_contact_ms` | milliseconds | `pelvis_onset_time`, `contact_time` | `(contact_time - pelvis_onset_time) * 1000`. |
| `pelvis_inflection_time` | seconds | pelvis angular velocity x/y/z | Same timestamp as `pelvis_onset_time`; retained so the viewer can mark the selected acceleration-burst reference point. |
| `pelvis_inflection_to_contact_ms` | milliseconds | `pelvis_inflection_time`, `contact_time` | `(contact_time - pelvis_inflection_time) * 1000`. |
| `pelvis_onset_method` | label | onset detection | Method label used for the pelvis onset. |
| `torso_onset_time` | seconds | torso angular velocity x/y/z | Peak positive signed angular-acceleration burst after the torso piecewise change point and before the torso angular-velocity peak. |
| `torso_to_contact_ms` | milliseconds | `torso_onset_time`, `contact_time` | `(contact_time - torso_onset_time) * 1000`. |
| `torso_inflection_time` | seconds | torso angular velocity x/y/z | Same timestamp as `torso_onset_time`; retained so the viewer can mark the selected acceleration-burst reference point. |
| `torso_inflection_to_contact_ms` | milliseconds | `torso_inflection_time`, `contact_time` | `(contact_time - torso_inflection_time) * 1000`. |
| `torso_onset_method` | label | onset detection | Method label used for the torso onset. |
| `lead_arm_onset_time` | seconds | lead elbow angular velocity x/y/z | Peak positive signed angular-acceleration burst after the lead-arm piecewise change point and before the lead-arm angular-velocity peak. Reference/QC only; not used in the primary initiation clock. |
| `lead_arm_to_contact_ms` | milliseconds | `lead_arm_onset_time`, `contact_time` | `(contact_time - lead_arm_onset_time) * 1000`. |
| `lead_arm_inflection_time` | seconds | lead elbow angular velocity x/y/z | Same timestamp as `lead_arm_onset_time`; retained so the viewer can mark the selected acceleration-burst reference point. |
| `lead_arm_inflection_to_contact_ms` | milliseconds | `lead_arm_inflection_time`, `contact_time` | `(contact_time - lead_arm_inflection_time) * 1000`. |
| `lead_arm_onset_method` | label | onset detection | Method label used for the lead-arm onset. |
| `lead_hand_onset_time` | seconds | lead hand global angular velocity x/y/z | Peak positive signed angular-acceleration burst after the lead-hand piecewise change point and before the lead-hand angular-velocity peak. |
| `lead_hand_to_contact_ms` | milliseconds | `lead_hand_onset_time`, `contact_time` | `(contact_time - lead_hand_onset_time) * 1000`. |
| `lead_hand_inflection_time` | seconds | lead hand global angular velocity x/y/z | Same timestamp as `lead_hand_onset_time`; retained so the viewer can mark the selected acceleration-burst reference point. |
| `lead_hand_inflection_to_contact_ms` | milliseconds | `lead_hand_inflection_time`, `contact_time` | `(contact_time - lead_hand_inflection_time) * 1000`. |
| `lead_hand_onset_method` | label | onset detection | Method label used for the lead-hand onset. |
| `detected_segment_count` | count | segment onsets | Number of segment onsets successfully detected. |
| `detected_initiation_segment_count` | count | pelvis, torso, lead hand onsets | Number of primary initiation-clock onsets successfully detected. |
| `composite_onset_time` | seconds | pelvis, torso, lead hand onsets | Earliest detected primary initiation onset for that swing. |
| `latest_onset_time` | seconds | pelvis, torso, lead hand onsets | Latest detected primary initiation onset for that swing. |
| `composite_swing_time_ms` | milliseconds | `composite_onset_time`, `contact_time` | `(contact_time - composite_onset_time) * 1000`. This is the primary movement-time clock. |
| `initiation_spread_ms` | milliseconds | pelvis, torso, lead hand onsets | `(latest_primary_segment_onset - earliest_primary_segment_onset) * 1000`. Smaller values mean more concurrent/pushier initiation. |
| `onset_qc` | label | onset detection | `ok`, `few_initiation_segments_detected`, `missing_contact`, or another detection status. |

## Sensitivity Onsets

Source tables: same as onset metrics.

| Metric | Units | Source | Meaning / Calculation |
| --- | --- | --- | --- |
| `config` | label | onset settings | Sensitivity setting label, such as `inflect_win450ms_smooth13ms_prom40`. |
| `composite_swing_time_ms` | milliseconds | sensitivity onsets | Composite swing time recalculated under that inflection setting. |
| `initiation_spread_ms` | milliseconds | sensitivity onsets | Initiation spread recalculated under that inflection setting. |
| `detected_segment_count` | count | sensitivity onsets | Number of segments detected under that onset definition. |
| `onset_qc` | label | sensitivity onsets | Detection status under that onset definition. |

## Barrel Metrics

Source table: `landmarks.zip`.

Primary barrel point: `sweet_spot_x/y/z`.

| Metric | Units | Source | Meaning / Calculation |
| --- | --- | --- | --- |
| `barrel_qc` | label | barrel calculation | `ok` or the reason a barrel metric could not be calculated. |
| `barrel_path_500ms_in` | inches | `sweet_spot_x/y/z` | Cumulative 3D sweet-spot distance from `contact_time - 0.50s` to contact. |
| `barrel_path_from_onset_in` | inches | `sweet_spot_x/y/z`, onset metrics if present | Cumulative 3D sweet-spot distance from detected barrel onset to contact when a barrel onset exists; otherwise this falls back to the final 500 ms window. |
| `barrel_path_final150ms_in` | inches | `sweet_spot_x/y/z` | Cumulative 3D sweet-spot distance from `contact_time - 0.150s` to contact. Statcast-style comparison window. |
| `barrel_avg_speed_500ms_mph` | mph | `barrel_path_500ms_in`, time | Average sweet-spot speed over final 500 ms window. |
| `barrel_avg_speed_from_onset_mph` | mph | `barrel_path_from_onset_in`, time | Average sweet-spot speed from detected barrel onset to contact. |
| `barrel_peak_speed_mph` | mph | derivative of `sweet_spot_x/y/z` | Maximum 3D sweet-spot speed in the final 500 ms window. |
| `barrel_peak_speed_time` | seconds | derivative of `sweet_spot_x/y/z` | Timestamp of `barrel_peak_speed_mph`. |
| `barrel_peak_speed_ms_before_contact` | milliseconds | `barrel_peak_speed_time`, `contact_time` | `(contact_time - barrel_peak_speed_time) * 1000`. |
| `sweet_spot_contact_x` | meters | `sweet_spot_x` | Sweet-spot x-position at nearest frame to contact. |
| `sweet_spot_contact_y` | meters | `sweet_spot_y` | Sweet-spot y-position at nearest frame to contact. |
| `sweet_spot_contact_z` | meters | `sweet_spot_z` | Sweet-spot z-position at nearest frame to contact. |
| `contact_forward_from_thorax_in` | inches | sweet spot, `thorax_ap` | Contact sweet-spot x-position minus thorax reference x-position. |
| `contact_vertical_from_thorax_in` | inches | sweet spot, `thorax_ap` | Contact sweet-spot z-position minus thorax reference z-position. |

## Peak-Velocity Sequencing

Source table: `joint_velos.zip`.

Peak magnitudes use resultant angular velocity magnitude from x/y/z components.

| Metric | Units | Source | Meaning / Calculation |
| --- | --- | --- | --- |
| `pelvis_peak_time` | seconds | pelvis angular velocity x/y/z | Time of maximum pelvis resultant angular velocity in final 500 ms before contact. |
| `pelvis_peak_ms_before_contact` | milliseconds | `pelvis_peak_time`, `contact_time` | `(contact_time - pelvis_peak_time) * 1000`. |
| `pelvis_peak_mag_deg_s` | deg/s | pelvis angular velocity x/y/z | Maximum resultant pelvis angular velocity. |
| `torso_peak_time` | seconds | torso angular velocity x/y/z | Time of maximum torso resultant angular velocity in final 500 ms before contact. |
| `torso_peak_ms_before_contact` | milliseconds | `torso_peak_time`, `contact_time` | `(contact_time - torso_peak_time) * 1000`. |
| `torso_peak_mag_deg_s` | deg/s | torso angular velocity x/y/z | Maximum resultant torso angular velocity. |
| `lead_hand_peak_time` | seconds | lead hand global angular velocity x/y/z | Time of maximum lead-hand resultant angular velocity in final 500 ms before contact. |
| `lead_hand_peak_ms_before_contact` | milliseconds | `lead_hand_peak_time`, `contact_time` | `(contact_time - lead_hand_peak_time) * 1000`. |
| `lead_hand_peak_mag_deg_s` | deg/s | lead hand global angular velocity x/y/z | Maximum resultant lead-hand angular velocity. |
| `lead_elbow_peak_time` | seconds | lead elbow angular velocity x/y/z | Time of maximum lead-elbow resultant angular velocity in final 500 ms before contact. |
| `lead_elbow_peak_ms_before_contact` | milliseconds | `lead_elbow_peak_time`, `contact_time` | `(contact_time - lead_elbow_peak_time) * 1000`. |
| `lead_elbow_peak_mag_deg_s` | deg/s | lead elbow angular velocity x/y/z | Maximum resultant lead-elbow angular velocity. |
| `peak_order` | label | peak times | Chronological order of detected segment peaks, such as `pelvis>torso>lead_elbow>lead_hand`. |
| `peak_order_score` | 0-3 score | `peak_order` | Adds 1 for each expected proximal-to-distal ordering pair: pelvis before torso, torso before lead elbow, lead elbow before lead hand. |

## Pitch-Machine Proxy Metrics

These are estimates, not measured pitch-release data. They exist only to keep the
65 mph from 40 ft machine context visible.

| Metric | Units | Source | Meaning / Calculation |
| --- | --- | --- | --- |
| `estimated_pitch_flight_time_ms` | milliseconds | assumed 40 ft / 65 mph | `40 / (65 * 1.4666667) * 1000`, approximately 419.58 ms. |
| `estimated_composite_onset_after_release_ms` | milliseconds | estimated flight time, composite swing time | `estimated_pitch_flight_time_ms - composite_swing_time_ms`. Approximate timing of composite onset after machine release, not a real measured release timestamp. |

## Modeling / Inclusion Flags

| Metric | Units | Source | Meaning / Calculation |
| --- | --- | --- | --- |
| `model_ready_primary` | boolean | QC plus primary metrics | `True` if contact is usable and the primary composite time, initiation spread, and barrel path from onset are available. |
