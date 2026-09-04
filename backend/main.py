from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import io

app = FastAPI(title="Cyber Threat Detection API")

# Allow the Streamlit frontend (or any origin) to call this API.
# In production, replace "*" with your frontend's actual URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model artifacts once at startup, not per-request
model = joblib.load("models/final_xgboost_model.pkl")
imputer = joblib.load("models/xgb_imputer.pkl")
features = joblib.load("models/xgb_features.pkl")


@app.get("/health")
def health():
    """Simple health check so Render (or you) can confirm the service is up."""
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Accepts a CSV of network traffic, returns predictions + probabilities.
    Same logic as the original Streamlit app, just exposed as an API.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    contents = await file.read()
    data = pd.read_csv(io.BytesIO(contents))

    missing_features = [col for col in features if col not in data.columns]
    if missing_features:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Missing required features",
                "missing_features": missing_features,
            },
        )

    X_input = data[features].copy()

    for i, column in enumerate(features):
        X_input[column] = X_input[column].fillna(imputer.statistics_[i])

    X_processed = X_input.values

    predictions = model.predict(X_processed)
    probabilities = model.predict_proba(X_processed)

    attack_probability = probabilities[:, 1]
    benign_probability = probabilities[:, 0]

    prediction_labels = pd.Series(predictions).map({0: "Benign", 1: "Attack"})

    results = pd.DataFrame({
        "Prediction": prediction_labels,
        "Benign Probability": (benign_probability * 100).round(2),
        "Attack Probability": (attack_probability * 100).round(2),
    })

    total_records = len(results)
    benign_count = int((predictions == 0).sum())
    attack_count = int((predictions == 1).sum())
    attack_percentage = round((attack_count / total_records) * 100, 2) if total_records else 0

    return {
        "summary": {
            "total_records": total_records,
            "benign_count": benign_count,
            "attack_count": attack_count,
            "attack_percentage": attack_percentage,
        },
        "results": results.to_dict(orient="records"),
    }
