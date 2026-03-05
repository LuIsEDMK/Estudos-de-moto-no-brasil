"""Lightweight utilities without pandas."""
import csv
from io import StringIO
from typing import List, Dict, Any, Optional


def load_csv_data(content: str) -> List[Dict[str, Any]]:
    """Load CSV content into list of dicts."""
    reader = csv.DictReader(StringIO(content))
    return [row for row in reader]


def filter_rows(data: List[Dict], **kwargs) -> List[Dict]:
    """Filter rows by key-value pairs."""
    result = data
    for key, value in kwargs.items():
        result = [row for row in result if row.get(key) == value]
    return result


def sort_rows(data: List[Dict], key: str, reverse: bool = False) -> List[Dict]:
    """Sort rows by key."""
    def get_sort_key(row):
        val = row.get(key)
        try:
            return float(val) if val is not None else 0
        except (ValueError, TypeError):
            return val or ""
    return sorted(data, key=get_sort_key, reverse=reverse)


def unique_values(data: List[Dict], key: str) -> List[str]:
    """Get unique values for a key."""
    values = set()
    for row in data:
        val = row.get(key)
        if val:
            values.add(val)
    return sorted(list(values))


def group_by(data: List[Dict], keys: List[str]) -> Dict[tuple, List[Dict]]:
    """Group data by multiple keys."""
    groups = {}
    for row in data:
        key = tuple(row.get(k) for k in keys)
        if key not in groups:
            groups[key] = []
        groups[key].append(row)
    return groups


def calc_desvalorizacao(data: List[Dict]) -> List[Dict]:
    """Calculate depreciation between consecutive years."""
    if len(data) < 2:
        return []
    
    sorted_data = sorted(data, key=lambda x: x.get('ano_modelo', 0), reverse=True)
    result = []
    
    for i in range(len(sorted_data) - 1):
        atual = sorted_data[i]
        anterior = sorted_data[i + 1]
        
        preco_atual = float(atual.get('preco_limpo', 0) or 0)
        preco_anterior = float(anterior.get('preco_limpo', 0) or 0)
        
        perda_reais = preco_atual - preco_anterior
        perda_pct = ((preco_atual - preco_anterior) / preco_atual * 100) if preco_atual else 0
        
        result.append({
            'ano_modelo': atual.get('ano_modelo'),
            'ano_anterior': anterior.get('ano_modelo'),
            'perda_reais': perda_reais,
            'perda_pct': perda_pct
        })
    
    return result


def simple_linear_regression(x: List[float], y: List[float]) -> Dict[str, float]:
    """Simple linear regression: y = slope * x + intercept."""
    n = len(x)
    if n < 2:
        return {'slope': 0, 'intercept': 0, 'r2': 0}
    
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    denominator = sum((xi - x_mean) ** 2 for xi in x)
    
    if denominator == 0:
        return {'slope': 0, 'intercept': y_mean, 'r2': 0}
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate R²
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    return {'slope': slope, 'intercept': intercept, 'r2': max(0, r2)}
