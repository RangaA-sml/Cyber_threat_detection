"""Shared UI, artifact loading, and inference helpers for SentinelAI."""
from pathlib import Path
import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "final_xgboost_model.pkl"
IMPUTER_PATH = ROOT / "models" / "xgb_imputer.pkl"
FEATURES_PATH = ROOT / "models" / "xgb_features.pkl"

GLOBAL_CSS = """
<style>
.block-container{max-width:1280px;padding-top:1.25rem;padding-bottom:3.5rem}
[data-testid="stSidebar"]{display:none}
[data-testid="stHeader"]{background:transparent}
.top-brand{display:flex;align-items:center;gap:.75rem;margin:.15rem 0 1rem}
.brand-icon{display:inline-grid;place-items:center;width:42px;height:42px;border-radius:13px;background:linear-gradient(145deg,#3b82f6,#173c9a);color:#fff;font-size:1.3rem;box-shadow:0 8px 20px #2563eb30}
.brand-title{font-size:1.05rem;font-weight:850;letter-spacing:-.025em;line-height:1.1}
.brand-sub{font-size:.62rem;letter-spacing:.17em;color:#8290a9;font-weight:800;margin-top:.25rem}
.nav-link div[data-testid="stPageLink"] a{border:1px solid rgba(128,145,170,.28);border-radius:12px;padding:.62rem .75rem;text-decoration:none;font-weight:750;justify-content:center;min-height:43px}
.nav-link div[data-testid="stPageLink"] a:hover{border-color:#3b82f6;background:rgba(59,130,246,.07)}
.hero{padding:clamp(1.6rem,4vw,3.6rem);border-radius:24px;background:linear-gradient(120deg,#0b1530 0%,#122a5a 58%,#1d4ed8 100%);color:white;margin:.7rem 0 2rem;position:relative;overflow:hidden}
.hero:after{content:'';position:absolute;width:290px;height:290px;border:1px solid #b9ceff30;border-radius:50%;right:-50px;top:-110px;box-shadow:0 0 0 40px #b9ceff0b,0 0 0 80px #b9ceff08;pointer-events:none}
.hero .eyebrow{color:#b9ceff;text-transform:uppercase;letter-spacing:.16em;font-size:.7rem;font-weight:850}
.hero h1{font-size:clamp(2.35rem,5vw,4.3rem);line-height:1.04;letter-spacing:-.05em;margin:.9rem 0 1rem;color:white}
.hero h1 span{color:#8fb2ff}
.hero p{max-width:780px;color:#d4def4;font-size:1.02rem;line-height:1.8;margin-bottom:0}
.section-label{font-size:.69rem;letter-spacing:.16em;text-transform:uppercase;font-weight:850;color:#3974e8}
.feature-card{height:100%;padding:1.35rem;border-radius:17px;border:1px solid rgba(128,145,170,.24);background:light-dark(#fff,#111a2d)}
.feature-card .icon{font-size:1.65rem;margin-bottom:.7rem}.feature-card h3{font-size:1.03rem;margin:0 0 .5rem}.feature-card p{font-size:.88rem;line-height:1.7;color:light-dark(#65718a,#aab7ce);margin:0}
.step-card{padding:1.1rem;border:1px solid rgba(128,145,170,.24);border-radius:15px;background:light-dark(#fff,#111a2d);height:100%}
.step-num{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:10px;background:#2563eb;color:white;font-weight:850;margin-bottom:.7rem}
.page-hero{padding:2rem 2.2rem;border-radius:20px;background:linear-gradient(120deg,light-dark(#f6f9ff,#0c1427),light-dark(#eaf1ff,#142344));border:1px solid rgba(128,145,170,.2);margin:.7rem 0 1.5rem}
.page-hero h1{margin:.55rem 0;font-size:clamp(2rem,4vw,3rem);letter-spacing:-.045em}
.page-hero p{color:light-dark(#65718a,#aab7ce);line-height:1.7;margin-bottom:0;max-width:850px}
div[data-testid="stMetric"]{padding:1rem 1.05rem;border:1px solid rgba(128,145,170,.24);border-radius:15px;background:light-dark(#fff,#111a2d)}
div[data-testid="stDataFrame"]{border:1px solid rgba(128,145,170,.2);border-radius:12px;overflow:hidden}
.footer{border-top:1px solid rgba(128,145,170,.2);padding-top:1rem;margin-top:2.5rem;color:#8290a9;font-size:.78rem}
@media(max-width:700px){.page-hero{padding:1.35rem}.hero{padding:1.5rem}.nav-link div[data-testid="stPageLink"] a{font-size:.78rem;padding:.55rem .35rem}}
</style>
"""


def render_navigation(active: str) -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown('''<div class="top-brand"><div class="brand-icon">⬡</div><div><div class="brand-title">SentinelAI</div><div class="brand-sub">NETWORK INTELLIGENCE</div></div></div>''', unsafe_allow_html=True)
    cols = st.columns([1, 1.25, 1.25])
    pages = [
        ("app.py", "⌂  Overview", "overview"),
        ("pages/1_Test_Model.py", "◈  Test the Model", "testing"),
        ("pages/2_About_Model.py", "ⓘ  About the Model", "about"),
    ]
    for col, (path, label, key) in zip(cols, pages):
        with col:
            st.page_link(path, label=label, use_container_width=True)
    st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
    st.divider()


@st.cache_resource(show_spinner="Loading trained model artifacts…")
def load_artifacts():
    missing = [p for p in (MODEL_PATH, IMPUTER_PATH, FEATURES_PATH) if not p.is_file()]
    if missing:
        return None, None, None, missing, None
    try:
        model = joblib.load(MODEL_PATH)
        imputer = joblib.load(IMPUTER_PATH)
        features = list(joblib.load(FEATURES_PATH))
        return model, imputer, features, [], None
    except Exception as exc:
        return None, None, None, [], str(exc)


def prepare_features(data: pd.DataFrame, features: list, imputer):
    missing = [col for col in features if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {', '.join(missing[:12])}" + (" …" if len(missing) > 12 else ""))
    X = data.loc[:, features].copy()
    for col in features:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    # Match the existing training workflow: fill numeric nulls using fitted imputer statistics.
    stats = getattr(imputer, "statistics_", None)
    if stats is None or len(stats) != len(features):
        raise ValueError("The saved imputer statistics do not match the saved feature list. Check the artifacts from training.")
    for i, col in enumerate(features):
        X[col] = X[col].fillna(stats[i])
    if X.isna().any().any():
        raise ValueError("Some features still contain missing values after imputation. Verify the saved imputer.")
    return X


def label_for(value):
    # Keep the project's documented binary convention, while allowing other classes to remain visible.
    try:
        number = int(value)
        if number == 0:
            return "Benign"
        if number == 1:
            return "Attack"
    except (TypeError, ValueError):
        pass
    return str(value)


def render_footer():
    st.markdown("<div class='footer'>SentinelAI · Cyber Threat Detection · Predictions are decision-support signals, not a guarantee of network safety.</div>", unsafe_allow_html=True)
