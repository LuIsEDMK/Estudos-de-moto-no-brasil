import pandas as pd

# O link da sua planilha (substitua pelo link que você copiou)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/199fjvVptWCdA3YD_bVwhrAJRS_PYyfqf0O8jbo4QFB4/edit?usp=sharing"


def validar_codigo_vip(codigo_digitado):
    """
    Conecta na planilha e verifica se o código existe.
    """
    if not codigo_digitado:
        return False

    try:
        # Transforma o link da planilha em um link de download de CSV (truque de mestre)
        csv_url = URL_PLANILHA.replace('/edit?usp=sharing', '/export?format=csv')
        csv_url = csv_url.replace('/edit#gid=', '/export?format=csv&gid=')  # Caso tenha abas específicas

        # Lê a planilha em tempo real (sem cache para não travar novos códigos)
        df_codigos = pd.read_csv(csv_url)

        # Limpa espaços em branco e garante que tudo seja string
        lista_codigos = df_codigos['codigos'].astype(str).str.strip().tolist()

        # Verifica se o código está lá (incluindo o seu código mestre)
        if codigo_digitado.strip() in lista_codigos or codigo_digitado == "MOTO990_MASTER":
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