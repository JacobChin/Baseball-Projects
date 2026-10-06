# Baseball-Projects

## Overview
This repository contains baseball analytics projects focused mainly on aiding in player development on the hitting side. I want to really dive into the science of hitting using data and help discover new techniques and be on the cutting edge of the race to keep up with the improved pitching MLB has to offer.

## OBP Biomechanical Swing Viewer:
This project builds on Driveline Baseball's OpenBiomechanics hitting data to create a frame-by-frame swing viewer and dataset-level analysis of attack angle, attack direction, bat speed, force timing, segment onsets, contact depth, swing length, and swing path tilt. The viewer highlights the portion of the barrel path where the sweet spot is moving through a selected attack-angle window, validates marker-derived attack angle and bat speed against OBP contact fields, and provides a cleaner way to QC and compare full swing movement patterns.

## Advanced Spray Chart:
This project builds an interactive spray chart and leaderboard tool for analyzing hitter contact quality in specific game contexts. The notebook combines Statcast batted-ball data with swing metrics and allows filtering by season, count, pitch group or pitch type, strike zone location, pitcher handedness, batted-ball result, spray angle range, and minimum batted balls. Zone filters are mirrored by hitter handedness so the same location concept can be compared across left-handed and right-handed hitters.

The leaderboard includes metrics such as xBA, xwOBA, EV50, median launch angle, squared-up rate, bat speed, swing length, attack angle, swing path tilt, and contact point out in front. It also includes a composite percentile tool that lets multiple metrics be combined into one ranking while choosing whether higher or lower values are preferred for each metric. A player lookup feature makes it possible to search for a specific hitter's row within the current filtered leaderboard without expanding the visible leaderboard to hundreds of rows.

## Optimal Contact Point:
This project analyzes the relationship between bat-ball contact location and batted ball outcomes using Statcast data retrieved via Python. The analysis models horizontal and vertical contact positions relative to the batter and examines their impact on exit velocity. The workflow includes data cleaning, feature selection, and exploratory data analysis using Pandas, with visualization techniques including scatter plots, binned aggregations, and 2D heatmaps to estimate conditional relationships between contact point and performance. The results highlight spatial sweet spots associated with higher exit velocities and illustrate how optimal contact depth varies with pitch location.

## Pitch Spin Project:
Tried to recreate the spin of pitches from the hitter/catcher perspective to a certain extent using Baseball Savant data. I quickly realized that grip and pronation/supination both play a significant role in seam orientation at release, and there is not public data on this for each pitcher. Nevertheless, I got a realistic 3D model of a baseball and was able to make it spin in the directions I wanted. With further data on seam orientation, I may return to this project and make it more realistic.

## Swing Biomechanics Project:
This analysis was taken from Driveline Baseball's OBP data and compares two players' swings who are the same height, weight, and age. Both hit balls with the same launch angle off a machine, but had significantly different bat speeds and exit velocities. The right-handed hitter produced significantly more bat speed, and this notebook dives into possible explanations, mainly focusing on pelvis and torso velocities, angles, and acceleration along with force production using force plate data. 3D models were created from the biomechanical data points so the swing can be inspected frame by frame.

## Pitch Tunneling Project:
This analysis aims to quantify the effectiveness of different pitch combinations and their tunneling. I built a model using all 2023 pitches to calculate the average tunneling efficiency of any two pitches in a pitcher's arsenal, focusing on pairs with similar release points and initial trajectories. Tunneling was measured by comparing the spatial separation of two pitches at the decision window, approximately 150 ms after release, using the combined X and Z distances to capture how similar the pitches appear to the hitter at that moment.

I then ranked pitchers based on this tunneling efficiency to identify which pitch combinations are most deceptive. In addition to the aggregate model, I developed a physics-based 3D simulation that reconstructs individual pitch trajectories from Statcast data and visualizes them from the hitter's point of view. This allows for direct comparison of specific pitch pairs, showing how they diverge over time and at the decision point. The simulation includes adjustable viewpoints, real-time animation, and strike zone context to better represent what a hitter actually sees. This analysis does not account for seam-shifted wake, spin axis nuances, or full aerodynamic modeling due to data limitations.
