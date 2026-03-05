"""Lightweight utilities to replace heavy dependencies."""
import csv
import json
from io import StringIO
from typing import List, Dict, Any, Optional, Callable


def load_csv_data(csv_content: str) -> List[Dict[str, Any]]:
    """Load CSV data using stdlib - replaces pandas.read_csv."""
    reader = csv.DictReader(StringIO(csv_content))
    rows = []
    for row in reader:
        # Convert numeric fields
        processed = {}
        for key, value in row.items():
            if value is None:
                processed[key] = None
                continue
            # Try int
            try:
                processed[key] = int(value)
                continue
            except (ValueError, TypeError):
                pass
            # Try float
            try:
                processed[key] = float(value)
                continue
            except (ValueError, TypeError):
                pass
            # Keep as string
            processed[key] = value
        rows.append(processed)
    return rows


def simple_linear_regression(x_vals: List[float], y_vals: List[float]) -> Dict[str, float]:
    """Simple linear regression: y = mx + b  (kept for backward compatibility)."""
    n = len(x_vals)
    if n < 2:
        return {"slope": 0.0, "intercept": 0.0, "r2": 0.0}
    x_mean = sum(x_vals) / n
    y_mean = sum(y_vals) / n
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
    denominator = sum((x - x_mean) ** 2 for x in x_vals)
    if denominator == 0:
        return {"slope": 0.0, "intercept": y_mean, "r2": 0.0}
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    y_pred = [slope * x + intercept for x in x_vals]
    ss_res = sum((y - yp) ** 2 for y, yp in zip(y_vals, y_pred))
    ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    return {"slope": slope, "intercept": intercept, "r2": r2}


def polynomial_regression(x_vals: List[float], y_vals: List[float], degree: int = 2) -> Dict[str, Any]:
    """
    Polynomial regression via normal equations (least squares).

    Model: y = a0 + a1*xc + a2*xc^2  where xc = x - mean(x)
    X is centered for numerical stability with large year values.

    Why quadratic for motorcycle prices?
        - New bikes lose value fast (steep drop years 0-3)
        - Older bikes depreciate more slowly (the curve flattens)
        - A straight line cannot capture this deceleration; a parabola can.

    Returns dict with:
        coeffs       – [a0, a1, a2] polynomial coefficients (centered x)
        r2           – coefficient of determination (higher = better fit)
        slope_at_mean – dy/dx at mean year (current local depreciation R$/year)
        predict(x)   – callable that takes original year, returns predicted price
    """
    n = len(x_vals)
    d = degree + 1  # number of coefficients

    def _linear_fallback() -> Dict[str, Any]:
        lin = simple_linear_regression(x_vals, y_vals)
        def _pred(x: float, _s: float = lin["slope"], _i: float = lin["intercept"]) -> float:
            return _s * x + _i
        return {
            "coeffs": [lin["intercept"], lin["slope"], 0.0],
            "r2": max(0.0, lin["r2"]),
            "slope_at_mean": lin["slope"],
            "predict": _pred,
        }

    if n < max(d, 5):  # Requer mínimo de 5 pontos para não dar overfit em grau 2
        return _linear_fallback()

    # ── Center x values to avoid catastrophic cancellation ──────────────────
    x_offset = sum(x_vals) / n
    xc = [x - x_offset for x in x_vals]

    # ── Build normal equations  X^T·X · a = X^T·y ───────────────────────────
    # power sums: xpow[k] = Σ xc_i^k
    xpow = [sum(xi ** k for xi in xc) for k in range(2 * degree + 1)]

    # (d×d) matrix
    XTX = [[xpow[i + j] for j in range(d)] for i in range(d)]
    
    # Adicionar penalização Ridge (L2 regularização) na diagonal principal (exceto no viés i=0)
    # Isso impede que os coeficientes explodam (overfitting)
    ridge_alpha = 2.0  # Fator de regularização
    for i in range(1, d):
        XTX[i][i] += ridge_alpha * n

    # d-vector
    XTy = [
        sum((xc[idx] ** i) * y_vals[idx] for idx in range(n))
        for i in range(d)
    ]

    # ── Gaussian elimination with partial pivoting ───────────────────────────
    aug = [XTX[i][:] + [XTy[i]] for i in range(d)]

    for col in range(d):
        # Partial pivot: find row with largest absolute value in this column
        pivot_row = max(range(col, d), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot_row][col]) < 1e-12:
            return _linear_fallback()  # singular matrix → degenerate data
        aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

        for row in range(col + 1, d):
            factor = aug[row][col] / aug[col][col]
            aug[row] = [aug[row][j] - factor * aug[col][j] for j in range(d + 1)]

    # ── Back substitution ────────────────────────────────────────────────────
    coeffs: List[float] = [0.0] * d
    for i in range(d - 1, -1, -1):
        s = aug[i][d] - sum(aug[i][j] * coeffs[j] for j in range(i + 1, d))
        coeffs[i] = s / aug[i][i]

    # ── Prediction helper (accepts original un-centered year values) ─────────
    captured_offset = x_offset
    captured_coeffs = coeffs[:]

    def predict(x_orig: float) -> float:
        xce = x_orig - captured_offset
        return sum(captured_coeffs[k] * (xce ** k) for k in range(d))

    # ── R² ───────────────────────────────────────────────────────────────────
    y_mean = sum(y_vals) / n
    y_pred = [predict(x) for x in x_vals]
    ss_res = sum((y - yp) ** 2 for y, yp in zip(y_vals, y_pred))
    ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
    r2 = max(0.0, 1.0 - ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    # ── Local slope at mean year ─────────────────────────────────────────────
    # d/dxc [a0 + a1·xc + a2·xc²] at xc = 0  →  a1  (just the linear term)
    # For higher-degree polys the derivative at xc=0 is still coeffs[1].
    slope_at_mean = coeffs[1] if d > 1 else 0.0

    return {
        "coeffs": coeffs,
        "r2": r2,
        "slope_at_mean": slope_at_mean,
        "predict": predict,
    }


def filter_rows(data: List[Dict], **conditions) -> List[Dict]:
    """Filter rows by conditions."""
    result = data
    for key, value in conditions.items():
        result = [row for row in result if row.get(key) == value]
    return result


def sort_rows(data: List[Dict], key: str, reverse: bool = False) -> List[Dict]:
    """Sort rows by key."""
    return sorted(data, key=lambda x: x.get(key, 0) if x.get(key) is not None else 0, reverse=reverse)


def group_by(data: List[Dict], keys: List[str]) -> Dict[tuple, List[Dict]]:
    """Group data by multiple keys."""
    groups: Dict[tuple, List[Dict]] = {}
    for row in data:
        group_key = tuple(row.get(k) for k in keys)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(row)
    return groups


def unique_values(data: List[Dict], key: str) -> List[Any]:
    """Get unique values for a key."""
    seen = set()
    result = []
    for row in data:
        val = row.get(key)
        if val not in seen:
            seen.add(val)
            result.append(val)
    return result


def calc_desvalorizacao(rows: List[Dict]) -> List[Dict]:
    """Calculate depreciation between consecutive years."""
    if len(rows) < 2:
        return []

    # Sort by year descending
    sorted_rows = sorted(rows, key=lambda x: x.get('ano_modelo', 0), reverse=True)
    result = []

    for i in range(len(sorted_rows) - 1):
        current = sorted_rows[i]
        next_row = sorted_rows[i + 1]

        preco_atual = current.get('preco_limpo', 0)
        preco_anterior = next_row.get('preco_limpo', 0)
        ano_atual = current.get('ano_modelo', 0)

        perda_reais = preco_atual - preco_anterior
        perda_pct = ((perda_reais / preco_anterior) * 100) if preco_anterior else 0

        result.append({
            'ano_modelo': ano_atual,
            'ano_anterior': next_row.get('ano_modelo'),
            'preco_atual': preco_atual,
            'preco_anterior': preco_anterior,
            'perda_reais': perda_reais,
            'perda_pct': perda_pct,
        })

    return result
