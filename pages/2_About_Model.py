import os
import joblib
import streamlit as st


def render_navigation(current_page):
    st.markdown("""<style>
    [data-testid="stSidebar"] {display:none;}
    .block-container {max-width:1240px;padding-top:1rem;padding-bottom:3rem;}
    div[data-testid="stPageLink"] a {
        min-height: 3.25rem; display:flex; align-items:center; justify-content:center;
        border:2px solid #2563eb !important; border-radius:13px; padding:.9rem 1rem;
        text-decoration:none !important; font-weight:850 !important; color:#ffffff !important;
        background:linear-gradient(135deg,#3478f6,#1d4ed8) !important;
        box-shadow:0 7px 18px rgba(37,99,235,.28); transition:all .18s ease;
    }
    div[data-testid="stPageLink"] a:hover {
        border-color:#1e40af !important; background:linear-gradient(135deg,#2563eb,#1e40af) !important;
        color:#ffffff !important; box-shadow:0 10px 24px rgba(37,99,235,.38); transform:translateY(-2px);
    }
    div[data-testid="stPageLink"] a:focus-visible {outline:3px solid #f59e0b !important;outline-offset:3px;}
    </style>""", unsafe_allow_html=True)
    n1, n2, n3 = st.columns([1, 1.25, 1.1])
    with n1:
        st.page_link("app.py", label="⌂  Overview", use_container_width=True)
    with n2:
        st.page_link("pages/1_Test_Model.py", label="🧪  Test the Model", use_container_width=True)
    with n3:
        st.page_link("pages/2_About_Model.py", label="ⓘ  About the Model", use_container_width=True)
    st.divider()

st.set_page_config(page_title="About the Model | SentinelAI", page_icon="🛡️", layout="wide")

render_navigation("about")
st.markdown("""
<style>
.block-container {max-width:1240px;padding-top:1.5rem;padding-bottom:3rem;}
.page-hero {padding:2rem 2.2rem;border-radius:18px;background:linear-gradient(120deg,light-dark(#f6f9ff,#0c1427),light-dark(#eaf1ff,#142344));border:1px solid light-dark(#e2e9f5,#293650);margin-bottom:1.5rem;}
.page-hero h1 {margin:.6rem 0;font-size:clamp(2rem,4vw,3rem);letter-spacing:-.04em;}
.page-hero p {color:light-dark(#65718a,#aab7ce);line-height:1.7;margin-bottom:0;}
.section-label {font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;color:#3974e8;}
.info-card {padding:1.2rem;border:1px solid light-dark(#e3e9f3,#293650);border-radius:16px;background:light-dark(#fff,#111a2d);height:100%;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-hero">
 <div class="section-label">PROJECT DOCUMENTATION</div>
 <h1>About the model</h1>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-label">MODEL COMPONENTS</div>', unsafe_allow_html=True)
st.header("Saved model artifacts")
items = [
    ("Trained XGBoost model", "models/final_xgboost_model.pkl", "Produces class predictions and, if supported, probabilities."),
    ("Fitted imputer", "models/xgb_imputer.pkl", "Stores training-set statistics used to fill missing numeric values."),
    ("Feature list", "models/xgb_features.pkl", "Defines the required input columns and their expected order."),
]
cols = st.columns(3)
for col, (title, path, description) in zip(cols, items):
    with col:
        exists = os.path.exists(path)
        st.markdown(f'<div class="info-card"><h3>{title}</h3><p style="color:light-dark(#65718a,#aab7ce);font-size:.9rem;line-height:1.6">{description}</p></div>', unsafe_allow_html=True)
        st.write("✅ Found" if exists else f"⚠️ Not found: `{path}`")

st.divider()
st.markdown('<div class="section-label">INFERENCE PIPELINE</div>', unsafe_allow_html=True)
st.header("How a prediction is generated")
for n, title, desc in [
    ("01", "Validate input", "Check that the uploaded CSV includes all required model features."),
    ("02", "Prepare features", "Select columns in the saved order and apply the same encodings and preprocessing used in training."),
    ("03", "Predict", "Pass the prepared data to the trained XGBoost classifier."),
    ("04", "Summarize", "Display predicted labels, supported probabilities, and record counts."),
]:
    with st.container(border=True):
        c1, c2 = st.columns([1, 8])
        c1.markdown(f"### {n}")
        c2.markdown(f"**{title}**  \n{desc}")

st.markdown('<div class="section-label">EVALUATION</div>', unsafe_allow_html=True)
st.header("Document verified model performance")
st.markdown("""
- Accuracy
- Precision, recall, and F1-score
- Confusion matrix
- Dataset source and class balance
- Known limitations and potential false positives/false negatives
""")

st.markdown("---")
st.markdown('<div class="section-label">CONTINUE EXPLORING</div>', unsafe_allow_html=True)
st.subheader("Continue to another section")
bottom1, bottom2, bottom3 = st.columns(3)
with bottom1:
    st.page_link("app.py", label="⌂  Overview  →", use_container_width=True)
with bottom2:
    st.page_link("pages/1_Test_Model.py", label="🧪  Test the Model  →", use_container_width=True)
with bottom3:
    st.page_link("pages/2_About_Model.py", label="ⓘ  About the Model", use_container_width=True)

