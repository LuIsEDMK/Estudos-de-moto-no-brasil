"""Lightweight utilities to replace heavy dependencies."""
import csv
import json
from io import StringIO
from typing import List, Dict, Any, Optional


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
    """
    Simple linear regression: y = mx + b
    Returns: {slope, intercept, r2_score}
    """
    n = len(x_vals)
    if n < 2:
        return {"slope": 0.0, "intercept": 0.0, "r2": 0.0}
    
    # Calculate means
    x_mean = sum(x_vals) / n
    y_mean = sum(y_vals) / n
    
    # Calculate slope (m) and intercept (b)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
    denominator = sum((x - x_mean) ** 2 for x in x_vals)
    
    if denominator == 0:
        return {"slope": 0.0, "intercept": y_mean, "r2": 0.0}
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate R²
    y_pred = [slope * x + intercept for x in x_vals]
    ss_res = sum((y - yp) ** 2 for y, yp in zip(y_vals, y_pred))
    ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {"slope": slope, "intercept": intercept, "r2": r2}


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
    groups = {}
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
