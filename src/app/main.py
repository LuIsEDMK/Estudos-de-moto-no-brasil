from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import json
import secrets
from typing import Optional, List, Dict, Any

from . import auth_vip
from .data_bundle import CSV_MOTOS, CSV_CARROS, CSV_CAMINHOES
from .utils import (
    load_csv_data, simple_linear_regression, polynomial_regression,
    filter_rows, sort_rows, unique_values, calc_desvalorizacao, group_by
)

app = FastAPI(title="MotoExpert AI")

@app.middleware("http")
async def set_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Allows Google Sign-in Popups to communicate with our app securely
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
    return response

# ---------------------------------------------------------------------------
# Templates — loaded from the bundled package
# ---------------------------------------------------------------------------
from jinja2 import PackageLoader, Environment, select_autoescape

jinja_env = Environment(
    loader=PackageLoader("app", "templates"),
    autoescape=select_autoescape(["html"]),
)

class _J2Templates:
    def __init__(self, env: Environment):
        self.env = env

    def TemplateResponse(self, name: str, context: dict):
        tmpl = self.env.get_template(name)
        html = tmpl.render(**context)
        return HTMLResponse(content=html)

templates = _J2Templates(jinja_env)

# ---------------------------------------------------------------------------
# Data — loaded from the bundled CSV
# ---------------------------------------------------------------------------
# Load once at startup
df_motos = load_csv_data(CSV_MOTOS)
df_carros = load_csv_data(CSV_CARROS)
df_caminhoes = load_csv_data(CSV_CAMINHOES)

def clean_data(df):
    for row in df:
        if row.get('ano_modelo') == 2026:
            row['ano_modelo'] = 2025
    return df

df_motos = clean_data(df_motos)
df_carros = clean_data(df_carros)
df_caminhoes = clean_data(df_caminhoes)

def get_df_by_type(tipo: str):
    if tipo == 'CAR': return df_carros
    if tipo == 'TRUCK': return df_caminhoes
    return df_motos


def gerar_relatorios_vip(data: List[Dict]) -> List[Dict]:
    """Generate VIP reports without pandas."""
    # Group by marca + modelo
    groups = group_by(data, ['nome_marca', 'nome_modelo'])
    
    relatorios = []
    for (marca, modelo), rows in groups.items():
        if len(rows) < 2:
            continue
        
        # Sort by ano_modelo descending
        sorted_rows = sorted(rows, key=lambda x: x.get('ano_modelo', 0), reverse=True)
        
        preco_novo = sorted_rows[0].get('preco_limpo', 0) or 0
        preco_velho = sorted_rows[-1].get('preco_limpo', 0) or 0
        ano_novo = sorted_rows[0].get('ano_modelo', 0)
        ano_velho = sorted_rows[-1].get('ano_modelo', 0)
        anos_vida = (ano_novo - ano_velho) or 1
        
        queda_total_pct = ((preco_novo - preco_velho) / preco_novo * 100) if preco_novo else 0
        queda_anual_media = (preco_novo - preco_velho) / anos_vida if anos_vida else 0
        
        relatorios.append({
            'nome_marca': marca,
            'nome_modelo': modelo,
            'ano_modelo_novo': ano_novo,
            'preco_limpo_novo': preco_novo,
            'preco_limpo_velho': preco_velho,
            'anos_de_vida': anos_vida,
            'queda_total_pct': queda_total_pct,
            'queda_anual_media': queda_anual_media,
        })
    
    return relatorios


df_relatorios_motos = gerar_relatorios_vip(df_motos)
df_relatorios_carros = gerar_relatorios_vip(df_carros)
df_relatorios_caminhoes = gerar_relatorios_vip(df_caminhoes)

def get_relatorios_by_type(tipo: str):
    if tipo == 'CAR': return df_relatorios_carros
    if tipo == 'TRUCK': return df_relatorios_caminhoes
    return df_relatorios_motos


def gerar_relatorios_vip(data: List[Dict]) -> List[Dict]:
    """Generate VIP reports without pandas."""
    # Group by marca + modelo
    groups = group_by(data, ['nome_marca', 'nome_modelo'])
    
    relatorios = []
    for (marca, modelo), rows in groups.items():
        if len(rows) < 2:
            continue
        
        # Sort by ano_modelo descending
        sorted_rows = sorted(rows, key=lambda x: x.get('ano_modelo', 0), reverse=True)
        
        mais_novo = sorted_rows[0]
        mais_velho = sorted_rows[-1]
        
        ano_novo = mais_novo.get('ano_modelo', 0)
        ano_velho = mais_velho.get('ano_modelo', 0)
        
        if ano_novo <= ano_velho:
            continue
        
        preco_novo = mais_novo.get('preco_limpo', 0)
        preco_velho = mais_velho.get('preco_limpo', 0)
        
        anos_vida = ano_novo - ano_velho
        queda_total_pct = ((preco_novo - preco_velho) / preco_novo * 100) if preco_novo else 0
        queda_anual_media = queda_total_pct / anos_vida if anos_vida else 0
        
        relatorios.append({
            'nome_marca': marca,
            'nome_modelo': modelo,
            'ano_modelo_novo': ano_novo,
            'ano_modelo_velho': ano_velho,
            'preco_limpo_novo': preco_novo,
            'preco_limpo_velho': preco_velho,
            'anos_de_vida': anos_vida,
            'queda_total_pct': queda_total_pct,
            'queda_anual_media': queda_anual_media,
        })
    
    return relatorios


df_relatorios = gerar_relatorios_vip(df_motos)

# ---------------------------------------------------------------------------
# Session State (in-memory, per-isolate)
# ---------------------------------------------------------------------------
class SessionState:
    def __init__(self):
        self.consultas_feitas = 0
        self.usuario_vip = False


sessions: dict[str, SessionState] = {}


def get_or_create_session(request: Request) -> tuple[str, SessionState]:
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        session_id = secrets.token_hex(16)
    if session_id not in sessions:
        sessions[session_id] = SessionState()
    session = sessions[session_id]
    
    # ── Restore VIP from signed cookie (survives isolate resets) ──
    if not session.usuario_vip:
        vip_token = request.cookies.get("vip_token", "")
        if vip_token and auth_vip.verify_vip_token(vip_token):
            session.usuario_vip = True
    
    return session_id, session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def definir_cor_risco(pct: float) -> str:
    # pct > 0 significa desvalorização (perda)
    # pct < 0 significa lucro financeiro
    if pct < 0:
        return '#008000'  # Verde (Lucro)
    elif pct <= 8:
        return '#FFB347'  # Laranja (Desvalorização normal até 8%)
    elif pct <= 15:
        return '#E50000'  # Vermelho (Desvalorização alta, 8% a 15%)
    else:
        return '#8B0000'  # Vermelho Escuro (Desvalorização abusiva > 15%)


def texto_dinamico_hover(valor_reais: float) -> str:
    # valor_reais > 0 means depreciation (loss)
    # valor_reais < 0 means appreciation (gain/profit)
    if valor_reais < 0:
        return f"Ganhou: R$ {abs(valor_reais):,.2f}"
    else:
        return f"Perdeu: R$ {valor_reais:,.2f}"


def formatar_impacto_anual(q: float) -> str:
    if q < 0:
        return f"+R$ {abs(q):,.2f}/ano (LUCRO)"
    else:
        return f"-R$ {q:,.2f}/ano"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    session_id, session = get_or_create_session(request)

    lista_marcas = sorted(unique_values(df_motos, 'nome_marca'))
    restantes = max(0, 2 - session.consultas_feitas)

    response = templates.TemplateResponse("index.html", {
        "request": request,
        "marcas": lista_marcas,
        "usuario_vip": session.usuario_vip,
        "consultas_feitas": session.consultas_feitas,
        "restantes": restantes,
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400 * 7)
    return response


@app.post("/api/login")
async def login(request: Request, credential: str = Form(...)):
    session_id, session = get_or_create_session(request)

    google_ok = False
    email = ""
    valido = False

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}")
            resp.raise_for_status()
            user_info = resp.json()
            email = user_info.get("email", "").lower().strip()
            google_ok = bool(email)

            # Valida se o email retornado pelo Google está na Planilha VIP
            valido = await auth_vip.validar_email_vip_async(email)

    except Exception as e:
        print(f"Login validation error: {e}")

    session.usuario_vip = valido
    response = JSONResponse({
        "google_ok": google_ok,
        "vip": valido,
        "email": email if google_ok else "",
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400 * 7)
    if valido:
        # Set signed VIP token cookie so status survives isolate resets
        vip_token = auth_vip.create_vip_token(email)
        response.set_cookie(key="vip_token", value=vip_token, httponly=True, max_age=86400 * 30, samesite="strict")
    return response


@app.post("/api/logout")
async def logout(request: Request):
    session_id, session = get_or_create_session(request)
    session.usuario_vip = False
    session.consultas_feitas = 0 
    
    response = JSONResponse({"status": "ok"})
    response.delete_cookie("vip_token")
    """
    Also removing JS driven cookie, but to be sure we clear the server-side token properly
    """
    return response


@app.post("/api/analyze")
async def analyze(request: Request, marca: str = Form(...), modelo: str = Form(...), tipo: str = Form("MOTORCYCLE")):
    session_id, session = get_or_create_session(request)
    
    if session.consultas_feitas >= 2 and not session.usuario_vip:
        raise HTTPException(status_code=403, detail="Limite gratuito atingido")
    
    session.consultas_feitas += 1
    
    # Filter data based on type
    df_data = get_df_by_type(tipo)
    df_filtrado = filter_rows(df_data, nome_marca=marca)
    df_final = filter_rows(df_filtrado, nome_modelo=modelo)
    df_final = sort_rows(df_final, 'ano_modelo', reverse=True)
    
    if not df_final:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    # Build table data
    tabela_data = []
    for idx, row in enumerate(df_final):
        valor = row.get('preco_limpo', 0)
        tabela_data.append({
            "ano": row.get('ano_modelo'),
            "valor": f"R$ {valor:,.2f}"
        })
    
    # Calculate depreciation
    grafico_data = calc_desvalorizacao(df_final)
    
    # Add colors and labels
    for item in grafico_data:
        item['cor_barra'] = definir_cor_risco(item['perda_pct'])
        # perda_pct positive = depreciation (loss)
        if item['perda_pct'] < 0:
            item['texto_exibicao'] = f"+{abs(item['perda_pct']):.1f}% (LUCRO)"
        else:
            item['texto_exibicao'] = f"-{item['perda_pct']:.1f}%"
        item['hover_exibicao'] = texto_dinamico_hover(item['perda_reais'])
        item['periodo'] = f"{item['ano_modelo']} -> {item['ano_anterior']}"
    

    
    # Build chart data for frontend (raw data, not Plotly JSON)
    chart_data = {
        "periodos": [item['periodo'] for item in grafico_data],
        # Negate perda_reais so loss points DOWN (y < 0) and profit points UP (y > 0)
        "valores": [-item['perda_reais'] for item in grafico_data],
        "cores": [item['cor_barra'] for item in grafico_data],
        "textos": [item['texto_exibicao'] for item in grafico_data],
        "hovers": [item['hover_exibicao'] for item in grafico_data],
    }
    
    # ── Polynomial Regression (grau 2) ─────────────────────────────────────
    # y = a₀ + a₁·xc + a₂·xc²  (xc = ano - média)
    # Captura a curva de desaceleração: moto perde valor rápido quando nova,
    # depois o ritmo de queda freia conforme fica mais velha.
    previsao_2026 = "N/A"
    previsibilidade = 0.0
    tendencia_reais = 0.0

    if len(df_final) >= 3:
        x_vals = [float(row.get('ano_modelo', 0)) for row in df_final]
        y_vals = [float(row.get('preco_limpo', 0)) for row in df_final]

        poly = polynomial_regression(x_vals, y_vals, degree=2)
        previsibilidade = poly['r2'] * 100
        tendencia_reais = poly['slope_at_mean']   # R$/ano no ano médio
        pred_raw = poly['predict'](2026.0)
        previsao_2026 = f"R$ {max(0.0, pred_raw):,.2f}"
    
    preco_mais_novo = df_final[0].get('preco_limpo', 0)
    preco_mais_velho = df_final[-1].get('preco_limpo', 0)
    desvalorizacao_total_pct = ((preco_mais_novo - preco_mais_velho) / preco_mais_novo * 100) if preco_mais_novo and len(df_final) > 1 else 0
    
    if desvalorizacao_total_pct < 0:
        desvalorizacao_str = f"+{abs(desvalorizacao_total_pct):.1f}% (LUCRO)"
    else:
        desvalorizacao_str = f"- {desvalorizacao_total_pct:.1f}%"

    response = JSONResponse({
        "marca": marca,
        "modelo": modelo,
        "preco_novo": f"R$ {preco_mais_novo:,.2f}",
        "preco_velho": f"R$ {preco_mais_velho:,.2f}",
        "desvalorizacao": desvalorizacao_str,
        "valorizou": desvalorizacao_total_pct < 0,  # True when vehicle appreciated in value
        "tabela": tabela_data,
        "grafico": chart_data,  # Raw data, not Plotly JSON
        "consultas_restantes": max(0, 2 - session.consultas_feitas),
        "vip_stats": {
            "previsao_2026": previsao_2026 if session.usuario_vip else "🔒 VIP Only",
            "previsibilidade": f"{previsibilidade:.1f}%" if session.usuario_vip else "🔒 VIP Only",
            "tendencia_anual": f"R$ {tendencia_reais:,.2f}/ano" if session.usuario_vip else "🔒 VIP Only",
        }
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400 * 7)
    return response


@app.get("/api/vip/reports")
async def get_vip_reports(request: Request, tipo: str = "MOTORCYCLE"):
    session_id, session = get_or_create_session(request)
    
    df_rels = get_relatorios_by_type(tipo)

    if not session.usuario_vip:
        # Show sample data based on type
        if tipo == 'CAR':
            degustacao = [
                {"ranking": "1º", "marca": "T*****", "modelo": "C******", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "2º", "marca": "V*********", "modelo": "G**", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "3º", "marca": "H****", "modelo": "C****", "preco": "R$ **.***,**", "perda": "🔒 VIP"}
            ]
        else:
            degustacao = [
                {"ranking": "1º", "marca": "H****", "modelo": "C* *** *****", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "2º", "marca": "Y*****", "modelo": "F***** ***", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "3º", "marca": "B**", "modelo": "G *** *", "preco": "R$ **.***,**", "perda": "🔒 VIP"}
            ]
        return {
            "vip": False,
            "degustacao": degustacao
        }

    def fmt_row_recentes(r, pos):
        q = r.get('queda_anual_media', 0)
        pct = r.get('queda_total_pct', 0)
        cor = definir_cor_risco(pct)
        return {
            "pos": pos,
            "marca": r.get('nome_marca', ''),
            "modelo": r.get('nome_modelo', ''),
            "ano": r.get('ano_modelo_novo', '-'),
            "preco": f"R$ {r.get('preco_limpo_novo', 0):,.2f}",
            "perda_ano": formatar_impacto_anual(q),
            "risco_cor": cor,
        }

    def fmt_row_baratas(r, pos):
        q = r.get('queda_anual_media', 0)
        pct = r.get('queda_total_pct', 0)
        cor = definir_cor_risco(pct)
        return {
            "pos": pos,
            "marca": r.get('nome_marca', ''),
            "modelo": r.get('nome_modelo', ''),
            "preco": f"R$ {r.get('preco_limpo_novo', 0):,.2f}",
            "perda_ano": formatar_impacto_anual(q),
            "risco_cor": cor,
        }

    def fmt_row_bombas(r, pos):
        q = r.get('queda_anual_media', 0)
        return {
            "pos": pos,
            "marca": r.get('nome_marca', ''),
            "modelo": r.get('nome_modelo', ''),
            "ano": r.get('ano_modelo_novo', '-'),
            "preco": f"R$ {r.get('preco_limpo_novo', 0):,.2f}",
            "perda_ano": formatar_impacto_anual(q),
            "risco_cor": "#E50000",
        }

    df_relatorios = get_relatorios_by_type(tipo)
    
    recentes = [r for r in df_relatorios if r.get('ano_modelo_novo', 0) >= 2024]
    recentes = sorted(recentes, key=lambda x: x.get('queda_anual_media', 0))[:10]

    bar_limit = 50000 if tipo == 'CAR' else 15000
    baratas = [
        r for r in df_relatorios
        if r.get('preco_limpo_novo', 0) <= bar_limit and r.get('ano_modelo_novo', 0) >= 2018
    ]
    baratas = sorted(baratas, key=lambda x: x.get('queda_anual_media', 0))[:10]

    # Limite financeiro para "carros/motos normais", evita que Ferraris entrem na lista de "bombas"
    if tipo == 'CAR':
        bomba_limit = 100000
    elif tipo == 'TRUCK':
        bomba_limit = 300000
    else:
        bomba_limit = 40000

    # Muro da vergonha - apenas veículos "normais" que REALMENTE perdem valor
    bombas = [
        r for r in df_relatorios 
        if r.get('ano_modelo_novo', 0) >= 2022 
        and r.get('queda_anual_media', 0) > 0
        and r.get('preco_limpo_novo', 0) <= bomba_limit
    ]
    bombas = sorted(bombas, key=lambda x: x.get('queda_anual_media', 0), reverse=True)[:10]

    return {
        "vip": True,
        "recentes": [fmt_row_recentes(r, i+1) for i, r in enumerate(recentes)],
        "baratas": [fmt_row_baratas(r, i+1) for i, r in enumerate(baratas)],
        "bombas": [fmt_row_bombas(r, i+1) for i, r in enumerate(bombas)],
    }


@app.post("/api/compare")
async def compare(
    request: Request,
    marca_a: str = Form(...),
    modelo_a: str = Form(...),
    marca_b: str = Form(...),
    modelo_b: str = Form(...),
    tipo: str = Form("MOTORCYCLE")
):
    session_id, session = get_or_create_session(request)
    
    if not session.usuario_vip:
        raise HTTPException(status_code=403, detail="Comparador exclusivo para VIP")
    
    df_data = get_df_by_type(tipo)
    df_a = filter_rows(df_data, nome_marca=marca_a, nome_modelo=modelo_a)
    df_b = filter_rows(df_data, nome_marca=marca_b, nome_modelo=modelo_b)
    
    df_a = sort_rows(df_a, 'ano_modelo')
    df_b = sort_rows(df_b, 'ano_modelo')
    
    # Raw data for frontend chart
    chart_data = {
        "moto_a": {
            "nome": modelo_a,
            "dados": [(r.get('ano_modelo'), r.get('preco_limpo')) for r in df_a]
        },
        "moto_b": {
            "nome": modelo_b,
            "dados": [(r.get('ano_modelo'), r.get('preco_limpo')) for r in df_b]
        }
    }
    
    # Find veredito
    df_relatorios = get_relatorios_by_type(tipo)
    res_a = [r for r in df_relatorios if r.get('nome_marca') == marca_a and r.get('nome_modelo') == modelo_a]
    res_b = [r for r in df_relatorios if r.get('nome_marca') == marca_b and r.get('nome_modelo') == modelo_b]
    
    veredito = None
    if res_a and res_b:
        # Usa percentuais para comparar as desvalorizações e permitir o .toFixed(1) + '%' no frontend
        v1 = res_a[0].get('queda_total_pct', 0)
        v2 = res_b[0].get('queda_total_pct', 0)
        melhor = modelo_a if v1 < v2 else modelo_b
        diferenca = abs(v1 - v2)
        veredito = {"vencedor": melhor, "diferenca": diferenca}
    
    return {"grafico": chart_data, "veredito": veredito}


@app.get("/api/marcas/{tipo}")
async def get_marcas(tipo: str):
    df_data = get_df_by_type(tipo)
    lista_marcas = sorted(unique_values(df_data, 'nome_marca'))
    return {"marcas": lista_marcas}


@app.get("/api/modelos/{tipo}/{marca}")
async def get_modelos(tipo: str, marca: str):
    df_data = get_df_by_type(tipo)
    df_filtrado = filter_rows(df_data, nome_marca=marca)
    # Convert to string before sorting to avoid TypeError between int and str
    modelos = sorted(unique_values(df_filtrado, 'nome_modelo'), key=lambda x: str(x))
    return {"modelos": modelos}
