# Baseball Swing Biomechanics Analysis

## Overview

This project analyzes biomechanical differences between baseball swings using motion capture and force plate data from the Driveline OpenBiomechanics dataset.

The goal is to understand how ground reaction forces from the lead-leg block translate into rotational acceleration and energy transfer through the kinetic chain.

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

## Key Findings

- Righty produced **higher peak force with shorter time to peak**
- Both swings had **similar impulse**, but different outcomes
- Righty showed **greater rotational efficiency**
- Lefty had **more hip-shoulder separation**, but less effective timing
- Sequencing was cleaner in the righty (**better energy transfer**)

---

## Player Development Insights

- Improve **rate of force development** (not just total force)
- Delay rotation until after **FP100**
- Focus on **pelvis → torso → arm sequencing**
- Prioritize **timing over raw separation**

---

## Project Structure

## Lefty vs Righty Comparison

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
