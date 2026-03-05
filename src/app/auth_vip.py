"""VIP authentication for Cloudflare Workers — async via httpx."""
import csv
import hmac
import hashlib
import time
import base64
from io import StringIO

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/199fjvVptWCdA3YD_bVwhrAJRS_PYyfqf0O8jbo4QFB4/edit?usp=sharing"

# Segredo para assinar os tokens VIP — mude se quiser invalidar todos os tokens
_VIP_SECRET = b"motoexpert_vip_secret_2025"


def _planilha_csv_url() -> str:
    url: str = URL_PLANILHA.replace("/edit?usp=sharing", "/export?format=csv")
    url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    return url


def _emails_da_planilha(csv_content: str) -> list[str]:
    """Parse CSV e retorna lista de emails válidos."""
    reader = csv.DictReader(StringIO(csv_content))
    emails = []
    for row in reader:
        # Suporta colunas chamadas 'email', 'emails' ou mantém 'codigos' para retrocompatibilidade
        val = row.get("email") or row.get("emails") or row.get("codigos")
        if val:
            emails.append(str(val).strip().lower())
    return emails


async def _fetch_planilha_async() -> str:
    """Fetch the Google Sheet CSV content using httpx (async, works on Workers)."""
    try:
        import httpx
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(_planilha_csv_url())
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        print(f"[auth_vip] Erro ao buscar planilha: {e}")
        return ""


# ---------------------------------------------------------------------------
# Signed VIP Token (persists across isolates via cookie)
# ---------------------------------------------------------------------------

def create_vip_token(email: str) -> str:
    """Cria um token VIP assinado com HMAC para persistir no cookie."""
    ts = str(int(time.time()))
    payload = f"{email}:{ts}"
    sig = hmac.new(_VIP_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()


def verify_vip_token(token: str) -> bool:
    """Verifica a assinatura e validade (30 dias) de um token VIP."""
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        # Format: email:timestamp:signature
        last_colon = decoded.rfind(":")
        payload = decoded[:last_colon]
        sig = decoded[last_colon + 1:]
        expected = hmac.new(_VIP_SECRET, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        ts_str = payload.rsplit(":", 1)[1]
        if int(time.time()) - int(ts_str) > 86400 * 30:
            return False
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

async def validar_email_vip_async(email_digitado: str) -> bool:
    """Valida se o email está na planilha Google Sheets VIP (async)."""
    if not email_digitado:
        return False

    email = email_digitado.strip().lower()

    csv_content = await _fetch_planilha_async()
    if not csv_content:
        return False

    emails_validos = _emails_da_planilha(csv_content)
    return email in emails_validos


async def validar_senha(senha: str) -> bool:
    """Entry point usado pelo FastAPI (async)."""
    return await validar_email_vip_async(senha)
