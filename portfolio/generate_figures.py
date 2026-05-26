"""
포트폴리오 PPT용 차트 생성 스크립트
실행: python portfolio/generate_figures.py
출력: portfolio/figures/ 폴더에 PNG 저장
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# 한글 폰트 설정 (Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

FIGURES_DIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# 1. EDA 발견 요약 — 결측률 상위 변수 바차트
# ─────────────────────────────────────────────
def fig_missing_rates():
    variables = [
        'Lactate\n(젖산)',
        'ABGA\n(동맥혈가스)',
        'GCS\n(의식수준)',
        'Urine Output\n(소변량)',
        'Creatinine\n(크레아티닌)',
    ]
    missing_pct = [72, 58, 41, 35, 28]
    colors = ['#E53935', '#FB8C00', '#FDD835', '#43A047', '#1E88E5']

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(variables, missing_pct, color=colors, height=0.55, edgecolor='none')

    for bar, pct in zip(bars, missing_pct):
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                f'{pct}%', va='center', fontsize=12, fontweight='bold', color='#333333')

    ax.set_xlim(0, 85)
    ax.set_xlabel('결측률 (%)', fontsize=11)
    ax.set_title('EDA 발견: 결측치 ≠ 누락\n"측정을 안 했다"는 것 자체가 임상 정보',
                 fontsize=13, fontweight='bold', pad=14)
    ax.axvline(x=50, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.text(51, -0.7, '50% 기준선', fontsize=9, color='gray')
    ax.invert_yaxis()
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(left=False)
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')

    note = ('* Lactate 72%: 검사 지시 자체가 "위험 의심" 신호\n'
            '→ 결측 여부를 별도 플래그 피처로 추가')
    ax.text(0, -1.4, note, fontsize=9, color='#555555', style='italic')

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, '01_missing_rates.png')
    plt.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'저장 완료: {path}')


# ─────────────────────────────────────────────
# 2. 환자 A vs B — 같은 혈압 90의 두 경로
# ─────────────────────────────────────────────
def fig_bp_comparison():
    hours = np.arange(0, 13)

    # 환자 A: 안정적으로 90 유지
    bp_a = [91, 90, 92, 89, 91, 90, 88, 91, 90, 89, 90, 91, 90]
    # 환자 B: 130에서 급락
    bp_b = [130, 128, 124, 118, 110, 104, 99, 94, 91, 90, 89, 90, 90]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(hours, bp_a, color='#1E88E5', linewidth=2.5, marker='o', markersize=5,
            label='환자 A — 안정적 유지 (위험 낮음)', linestyle='--', alpha=0.85)
    ax.plot(hours, bp_b, color='#E53935', linewidth=2.5, marker='o', markersize=5,
            label='환자 B — 급격한 하락 (위험 높음)')

    ax.axhline(y=90, color='gray', linestyle=':', linewidth=1, alpha=0.7)
    ax.text(12.1, 90, '90 mmHg\n(두 환자 동일)', fontsize=9, color='gray', va='center')

    # 위험 구간 표시
    ax.fill_between(hours[8:], [75]*5, [95]*5, color='#E53935', alpha=0.08)
    ax.annotate('급락 구간\n(2h 만에 39↓)', xy=(7, 99), xytext=(5.5, 108),
                fontsize=9, color='#E53935',
                arrowprops=dict(arrowstyle='->', color='#E53935', lw=1.2))

    ax.set_ylim(70, 145)
    ax.set_xlim(-0.3, 13.5)
    ax.set_xlabel('시간 (h)', fontsize=11)
    ax.set_ylabel('수축기 혈압 (mmHg)', fontsize=11)
    ax.set_title('같은 혈압 90, 다른 위험도\n"수치보다 변화의 방향과 속도"',
                 fontsize=13, fontweight='bold', pad=14)
    ax.legend(fontsize=10, loc='lower left')
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')

    note = '→ Delta(변화량) + Slope(기울기) 피처로 "속도"를 모델에 반영'
    ax.text(0, 73, note, fontsize=9, color='#555555', style='italic')

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, '02_bp_comparison.png')
    plt.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'저장 완료: {path}')


# ─────────────────────────────────────────────
# 3. 피처 구성 — 카테고리별 트리맵
# ─────────────────────────────────────────────
def fig_feature_treemap():
    try:
        import squarify
    except ImportError:
        print('squarify 미설치 — pip install squarify 후 재실행. 트리맵 건너뜀.')
        _fig_feature_bar_fallback()
        return

    categories = [
        '활력징후\n통계\n(20)',
        '추세\nDelta·Slope\n(10)',
        '검사 결과\nLab\n(6)',
        '의식 수준\nGCS\n(4)',
        '임상 복합\nMEWS·NEWS\n(3)',
        '소변량\nUrine\n(3)',
        '결측 플래그\n(3)',
        '활력징후\n원본\n(7)',
    ]
    sizes = [20, 10, 6, 4, 3, 3, 3, 7]
    colors = ['#1565C0', '#E53935', '#2E7D32', '#6A1B9A',
              '#E65100', '#00838F', '#4E342E', '#1E88E5']

    fig, ax = plt.subplots(figsize=(10, 6))
    squarify.plot(sizes=sizes, label=categories, color=colors, alpha=0.85,
                  text_kwargs={'fontsize': 10, 'color': 'white', 'fontweight': 'bold'},
                  ax=ax)
    ax.axis('off')
    ax.set_title('41개 피처 구성 — 카테고리별 비중\n(숫자는 피처 수)',
                 fontsize=13, fontweight='bold', pad=14)
    fig.patch.set_facecolor('white')

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, '03_feature_treemap.png')
    plt.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'저장 완료: {path}')


def _fig_feature_bar_fallback():
    """squarify 없을 때 대체 수평 바차트"""
    categories = [
        '활력징후 통계 (6h 평균·최솟값 등)',
        '추세 Delta·Slope',
        '활력징후 원본',
        '검사 결과 (Lab)',
        '의식 수준 (GCS)',
        '임상 복합지표 (MEWS·NEWS·Shock)',
        '소변량',
        '결측 플래그',
    ]
    sizes = [20, 10, 7, 6, 4, 3, 3, 3]
    colors = ['#1565C0', '#E53935', '#1E88E5', '#2E7D32',
              '#6A1B9A', '#E65100', '#00838F', '#4E342E']

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(categories, sizes, color=colors, height=0.6, edgecolor='none')
    for bar, s in zip(bars, sizes):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                str(s), va='center', fontsize=11, fontweight='bold')
    ax.set_xlabel('피처 수', fontsize=11)
    ax.set_title('41개 피처 구성 — 카테고리별 분포', fontsize=13, fontweight='bold', pad=14)
    ax.invert_yaxis()
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(left=False)
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, '03_feature_treemap.png')
    plt.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'저장 완료 (대체 바차트): {path}')


# ─────────────────────────────────────────────
# 4. SHAP 상위 10개 피처 수평 바차트
# ─────────────────────────────────────────────
def fig_shap_top10():
    features = [
        'GCS Total (의식 수준 총점)',
        'Shock Index (쇼크 지수)',
        'SBP Slope 3h (혈압 기울기)',
        'Lactate (젖산 수치)',
        'lactate_missing (검사 여부)',
        'MEWS Score (조기 경고 점수)',
        'SpO2 Min 6h (산소포화도 최솟값)',
        'HR Delta 1h (심박수 변화량)',
        'Urine Rate (소변 속도)',
        'NEWS Score (국가 조기경고 점수)',
    ]
    shap_vals = [0.38, 0.29, 0.24, 0.21, 0.18, 0.16, 0.14, 0.12, 0.10, 0.09]
    colors = ['#E53935' if v > 0.20 else '#FB8C00' if v > 0.13 else '#FDD835'
              for v in shap_vals]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(features[::-1], shap_vals[::-1], color=colors[::-1],
                   height=0.6, edgecolor='none')

    for bar, val in zip(bars, shap_vals[::-1]):
        ax.text(bar.get_width() + 0.003, bar.get_y() + bar.get_height() / 2,
                f'{val:.2f}', va='center', fontsize=10, fontweight='bold', color='#333333')

    ax.set_xlabel('평균 |SHAP 값| (예측값에 대한 기여도)', fontsize=10)
    ax.set_title('SHAP 상위 10개 피처\n"모델이 위험하다고 판단한 근거"',
                 fontsize=13, fontweight='bold', pad=14)

    # 범례
    high = mpatches.Patch(color='#E53935', label='매우 높은 기여')
    mid = mpatches.Patch(color='#FB8C00', label='중간 기여')
    low = mpatches.Patch(color='#FDD835', label='낮은 기여')
    ax.legend(handles=[high, mid, low], fontsize=9, loc='lower right')

    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(left=False)
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')

    note = '* 값은 예시 — 실제 SHAP 계산 결과로 교체 필요'
    ax.text(0, -1.1, note, fontsize=8, color='#888888', style='italic',
            transform=ax.get_yaxis_transform())

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, '04_shap_top10.png')
    plt.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'저장 완료: {path}')


if __name__ == '__main__':
    print('차트 생성 시작...')
    fig_missing_rates()
    fig_bp_comparison()
    fig_feature_treemap()
    fig_shap_top10()
    print(f'\n완료. 저장 위치: {FIGURES_DIR}')
