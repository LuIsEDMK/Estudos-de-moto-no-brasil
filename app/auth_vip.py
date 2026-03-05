"""VIP authentication using Google Sheets CSV."""
import csv
from io import StringIO
from datetime import datetime
from typing import Optional

# Google Sheets URL
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/199fjvVptWCdA3YD_bVwhrAJRS_PYyfqf0O8jbo4QFB4/edit?usp=sharing"


def _fetch_csv(url: str) -> str:
    """Fetch CSV from Google Sheets."""
    try:
        import urllib.request
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv')
        csv_url = csv_url.replace('/edit#gid=', '/export?format=csv&gid=')
        with urllib.request.urlopen(csv_url, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception:
        return ""


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse date from string."""
    if not date_str or not date_str.strip():
        return None
    
    date_str = date_str.strip()
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _is_active(status: str) -> bool:
    """Check if status is active."""
    if not status:
        return False
    return status.strip().lower() in ['ativo', 'pago', 'paga', 'active', 'paid', 'sim', 'yes', 'ok']


def validar_email_vip(email: str) -> bool:
    """Validate email against VIP list."""
    if not email:
        return False
    
    email = email.strip().lower()
    
    # Master code for testing
    if email == "moto990_master":
        return True
    
    # Fetch and parse CSV
    csv_content = _fetch_csv(URL_PLANILHA)
    if not csv_content:
        return False
    
    reader = csv.DictReader(StringIO(csv_content))
    
    for row in reader:
        row_email = str(row.get('Email_Pagador', '')).strip().lower()
        
        if email == row_email:
            # Check status
            status = row.get('Status', '')
            if not _is_active(status):
                return False
            
            # Check expiration date if present
            validade = row.get('Validade', '')
            if validade and validade.strip():
                exp_date = _parse_date(validade)
                if exp_date and exp_date < datetime.now():
                    return False
            
            return True
    
    return False


def validar_senha(senha: str) -> bool:
    """Alias for validar_email_vip."""
    return validar_email_vip(senha)
