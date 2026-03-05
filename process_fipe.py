import csv
import re

def clean_price(price_str):
    # "R$ 2.392,00" -> 2392.0
    if not price_str: return 0.0
    clean = re.sub(r'[^\d,]', '', price_str)
    clean = clean.replace(',', '.')
    try:
        return float(clean)
    except:
        return 0.0

def process_file():
    input_file = 'tabela-fipe.csv'
    outputs = {
        'MOTORCYCLE': 'base_motos_VIP_mestre.csv',
        'CAR': 'base_carros_VIP_mestre.csv',
        'TRUCK': 'base_caminhoes_VIP_mestre.csv'
    }
    
    writers = {}
    files = {}
    
    headers = ['nome_marca', 'nome_modelo', 'ano_modelo', 'preco_limpo', 'eh_zero_km']
    
    for t, filename in outputs.items():
        f = open(filename, 'w', encoding='utf-8', newline='')
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writers[t] = writer
        files[t] = f

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vtype = row['Type']
                if vtype in writers:
                    raw_year = row['Year Value'].split(' ')[0]
                    eh_zero = False
                    if raw_year == '32000':
                        eh_zero = True
                        year_val = '2026' # Standardize 32000 as current year for regression
                    else:
                        try:
                            year_val = str(int(raw_year))
                            if int(year_val) >= 2026:
                                eh_zero = True
                        except:
                            continue # Skip invalid years
                    
                    writers[vtype].writerow({
                        'nome_marca': row['Brand Value'].strip(),
                        'nome_modelo': row['Model Value'].strip(),
                        'ano_modelo': year_val,
                        'preco_limpo': clean_price(row['Price']),
                        'eh_zero_km': eh_zero
                    })
    finally:
        for f in files.values():
            f.close()

if __name__ == '__main__':
    process_file()
    print("Arquivos processados com sucesso.")
