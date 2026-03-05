"""
Diagnóstico de Overfitting — Regressão Polinomial Grau 2
=========================================================
Métricas analisadas:
  - R² (treino)        : alto = bom fit, mas ≈1.0 com poucos pontos = overfitting suspeito
  - Leave-One-Out CV   : R² médio quando se retira 1 ponto por vez. Se cair muito vs R²-treino → overfitting
  - Previsão 2026      : valor extrapolado. Se for negativo ou absurdo → curva explodindo (overfitting típico)
  - Nº de pontos       : com n < 5 para grau 2, há risco alto
"""

import sys
import os
import csv

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'app'))

from utils import polynomial_regression, load_csv_data, filter_rows, sort_rows, simple_linear_regression

# ── Carregar bases
BASE_MOTOS = os.path.join(os.path.dirname(__file__), 'base_motos_VIP_mestre.csv')
BASE_CARROS = os.path.join(os.path.dirname(__file__), 'base_carros_VIP_mestre.csv')
BASE_CAMINHOES = os.path.join(os.path.dirname(__file__), 'base_caminhoes_VIP_mestre.csv')


def loocv_r2(x_vals, y_vals, degree=2):
    """Leave-One-Out Cross Validation — retira 1 ponto por vez e avalia erro de previsão."""
    n = len(x_vals)
    if n < (degree + 2):
        return None  # Não tem dados suficientes para LOOCV com esse grau

    erros = []
    y_mean = sum(y_vals) / n
    for i in range(n):
        x_train = [x_vals[j] for j in range(n) if j != i]
        y_train = [y_vals[j] for j in range(n) if j != i]
        x_test = x_vals[i]
        y_test = y_vals[i]
        try:
            poly = polynomial_regression(x_train, y_train, degree=degree)
            y_hat = poly['predict'](x_test)
            erros.append((y_test - y_hat) ** 2)
        except Exception:
            continue

    if not erros:
        return None

    mse_cv = sum(erros) / len(erros)
    ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
    r2_cv = 1.0 - (mse_cv * n / ss_tot) if ss_tot > 0 else 0.0
    return r2_cv


def analisar_modelo(nome_marca, nome_modelo, rows, degree=2):
    df_filtrado = [r for r in rows if r.get('nome_marca') == nome_marca and r.get('nome_modelo') == nome_modelo]
    df_sorted = sort_rows(df_filtrado, 'ano_modelo')

    x_vals = [float(r.get('ano_modelo', 0)) for r in df_sorted]
    y_vals = [float(r.get('preco_limpo', 0)) for r in df_sorted]

    n = len(x_vals)
    if n < 3:
        return None

    poly = polynomial_regression(x_vals, y_vals, degree=degree)
    r2_treino = poly['r2']
    previsao_2026 = poly['predict'](2026.0)
    r2_cv = loocv_r2(x_vals, y_vals, degree=degree)
    gap = (r2_treino - r2_cv) if r2_cv is not None else None
    preco_atual = y_vals[-1] if y_vals else 0
    previsao_razoavel = (0 < previsao_2026 < preco_atual * 3)  # Previsão dentro de 3x o preço atual

    alerta = []
    if r2_treino > 0.98 and n < 6:
        alerta.append("⚠️  R² alto com poucos pontos (suspeito de overfit)")
    if gap is not None and gap > 0.15:
        alerta.append(f"⚠️  Gap R²-treino vs LOOCV = {gap:.2f} (overfit detectado)")
    if not previsao_razoavel:
        alerta.append(f"⚠️  Previsão 2026 absurda: R${previsao_2026:,.0f} (curva explodindo)")

    return {
        'marca': nome_marca,
        'modelo': nome_modelo,
        'n': n,
        'r2_treino': r2_treino,
        'r2_loocv': r2_cv,
        'gap': gap,
        'previsao_2026': previsao_2026,
        'preco_atual': preco_atual,
        'alertas': alerta,
    }


def processar_base(caminho, tipo_label, amostra=30):
    print(f"\n{'='*70}")
    print(f"  BASE: {tipo_label}  →  {os.path.basename(caminho)}")
    print(f"{'='*70}")

    if not os.path.exists(caminho):
        print(f"  Arquivo não encontrado: {caminho}")
        return

    with open(caminho, encoding='utf-8') as f:
        rows = load_csv_data(f.read())

    # Pegar combinações únicas de marca+modelo
    pares = list({(r.get('nome_marca', ''), r.get('nome_modelo', '')) for r in rows if r.get('nome_marca') and r.get('nome_modelo')})
    pares = sorted(pares, key=lambda p: (str(p[0]), str(p[1])))[:amostra]  # amostra dos primeiros N

    total = 0
    com_alerta = 0
    resultados = []

    for marca, modelo in pares:
        res = analisar_modelo(marca, modelo, rows)
        if res is None:
            continue
        total += 1
        if res['alertas']:
            com_alerta += 1
        resultados.append(res)

    # Mostrar os piores casos (maior gap, ou com alertas)
    resultados_com_alerta = [r for r in resultados if r['alertas']]
    resultados_sem_alerta = [r for r in resultados if not r['alertas']]

    print(f"\n  📊 Total analisado: {total} modelos | ⚠️  Com alertas: {com_alerta}")

    if resultados_com_alerta:
        print(f"\n  🚨 MODELOS COM PROBLEMA DETECTADO:")
        print(f"  {'Marca':<20} {'Modelo':<35} {'n':>3} {'R²-train':>9} {'R²-LOOCV':>9} {'Gap':>6} {'Prev2026':>14} {'Alertas'}")
        print(f"  {'-'*130}")
        for r in sorted(resultados_com_alerta, key=lambda x: -(x['gap'] or 0))[:20]:
            gap_str = f"{r['gap']:.3f}" if r['gap'] is not None else "N/A"
            r2cv_str = f"{r['r2_loocv']:.3f}" if r['r2_loocv'] is not None else "N/A"
            alertas_str = ' | '.join(r['alertas'])
            print(f"  {r['marca']:<20} {r['modelo']:<35} {r['n']:>3} {r['r2_treino']:>9.3f} {r2cv_str:>9} {gap_str:>6} R${r['previsao_2026']:>12,.0f}   {alertas_str}")
    else:
        print(f"\n  ✅ Nenhum problema de overfitting detectado na amostra!")

    # Estatísticas gerais
    if resultados:
        r2_medios = [r['r2_treino'] for r in resultados]
        gaps = [r['gap'] for r in resultados if r['gap'] is not None]
        print(f"\n  📈 R² médio (treino): {sum(r2_medios)/len(r2_medios):.3f}")
        if gaps:
            print(f"  📉 Gap médio (overfitting): {sum(gaps)/len(gaps):.3f}")
            print(f"  📉 Gap máximo: {max(gaps):.3f}")


def main():
    print("\n" + "="*70)
    print("  DIAGNÓSTICO DE OVERFITTING — REGRESSÃO POLINOMIAL GRAU 2")
    print("="*70)

    processar_base(BASE_MOTOS, "MOTOS", amostra=50)
    processar_base(BASE_CARROS, "CARROS", amostra=50)
    processar_base(BASE_CAMINHOES, "CAMINHÕES", amostra=30)

    print(f"\n{'='*70}")
    print("  RESUMO DA ANÁLISE")
    print(f"{'='*70}")
    print("""
  Interpretação dos resultados:
  ─────────────────────────────
  ✅ Gap < 0.10  → Modelo generalizando bem (sem overfitting)
  ⚠️  Gap 0.10~0.25 → Leve overfitting (atenção em amostras pequenas)
  🚨 Gap > 0.25   → Overfitting severo (curva memoriza os dados)
  🚨 Previsão negativa/absurda → Extrapolação da curva explodindo

  Causa mais comum: poucos pontos (n < 5) com grau 2.
  Grau 2 exige no mínimo 3 pontos, mas é confiável com n ≥ 6.
  """)


if __name__ == '__main__':
    main()
