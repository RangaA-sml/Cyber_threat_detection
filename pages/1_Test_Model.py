import os
import joblib
import pandas as pd
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

st.set_page_config(page_title="Test the Model", page_icon="🛡️", layout="wide")

render_navigation("testing")
st.markdown("""
<style>
.block-container {max-width:1240px;padding-top:1.5rem;padding-bottom:3rem;}
.page-hero {padding:2rem 2.2rem;border-radius:18px;background:linear-gradient(120deg,light-dark(#f6f9ff,#0c1427),light-dark(#eaf1ff,#142344));border:1px solid light-dark(#e2e9f5,#293650);margin-bottom:1.5rem;}
.page-hero h1 {margin:.6rem 0;font-size:clamp(2rem,4vw,3rem);letter-spacing:-.04em;}
.page-hero p {color:light-dark(#65718a,#aab7ce);line-height:1.7;margin-bottom:0;max-width:800px;}
.section-label {font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;color:#3974e8;}
div[data-testid="stMetric"] {padding:1rem;border:1px solid rgba(128,145,170,.24);border-radius:14px;background:light-dark(#fff,#111a2d);}
.panel {padding:1.2rem;border:1px solid light-dark(#e3e9f3,#293650);border-radius:16px;background:light-dark(#fff,#111a2d);}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-hero">
 <div class="section-label">MODEL WORKSPACE</div>
 <h1>Test your network traffic</h1>
 <p>Upload a CSV dataset, validate its features, and review predictions from your saved XGBoost model.</p>
</div>
""", unsafe_allow_html=True)

MODEL_PATH = "models/final_xgboost_model.pkl"
IMPUTER_PATH = "models/xgb_imputer.pkl"
FEATURES_PATH = "models/xgb_features.pkl"

@st.cache_resource
def load_artifacts():
    return joblib.load(MODEL_PATH), joblib.load(IMPUTER_PATH), list(joblib.load(FEATURES_PATH))

missing_paths = [p for p in (MODEL_PATH, IMPUTER_PATH, FEATURES_PATH) if not os.path.exists(p)]
if missing_paths:
    st.error("Model files not found. Run Streamlit from your project root and confirm these paths:")
    for p in missing_paths:
        st.code(p)
    st.stop()

try:
    model, imputer, features = load_artifacts()
except Exception as exc:
    st.error(f"Unable to load model artifacts: {exc}")
    st.stop()

st.success("Model loaded successfully.")
with st.expander("View model input requirements"):
    st.write(f"Expected feature count: **{len(features)}**")
    st.write("The CSV must contain every required feature. Extra columns are ignored for prediction.")
    st.code(", ".join(features))

a, b = st.columns(2)
for col, label, path, filename in [
    (a, "🟢 Download Benign Sample", "benign_sample.csv", "benign_sample.csv"),
    (b, "🔴 Download Attack Sample", "attack_sample.csv", "attack_sample.csv"),
]:
    with col:
        if os.path.exists(path):
            with open(path, "rb") as f:
                payload = f.read()
            st.download_button(label, payload, filename, "text/csv", use_container_width=True)
        else:
            st.warning(f"Sample file not found: `{path}`. Add your real sample file to enable this download.")

st.divider()
st.markdown('<div class="section-label">INPUT DATA</div>', unsafe_allow_html=True)
st.header("Upload network traffic CSV")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], help="Use the feature definitions and preprocessing expected by your trained model.")

if uploaded_file is not None:
    try:
        data = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read the CSV: {exc}")
        st.stop()

    if data.empty:
        st.warning("The CSV contains no data rows.")
        st.stop()

    m1, m2, m3 = st.columns(3)
    m1.metric("Records", f"{len(data):,}")
    m2.metric("CSV columns", f"{len(data.columns):,}")
    m3.metric("Required features", f"{len(features):,}")

    with st.expander("Preview uploaded data", expanded=True):
        st.dataframe(data.head(10), use_container_width=True)

    missing_features = [col for col in features if col not in data.columns]
    if missing_features:
        st.error(f"{len(missing_features)} required feature(s) are missing.")
        st.dataframe(pd.DataFrame({"Missing feature": missing_features}), use_container_width=True)
        st.stop()

    st.info("All required feature columns are present. Confirm that feature types and encodings match training before running predictions.")
    if st.button("🚀 Run threat detection", type="primary", use_container_width=True):
        try:
            X = data.loc[:, features].copy()
            for i, col in enumerate(features):
                X[col] = pd.to_numeric(X[col], errors="coerce")
                X[col] = X[col].fillna(imputer.statistics_[i])

            X_processed = X.to_numpy()
            predictions = model.predict(X_processed)
            results = pd.DataFrame({"Prediction code": predictions})

            label_map = {0: "Benign", 1: "Attack"}
            results["Prediction"] = pd.Series(predictions).map(label_map).fillna(pd.Series(predictions).astype(str))

            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(X_processed)
                classes = list(getattr(model, "classes_", []))
                for class_code, probs in zip(classes, probabilities.T):
                    label = label_map.get(class_code, f"Class {class_code}")
                    results[f"{label} Probability (%)"] = (probs * 100).round(2)

            total = len(predictions)
            benign = int((predictions == 0).sum())
            attacks = int((predictions == 1).sum())
            other = total - benign - attacks
            st.session_state["sentinel_results"] = results
            st.session_state["sentinel_summary"] = (total, benign, attacks, other)
        except Exception as exc:
            st.error(f"Prediction failed. Check input types and training-time preprocessing. Details: {exc}")

if "sentinel_results" in st.session_state:
    results = st.session_state["sentinel_results"]
    total, benign, attacks, other = st.session_state["sentinel_summary"]
    st.divider()
    st.markdown('<div class="section-label">DETECTION OUTPUT</div>', unsafe_allow_html=True)
    st.header("Detection summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total records", f"{total:,}")
    c2.metric("Benign", f"{benign:,}")
    c3.metric("Potential attacks", f"{attacks:,}")
    c4.metric("Attack percentage", f"{(attacks / total * 100) if total else 0:.2f}%")

    if attacks:
        st.error(f"Potential attack predictions found in {attacks:,} record(s). Review the results carefully.")
    else:
        st.success("No records were classified as Attack by this model.")
    if other:
        st.warning(f"{other:,} records have class labels other than 0 or 1. Check your label mapping.")

    st.subheader("Detailed prediction results")
    st.dataframe(results, use_container_width=True)
    st.download_button(
        "⬇️ Download prediction results",
        results.to_csv(index=False).encode("utf-8"),
        "cyber_threat_predictions.csv",
        "text/csv",
        type="primary",
    )

st.markdown("---")
st.markdown('<div class="section-label">CONTINUE EXPLORING</div>', unsafe_allow_html=True)
st.subheader("Continue to another section")
bottom1, bottom2, bottom3 = st.columns(3)
with bottom1:
    st.page_link("app.py", label="⌂  Overview  →", use_container_width=True)
with bottom2:
    st.page_link("pages/1_Test_Model.py", label="🧪  Test the Model", use_container_width=True)
with bottom3:
    st.page_link("pages/2_About_Model.py", label="ⓘ  About the Model  →", use_container_width=True)
st.caption("Predictions are model outputs, not a guarantee that traffic is safe or malicious. Validate results using your security workflow.")
