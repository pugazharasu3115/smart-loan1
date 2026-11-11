import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

ML_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(ML_DIR, "credit_risk_model.pkl")
METRICS_FILE = os.path.join(ML_DIR, "model_comparison.json")

def generate_synthetic_credit_data(n_samples: int = 3000, random_state: int = 42) -> pd.DataFrame:
    """Generates synthetic banking credit risk dataset for academic training."""
    np.random.seed(random_state)
    
    incomes = np.random.lognormal(mean=10.8, sigma=0.6, size=n_samples) # ₹25k - ₹200k
    incomes = np.clip(incomes, 15000, 400000)
    
    loan_amounts = np.random.uniform(50000, 2500000, size=n_samples)
    tenures = np.random.choice([12, 24, 36, 48, 60, 84, 120], size=n_samples)
    cibil_scores = np.random.normal(loc=720, scale=80, size=n_samples)
    cibil_scores = np.clip(cibil_scores, 300, 900)
    
    active_loans = np.random.poisson(lam=1.8, size=n_samples)
    active_loans = np.clip(active_loans, 0, 10)
    
    overdue_amounts = np.where(
        np.random.rand(n_samples) > 0.75,
        np.random.exponential(scale=35000, size=n_samples),
        0.0
    )
    overdue_amounts = np.clip(overdue_amounts, 0, 300000)
    
    credit_utilization = np.random.beta(a=2, b=5, size=n_samples) # average 0.28
    
    # Calculate Monthly EMI estimate (approx 10.5% rate)
    monthly_rate = 0.105 / 12
    emis = loan_amounts * (monthly_rate * (1 + monthly_rate)**tenures) / ((1 + monthly_rate)**tenures - 1)
    
    existing_emis = active_loans * np.random.uniform(2000, 15000, size=n_samples)
    dti_ratios = (existing_emis + emis) / incomes
    dti_ratios = np.clip(dti_ratios, 0.05, 1.8)
    
    # Latent risk score calculation
    risk_score = (
        - 0.008 * (cibil_scores - 650)
        + 2.2 * (dti_ratios - 0.40)
        + 0.00003 * overdue_amounts
        + 1.8 * (credit_utilization - 0.35)
        + 0.25 * (active_loans - 2)
        - 0.000008 * (incomes - 50000)
        + np.random.normal(0, 0.45, size=n_samples)
    )
    
    # Sigmoid to convert to probability
    prob_default = 1 / (1 + np.exp(-risk_score))
    default_labels = (prob_default > 0.50).astype(int)
    
    df = pd.DataFrame({
        "monthly_income": incomes,
        "loan_amount": loan_amounts,
        "loan_tenure_months": tenures,
        "cibil_score": cibil_scores,
        "active_loans_count": active_loans,
        "total_overdue_amount": overdue_amounts,
        "credit_utilization_ratio": credit_utilization,
        "dti_ratio": dti_ratios,
        "default_risk": default_labels
    })
    return df

def train_and_save_models():
    """Trains Logistic Regression, Random Forest, and Gradient Boosting models."""
    df = generate_synthetic_credit_data(n_samples=3500)
    
    feature_cols = [
        "monthly_income", "loan_amount", "loan_tenure_months",
        "cibil_score", "active_loans_count", "total_overdue_amount",
        "credit_utilization_ratio", "dti_ratio"
    ]
    
    X = df[feature_cols]
    y = df["default_risk"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, max_depth=5, random_state=42)
    }
    
    comparison_results = {}
    best_model_name = "Gradient Boosting"
    best_model = None
    
    for name, model in models.items():
        if name == "Logistic Regression":
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            y_prob = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1]
            
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
        
        comparison_results[name] = {
            "Accuracy": round(float(acc * 100), 2),
            "Precision": round(float(prec * 100), 2),
            "Recall": round(float(rec * 100), 2),
            "F1_Score": round(float(f1 * 100), 2),
            "ROC_AUC": round(float(auc), 4)
        }
        
        if name == best_model_name:
            best_model = model

    # Feature Importance
    feature_importances = dict(zip(feature_cols, [round(float(v), 4) for v in best_model.feature_importances_]))
    
    # Save package
    model_payload = {
        "model": best_model,
        "scaler": scaler,
        "feature_names": feature_cols,
        "feature_importances": feature_importances,
        "baseline_means": df[feature_cols].mean().to_dict(),
        "baseline_stds": df[feature_cols].std().to_dict(),
        "comparison_results": comparison_results
    }
    
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model_payload, f)
        
    import json
    with open(METRICS_FILE, "w") as f:
        json.dump({
            "models_comparison": comparison_results,
            "feature_importance": feature_importances,
            "best_model": best_model_name
        }, f, indent=2)
        
    print("Credit Risk ML Models trained and saved successfully!")
    return model_payload

if __name__ == "__main__":
    train_and_save_models()
