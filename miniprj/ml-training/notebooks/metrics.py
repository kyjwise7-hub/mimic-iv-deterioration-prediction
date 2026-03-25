# ==============================================================================
# metrics.py - 모델 성능 평가 유틸리티
# ==============================================================================
#
# 사용법:
#   from metrics import evaluate_model, plot_roc_curves, plot_pr_curves, print_summary
#
# 주요 함수:
#   - evaluate_model(): 단일 모델 평가 (AUROC, AUPRC, F1, etc.)
#   - evaluate_all_models(): 4개 모델 일괄 평가
#   - plot_roc_curves(): ROC 곡선 시각화
#   - plot_pr_curves(): PR 곡선 시각화
#   - print_summary(): 결과 요약 테이블 출력
#   - save_results(): 결과 저장 (JSON, CSV)
# ==============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_auc_score, average_precision_score, 
    precision_recall_curve, roc_curve,
    f1_score, precision_score, recall_score,
    confusion_matrix, classification_report
)
import json
import os
from datetime import datetime


# ==============================================================================
# 단일 모델 평가
# ==============================================================================

def evaluate_model(y_true, y_prob, threshold=0.5):
    """
    단일 모델의 성능 평가
    
    Parameters:
    -----------
    y_true : array-like
        실제 레이블 (0 or 1)
    y_prob : array-like
        예측 확률 (0~1)
    threshold : float
        분류 임계값 (default: 0.5)
    
    Returns:
    --------
    dict : 성능 지표 딕셔너리
        - auroc: Area Under ROC Curve
        - auprc: Area Under PR Curve
        - f1: F1 Score
        - precision: Precision
        - recall: Recall (Sensitivity)
        - specificity: Specificity
        - threshold: 사용된 임계값
    """
    # 확률 → 이진 예측
    y_pred = (y_prob >= threshold).astype(int)
    
    # 기본 지표
    auroc = roc_auc_score(y_true, y_prob)
    auprc = average_precision_score(y_true, y_prob)
    
    # 분류 지표
    f1 = f1_score(y_true, y_pred, zero_division=0)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    
    # Confusion Matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    return {
        'auroc': round(auroc, 4),
        'auprc': round(auprc, 4),
        'f1': round(f1, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'specificity': round(specificity, 4),
        'threshold': threshold,
        'tp': int(tp),
        'fp': int(fp),
        'tn': int(tn),
        'fn': int(fn)
    }


def find_optimal_threshold(y_true, y_prob, metric='f1'):
    """
    최적 임계값 탐색
    
    Parameters:
    -----------
    y_true : array-like
        실제 레이블
    y_prob : array-like
        예측 확률
    metric : str
        최적화 기준 ('f1', 'youden', 'precision_recall_balance')
    
    Returns:
    --------
    float : 최적 임계값
    """
    thresholds = np.arange(0.01, 1.0, 0.01)
    
    if metric == 'f1':
        scores = []
        for t in thresholds:
            y_pred = (y_prob >= t).astype(int)
            scores.append(f1_score(y_true, y_pred, zero_division=0))
        best_idx = np.argmax(scores)
        
    elif metric == 'youden':
        # Youden's J = Sensitivity + Specificity - 1
        fpr, tpr, thresh = roc_curve(y_true, y_prob)
        j_scores = tpr - fpr
        best_idx = np.argmax(j_scores)
        return thresh[best_idx]
        
    elif metric == 'precision_recall_balance':
        precision, recall, thresh = precision_recall_curve(y_true, y_prob)
        # F1 = 2 * (precision * recall) / (precision + recall)
        f1_scores = 2 * (precision[:-1] * recall[:-1]) / (precision[:-1] + recall[:-1] + 1e-8)
        best_idx = np.argmax(f1_scores)
        return thresh[best_idx]
    
    return thresholds[best_idx]


# ==============================================================================
# 다중 모델 평가 (4개 타겟)
# ==============================================================================

def evaluate_all_models(models, X, y_dict, threshold=0.5):
    """
    4개 모델 일괄 평가
    
    Parameters:
    -----------
    models : dict
        {'death': model, 'vent': model, 'pressor': model, 'composite': model}
    X : DataFrame
        피처 데이터
    y_dict : dict
        {'death': y, 'vent': y, 'pressor': y, 'composite': y}
    threshold : float
        분류 임계값
    
    Returns:
    --------
    dict : 모델별 성능 지표
    """
    results = {}
    
    for name, model in models.items():
        if model is None:
            continue
        y_true = y_dict[name]
        y_prob = model.predict_proba(X)[:, 1]
        results[name] = evaluate_model(y_true, y_prob, threshold)
    
    return results


# ==============================================================================
# 시각화
# ==============================================================================

def plot_roc_curves(results_dict, y_true_dict, y_prob_dict, save_path=None):
    """
    ROC 곡선 시각화 (4개 모델)
    
    Parameters:
    -----------
    results_dict : dict
        evaluate_all_models() 결과
    y_true_dict : dict
        실제 레이블 딕셔너리
    y_prob_dict : dict
        예측 확률 딕셔너리
    save_path : str, optional
        저장 경로
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    colors = {'death': '#e74c3c', 'vent': '#3498db', 'pressor': '#2ecc71', 'composite': '#9b59b6'}
    titles = {
        'death': 'Mortality (24h)',
        'vent': 'Ventilator (12h)',
        'pressor': 'Vasopressor (12h)',
        'composite': 'Composite (24h)'
    }
    
    for idx, (name, y_true) in enumerate(y_true_dict.items()):
        ax = axes[idx]
        y_prob = y_prob_dict[name]
        
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auroc = results_dict[name]['auroc']
        
        ax.plot(fpr, tpr, color=colors.get(name, 'blue'), lw=2, 
                label=f'AUROC = {auroc:.3f}')
        ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
        ax.set_xlabel('False Positive Rate', fontsize=11)
        ax.set_ylabel('True Positive Rate', fontsize=11)
        ax.set_title(titles.get(name, name), fontsize=12, fontweight='bold')
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ ROC curves saved: {save_path}")
    
    plt.show()


def plot_pr_curves(results_dict, y_true_dict, y_prob_dict, save_path=None):
    """
    Precision-Recall 곡선 시각화 (4개 모델)
    
    Parameters:
    -----------
    results_dict : dict
        evaluate_all_models() 결과
    y_true_dict : dict
        실제 레이블 딕셔너리
    y_prob_dict : dict
        예측 확률 딕셔너리
    save_path : str, optional
        저장 경로
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    colors = {'death': '#e74c3c', 'vent': '#3498db', 'pressor': '#2ecc71', 'composite': '#9b59b6'}
    titles = {
        'death': 'Mortality (24h)',
        'vent': 'Ventilator (12h)',
        'pressor': 'Vasopressor (12h)',
        'composite': 'Composite (24h)'
    }
    
    for idx, (name, y_true) in enumerate(y_true_dict.items()):
        ax = axes[idx]
        y_prob = y_prob_dict[name]
        
        precision, recall, _ = precision_recall_curve(y_true, y_prob)
        auprc = results_dict[name]['auprc']
        baseline = y_true.mean()
        
        ax.plot(recall, precision, color=colors.get(name, 'blue'), lw=2,
                label=f'AUPRC = {auprc:.3f}')
        ax.axhline(y=baseline, color='gray', linestyle='--', lw=1, 
                   label=f'Baseline = {baseline:.3f}')
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
        ax.set_xlabel('Recall', fontsize=11)
        ax.set_ylabel('Precision', fontsize=11)
        ax.set_title(titles.get(name, name), fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ PR curves saved: {save_path}")
    
    plt.show()


def plot_combined_roc(results_dict, y_true_dict, y_prob_dict, save_path=None):
    """
    단일 그래프에 4개 ROC 곡선 표시
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    
    colors = {'death': '#e74c3c', 'vent': '#3498db', 'pressor': '#2ecc71', 'composite': '#9b59b6'}
    labels = {
        'death': 'Mortality',
        'vent': 'Ventilator',
        'pressor': 'Vasopressor',
        'composite': 'Composite'
    }
    
    for name, y_true in y_true_dict.items():
        y_prob = y_prob_dict[name]
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auroc = results_dict[name]['auroc']
        
        ax.plot(fpr, tpr, color=colors.get(name, 'blue'), lw=2,
                label=f'{labels.get(name, name)} (AUROC={auroc:.3f})')
    
    ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ROC Curves - All Models', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Combined ROC saved: {save_path}")
    
    plt.show()


# ==============================================================================
# 결과 출력
# ==============================================================================

def print_summary(results_dict, title="Model Performance Summary"):
    """
    성능 결과 테이블 출력
    
    Parameters:
    -----------
    results_dict : dict
        evaluate_all_models() 결과
    title : str
        테이블 제목
    """
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")
    
    # 헤더
    print(f"\n{'Model':<12} {'AUROC':>8} {'AUPRC':>8} {'F1':>8} {'Precision':>10} {'Recall':>8} {'Specificity':>11}")
    print("-" * 70)
    
    # 각 모델 결과
    for name, metrics in results_dict.items():
        print(f"{name:<12} {metrics['auroc']:>8.4f} {metrics['auprc']:>8.4f} "
              f"{metrics['f1']:>8.4f} {metrics['precision']:>10.4f} "
              f"{metrics['recall']:>8.4f} {metrics['specificity']:>11.4f}")
    
    print("-" * 70)
    
    # 평균
    avg_auroc = np.mean([m['auroc'] for m in results_dict.values()])
    avg_auprc = np.mean([m['auprc'] for m in results_dict.values()])
    print(f"{'Average':<12} {avg_auroc:>8.4f} {avg_auprc:>8.4f}")
    print()


def print_confusion_matrices(results_dict):
    """
    Confusion Matrix 출력
    """
    print("\n=== Confusion Matrices ===\n")
    
    for name, metrics in results_dict.items():
        print(f"[{name.upper()}]")
        print(f"                 Predicted")
        print(f"              Neg      Pos")
        print(f"Actual Neg  {metrics['tn']:>6}   {metrics['fp']:>6}")
        print(f"       Pos  {metrics['fn']:>6}   {metrics['tp']:>6}")
        print()


# ==============================================================================
# 결과 저장
# ==============================================================================

def save_results(results_dict, output_dir, prefix=""):
    """
    결과를 JSON과 CSV로 저장
    
    Parameters:
    -----------
    results_dict : dict
        성능 결과 딕셔너리
    output_dir : str
        저장 경로
    prefix : str
        파일명 접두사 (예: 'xgboost_', 'lightgbm_')
    
    Returns:
    --------
    dict : 저장된 파일 경로들
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON 저장
    json_path = os.path.join(output_dir, f'{prefix}results_{timestamp}.json')
    with open(json_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    # CSV 저장 (비교용)
    df_results = pd.DataFrame(results_dict).T
    csv_path = os.path.join(output_dir, f'{prefix}results_{timestamp}.csv')
    df_results.to_csv(csv_path)
    
    # 최신 결과 복사 (덮어쓰기)
    latest_json = os.path.join(output_dir, f'{prefix}results_latest.json')
    latest_csv = os.path.join(output_dir, f'{prefix}results_latest.csv')
    
    with open(latest_json, 'w') as f:
        json.dump(results_dict, f, indent=2)
    df_results.to_csv(latest_csv)
    
    print(f"✓ Results saved:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")
    print(f"  - {latest_json} (latest)")
    
    return {
        'json': json_path,
        'csv': csv_path,
        'latest_json': latest_json,
        'latest_csv': latest_csv
    }


# ==============================================================================
# 모델 비교
# ==============================================================================

def compare_models(results_list, model_names):
    """
    여러 모델 (XGBoost, LightGBM 등) 비교
    
    Parameters:
    -----------
    results_list : list of dict
        각 모델의 results_dict 리스트
    model_names : list of str
        모델 이름 리스트
    
    Returns:
    --------
    DataFrame : 비교 테이블
    """
    comparison = []
    
    for model_name, results in zip(model_names, results_list):
        for target, metrics in results.items():
            comparison.append({
                'Model': model_name,
                'Target': target,
                'AUROC': metrics['auroc'],
                'AUPRC': metrics['auprc'],
                'F1': metrics['f1']
            })
    
    df = pd.DataFrame(comparison)
    
    # 피벗 테이블
    pivot = df.pivot_table(
        index='Target',
        columns='Model',
        values=['AUROC', 'AUPRC'],
        aggfunc='first'
    )
    
    return pivot


# ==============================================================================
# Feature Importance
# ==============================================================================

def plot_feature_importance(model, feature_names, top_n=20, save_path=None, title="Feature Importance"):
    """
    피처 중요도 시각화
    
    Parameters:
    -----------
    model : trained model
        학습된 모델 (XGBoost, LightGBM 등)
    feature_names : list
        피처 이름 리스트
    top_n : int
        상위 N개만 표시
    save_path : str, optional
        저장 경로
    title : str
        그래프 제목
    """
    # 피처 중요도 추출
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
    elif hasattr(model, 'get_score'):
        importance_dict = model.get_score(importance_type='gain')
        importance = [importance_dict.get(f, 0) for f in feature_names]
    else:
        print("⚠️ Model does not have feature importance")
        return
    
    # 정렬
    indices = np.argsort(importance)[::-1][:top_n]
    
    # 시각화
    fig, ax = plt.subplots(figsize=(10, 8))
    
    y_pos = np.arange(len(indices))
    ax.barh(y_pos, [importance[i] for i in indices[::-1]], color='steelblue')
    ax.set_yticks(y_pos)
    ax.set_yticklabels([feature_names[i] for i in indices[::-1]])
    ax.set_xlabel('Importance', fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Feature importance saved: {save_path}")
    
    plt.show()
    
    return dict(zip([feature_names[i] for i in indices], [importance[i] for i in indices]))
