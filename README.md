# Baseball-Projects

## Overview
This repository contains baseball analytics projects focused mainly on aiding in player development on the hitting side.
I want to really dive into the science of hitting using data and help discover new techniques and be on the cutting edge of the race
to keep up with the improved pitching MLB has to offer.

## Pitch Tunneling Project:
This analysis aims to calculate effectiveness of different pitch combinations and their tunneling. I built a model using all 2024 
pitches that will calculate the average (tunneling efficiency) of any two pitches in a pitcher's arsenal with relatively the same 
release point from release to decision window (150ms). This was done by taking the sum of the difference of the x and z distances 
of these two pitches (how similar do they look at the decision point). I also ranked these by best tunneling efficiency and worst
for certain pitches to see which pitchers tunneled the best (keep in mind this doesn't account for spin, just purely the location
of the ball at the decision point). Keep in mind ball flight calculations were limited due to lack of data for seam orientation
and atmospheric conditions.

## Swing Biomechanics Project:
This analysis was taken from Driveline Baseball's OBP Data, which compares two players' swings that are the same height, weight and age.
Both were hit with the same launch angle off of a machine, but have significantly different bat speed/exit velocities. The righty
produces significantly more bat speed, and this notebook dives into some of the possibilities behind this, mainly focusing on the
pelvis and torso velocities, angles, and acceleration along with force production using force plate data. 3D models were created of
the swing using the biomech data points over time, where you can go frame by frame in each swing.

## Pitch Spin Project:
Tried to recreate the spin of pitches from the hitter (catcher's) perspective to a certain extent using baseball savant data. 
Quickly realized that grip and pronation/supination both play a significant role in seam orientation at release, and there isn't 
public data on this for each pitcher. Nevertheless, I got a pretty realistic 3D model of a baseball and was able to make it spin 
in the directions that I wanted it too, and maybe with further data on seam orientation I can return to this project and make it
more realistic.

## Optimal Contact Point:
This project analyzes the relationship between bat–ball contact location and batted ball outcomes using Statcast data retrieved via Python.
The analysis models horizontal and vertical contact positions relative to the batter and examines their impact on exit velocity. The workflow
includes data cleaning, feature selection, and exploratory data analysis using Pandas, with visualization techniques including scatter plots,
binned aggregations, and 2D heatmaps to estimate conditional relationships between contact point and performance. The results highlight spatial
“sweet spots” associated with higher exit velocities and illustrate how optimal contact depth varies with pitch location.
