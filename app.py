import streamlit as st
import joblib
import pandas as pd


st.set_page_config(
    page_title="Cyber Threat Detection",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Cyber Threat Detection")

st.write(
    "Upload network traffic data to detect potential cyber threats "
    "using a trained XGBoost machine learning model."
)

model = joblib.load("models/final_xgboost_model.pkl")
imputer = joblib.load("models/xgb_imputer.pkl")
features = joblib.load("models/xgb_features.pkl")

st.success("✅ XGBoost model loaded successfully!")

# Test the model with sample network traffic
st.subheader("🧪 Try the Detection System")

st.write(
    "Upload a network traffic CSV file to detect whether the traffic is benign or potentially malicious."
)

st.write(
    "For demonstration, download a benign or attack sample and upload it below."
)

col1, col2 = st.columns(2)

with col1:

    with open("benign_sample.csv", "rb") as file:
        benign_csv = file.read()

    st.download_button(
        label="🟢 Download Benign Sample",
        data=benign_csv,
        file_name="benign_sample.csv",
        mime="text/csv"
    )

with col2:

    with open("attack_sample.csv", "rb") as file:
        attack_csv = file.read()

    st.download_button(
        label="🔴 Download Attack Sample",
        data=attack_csv,
        file_name="attack_sample.csv",
        mime="text/csv"
    )

# uploaded_file section

st.subheader("📂 Network Traffic Data")

uploaded_file = st.file_uploader(
    "Upload a CSV file containing network traffic data",
    type=["csv"]
)

if uploaded_file is not None:

    data = pd.read_csv(uploaded_file)

    st.success("CSV uploaded successfully!")

    st.write("Dataset shape:", data.shape)

    # Check required features
    missing_features = [col for col in features if col not in data.columns]

    if missing_features:

        st.error(
            f"❌ Missing {len(missing_features)} required features."
        )

        st.write("Missing features:")
        st.write(missing_features)

    else:
        st.success("✅ All required features are present.")

        # Select features in exactly the same order used during training
        X_input = data[features]

        st.write("Model input shape:", X_input.shape)

        st.dataframe(data.head())

        # Apply the saved imputer statistics manually
        X_processed = X_input.copy()

        for i, column in enumerate(features):
            X_processed[column] = X_processed[column].fillna(
                imputer.statistics_[i]
            )

        # Convert to NumPy array after filling all columns
        X_processed = X_processed.values

        # Make predictions
        predictions = model.predict(X_processed)

        # Get probability of Attack
        probabilities = model.predict_proba(X_processed)

        attack_probability = probabilities[:, 1]
        benign_probability = probabilities[:, 0]

        # Convert predictions to labels
        prediction_labels = pd.Series(predictions).map({
            0: "Benign",
            1: "Attack"
        })

        results = pd.DataFrame({
            "Prediction": prediction_labels,
            "Benign Probability": benign_probability,
            "Attack Probability": attack_probability
        })

        # Format probabilities as percentages
        results["Benign Probability"] = (
            results["Benign Probability"] * 100
        ).round(2)

        results["Attack Probability"] = (
            results["Attack Probability"] * 100
        ).round(2)

        # Summary
        total_records = len(results)
        benign_count = (predictions == 0).sum()
        attack_count = (predictions == 1).sum()

        attack_percentage = (
            attack_count / total_records
        ) * 100

        st.subheader("📊 Detection Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Records", total_records)

        with col2:
            st.metric("Benign", benign_count)

        with col3:
            st.metric("Potential Attacks", attack_count)

        with col4:
            st.metric(
                "Attack Percentage",
                f"{attack_percentage:.2f}%"
            )

        # Overall result
        st.subheader("🛡️ Overall Detection Result")

        if attack_count > 0:
            st.error(
                f"🚨 Potential Attack Detected "
                f"in {attack_count} record(s)"
            )
        else:
            st.success(
                "✅ No potential attacks detected"
            )

        # Detailed results
        st.subheader("🔍 Prediction Results")

        st.dataframe(
            results,
            use_container_width=True
        )

        # Download prediction results
        results_csv = results.to_csv(index=False)

        st.download_button(
            label="⬇️ Download Prediction Results",
            data=results_csv,
            file_name="cyber_threat_predictions.csv",
            mime="text/csv"
        )


# Cyber Threat Detection Workflow

st.subheader("🔄 Cyber Threat Detection Workflow")

st.image(
    "cyber_threat_workflow.png",
    caption="End-to-End Cyber Threat Detection Workflow",
    use_container_width=True
)