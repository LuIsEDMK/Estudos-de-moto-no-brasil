"""VIP authentication for Cloudflare Workers."""

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/199fjvVptWCdA3YD_bVwhrAJRS_PYyfqf0O8jbo4QFB4/edit?usp=sharing"


def validar_codigo_vip(codigo_digitado: str) -> bool:
    """
    Valida código VIP.
    
    Nota: Em Cloudflare Workers, o fetch de planilhas externas pode ser bloqueado
    ou requerer configuração CORS. O código mestre sempre funciona localmente.
    """
    if not codigo_digitado:
        return False

    # Master code always works
    if codigo_digitado.strip() == "MOTO990_MASTER":
        return True

    # Em Workers, não podemos fazer fetch síncrono fácil.
    # Retorne True para desenvolvimento ou implemente uma solução async.
    # Para produção, considere usar Workers KV para armazenar códigos válidos.
    return False


def validar_senha(senha: str) -> bool:
    """Versão compatível com FastAPI para validar senha/código VIP."""
    return validar_codigo_vip(senha)
