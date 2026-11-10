"""
Model Architecture Factory for CKD Prediction.
Implements the Primary Champion Models (Random Forest, XGBoost) and
Benchmark Comparison Models (Logistic Regression L1, SVM RBF, AdaBoost, Decision Tree)
as defined by Jawad et al. (2024) and Moreno-Sánchez (2023).
"""

import logging
from typing import Dict, Any, Optional
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from xgboost import XGBClassifier

from src.config import MODEL_CONFIGS, RANDOM_STATE

logger = logging.getLogger(__name__)


def create_model(model_name: str, **custom_kwargs) -> Any:
    """
    Instantiates a classifier according to clinical specifications.
    
    Args:
        model_name: One of ['random_forest', 'xgboost', 'logistic_regression', 'svm', 'adaboost', 'decision_tree']
        custom_kwargs: Override any default hyperparameters.
        
    Returns:
        Configured scikit-learn or XGBoost estimator.
    """
    name_key = model_name.lower().replace("-", "_").replace(" ", "_")
    if name_key not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model '{model_name}'. Available: {list(MODEL_CONFIGS.keys())}")

    config = MODEL_CONFIGS[name_key]
    params = config["params"].copy()
    params.update(custom_kwargs)

    if name_key == "random_forest":
        return RandomForestClassifier(**params)
    elif name_key == "xgboost":
        return XGBClassifier(**params)
    elif name_key == "logistic_regression":
        return LogisticRegression(**params)
    elif name_key == "svm":
        return SVC(**params)
    elif name_key == "adaboost":
        return AdaBoostClassifier(**params)
    elif name_key == "decision_tree":
        return DecisionTreeClassifier(**params)
    else:
        raise ValueError(f"Unsupported model mapping: {name_key}")


def get_all_models() -> Dict[str, Any]:
    """
    Returns a dictionary of all 6 clinical benchmark and champion models.
    """
    return {
        model_name: create_model(model_name)
        for model_name in MODEL_CONFIGS.keys()
    }


def get_champion_models() -> Dict[str, Any]:
    """
    Returns the two primary champion models: Random Forest and XGBoost.
    """
    return {
        "random_forest": create_model("random_forest"),
        "xgboost": create_model("xgboost"),
    }


if __name__ == "__main__":
    models = get_all_models()
    print("Configured models for CKD benchmarking:")
    for name, model in models.items():
        is_champ = MODEL_CONFIGS[name]["is_champion"]
        champ_tag = "[CHAMPION]" if is_champ else "[BENCHMARK]"
        print(f"  {champ_tag:12} {name:20} -> {model.__class__.__name__}")

