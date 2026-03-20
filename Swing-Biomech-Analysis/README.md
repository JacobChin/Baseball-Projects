# Baseball Swing Biomechanics Analysis

## Summary

This analysis compares two biomechanically similar hitters under identical conditions and identifies key differences in force application, sequencing, and rotational efficiency that explain a ~9 mph difference in bat speed.

## Overview

This project analyzes biomechanical differences between baseball swings using motion capture and force plate data from the Driveline OpenBiomechanics dataset, mainly focusing on the pelvis and torso.

This takes two swings from different players, one from a lefty and one from a righty. These players are both the same height, weight, age, and playing level.

All swings were off of the same machine set at ~65 mph from ~40 ft away from home plate, and both of these swings had the same launch angle and were to the pull side.

The lefty had a max bat speed of 68.25 and a bat speed of 67.29 at contact, while the righty had a max bat speed of 76.32 and a bat speed of 74.51 at contact.

The goal is to understand some of the reasons why the righty is able to produce such a significant amount of bat speed compared to the lefty.

The analysis combines force plate data, joint kinematics, angular velocities, and hip-shoulder separation to evaluate swing efficiency and sequencing.

---

## Event Definitions

Key swing events were defined using dataset-provided times:

- **FP10** — lead-leg vertical force reaches **10% bodyweight**
- **FP100** — lead-leg vertical force reaches **100% bodyweight**
- **Contact** — provided bat-ball contact time

These were converted into frame indices for alignment across all signals.

---

## Analysis Windows

The swing was segmented into:

- **FP10-20 → FP10** *(20 frames before fp10 to fp10)*
- **FP10 → FP100** 
- **FP100 → FP100+20** *(fp 100 to 20 frames after fp100)*
- **FP100+20 → Contact**
- **Lefty Frames: 487-507, 507-523, 523-543, 543-571**
- **Righty Frames: 707-727, 727-744, 744-764, 764-797**

---
## Methods

### Data Source
All data were obtained from the Driveline OpenBiomechanics dataset, including synchronized motion capture and force plate recordings.

---

### Signal Processing and Alignment
- Motion capture data were sampled at 360 Hz  
- Force plate data were sampled at a higher analog frequency and converted to the motion capture frame scale  
- All signals were aligned using shared event markers (FP10, FP100, Contact)

Force plate data were mapped to the motion capture timeline using sampling rate conversion to ensure temporal consistency across kinematic and kinetic variables.

---

### Event-Based Segmentation
The swing was segmented into four biomechanically meaningful windows based on lead-leg force development:

1. FP10-20 → FP10  
2. FP10 → FP100  
3. FP100 → FP100+20  
4. FP100+20 → Contact  

These windows were chosen to capture:
- Initial force acceptance  
- Force buildup  
- Transition to rotational acceleration  
- Final acceleration into contact  

---

### Kinematic Analysis
Joint angles and angular velocities were analyzed for:
- Pelvis  
- Torso  
- Lead elbow  
- Lead hand  

Angular velocity magnitudes were computed using 3D components:

\[
|\omega| = \sqrt{\omega_x^2 + \omega_y^2 + \omega_z^2}
\]

Peak velocities and timing of peak velocities were extracted for each segment.

---

### Acceleration and Sequencing
Average angular acceleration was computed within each window:

\[
\alpha = \frac{\Delta \omega}{\Delta t}
\]

Segmental sequencing was evaluated using:
- Timing differences between peak velocities  
- Frame and time offsets relative to FP10  

---

### Force Plate Analysis
Vertical ground reaction forces (Fz) were analyzed for both lead and rear legs.

Metrics included:
- Force-time curves  
- Peak force magnitude and timing  
- Rear-foot unloading behavior  

Impulse was computed for each window:

\[
\text{Impulse} = \sum F \cdot \Delta t
\]

---

### Efficiency Metric
An efficiency metric was defined as:

\[
\text{Efficiency} = \frac{\text{Segment Acceleration}}{\text{Impulse}}
\]

This quantifies how effectively force production translates into rotational acceleration.

Efficiency was evaluated for windows with sufficient force magnitude (FP10 onward) to ensure stability of the metric.

---

### Comparative Approach
All metrics were computed independently for each swing and compared directly to identify differences in:
- Force production  
- Rotational output  
- Sequencing  
- Energy transfer efficiency  

## Lefty vs Righty Comparison

<table>
<tr>
<td align="center"><b>Lefty</b></td>
<td align="center"><b>Righty</b></td>
</tr>
<tr>
<td><img src="Figures/LeftySwing.gif" width="350"></td>
<td><img src="Figures/RightySwing.gif" width="350"></td>
</tr>
</table>

*Both swings are visualized from a consistent side-view perspective for direct comparison of sequencing and rotation.*

<table>
  <tr>
    <td align="center"><b>Lefty (FP100 – Side View)</b></td>
    <td align="center"><b>Righty (FP100 – Side View)</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty%20Fp100%20Side%20View_Zoom.png" width="200"/></td>
    <td><img src="Figures/Righty%20FP100%20Side%20View_Zoom.png" width="200"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty (FP100 – Back View)</b></td>
    <td align="center"><b>Righty (FP100 – Back View)</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty%20FP100%20Back%20View_Zoom.png" width="200"/></td>
    <td><img src="Figures/Righty%20FP100%20Back%20View_Zoom.png" width="200"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty%20Zoomed%203D%20angular%20Velos%20Graph.png" width="400"/></td>
    <td><img src="Figures/Righty%20Zoomed%203D%20angular%20Velos%20Graph.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty%20Metrics%20at%20FP100.png" width="400"/></td>
    <td><img src="Figures/Righty%20Metrics%20at%20FP100.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty_All_Pelvis_Velos_Acc.png" width="400"/></td>
    <td><img src="Figures/Righty_All_Pelvis_Velos_Acc.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty_Torso_Velos.png" width="400"/></td>
    <td><img src="Figures/Righty_Torso_Velos.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty_Elbow_Velos.png" width="400"/></td>
    <td><img src="Figures/Righty_Elbow_Velos.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty_Hand_Velos.png" width="400"/></td>
    <td><img src="Figures/Righty_Hand_Velos.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty_Peak_Velos.png" width="400"/></td>
    <td><img src="Figures/Righty_Peak_Velos.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty_Frame_Diff.png" width="400"/></td>
    <td><img src="Figures/Righty_Frame_Diff.png" width="400"/></td>
  </tr>
</table>

<table>
<tr>
  <td align="center"><b>Lefty</b></td>
  <td align="center"><b>Righty</b></td>
</tr>
<tr>
  <td><img src="Figures/Lefty%20Pelvis%20angles.png" width="400"/></td>
  <td><img src="Figures/Righty%20Pelvis%20angles.png" width="400"/></td>
</tr>
</table>

<table>
<tr>
  <td align="center"><b>Lefty</b></td>
  <td align="center"><b>Righty</b></td>
</tr>
<tr>
  <td><img src="Figures/Lefty%20Torso%20Angles.png" width="400"/></td>
  <td><img src="Figures/Righty%20Torso%20Angles.png" width="400"/></td>
</tr>
</table>

<table>
<tr>
  <td align="center"><b>Lefty</b></td>
  <td align="center"><b>Righty</b></td>
</tr>
<tr>
  <td><img src="Figures/Lefty_Pelvis_Angle_Changes.png" width="400"/></td>
  <td><img src="Figures/Righty_Pelvis_Angle_Changes.png" width="400"/></td>
</tr>
</table>

<table>
<tr>
  <td align="center"><b>Lefty</b></td>
  <td align="center"><b>Righty</b></td>
</tr>
<tr>
  <td><img src="Figures/Lefty_Torso_Angle_Changes.png" width="400"/></td>
  <td><img src="Figures/Righty_Torso_Angle_Changes.png" width="400"/></td>
</tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty_Rear_Foot_Graph.png" width="400"/></td>
    <td><img src="Figures/Righty_Rear_Foot_Graph.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty%20Peak%20Force%20Graph.png" width="400"/></td>
    <td><img src="Figures/Righty%20Peak%20Force%20Graph.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty%20Peak%20Force%20Numbers.png" width="400"/></td>
    <td><img src="Figures/Righty%20Peak%20Force%20Numbers.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty%20Impulse.png" width="400"/></td>
    <td><img src="Figures/Righty%20Impulse.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty%20Efficiency.png" width="400"/></td>
    <td><img src="Figures/Righty%20Efficiency.png" width="400"/></td>
  </tr>
</table>

## Key Takeaways

### 1. Greater Rotational Output Drives Higher Bat Speed
The right-handed hitter produced consistently higher angular velocities across all segments (pelvis, torso, elbow, and hand), culminating in substantially greater bat speed at contact. This indicates that the primary driver of the bat speed difference is increased rotational output rather than differences in setup or stride.

---

### 2. More Efficient Force-to-Rotation Conversion (FP10 → FP100)
During the critical force development window (FP10 → FP100), the righty demonstrated higher pelvis acceleration per unit of force (efficiency), suggesting more effective conversion of ground reaction force into rotational motion.  

This indicates superior use of the lead leg as a rotational driver rather than simply a stabilizing structure.

---

### 3. Superior Late-Phase Acceleration (FP100 → FP100+20)
The righty generated significantly greater pelvis and torso acceleration immediately after reaching peak force (FP100), highlighting a more effective transition from force production to rotational acceleration.  

This phase is critical for downstream energy transfer into the upper segments and ultimately the bat.

---

### 4. Earlier and More Rapid Kinematic Sequencing
The righty exhibited tighter sequencing between segments:
- Smaller pelvis → torso timing gap  
- Faster progression from torso → elbow → hand  

This indicates a more efficient kinetic chain, allowing energy to transfer more quickly and effectively through the system.

---

### 5. Greater Distal Segment Acceleration (Elbow and Hand)
The righty showed substantially higher angular velocities and accelerations in the elbow and hand segments, particularly in the late swing phases.  

This suggests that upstream improvements (pelvis/torso) are effectively cascading into distal segments, amplifying bat speed.

---

### 6. Rear-Foot Force Behavior Indicates Different Transfer Strategies
The lefty demonstrated a clear rear-foot unloading pattern approaching contact, while the righty maintained rear-foot force deeper into the swing.  

This suggests differing force-transfer strategies:
- **Lefty:** earlier unloading and forward shift  
- **Righty:** sustained rear-side force contributing to continued rotational support  

The righty’s pattern appears more effective in maintaining rotational acceleration into contact.

---

### 7. Similar Setup, Different Outcomes
Despite nearly identical conditions (pitch speed, distance, launch angle, player characteristics), the two swings produced significantly different outputs.  

This reinforces that **small differences in sequencing and force application can result in large differences in performance outcomes**.

---

### Overall Conclusion
The right-handed hitter’s higher bat speed is primarily driven by:
- More efficient force utilization during FP10 → FP100  
- Stronger and better-timed rotational acceleration after FP100  
- Tighter kinematic sequencing  
- Greater amplification into distal segments  

Together, these factors create a more effective kinetic chain and higher bat speed at contact.
