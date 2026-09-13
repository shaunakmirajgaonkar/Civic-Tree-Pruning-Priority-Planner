# Civic Tree-Pruning Priority Planner

A privacy-conscious, local-first Streamlit dashboard for screening municipal trees that may need pruning review using branch condition, power-line proximity, pedestrian use, wind risk, inspection history, dead branches, incidents, and maintenance signals.

## Features
- Explainable 0–100 pruning priority score
- Routine / Watch / High / Critical classification
- Priority landscape and zone benchmarking
- Pruning work queue
- Tree-level risk anatomy and top drivers
- Power-line, pedestrian, wind, inspection, branch-condition and maintenance signals
- Scenario Lab for branch condition, utility proximity, wind risk and pedestrian exposure
- Local CSV upload with required-column validation
- Filtered CSV export
- Local SVG visual assets
- No external APIs or cloud inference required

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The included sample CSV is designed for immediate testing.

## Decision-support notice
This application is a screening and planning tool. Scores do not certify tree safety, prescribe pruning work, or replace qualified arborist inspection, utility review, traffic assessment, emergency procedures, or municipal policy.
