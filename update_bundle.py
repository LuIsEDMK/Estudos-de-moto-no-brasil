"""
Gera o data_bundle.py com os 3 CSVs comprimidos com zlib + base64.
Isso reduz drasticamente o tamanho do arquivo.
"""
import base64
import zlib
import os

def bundle():
    files = {
        'CSV_MOTOS': 'base_motos_VIP_mestre.csv',
        'CSV_CARROS': 'base_carros_VIP_mestre.csv',
        'CSV_CAMINHOES': 'base_caminhoes_VIP_mestre.csv'
    }

    out_lines = [
        'import base64\n',
        'import zlib\n',
        '\n',
        'def _decode(b64: str) -> str:\n',
        '    """Decode a zlib-compressed, base64-encoded string."""\n',
        '    return zlib.decompress(base64.b64decode(b64)).decode("utf-8")\n',
        '\n',
    ]

    for var_name, filename in files.items():
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                raw = f.read()
            compressed = zlib.compress(raw, level=9)
            b64 = base64.b64encode(compressed).decode('utf-8')
            raw_kb = len(raw) / 1024
            comp_kb = len(compressed) / 1024
            print(f'{filename}: {raw_kb:.0f} KB -> {comp_kb:.0f} KB compressed ({100*comp_kb/raw_kb:.0f}%)')
            out_lines.append(f'_{var_name} = "{b64}"\n')
            out_lines.append(f'{var_name}: str = _decode(_{var_name})\n\n')
        else:
            print(f'WARNING: {filename} not found, skipping.')

    # Backward compatibility
    out_lines.append('CSV_DATA = CSV_MOTOS\n')

    with open('src/app/data_bundle.py', 'w', encoding='utf-8') as f:
        f.writelines(out_lines)

    size_kb = os.path.getsize('src/app/data_bundle.py') / 1024
    print(f'\ndata_bundle.py: {size_kb:.0f} KB total')
    print('Bundle atualizado com sucesso.')

if __name__ == '__main__':
    bundle()
