import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    confusion_matrix,
    classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns
import os

def evaluate_model(y_true: np.ndarray, y_pred_prob: np.ndarray, threshold: float = 0.5) -> dict:
    """
    Evaluates a binary classification model and returns a dictionary of metrics.
    """
    y_pred = (y_pred_prob >= threshold).astype(int)
    
    metrics = {
        "roc_auc": float(roc_auc_score(y_true, y_pred_prob)),
        "pr_auc": float(average_precision_score(y_true, y_pred_prob)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "positive_label_prevalence": float(np.mean(y_true)),
        "threshold": threshold
    }
    
    return metrics

def generate_classification_report(y_true: np.ndarray, y_pred_prob: np.ndarray, threshold: float = 0.5) -> dict:
    """
    Returns the classification report as a dictionary.
    """
    y_pred = (y_pred_prob >= threshold).astype(int)
    return classification_report(y_true, y_pred, output_dict=True, zero_division=0)

def plot_confusion_matrix(y_true: np.ndarray, y_pred_prob: np.ndarray, threshold: float, save_path: str):
    """
    Plots and saves the confusion matrix to a file.
    """
    y_pred = (y_pred_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Non-Stressed (0)', 'Stressed (1)'],
                yticklabels=['Non-Stressed (0)', 'Stressed (1)'])
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title(f'Confusion Matrix (Threshold = {threshold})')
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def evaluate_baseline(y_true: np.ndarray) -> dict:
    """
    Evaluates a naive majority-class baseline.
    """
    # Majority class is usually 0
    majority_class = 0 if np.mean(y_true) < 0.5 else 1
    y_pred = np.full_like(y_true, fill_value=majority_class)
    y_pred_prob = np.full_like(y_true, fill_value=float(majority_class), dtype=float)
    
    return evaluate_model(y_true, y_pred_prob, threshold=0.5)
