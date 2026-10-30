from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from sentinel_utils import (
    load_artifacts,
    label_for,
    prepare_features,
    render_footer,
    render_navigation,
)
from security_store import store_attack_predictions


st.set_page_config(
    page_title="Test the Model | SentinelAI",
    page_icon="🛡️",
    layout="wide",
)

render_navigation("testing")

st.markdown(
    """
    <div class="page-hero">
      <div class="section-label">MODEL WORKSPACE</div>
      <h1>Test your network traffic</h1>
      <p>Upload a network traffic CSV and run the saved XGBoost model.
      Malicious predictions are automatically forwarded to the Security
      Operations Center for analyst review.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Load the existing trained model and preprocessing artifacts.
model, imputer, features, missing_paths, load_error = load_artifacts()

if missing_paths:
    st.error("Model files were not found. Confirm that these files exist inside the models/ folder:")
    for path in missing_paths:
        try:
            st.code(str(path.relative_to(Path(__file__).resolve().parents[1])))
        except ValueError:
            st.code(str(path))
    st.stop()

if load_error:
    st.error(f"Unable to load model artifacts: {load_error}")
    st.stop()

st.success(f"Model loaded successfully · {len(features)} expected input features")

with st.expander("View model input requirements"):
    st.write(f"Expected feature count: **{len(features)}**")
    st.write("The CSV must contain every required model feature. Extra columns, including Demo Severity metadata, are ignored by model inference.")
    st.code(", ".join(features))

# One combined demonstration dataset download.
root = Path(__file__).resolve().parents[1]
dataset_filename = "network_traffic_mixed_demo.csv"
dataset_path = root / dataset_filename

if dataset_path.is_file():
    st.download_button(
        label="📥 Download Mixed Network Traffic Dataset",
        data=dataset_path.read_bytes(),
        file_name=dataset_filename,
        mime="text/csv",
        use_container_width=True,
        type="primary",
    )
else:
    st.warning(f"Combined demonstration dataset not found: {dataset_filename}")

st.divider()
st.markdown('<div class="section-label">INPUT DATA</div>', unsafe_allow_html=True)
st.header("Upload network traffic CSV")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Upload a CSV containing all required features expected by the trained model.",
)

if uploaded_file is not None:
    content = uploaded_file.getvalue()
    signature = hashlib.sha256(
        uploaded_file.name.encode("utf-8") + content
    ).hexdigest()

    # Clear the previous on-screen run result when a different file is selected.
    if st.session_state.get("_sentinel_upload_signature") != signature:
        st.session_state.pop("sentinel_run_message", None)
        st.session_state.pop("sentinel_run_counts", None)
        st.session_state["_sentinel_upload_signature"] = signature

    try:
        data = pd.read_csv(BytesIO(content))
    except Exception as exc:
        st.error(f"Could not read the CSV: {exc}")
        st.stop()

    if data.empty:
        st.warning("The CSV contains no data rows.")
        st.stop()

    missing_features = [column for column in features if column not in data.columns]
    if missing_features:
        st.error(f"{len(missing_features)} required feature(s) are missing.")
        st.write(", ".join(missing_features))
        st.stop()

    st.info(
        f"CSV loaded: **{len(data):,} records** · "
        f"All {len(features)} required model features are present."
    )

    if st.button(
        "🚀 Run threat detection",
        type="primary",
        use_container_width=True,
    ):
        try:
            X = prepare_features(data, features, imputer)
            predictions = model.predict(X.to_numpy())

            results = pd.DataFrame(
                {
                    "Record #": range(1, len(predictions) + 1),
                    "Prediction code": predictions,
                    "Prediction": [label_for(value) for value in predictions],
                }
            )

            # Keep model confidence available to the incident backend.
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(X.to_numpy())
                classes = list(getattr(model, "classes_", []))

                for class_index, class_code in enumerate(classes):
                    class_label = label_for(class_code)
                    results[f"{class_label} Probability (%)"] = (
                        probabilities[:, class_index] * 100
                    ).round(2)

                if classes:
                    class_to_column = {
                        str(code): index for index, code in enumerate(classes)
                    }
                    confidence_values = []
                    for row_index, predicted in enumerate(predictions):
                        class_index = class_to_column.get(str(predicted))
                        confidence_values.append(
                            round(
                                float(probabilities[row_index, class_index] * 100),
                                2,
                            )
                            if class_index is not None
                            else None
                        )
                    results["Prediction Confidence (%)"] = confidence_values

            total = len(predictions)
            benign = sum(label_for(value) == "Benign" for value in predictions)
            attacks = sum(label_for(value) == "Attack" for value in predictions)
            other = total - benign - attacks

            # Create/replace the SOC incident queue using the existing backend.
            incident_ids = store_attack_predictions(
                data,
                results,
                uploaded_file.name,
            )

            st.session_state["sentinel_run_counts"] = {
                "total": total,
                "benign": benign,
                "attacks": attacks,
                "other": other,
                "alerts": len(incident_ids),
            }
            st.session_state["sentinel_run_message"] = (
                f"Analysis completed for {total:,} records."
            )

        except Exception as exc:
            st.error(
                "Prediction failed. Check input types and training-time "
                f"preprocessing. Details: {exc}"
            )

# Compact completion message only: no CSV preview, metric cards,
# detection-summary dashboard, or detailed prediction table.
if "sentinel_run_counts" in st.session_state:
    counts = st.session_state["sentinel_run_counts"]

    st.divider()
    st.markdown('<div class="section-label">ANALYSIS STATUS</div>', unsafe_allow_html=True)
    st.success(st.session_state.get("sentinel_run_message", "Analysis completed."))

    if counts["attacks"] > 0:
        st.warning(
            f"{counts['attacks']:,} records were classified as potential attacks. "
            f"{counts['alerts']:,} incident(s) were forwarded to the Security Operations Center."
        )
    else:
        st.success("No records were classified as attacks. No SOC incidents were generated.")

    if counts["other"] > 0:
        st.warning(
            f"{counts['other']:,} records have class labels other than Benign or Attack. "
            "Verify the model's class-label mapping."
        )

    st.page_link(
        "pages/3_Security_Team.py",
        label="🛡️ Open Security Operations Center",
        use_container_width=True,
    )

st.markdown("---")
st.markdown('<div class="section-label">NEXT STEP</div>', unsafe_allow_html=True)
st.write(
    "Security analysts can review generated incidents, assign ownership, "
    "record investigation notes and track incident resolution in the SOC."
)
st.page_link(
    "pages/3_Security_Team.py",
    label="Open Security Operations Center →",
    use_container_width=True,
)
render_footer()
