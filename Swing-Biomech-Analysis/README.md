# Baseball Swing Biomechanics Analysis

## Summary

This analysis compares two biomechanically similar hitters under identical conditions and explains a ~10 mph difference in bat speed through differences in force utilization, rotational timing, and kinetic chain efficiency.

Despite generating nearly identical total force, the higher-performing hitter demonstrates superior force-to-rotation conversion, more effective late-phase acceleration, tighter kinematic sequencing, and a longer, more efficient barrel path. These factors collectively result in greater distal segment speeds and increased bat speed at contact.

This study highlights that bat speed is not primarily driven by force production alone, but by how efficiently that force is transferred through the kinetic chain.

## Overview

This project analyzes biomechanical differences between baseball swings using motion capture and force plate data from the Driveline OpenBiomechanics dataset, mainly focusing on the pelvis and torso.

This takes two swings from different players, one from a lefty and one from a righty. These players are both the same height, weight, age, and playing level.

All swings were off of the same machine set at ~65 mph from ~40 ft away from home plate, and both of these swings had the same launch angle and were to the pull side.

Both pitches were in the middle and inside zone to each hitter.

The lefty had a max bat speed of 68.25 and a bat speed of 67.29 at contact, while the righty had a max bat speed of 78.31 and a bat speed of 77.40 at contact.

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
## Barrel Path and Contact Position

### Barrel Path Length

Barrel path length was defined as the total distance traveled by the distal end of the bat from FP10 to contact. The distal bat position was approximated using the midpoint between MARKER2 and MARKER3, which together represent the tip region of the bat.

At each frame, the position of the bat tip was computed as:

tip = 0.5 × (MARKER2 + MARKER3)

The total path length was then calculated by summing the frame-to-frame Euclidean distances of this point from FP10 to contact:

Path Length = Σ √[(Δx)² + (Δy)² + (Δz)²]

This provides a measure of how far the bat travels through space during the acceleration phase of the swing.

---

### Contact Position (Forward Distance)

Contact position was defined as the forward (x-axis) distance between the hitter’s sternum marker (STRN) and the bat tip at the frame of contact.

In the dataset’s coordinate system:
- +x points from home plate toward the pitcher  
- +y points toward the right-handed batter’s box  
- +z points upward  

The bat contact point was approximated using the same distal bat estimate:

contact_point = 0.5 × (MARKER2 + MARKER3)

The forward distance at contact was then computed as:

Δx = x_contact − x_sternum

This value represents how far “out in front” of the torso contact occurs, independent of vertical or lateral position.

---

### Notes on Bat Representation

MARKER2 and MARKER3 define the distal end of the bat rather than the exact barrel sweet spot. As a result, both barrel path length and contact position are approximations of true barrel behavior. However, this approach provides a consistent and reliable proxy for comparing swing kinematics across players.

---
### Kinematic Analysis
Joint angles and angular velocities were analyzed for:
- Pelvis  
- Torso  
- Lead elbow  
- Lead hand  

Angular velocity magnitudes were computed using 3D components:

**|ω| = √(ωₓ² + ωᵧ² + ω_z²)**

Peak velocities and timing of peak velocities were extracted for each segment.

---

### Acceleration and Sequencing
Average angular acceleration was computed within each window:

**α = (ω_final − ω_initial) / Δt**

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

**Impulse = Σ(F · Δt)**

---

### Efficiency Metric
An efficiency metric was defined as:

**Efficiency = Acceleration / Impulse**

This quantifies how effectively force production translates into rotational acceleration.

Efficiency was evaluated for windows with sufficient force magnitude (FP10 onward) to ensure stability of the metric.

---

### Comparative Approach
All metrics were computed independently for each swing and compared directly to identify differences in:
- Force production  
- Rotational output  
- Sequencing  
- Energy transfer efficiency

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
    <td><img src="Figures/Lefty_Path.png" width="400"/></td>
    <td><img src="Figures/Righty_Path.png" width="400"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>Lefty</b></td>
    <td align="center"><b>Righty</b></td>
  </tr>
  <tr>
    <td><img src="Figures/Lefty_Contact_Point.png" width="400"/></td>
    <td><img src="Figures/Righty_Contact_Point.png" width="400"/></td>
  </tr>
</table>

# Segment Velocities and Acceleration
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

# Angles

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

# Force Production

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

### 1. Setup is Similar, but Rotational Strategy Differs Early

Both hitters demonstrate nearly identical setup characteristics, including stride length and overall positioning. However, key differences emerge at FP100:

- The lefty exhibits a more open pelvis relative to the pitcher  
- The lefty achieves greater early hip-shoulder separation (27.66° vs. 16.16°)  
- The righty maintains a more closed pelvis and torso orientation  

This indicates that the lefty initiates rotation earlier, while the righty delays rotational opening.

---

### 2. Early vs Late Acceleration Strategy

The lefty generates higher pelvis velocity early in the swing (FP10), reflecting an **early-acceleration strategy**.  

In contrast, the righty demonstrates lower early velocity but significantly greater acceleration after FP100, indicating a **delayed but more explosive acceleration pattern**.

This difference in timing of acceleration is a key separator between the two swings.

---

### 3. Superior Late-Phase Acceleration Drives Performance

From FP100 → FP100+20, the righty exhibits substantially higher pelvis and torso acceleration, representing a more effective transition from force production into rotational motion.

This late-phase acceleration is critical, as it directly feeds into distal segment speed and ultimately bat speed at contact.

---

### 4. More Efficient Kinematic Sequencing in the Righty

The righty demonstrates tighter and more efficient sequencing:

- Smaller pelvis → torso timing gap  
- Faster progression from torso → elbow → hand  
- More synchronized peak velocities across segments  

This allows energy to transfer more efficiently through the kinetic chain, minimizing energy loss between segments.

---

### 5. Greater Distal Segment Output (Elbow and Hand)

The righty produces significantly higher angular velocities in the elbow and hand, particularly in the late phases of the swing.

This confirms that upstream advantages (force timing and rotational acceleration) are effectively transferred into the distal segments, amplifying bat speed.

---

### 6. Rotational Patterns: Early Opening vs Sustained Rotation

Angle data shows that the lefty:

- Opens the pelvis earlier  
- Builds separation sooner  
- Rotates more gradually through the swing  

Whereas the righty:

- Stays closed longer  
- Builds separation later  
- Rotates more aggressively in the later phases  

---

### 7. Longer Barrel Path and More Forward Contact Support Greater Acceleration

The righty exhibits:

- A longer barrel path (128.48 in vs. 116.10 in)  
- A more forward contact position (21.88 in vs. 19.10 in)  

This indicates that the righty is able to accelerate the bat over a greater distance and carry that acceleration further into contact.
.

---

### 8. Similar Force Production, Different Outcomes

Both hitters generate nearly identical impulse during FP10 → FP100, indicating similar total force production.

However, the righty demonstrates significantly higher pelvis acceleration per unit of force, especially during:

- FP10 → FP100  
- FP100 → FP100+20  

This indicates that performance differences are driven not by force magnitude, but by **how efficiently force is converted into rotation**.

---

### 9. Earlier Force Utilization and Sustained Rear-Side Support

The righty reaches peak force earlier after FP100 and maintains rear-foot force deeper into the swing, while the lefty unloads the rear foot earlier.

This suggests that the righty:

- Utilizes force earlier in the swing  
- Maintains rotational support longer  
- Sustains acceleration deeper into the swing  

---

### 10. Force and Kinematics Combine to Drive Bat Speed Differences

The righty’s higher bat speed is the result of a combination of:

- More efficient force-to-rotation conversion  
- Stronger late-phase acceleration  
- More effective sequencing  
- Greater distal segment amplification  
- Longer and more efficient barrel path  

Together, these factors create a more effective kinetic chain and allow for greater bat speed at contact.

---

## Limitations and Future Work

Several additional factors could further strengthen this analysis:

- Quantifying the direction and vector of the lead leg block to better understand how force is applied into rotation  
- Incorporating athlete force capacity metrics (e.g., IMTP, countermovement jump) to contextualize force production capabilities  
- Tracking bat speed continuously throughout the swing to better characterize acceleration profiles  
- Accounting for bat moment of inertia (MOI), which can significantly influence achievable bat speed  
- Evaluating performance under game-like time constraints to assess whether these efficiency patterns persist under pressure  

These additions would provide a more complete understanding of how physical capacity, mechanics, and constraints interact to influence swing performance.

Lastly, being able to test these two swings in a game like environment with time constraints would be interesting to see if the efficiency of the right handed swing will break or not.


