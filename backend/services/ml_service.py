import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

ML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_FILE = os.path.join(ML_DIR, "ml_models", "credit_risk_model.pkl")

class MLService:
    _model_data = None

    @classmethod
    def load_model(cls):
        if cls._model_data is None:
            if not os.path.exists(MODEL_FILE):
                from backend.ml_models.train_model import train_and_save_models
                cls._model_data = train_and_save_models()
            else:
                with open(MODEL_FILE, "rb") as f:
                    cls._model_data = pickle.load(f)
        return cls._model_data

    @classmethod
    def predict_credit_risk(cls, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs ML prediction & computes Explainable AI (SHAP-style) attribution scores.
        """
        model_payload = cls.load_model()
        model = model_payload["model"]
        feature_names = model_payload["feature_names"]
        baselines = model_payload["baseline_means"]
        stds = model_payload["baseline_stds"]
        
        row = {
            "monthly_income": float(features_dict.get("monthly_income", 50000)),
            "loan_amount": float(features_dict.get("loan_amount", 500000)),
            "loan_tenure_months": int(features_dict.get("loan_tenure_months", 36)),
            "cibil_score": int(features_dict.get("cibil_score", 750)),
            "active_loans_count": int(features_dict.get("active_loans_count", 1)),
            "total_overdue_amount": float(features_dict.get("total_overdue_amount", 0)),
            "credit_utilization_ratio": float(features_dict.get("credit_utilization_ratio", 0.25)),
            "dti_ratio": float(features_dict.get("dti_ratio", 0.30)),
        }
        
        df_input = pd.DataFrame([row])[feature_names]
        
        # Predict probability of high risk
        proba = float(model.predict_proba(df_input)[0, 1])
        
        if proba < 0.35:
            risk_category = "LOW"
            action = "Recommend Instant Approval"
        elif proba <= 0.65:
            risk_category = "MEDIUM"
            action = "Recommend Additional Collateral or Underwriter Review"
        else:
            risk_category = "HIGH"
            action = "Recommend Rejection due to Credit Risk"

        # Calculate SHAP-style Explainable Feature Contributions
        importances = model_payload.get("feature_importances", {})
        shap_contributions: List[Dict[str, Any]] = []
        
        for feat in feature_names:
            val = row[feat]
            mean_val = baselines.get(feat, val)
            std_val = stds.get(feat, 1.0) if stds.get(feat, 1.0) != 0 else 1.0
            
            z_score = (val - mean_val) / std_val
            weight = importances.get(feat, 0.12)
            
            if feat in ["cibil_score", "monthly_income"]:
                impact = -1.0 * z_score * weight * 100.0
            else:
                impact = 1.0 * z_score * weight * 100.0
                
            impact_clipped = round(float(np.clip(impact, -45.0, 45.0)), 2)
            
            if feat == "cibil_score":
                interp = f"CIBIL Score ({val:.0f}) reduces default risk significantly." if impact_clipped < 0 else f"Low CIBIL Score ({val:.0f}) elevates default risk."
            elif feat == "dti_ratio":
                interp = f"DTI Ratio ({val*100:.1f}%) is safe and manageable." if impact_clipped < 0 else f"High Debt-to-Income ratio ({val*100:.1f}%) strains repayment capacity."
            elif feat == "total_overdue_amount":
                interp = "Zero past overdue delinquencies." if val == 0 else f"Outstanding overdue of INR {val:,.0f} signals payment stress."
            elif feat == "credit_utilization_ratio":
                interp = f"Prudent credit line utilization ({val*100:.1f}%)." if impact_clipped < 0 else f"High credit line utilization ({val*100:.1f}%)."
            elif feat == "monthly_income":
                interp = f"Strong monthly earnings (INR {val:,.0f}) support loan servicing." if impact_clipped < 0 else f"Moderate income (INR {val:,.0f}) relative to loan size."
            else:
                interp = f"{feat.replace('_', ' ').title()}: {val}"
                
            shap_contributions.append({
                "feature_name": feat,
                "feature_value": val,
                "contribution_score": impact_clipped,
                "interpretation": interp
            })

        shap_contributions.sort(key=lambda x: abs(x["contribution_score"]), reverse=True)

        return {
            "risk_category": risk_category,
            "risk_probability": round(proba, 4),
            "model_name": "Gradient Boosting Classifier (Trained & Calibrated)",
            "dti_ratio": row["dti_ratio"],
            "shap_contributions": shap_contributions,
            "recommended_action": action,
            "model_metrics": model_payload.get("comparison_results", {})
        }
