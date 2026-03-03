"""
Lightweight FastAPI app for local development.
Uses standard library + FastAPI instead of pandas/plotly/scikit-learn.
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import secrets
from typing import Optional, List, Dict, Any

# Import lightweight utils
from app.utils import (
    load_csv_data, simple_linear_regression, filter_rows, sort_rows,
    unique_values, calc_desvalorizacao, group_by
)
import auth_vip

app = FastAPI(title="MotoExpert AI")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- Session State Simulation (In-Memory) ---
class SessionState:
    def __init__(self):
        self.consultas_feitas = 0
        self.usuario_vip = False


sessions = {}


def get_or_create_session(request: Request) -> tuple[str, SessionState]:
    """Get existing session or create new one with unique ID."""
    session_id = request.cookies.get("session_id")
    
    if not session_id or session_id not in sessions:
        session_id = secrets.token_hex(16)
    
    if session_id not in sessions:
        sessions[session_id] = SessionState()
    
    return session_id, sessions[session_id]


# --- Data Loading ---
def load_data():
    with open("base_motos_VIP_mestre.csv", "r", encoding="utf-8") as f:
        content = f.read()
    data = load_csv_data(content)
    # Fix 2026 -> 2025
    for row in data:
        if row.get('ano_modelo') == 2026:
            row['ano_modelo'] = 2025
    return data


def gerar_relatorios_vip(data: List[Dict]) -> List[Dict]:
    """Generate VIP reports without pandas."""
    groups = group_by(data, ['nome_marca', 'nome_modelo'])
    
    relatorios = []
    for (marca, modelo), rows in groups.items():
        if len(rows) < 2:
            continue
        
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


# Load data at startup
df_motos = load_data()
df_relatorios = gerar_relatorios_vip(df_motos)


# --- Pydantic Models ---
class AnalysisRequest(BaseModel):
    marca: str
    modelo: str


class CompareRequest(BaseModel):
    marca_a: str
    modelo_a: str
    marca_b: str
    modelo_b: str


class LoginRequest(BaseModel):
    senha: str


# --- Helper Functions ---
def definir_cor_risco(pct):
    if pct <= -15:
        return '#8B0000'
    elif pct <= -8:
        return '#E50000'
    elif pct < 0:
        return '#FFB347'
    else:
        return '#008000'


def texto_dinamico_hover(valor_reais):
    if valor_reais > 0:
        return f"Ganhou: R$ {valor_reais:,.2f}"
    else:
        return f"Perdeu: R$ {abs(valor_reais):,.2f}"


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    session_id, session = get_or_create_session(request)
    
    lista_marcas = sorted(unique_values(df_motos, 'nome_marca'))
    restantes = max(0, 6 - session.consultas_feitas)
    
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "marcas": lista_marcas,
        "usuario_vip": session.usuario_vip,
        "consultas_feitas": session.consultas_feitas,
        "restantes": restantes
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400*7)
    return response


@app.post("/api/login")
async def login(request: Request, senha: str = Form(...)):
    session_id, session = get_or_create_session(request)
    
    try:
        valido = auth_vip.validar_senha(senha)
    except Exception as e:
        print(f"Login validation error: {e}")
        valido = False

    session.usuario_vip = valido
    response = JSONResponse({"success": valido, "vip": valido})
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400*7)
    return response


@app.post("/api/analyze")
async def analyze(request: Request, marca: str = Form(...), modelo: str = Form(...)):
    session_id, session = get_or_create_session(request)
    
    # Check limit
    if session.consultas_feitas >= 6 and not session.usuario_vip:
        raise HTTPException(status_code=403, detail="Limite gratuito atingido")
    
    session.consultas_feitas += 1
    
    # Filter data
    df_filtrado = filter_rows(df_motos, nome_marca=marca)
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
            "valor": f"R$ {valor:,.2f}" if session.usuario_vip or idx >= 3 else "🔒 Exclusivo VIP"
        })
    
    # Calculate depreciation
    grafico_data = calc_desvalorizacao(df_final)
    
    # Add colors and labels
    for item in grafico_data:
        item['cor_barra'] = definir_cor_risco(item['perda_pct'])
        item['texto_exibicao'] = f"+{item['perda_pct']:.1f}%" if item['perda_pct'] > 0 else f"{item['perda_pct']:.1f}%"
        item['hover_exibicao'] = texto_dinamico_hover(item['perda_reais'])
        item['periodo'] = f"{item['ano_modelo']} -> {item['ano_anterior']}"
    
    # Hide recent data for non-VIP
    if not session.usuario_vip and len(grafico_data) >= 2:
        media_falsa = sum(item['perda_reais'] for item in grafico_data) / len(grafico_data)
        for i in range(min(2, len(grafico_data))):
            grafico_data[i]['perda_reais'] = media_falsa
            grafico_data[i]['cor_barra'] = '#D3D3D3'
            grafico_data[i]['texto_exibicao'] = "🔒 VIP"
            grafico_data[i]['hover_exibicao'] = "🔒 Assine para ver"
    
    # Build chart data for frontend
    chart_data = {
        "periodos": [item['periodo'] for item in grafico_data],
        "valores": [item['perda_reais'] for item in grafico_data],
        "cores": [item['cor_barra'] for item in grafico_data],
        "textos": [item['texto_exibicao'] for item in grafico_data],
        "hovers": [item['hover_exibicao'] for item in grafico_data],
    }
    
    # Regression Analysis
    previsao_2026 = "N/A"
    previsibilidade = 0.0
    tendencia_reais = 0.0
    
    if len(df_final) >= 3:
        x_vals = [row.get('ano_modelo', 0) for row in df_final]
        y_vals = [row.get('preco_limpo', 0) for row in df_final]
        
        result = simple_linear_regression(x_vals, y_vals)
        previsibilidade = result['r2'] * 100
        tendencia_reais = result['slope']
        pred = result['slope'] * 2026 + result['intercept']
        previsao_2026 = f"R$ {max(0, pred):,.2f}"
    
    preco_mais_novo = df_final[0].get('preco_limpo', 0)
    preco_mais_velho = df_final[-1].get('preco_limpo', 0)
    desvalorizacao_total_pct = ((preco_mais_novo - preco_mais_velho) / preco_mais_novo * 100) if preco_mais_novo and len(df_final) > 1 else 0
    
    response = JSONResponse({
        "marca": marca,
        "modelo": modelo,
        "preco_novo": f"R$ {preco_mais_novo:,.2f}" if session.usuario_vip else "🔒 R$ *** (VIP)",
        "preco_velho": f"R$ {preco_mais_velho:,.2f}",
        "desvalorizacao": f"- {desvalorizacao_total_pct:.1f}%" if session.usuario_vip else "🔒 Oculto",
        "tabela": tabela_data,
        "grafico": chart_data,
        "consultas_restantes": max(0, 6 - session.consultas_feitas),
        "vip_stats": {
            "previsao_2026": previsao_2026 if session.usuario_vip else "🔒 VIP Only",
            "previsibilidade": f"{previsibilidade:.1f}%" if session.usuario_vip else "🔒 VIP Only",
            "tendencia_anual": f"R$ {tendencia_reais:,.2f}" if session.usuario_vip else "🔒 VIP Only"
        }
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400*7)
    return response


@app.get("/api/vip/reports")
async def get_vip_reports(request: Request):
    session_id, session = get_or_create_session(request)
    
    if not session.usuario_vip:
        # Return teaser data
        return {
            "vip": False,
            "degustacao": [
                {"ranking": "1º", "marca": "H****", "modelo": "C* *** *****", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "2º", "marca": "Y*****", "modelo": "F***** ***", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "3º", "marca": "B**", "modelo": "G *** *", "preco": "R$ **.***,**", "perda": "🔒 VIP"}
            ]
        }
    
    # Top 10 moedas fortes
    recentes = [r for r in df_relatorios if r.get('ano_modelo_novo', 0) >= 2024]
    recentes = sorted(recentes, key=lambda x: x.get('queda_anual_media', 0))[:10]
    
    # Guerreiras baratas
    baratas = [
        r for r in df_relatorios 
        if r.get('preco_limpo_novo', 0) <= 15000 and r.get('ano_modelo_novo', 0) >= 2018
    ]
    baratas = sorted(baratas, key=lambda x: x.get('queda_anual_media', 0))[:10]
    
    # Muro da vergonha
    bombas = [r for r in df_relatorios if r.get('ano_modelo_novo', 0) >= 2022]
    bombas = sorted(bombas, key=lambda x: x.get('queda_anual_media', 0), reverse=True)[:10]
    
    return {
        "vip": True,
        "recentes": recentes,
        "baratas": baratas,
        "bombas": bombas
    }


@app.post("/api/compare")
async def compare(
    request: Request,
    marca_a: str = Form(...),
    modelo_a: str = Form(...),
    marca_b: str = Form(...),
    modelo_b: str = Form(...),
):
    session_id, session = get_or_create_session(request)
    
    if not session.usuario_vip:
        raise HTTPException(status_code=403, detail="Comparador exclusivo para VIP")
    
    df_a = filter_rows(df_motos, nome_marca=marca_a, nome_modelo=modelo_a)
    df_b = filter_rows(df_motos, nome_marca=marca_b, nome_modelo=modelo_b)

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
    df_filtrado = filter_rows(df_motos, nome_marca=marca)
    modelos = sorted(unique_values(df_filtrado, 'nome_modelo'))
    return {"modelos": modelos}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
