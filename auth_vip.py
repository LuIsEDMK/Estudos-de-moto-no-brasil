"""VIP authentication - lightweight version without pandas."""
import csv
from io import StringIO

# O link da sua planilha
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/199fjvVptWCdA3YD_bVwhrAJRS_PYyfqf0O8jbo4QFB4/edit?usp=sharing"


def _fetch_csv_content(url: str) -> str:
    """Fetch CSV content from URL."""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception:
        return ""


def validar_codigo_vip(codigo_digitado: str) -> bool:
    """
    Conecta na planilha e verifica se o código existe.
    """
    if not codigo_digitado:
        return False

    # Master code always works
    if codigo_digitado.strip() == "MOTO990_MASTER":
        return True

    try:
        # Transforma o link da planilha em um link de download de CSV
        csv_url = URL_PLANILHA.replace('/edit?usp=sharing', '/export?format=csv')
        csv_url = csv_url.replace('/edit#gid=', '/export?format=csv&gid=')

        # Fetch CSV content
        csv_content = _fetch_csv_content(csv_url)
        if not csv_content:
            return False

        # Parse CSV using stdlib
        reader = csv.DictReader(StringIO(csv_content))
        for row in reader:
            codigo_planilha = str(row.get('codigos', '')).strip()
            if codigo_digitado.strip() == codigo_planilha:
                return True
        
        return False
    except Exception as e:
        print(f"Erro na conexão com o Banco de Dados VIP: {e}")
        return False


def validar_senha(senha: str) -> bool:
    """
    Versão compatível com FastAPI para validar senha/código VIP.
    """
    return validar_codigo_vip(senha)
