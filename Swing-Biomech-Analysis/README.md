# Baseball Swing Biomechanics Analysis

## Overview

This project analyzes biomechanical differences between baseball swings using motion capture and force plate data from the Driveline OpenBiomechanics dataset.

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

---

## Methods

### Force Plate Analysis

- Peak vertical force (Fz)
- Time to peak force
- Impulse across windows
- Force curve shape

### Rotational Kinematics

- Pelvis angular velocity
- Torso angular velocity
- Elbow and hand velocity
- Sequencing timing

### Hip-Shoulder Separation

- Separation at key events
- Maximum separation
- Separation velocity

---

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
    <td><img src="Figures/Lefty%20HSS.png" width="400"/></td>
    <td><img src="Figures/Righty%20HSS.png" width="400"/></td>
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
