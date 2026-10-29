# Baseball-Projects

## Overview
This repository contains baseball analytics projects focused mainly on aiding in player development on the hitting side. I want to really dive into the science of hitting using data and help discover new techniques and be on the cutting edge of the race to keep up with the improved pitching MLB has to offer.

## OBP Biomechanical Swing Viewer:

[Open the live OBP Biomechanical Swing Viewer app](https://share.streamlit.io/jacobchin/baseball-projects/main/OBP-Biomechanical-Swing-Viewer/app.py)

The free Streamlit app may be asleep after a period of inactivity. Anyone can wake it from the app page; allow about a minute for it to restart.
This project builds on Driveline Baseball's OpenBiomechanics hitting data to create a frame-by-frame swing viewer and dataset-level analysis of attack angle, attack direction, bat speed, force timing, segment onsets, contact depth, swing length, and swing path tilt. The viewer highlights the portion of the barrel path where the sweet spot is moving through a selected attack-angle window, validates marker-derived attack angle and bat speed against OBP contact fields, and provides a cleaner way to QC and compare full swing movement patterns.

## Advanced Spray Chart:

[Open the live Advanced Spray Chart app](https://jacobchin-advanced-spray-chart.streamlit.app/)

This project is an interactive Streamlit spray chart and leaderboard app built from Statcast batted-ball and bat-tracking data covering 2024 through 2026. It can be launched directly without running notebook setup cells and includes a compact app-ready dataset in the project folder. Users can filter by season, hitter, count, pitch group or pitch type, strike zone location, pitcher handedness, batted-ball result, normalized spray angle, and minimum batted balls. Zone filters mirror automatically by hitter handedness.

The app includes xBA, xwOBA, EV50, median launch angle, squared-up rate, bat speed, swing length, attack angle, swing path tilt, and contact point out in front. Squared-up contact can be defined at a custom threshold, with optional over/under point filtering. The leaderboard also supports multi-metric composite percentiles, searchable player rows, and downloadable interactive charts and CSV tables.
## Lineup Optimizer:

[Open the live Lineup Optimizer app](https://jacobchin-lineup-optimizer.streamlit.app/)

Lineup Optimizer is an interactive Streamlit offense simulator for selecting any nine 2025 hitters, creating custom hitters, simulating an ordered lineup, and searching candidate batting orders. Duplicate hitters are allowed, making clone-lineup experiments such as nine Aaron Judges possible.

The production model combines season-level plate-appearance outcomes with direct 2021-2025 runner-movement transitions, Sprint Speed-sensitive advancement, contextual stolen-base behavior, a fitted double-play adjustment, and an optional contextual non-intentional walk model. The project also includes lineups by decade, all-time lineup results, along with a detailed model specification and limitations.
## Optimal Contact Point:
This project analyzes the relationship between bat-ball contact location and batted ball outcomes using Statcast data retrieved via Python. The analysis models horizontal and vertical contact positions relative to the batter and examines their impact on exit velocity. The workflow includes data cleaning, feature selection, and exploratory data analysis using Pandas, with visualization techniques including scatter plots, binned aggregations, and 2D heatmaps to estimate conditional relationships between contact point and performance. The results highlight spatial sweet spots associated with higher exit velocities and illustrate how optimal contact depth varies with pitch location.

## Pitch Spin Project:
Tried to recreate the spin of pitches from the hitter/catcher perspective to a certain extent using Baseball Savant data. I quickly realized that grip and pronation/supination both play a significant role in seam orientation at release, and there is not public data on this for each pitcher. Nevertheless, I got a realistic 3D model of a baseball and was able to make it spin in the directions I wanted. With further data on seam orientation, I may return to this project and make it more realistic.

## Swing Biomechanics Project:
This analysis was taken from Driveline Baseball's OBP data and compares two players' swings who are the same height, weight, and age. Both hit balls with the same launch angle off a machine, but had significantly different bat speeds and exit velocities. The right-handed hitter produced significantly more bat speed, and this notebook dives into possible explanations, mainly focusing on pelvis and torso velocities, angles, and acceleration along with force production using force plate data. 3D models were created from the biomechanical data points so the swing can be inspected frame by frame.

## Pitch Tunneling Project:
This analysis aims to quantify the effectiveness of different pitch combinations and their tunneling. I built a model using all 2023 pitches to calculate the average tunneling efficiency of any two pitches in a pitcher's arsenal, focusing on pairs with similar release points and initial trajectories. Tunneling was measured by comparing the spatial separation of two pitches at the decision window, approximately 150 ms after release, using the combined X and Z distances to capture how similar the pitches appear to the hitter at that moment.

I then ranked pitchers based on this tunneling efficiency to identify which pitch combinations are most deceptive. In addition to the aggregate model, I developed a physics-based 3D simulation that reconstructs individual pitch trajectories from Statcast data and visualizes them from the hitter's point of view. This allows for direct comparison of specific pitch pairs, showing how they diverge over time and at the decision point. The simulation includes adjustable viewpoints, real-time animation, and strike zone context to better represent what a hitter actually sees. This analysis does not account for seam-shifted wake, spin axis nuances, or full aerodynamic modeling due to data limitations.
