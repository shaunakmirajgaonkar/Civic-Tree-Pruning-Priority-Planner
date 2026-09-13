# Project Overview

## Purpose
Support local municipal planning teams by screening trees for potential pruning-review priority.

## Main signals
Branch condition, power-line distance, pedestrian exposure, wind risk, inspection condition, dead branches, inspection age, pruning age, incidents, road exposure, school proximity, and crew access.

## Scoring
The dashboard combines normalized local signals into an explainable 0–100 screening score. Higher scores indicate stronger reasons for additional review. The weighting is intentionally transparent in `app.py`.

## Outputs
Priority class, suggested review window, top risk drivers, operational queue, zone benchmark, scenario impact, and CSV export.
