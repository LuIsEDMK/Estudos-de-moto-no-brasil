"""MotoExpert AI - FastAPI Backend."""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import secrets
from typing import List, Dict, Any

from .utils import (
    load_csv_data, simple_linear_regression, filter_rows, sort_rows,
    unique_values, calc_desvalorizacao, group_by
)
from .auth_vip import validar_senha

app = FastAPI(title="MotoExpert AI")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Session management
class SessionState:
    def __init__(self):
        self.consultas_feitas = 0
        self.usuario_vip = False


sessions: Dict[str, SessionState] = {}


def get_session(request: Request) -> tuple[str, SessionState]:
    """Get or create session."""
    session_id = request.cookies.get("session_id")
    
    if not session_id or session_id not in sessions:
        session_id = secrets.token_hex(16)
    
    if session_id not in sessions:
        sessions[session_id] = SessionState()
    
    return session_id, sessions[session_id]


# Load motorcycle data
def load_moto_data():
    with open("base_motos_VIP_mestre.csv", "r", encoding="utf-8") as f:
        content = f.read()
    data = load_csv_data(content)
    # Fix 2026 -> 2025
    for row in data:
        if row.get('ano_modelo') == '2026':
            row['ano_modelo'] = '2025'
    return data


def generate_vip_reports(data: List[Dict]) -> List[Dict]:
    """Generate VIP depreciation reports."""
    groups = group_by(data, ['nome_marca', 'nome_modelo'])
    reports = []
    
    for (marca, modelo), rows in groups.items():
        if len(rows) < 2:
            continue
        
        sorted_rows = sorted(rows, key=lambda x: int(x.get('ano_modelo', 0) or 0), reverse=True)
        novo = sorted_rows[0]
        velho = sorted_rows[-1]
        
        ano_novo = int(novo.get('ano_modelo', 0) or 0)
        ano_velho = int(velho.get('ano_modelo', 0) or 0)
        
        if ano_novo <= ano_velho:
            continue
        
        preco_novo = float(novo.get('preco_limpo', 0) or 0)
        preco_velho = float(velho.get('preco_limpo', 0) or 0)
        
        anos_vida = ano_novo - ano_velho
        queda_pct = ((preco_novo - preco_velho) / preco_novo * 100) if preco_novo else 0
        queda_anual = queda_pct / anos_vida if anos_vida else 0
        
        reports.append({
            'nome_marca': marca,
            'nome_modelo': modelo,
            'ano_modelo_novo': ano_novo,
            'ano_modelo_velho': ano_velho,
            'preco_limpo_novo': preco_novo,
            'preco_limpo_velho': preco_velho,
            'anos_de_vida': anos_vida,
            'queda_total_pct': queda_pct,
            'queda_anual_media': queda_anual,
        })
    
    return reports


# Initialize data
df_motos = load_moto_data()
df_relatorios = generate_vip_reports(df_motos)


# Helper functions
def get_risk_color(pct: float) -> str:
    if pct <= -15:
        return '#8B0000'
    elif pct <= -8:
        return '#E50000'
    elif pct < 0:
        return '#FFB347'
    return '#008000'


def format_hover(valor: float) -> str:
    if valor > 0:
        return f"Ganhou: R$ {valor:,.2f}"
    return f"Perdeu: R$ {abs(valor):,.2f}"


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    session_id, session = get_session(request)
    marcas = sorted(unique_values(df_motos, 'nome_marca'))
    restantes = max(0, 6 - session.consultas_feitas)
    
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "marcas": marcas,
        "usuario_vip": session.usuario_vip,
        "consultas_feitas": session.consultas_feitas,
        "restantes": restantes
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400*7)
    return response


@app.post("/api/login")
async def login(request: Request, senha: str = Form(...)):
    session_id, session = get_session(request)
    
    try:
        valido = validar_senha(senha)
    except Exception as e:
        print(f"Login error: {e}")
        valido = False
    
    session.usuario_vip = valido
    response = JSONResponse({"success": valido, "vip": valido})
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400*7)
    return response


@app.post("/api/analyze")
async def analyze(request: Request, marca: str = Form(...), modelo: str = Form(...)):
    session_id, session = get_session(request)
    
    # Check limit
    if session.consultas_feitas >= 6 and not session.usuario_vip:
        raise HTTPException(status_code=403, detail="Limite gratuito atingido")
    
    session.consultas_feitas += 1
    
    # Filter data
    filtrado = filter_rows(df_motos, nome_marca=marca, nome_modelo=modelo)
    filtrado = sort_rows(filtrado, 'ano_modelo', reverse=True)
    
    if not filtrado:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    # Build table
    tabela = []
    for idx, row in enumerate(filtrado):
        valor = float(row.get('preco_limpo', 0) or 0)
        tabela.append({
            "ano": row.get('ano_modelo'),
            "valor": f"R$ {valor:,.2f}" if session.usuario_vip or idx >= 3 else "🔒 Exclusivo VIP"
        })
    
    # Calculate depreciation
    grafico_data = calc_desvalorizacao(filtrado)
    
    for item in grafico_data:
        item['cor_barra'] = get_risk_color(item['perda_pct'])
        item['texto_exibicao'] = f"{item['perda_pct']:+.1f}%"
        item['hover_exibicao'] = format_hover(item['perda_reais'])
        item['periodo'] = f"{item['ano_modelo']} -> {item['ano_anterior']}"
    
    # Hide recent data for non-VIP
    if not session.usuario_vip and len(grafico_data) >= 2:
        media = sum(item['perda_reais'] for item in grafico_data) / len(grafico_data)
        for i in range(min(2, len(grafico_data))):
            grafico_data[i]['perda_reais'] = media
            grafico_data[i]['cor_barra'] = '#D3D3D3'
            grafico_data[i]['texto_exibicao'] = "🔒 VIP"
            grafico_data[i]['hover_exibicao'] = "🔒 Assine para ver"
    
    chart_data = {
        "periodos": [item['periodo'] for item in grafico_data],
        "valores": [item['perda_reais'] for item in grafico_data],
        "cores": [item['cor_barra'] for item in grafico_data],
        "textos": [item['texto_exibicao'] for item in grafico_data],
        "hovers": [item['hover_exibicao'] for item in grafico_data],
    }
    
    # Regression
    previsao_2026 = "N/A"
    previsibilidade = 0.0
    tendencia = 0.0
    
    if len(filtrado) >= 3:
        x_vals = [int(r.get('ano_modelo', 0) or 0) for r in filtrado]
        y_vals = [float(r.get('preco_limpo', 0) or 0) for r in filtrado]
        
        result = simple_linear_regression(x_vals, y_vals)
        previsibilidade = result['r2'] * 100
        tendencia = result['slope']
        pred = result['slope'] * 2026 + result['intercept']
        previsao_2026 = f"R$ {max(0, pred):,.2f}"
    
    preco_novo = float(filtrado[0].get('preco_limpo', 0) or 0)
    preco_velho = float(filtrado[-1].get('preco_limpo', 0) or 0)
    desval_pct = ((preco_novo - preco_velho) / preco_novo * 100) if preco_novo and len(filtrado) > 1 else 0
    
    response = JSONResponse({
        "marca": marca,
        "modelo": modelo,
        "preco_novo": f"R$ {preco_novo:,.2f}" if session.usuario_vip else "🔒 R$ *** (VIP)",
        "preco_velho": f"R$ {preco_velho:,.2f}",
        "desvalorizacao": f"- {desval_pct:.1f}%" if session.usuario_vip else "🔒 Oculto",
        "tabela": tabela,
        "grafico": chart_data,
        "consultas_restantes": max(0, 6 - session.consultas_feitas),
        "vip_stats": {
            "previsao_2026": previsao_2026 if session.usuario_vip else "🔒 VIP Only",
            "previsibilidade": f"{previsibilidade:.1f}%" if session.usuario_vip else "🔒 VIP Only",
            "tendencia_anual": f"R$ {tendencia:,.2f}" if session.usuario_vip else "🔒 VIP Only"
        }
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400*7)
    return response


@app.get("/api/vip/reports")
async def vip_reports(request: Request):
    session_id, session = get_session(request)
    
    if not session.usuario_vip:
        return {
            "vip": False,
            "degustacao": [
                {"ranking": "1º", "marca": "H****", "modelo": "C* *** *****", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "2º", "marca": "Y*****", "modelo": "F***** ***", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "3º", "marca": "B**", "modelo": "G *** *", "preco": "R$ **.***,**", "perda": "🔒 VIP"}
            ]
        }
    
    recentes = [r for r in df_relatorios if r.get('ano_modelo_novo', 0) >= 2024]
    recentes = sorted(recentes, key=lambda x: x.get('queda_anual_media', 0))[:10]
    
    baratas = [r for r in df_relatorios if r.get('preco_limpo_novo', 0) <= 15000 and r.get('ano_modelo_novo', 0) >= 2018]
    baratas = sorted(baratas, key=lambda x: x.get('queda_anual_media', 0))[:10]
    
    bombas = [r for r in df_relatorios if r.get('ano_modelo_novo', 0) >= 2022]
    bombas = sorted(bombas, key=lambda x: x.get('queda_anual_media', 0), reverse=True)[:10]
    
    return {"vip": True, "recentes": recentes, "baratas": baratas, "bombas": bombas}


@app.post("/api/compare")
async def compare(
    request: Request,
    marca_a: str = Form(...),
    modelo_a: str = Form(...),
    marca_b: str = Form(...),
    modelo_b: str = Form(...),
):
    session_id, session = get_session(request)
    
    if not session.usuario_vip:
        raise HTTPException(status_code=403, detail="Comparador exclusivo para VIP")
    
    df_a = sort_rows(filter_rows(df_motos, nome_marca=marca_a, nome_modelo=modelo_a), 'ano_modelo')
    df_b = sort_rows(filter_rows(df_motos, nome_marca=marca_b, nome_modelo=modelo_b), 'ano_modelo')
    
    chart_data = {
        "moto_a": {"nome": modelo_a, "dados": [(r.get('ano_modelo'), float(r.get('preco_limpo', 0) or 0)) for r in df_a]},
        "moto_b": {"nome": modelo_b, "dados": [(r.get('ano_modelo'), float(r.get('preco_limpo', 0) or 0)) for r in df_b]}
    }
    
    res_a = [r for r in df_relatorios if r.get('nome_marca') == marca_a and r.get('nome_modelo') == modelo_a]
    res_b = [r for r in df_relatorios if r.get('nome_marca') == marca_b and r.get('nome_modelo') == modelo_b]
    
    veredito = None
    if res_a and res_b:
        v1 = res_a[0].get('queda_anual_media', 0)
        v2 = res_b[0].get('queda_anual_media', 0)
        melhor = modelo_a if v1 < v2 else modelo_b
        diferenca = abs(v1 - v2)
        veredito = {"vencedor": melhor, "diferenca": diferenca}
    
    return {"grafico": chart_data, "veredito": veredito}


@app.get("/api/modelos/{marca}")
async def get_modelos(marca: str):
    filtrado = filter_rows(df_motos, nome_marca=marca)
    modelos = sorted(unique_values(filtrado, 'nome_modelo'))
    return {"modelos": modelos}
