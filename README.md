# SentinelAI — Cyber Threat Detection (Streamlit)

A professional multipage Streamlit interface for a saved XGBoost network traffic classifier. Use the clickable navigation links at the top of each page; the default left sidebar page menu is hidden.

## Files
- `app.py`: project overview
- `pages/1_Test_Model.py`: CSV upload, prediction, results and export
- `pages/2_About_Model.py`: model documentation
- `.streamlit/config.toml`: hides the default sidebar page menu
- `requirements.txt`: Python dependencies

## Add your existing files
Copy your current `models/` folder and your real `benign_sample.csv` and `attack_sample.csv` into the project root. The workflow image is not required.

Expected model paths:
- `models/final_xgboost_model.pkl`
- `models/xgb_imputer.pkl`
- `models/xgb_features.pkl`

## Run
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
Run this command from the project root.

## Important
The testing page uses the imputer statistics and feature order from your existing code. Ensure it matches the full preprocessing pipeline used during training, including any categorical encoders. Confirm class labels before assuming `0 = Benign` and `1 = Attack`.
