# OBP Biomechanical Swing Viewer

## Summary

This project uses Driveline Baseball's OpenBiomechanics Project (OBP) hitting dataset to study how hitters move through the attack-angle window around contact. The main output is an interactive swing viewer that combines motion-capture landmarks, force events, segment-onset timing, bat speed, attack angle, attack direction, and contact-depth measurements into one frame-by-frame visualization.

The viewer highlights the part of the barrel path where the sweet spot is moving through an adjustable ideal attack-angle range. The default range is 5-20 degrees, matching the common Statcast-style ideal attack-angle window. The red barrel ribbon is clipped with sub-frame interpolation so the visual ribbon begins and ends at the estimated attack-angle boundary crossing, even when the exact 5 or 20 degree point falls between sampled frames.

## Project Goals

- Build a QC-friendly swing viewer for OBP swings.
- Estimate frame-by-frame attack angle, attack direction, and bat speed from marker data.
- Identify how long each hitter spends in an ideal attack-angle window.
- Measure where that ideal zone occurs relative to the hitter's center of mass.
- Compare marker-derived contact metrics against OBP-provided contact bat speed and attack angle fields.
- Preserve force and segment-onset landmarks so swing-path metrics can be interpreted alongside lower-body timing.

## Dataset Context

The analysis uses Driveline's OBP baseball hitting dataset. The swings were collected while hitters faced a pitching machine set around 65 mph from roughly 40 ft away. That means the project is focused on movement quality and swing geometry, not pitcher deception or game-like pitch variation.

Raw OBP data is not included in this repository. To regenerate the full analysis, download the OBP data locally and place it in the expected structure described below.

## Included Example Viewer

Open one of these standalone HTML files in a browser:

- [Viewer index](Viewer-Examples/index.html)
- [Example 180_1](Viewer-Examples/180_1.html)
- [Example 398_4](Viewer-Examples/398_4.html)
- [Example 282_1](Viewer-Examples/282_1.html)
- [Example 24_3](Viewer-Examples/24_3.html)
- [Example 181_8](Viewer-Examples/181_8.html)

The HTML files are self-contained examples, so they can be opened without running Python.

## Viewer Features

The swing viewer includes:

- side, top, and front views of the swing
- timeline markers for force events, segment onsets, max segment velocity, and contact
- a red barrel ribbon for the contact-relevant ideal attack-angle segment
- adjustable ideal attack-angle range controls
- live frame readouts for attack angle, attack direction, and bat speed
- hitter info and contact metrics
- clickable event buttons that jump to key frames
- toggleable traces for pelvis, torso, lead arm, lead hand, center of mass, and barrel

## Key Metric Definitions

A fuller definitions page is included here:

- [Viewer metric definitions](docs/viewer_definitions.html)

Important definitions:

### Attack Angle

Attack angle is the vertical direction of the sweet spot's velocity relative to the ground. A value of 0 degrees means the sweet spot is moving parallel to the ground; positive values mean the sweet spot is moving upward.

### Attack Direction

Attack direction is the horizontal direction of the sweet spot's velocity. Pull-side direction is positive, opposite-field direction is negative, and values near 0 degrees represent a middle-field direction.

### Ideal Zone Time

Ideal zone time is the total time, in milliseconds, spent in the selected attack-angle range after speed, swing-window, and contact-relevant segment filters are applied.

### Ideal Zone COM-to-Barrel Out-Front Range

This is the range of sweet-spot depth relative to the hitter's center of mass during the selected ideal attack-angle segment. OBP uses +X as the pitcher direction, so positive values mean the sweet spot is farther toward the pitcher than the hitter's COM.

### Out Front (Contact COM)

This is a dynamic contact-depth metric: sweet spot X at contact minus COM X at contact. It behaves more like an extension/depth-at-impact measure.

### Out Front (Rear-most COM)

This compares the contact sweet-spot position against the hitter's most catcher-side COM position from 500 ms before contact through contact. This is closer to a pre-swing body-position reference and better reflects how much the hitter moved forward before contact.

## Current Dataset-Level Results

Across 677 OBP swings in the current processed dataset:

- Median ideal zone time: 14.0 ms
- Median ideal-zone path length: 8.24 inches
- Median contact out front using contact COM: 17.2 inches
- Median contact out front using rear-most COM: 29.6 inches
- Median marker-derived contact attack angle: 4.6 degrees
- Median marker-derived contact bat speed: 67.6 mph

These results are available in [outputs/attack_angle_zone_metrics.csv](outputs/attack_angle_zone_metrics.csv).

## Validation Notes

OBP provides contact-level bat speed and attack angle variables. This project recomputed sweet-spot velocity from marker positions so bat speed and attack angle could be shown across the entire swing path, not just at contact.

Marker-derived contact attack angle validated strongly against OBP's attack angle contact variable:

- Pearson r: about 0.997
- Mean difference: about 0.08 degrees
- RMSE: about 0.49 degrees

See:

- [Attack angle contact comparison](Figures/attack_angle_contact_comparison.png)
- [Marker AA vs OBP contact AA diagnostic](Figures/diagnostics/marker_aa_vs_attack_angle_contact_x.png)

## Figures

Selected figures are included in [Figures](Figures):

- [Attack zone time distribution](Figures/attack_zone_time_distribution.png)
- [Contact metrics distributions](Figures/contact_metrics_distributions.png)
- [Contact out-front distribution](Figures/contact_out_front_distribution.png)
- [Top hitters by attack zone time](Figures/top_hitters_attack_zone_time.png)
- [Attack angle contact comparison](Figures/attack_angle_contact_comparison.png)

## Project Structure

```text
OBP-Attack-Angle-Swing-Viewer/
  README.md
  requirements.txt
  scripts/
    run_obp_swing_time.py
    analyze_attack_angle_zone.py
    create_swing_qc_viewer.py
    analyze_initiation_relationships.py
  src/
    obp_swing_time/
      pipeline.py
  outputs/
    attack_angle_zone_metrics.csv
    attack_angle_zone_hitter_summary.csv
    attack_angle_contact_comparison_summary.csv
    ...
  Figures/
    *.png
    diagnostics/*.png
  Viewer-Examples/
    index.html
    definitions.html
    180_1.html
    398_4.html
    ...
  docs/
    viewer_definitions.html
    calculated_metrics.md
```

## Local Data Expected for Full Regeneration

Default local data root:

```text
E:\Baseball\Data\OBP
```

Expected files:

```text
Baseball Hitting\2-12-26.OBP.csv
Baseball Hitting\poi_metrics.csv
Baseball Hitting\hittrax.csv
3D\landmarks.zip
3D\joint_velos.zip
3D\force_plate.zip
```

## How to Reproduce

From this project folder:

```powershell
py scripts\run_obp_swing_time.py
py scripts\analyze_attack_angle_zone.py
```

The first script builds the processed model dataset and supporting event tables. The second script calculates attack-angle metrics, writes CSV summaries, generates figures, and creates the HTML swing viewers.

## Notes and Limitations

- The exact bat-ball impact location on the barrel is not directly known, so the sweet spot/barrel proxy is reconstructed from available bat markers.
- Attack direction, swing length, and swing path tilt are project-derived metrics because matching OBP/Blast reference fields were not available.
- Contact out-front values are coordinate-system dependent. OBP uses +X toward the pitcher, while Baseball Savant CSV documentation refers to mound-to-plate as Y.
- Since the data came from a pitching machine environment, findings should be interpreted as swing-movement relationships rather than game-decision relationships.

## Included Processed Support Tables

A few small processed CSVs are included so the analysis is easier to inspect without reopening the full raw OBP archives:

- `outputs/model_dataset.csv`
- `outputs/swing_manifest.csv`
- `outputs/onset_metrics.csv`
- `outputs/initiation_analysis/velocity20_primary_model/velocity20_primary_onset_rows.csv`

The full raw marker, force plate, and joint-velocity archives are intentionally not included because they are large and should be downloaded from the OBP source data when regenerating everything from scratch.

