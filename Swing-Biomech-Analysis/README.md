Baseball Swing Biomechanics Analysis
Overview

This project analyzes biomechanical differences between baseball swings using motion capture and force plate data from the Driveline OpenBiomechanics dataset.

The goal is to understand how ground reaction forces from the lead-leg block translate into rotational acceleration and energy transfer through the kinetic chain.

The analysis combines force plate data, joint kinematics, angular velocities, and hip-shoulder separation to evaluate swing efficiency and sequencing.

Event Definitions

Key swing events were defined using dataset-provided times:

FP10 – lead-leg vertical force reaches 10% bodyweight

FP100 – lead-leg vertical force reaches 100% bodyweight

Contact – provided bat-ball contact time

These were converted into frame indices for alignment across all signals.

Analysis Windows

The swing was segmented into:

FP10-20 → FP10 (early loading)

FP10 → FP100 (force development)

FP100 → FP100+20 (early rotation)

FP100+20 → Contact (energy transfer phase)

Methods
Force Plate Analysis

Peak vertical force (Fz)

Time to peak force

Impulse across windows

Force curve shape

Rotational Kinematics

Angular velocity magnitude:

|ω| = sqrt(wx² + wy² + wz²)

Segments:

Pelvis

Torso

Lead elbow

Lead hand

Hip-Shoulder Separation (HSS)
HSS = torso_angle_z - pelvis_angle_z

Measured:

Value at key events

Maximum separation

Separation velocity

Efficiency Metric
Efficiency = pelvis angular acceleration / impulse

This evaluates how effectively force becomes rotation.

Key Visualizations
Sequencing

Force Curve

Hip-Shoulder Separation

Lefty vs Righty Comparison
1. Force Production

Both swings produced similar total impulse

Righty produced:

Higher peak force

Shorter time to peak

Sharper force curve

Interpretation:

The righty creates a more effective lead-leg block, which is critical for rotational acceleration.

2. Rotational Acceleration

Righty showed significantly higher:

Pelvis angular acceleration

Early post-FP100 rotational gain

Lefty:

Lower acceleration despite similar impulse

Interpretation:

The difference is not strength — it is force application timing and efficiency.

3. Efficiency (Force → Rotation)

Righty:

Much higher acceleration per impulse

Lefty:

Lower efficiency across all windows

Interpretation:

Righty converts force into rotation more effectively.

4. Hip-Shoulder Separation

Lefty showed:

Greater maximum separation

Righty showed:

Better timing and utilization of separation

Interpretation:

Separation magnitude alone does not determine performance — timing matters more.

5. Sequencing

Righty:

Pelvis → Torso → Elbow → Hand

Clear proximal-to-distal transfer

Lefty:

More overlap between peaks

Less clean sequencing

Interpretation:

Righty transfers energy more efficiently through the kinetic chain.

6. Pre-FP10 Behavior

Lefty:

More early rotation before FP10

Higher early pelvis acceleration

Interpretation:

Possible early leakage of rotational energy before the lead-leg block.

7. Lead-Leg Block Mechanics

Righty:

Faster force rise

Earlier peak

More abrupt block

Lefty:

Slower force buildup

More spread-out force application

Interpretation:

The rate of force development, not just magnitude, is critical.

Key Insights

Peak force alone does not determine performance

Impulse can be similar across swings with different outcomes

Efficiency (acceleration per impulse) is a key differentiator

Hip-shoulder separation magnitude is not sufficient on its own

Sequencing and timing are critical for energy transfer

Lead-leg block characteristics strongly influence rotational output

Player Development Takeaways

This analysis suggests several actionable training insights:

1. Improve Rate of Force Development

Focus on:

Explosive lower-body training

Lead-leg block stiffness

Rapid force application

2. Optimize Timing of Rotation

Avoid:

Early torso or pelvis rotation before FP10

Train:

Delayed rotation until after force is established

3. Improve Force → Rotation Transfer

Focus on:

Pelvis acceleration immediately after FP100

Efficient kinetic chain sequencing

4. Prioritize Sequencing Over Raw Force

Training should emphasize:

Pelvis-first movement

Clean segment timing

5. Separation Timing Over Magnitude

More separation is not always better —
how and when it is used matters more.

Tools Used

Python

NumPy

Pandas

Matplotlib

SciPy

Jupyter Notebook

Repository Structure
Swing-Biomech-Analysis
│
├── swing_biomech_analysis.ipynb
├── README.md
└── figures
Author

Jacob Chin
Data Science & Baseball Biomechanics
