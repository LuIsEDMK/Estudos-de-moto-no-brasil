#!/usr/bin/env python3
"""Convert CSV data to JSON for SvelteKit app."""
import csv
import json

# Read CSV and convert to JSON
with open('base_motos_VIP_mestre.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = []
    for row in reader:
        # Normalize 2026 -> 2025
        ano = row['ano_modelo']
        if ano == '2026':
            ano = '2025'

        data.append({
            'codigo_fipe': '',
            'marca': row['nome_marca'],
            'modelo': row['nome_modelo'],
            'ano_modelo': ano,
            'preco': str(row['preco_limpo']),
            'preco_limpo': float(row['preco_limpo']) if row['preco_limpo'] else 0,
            'tipo': 'MOTORCYCLE'
        })

# Write JSON
with open('motoexpert-ai/src/lib/server/data_bundle.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Converted {len(data)} records to JSON")
