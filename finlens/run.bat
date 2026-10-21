@echo off
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
pip install -q -r requirements.txt
if not exist model\tone_model.joblib python train_model.py
start "" http://localhost:5000
python app.py
