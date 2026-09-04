import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(
    page_title="Cyber Threat Detection",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Cyber Threat Detection")

st.write(
    "Upload network traffic data to detect potential cyber threats "
    "using a trained XGBoost machine learning model, served via a FastAPI backend."
)

# Set this to your deployed backend's URL (Render will give you one like
# https://cyber-threat-api.onrender.com). Can also be set as an env var.
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Check backend health
try:
    health = requests.get(f"{API_URL}/health", timeout=5)
    if health.status_code == 200:
        st.success("✅ Detection API is reachable and model is loaded!")
    else:
        st.warning("⚠️ API responded but health check failed.")
except requests.exceptions.RequestException:
    st.error(f"❌ Could not reach the API at {API_URL}. Is the backend running?")

st.subheader("🧪 Try the Detection System")

st.write(
    "Upload a network traffic CSV file to detect whether the traffic is benign or potentially malicious."
)

st.write("For demonstration, download a benign or attack sample and upload it below.")

col1, col2 = st.columns(2)

with col1:
    if os.path.exists("benign_sample.csv"):
        with open("benign_sample.csv", "rb") as file:
            benign_csv = file.read()
        st.download_button(
            label="🟢 Download Benign Sample",
            data=benign_csv,
            file_name="benign_sample.csv",
            mime="text/csv"
        )

with col2:
    if os.path.exists("attack_sample.csv"):
        with open("attack_sample.csv", "rb") as file:
            attack_csv = file.read()
        st.download_button(
            label="🔴 Download Attack Sample",
            data=attack_csv,
            file_name="attack_sample.csv",
            mime="text/csv"
        )

st.subheader("📂 Network Traffic Data")

uploaded_file = st.file_uploader(
    "Upload a CSV file containing network traffic data",
    type=["csv"]
)

if uploaded_file is not None:

    st.success("CSV uploaded successfully!")

    # Send the file to the FastAPI backend for prediction
    with st.spinner("Sending data to detection API..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            response = requests.post(f"{API_URL}/predict", files=files, timeout=30)
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Request to API failed: {e}")
            response = None

    if response is not None:
        if response.status_code != 200:
            st.error("❌ API returned an error:")
            st.json(response.json())
        else:
            payload = response.json()
            summary = payload["summary"]
            results = pd.DataFrame(payload["results"])

            st.subheader("📊 Detection Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Records", summary["total_records"])
            with col2:
                st.metric("Benign", summary["benign_count"])
            with col3:
                st.metric("Potential Attacks", summary["attack_count"])
            with col4:
                st.metric("Attack Percentage", f"{summary['attack_percentage']}%")

            st.subheader("🛡️ Overall Detection Result")

            if summary["attack_count"] > 0:
                st.error(f"🚨 Potential Attack Detected in {summary['attack_count']} record(s)")
            else:
                st.success("✅ No potential attacks detected")

            st.subheader("🔍 Prediction Results")

            st.dataframe(results, use_container_width=True)

            results_csv = results.to_csv(index=False)

            st.download_button(
                label="⬇️ Download Prediction Results",
                data=results_csv,
                file_name="cyber_threat_predictions.csv",
                mime="text/csv"
            )

st.subheader("🔄 Cyber Threat Detection Workflow")

if os.path.exists("cyber_threat_workflow.png"):
    st.image(
        "cyber_threat_workflow.png",
        caption="End-to-End Cyber Threat Detection Workflow",
        use_container_width=True
    )
