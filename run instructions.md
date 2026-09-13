# Run Instructions — Mac / zsh

```bash
cd ~/Downloads
unzip -o Civic_Tree_Pruning_Priority_Planner_LATEST_ONLY.zip
cd Civic_Tree_Pruning_Priority_Planner
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Do not type the `%` or `$` shell prompt characters shown by some terminals.
