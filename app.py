import streamlit as st

st.set_page_config(page_title="Cyber Threat Detection", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1240px; padding-top: 1.5rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(128,145,170,.22);}
.hero {padding: clamp(2rem,5vw,4rem); border-radius: 22px; background: linear-gradient(120deg,#0b1530 0%,#122a5a 60%,#1d4ed8 100%); color: white; margin: .4rem 0 2rem;}
.hero .eyebrow {color:#b9ceff; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:800;}
.hero h1 {font-size: clamp(2.5rem,5vw,4.2rem); line-height:1.05; letter-spacing:-.045em; margin:.9rem 0 1rem; color:white;}
.hero h1 span {color:#8fb2ff;}
.hero p {max-width:760px; color:#d4def4; font-size:1.05rem; line-height:1.8;}
.hero-note {display:inline-block; padding:.55rem .85rem; border:1px solid #7896d866; border-radius:999px; color:#dce7ff; font-size:.75rem; margin-bottom:.5rem;}
.section-label {font-size:.72rem; letter-spacing:.15em; text-transform:uppercase; font-weight:800; color:#3974e8;}
div[data-testid="stMetric"] {padding:1rem 1.1rem; border:1px solid rgba(128,145,170,.24); border-radius:15px; background:light-dark(#ffffff,#111a2d);}
div[data-testid="stMetricLabel"] {font-size:.82rem;}
.feature-card {height:100%; padding:1.35rem; border-radius:17px; border:1px solid light-dark(#e3e9f3,#293650); background:light-dark(#fff,#111a2d);}
.feature-card .icon {font-size:1.65rem; margin-bottom:.7rem;}
.feature-card h3 {font-size:1.05rem; margin:0 0 .5rem;}
.feature-card p {font-size:.9rem; line-height:1.7; color:light-dark(#65718a,#aab7ce); margin:0;}
.step-card {padding:1.1rem; border:1px solid light-dark(#e3e9f3,#293650); border-radius:15px; background:light-dark(#fff,#111a2d);}
.step-num {display:inline-flex; width:34px; height:34px; border-radius:10px; background:#2563eb; color:white; align-items:center; justify-content:center; font-weight:800; margin-bottom:.7rem;}
.cta {padding:1.7rem; border-radius:18px; background:light-dark(#101d3b,#101d3b); color:white;}
.cta h3 {color:white; margin:.3rem 0;}
.cta p {color:#c1cde4;}
hr {border-color:rgba(128,145,170,.2);}
</style>
""", unsafe_allow_html=True)

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

render_navigation("overview")

st.markdown("""
<div class="hero">
  <div class="hero-note">✦ MACHINE LEARNING · NETWORK SECURITY</div>
  <div class="eyebrow">SENTINELAI · NETWORK INTELLIGENCE</div>
  <h1>Cyber Threat Detection.<br>Detect threats.<br><span>Protect what matters.</span></h1>
  <p>A machine-learning powered network traffic analyzer designed to classify network records as benign or potentially malicious using a trained XGBoost model.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-label">THE PROJECT</div>', unsafe_allow_html=True)
st.header("Security insights, made clearer.")
st.write("An end-to-end demonstration of a supervised learning workflow for network threat detection.")

c1, c2, c3 = st.columns(3)
cards = [
    ("⌁", "Network traffic analysis", "Review structured network records from a CSV dataset and prepare them for automated analysis."),
    ("◈", "XGBoost classifier", "Use a trained gradient-boosted model to classify traffic patterns from learned feature relationships."),
    ("⛨", "Detection insights", "Explore predicted labels, class probabilities, and a summary of potentially suspicious records."),
]
for col, (icon, title, body) in zip((c1,c2,c3), cards):
    with col:
        st.markdown(f'<div class="feature-card"><div class="icon">{icon}</div><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)

st.write("")
st.markdown('<div class="section-label">WORKFLOW</div>', unsafe_allow_html=True)
st.header("From traffic data to detection")
st.write("A simple, transparent process from input to model output.")
w1, w2, w3 = st.columns(3)
steps = [
    ("01", "Upload data", "Provide a CSV containing the network features expected by the trained model."),
    ("02", "Run inference", "Validate features, apply the saved preprocessing, and generate model predictions."),
    ("03", "Review results", "Inspect benign and potential attack counts and export detailed predictions."),
]
for col, (num, title, body) in zip((w1,w2,w3), steps):
    with col:
        st.markdown(f'<div class="step-card"><div class="step-num">{num}</div><h3>{title}</h3><p style="color:light-dark(#65718a,#aab7ce);line-height:1.65;font-size:.9rem">{body}</p></div>', unsafe_allow_html=True)

st.write("")
st.markdown('<div class="section-label">TECHNOLOGY STACK</div>', unsafe_allow_html=True)
st.write("Python　·　Streamlit　·　XGBoost　·　Pandas　·　Scikit-learn　·　Joblib")

st.markdown("""
<div class="cta">
  <div style="color:#9bb9ff;font-size:.72rem;letter-spacing:.15em;font-weight:800;">READY TO EXPLORE?</div>
  <h3>Test the detection workflow.</h3>
  <p>Use the navigation links at the top to open <b>Test the Model</b>, upload network traffic data, and review predictions.</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")
st.markdown('<div class="section-label">CONTINUE EXPLORING</div>', unsafe_allow_html=True)
st.subheader("Where would you like to go next?")
bottom1, bottom2, bottom3 = st.columns(3)
with bottom1:
    st.page_link("app.py", label="⌂  Overview", use_container_width=True)
with bottom2:
    st.page_link("pages/1_Test_Model.py", label="🧪  Test the Model  →", use_container_width=True)
with bottom3:
    st.page_link("pages/2_About_Model.py", label="ⓘ  About the Model  →", use_container_width=True)
st.caption("SentinelAI is a project demonstration. Model predictions should be reviewed as indicators, not as a guarantee of network safety.")
