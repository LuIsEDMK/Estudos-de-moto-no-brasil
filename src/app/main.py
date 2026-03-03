from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.utils
import json
import secrets
from io import StringIO
from typing import Optional

from . import auth_vip
from .data_bundle import CSV_DATA

app = FastAPI(title="MotoExpert AI")

# ---------------------------------------------------------------------------
# Templates — loaded from the bundled package (works in Cloudflare Workers)
# ---------------------------------------------------------------------------
# Jinja2's PackageLoader reads templates that are bundled *inside* the Python
# package (src/app/templates/), so they travel with the Worker deployment.
from jinja2 import PackageLoader, Environment, select_autoescape

jinja_env = Environment(
    loader=PackageLoader("app", "templates"),
    autoescape=select_autoescape(["html"]),
)

class _J2Templates:
    """Thin wrapper so we can call .TemplateResponse() like FastAPI's Jinja2Templates."""
    def __init__(self, env: Environment):
        self.env = env

    def TemplateResponse(self, name: str, context: dict):
        tmpl = self.env.get_template(name)
        html = tmpl.render(**context)
        return HTMLResponse(content=html)

templates = _J2Templates(jinja_env)

# ---------------------------------------------------------------------------
# Data — loaded from the bundled CSV inside the package
# ---------------------------------------------------------------------------
def _load_bundled_csv() -> pd.DataFrame:
    """Load CSV from the bundled Python data module."""
    df = pd.read_csv(StringIO(CSV_DATA))
    df.loc[df['ano_modelo'] == 2026, 'ano_modelo'] = 2025
    return df


df_motos = _load_bundled_csv()


def gerar_relatorios_vip(df):
    df_ordenado = df.sort_values(['nome_marca', 'nome_modelo', 'ano_modelo'], ascending=[True, True, False])
    modelos_recentes = df_ordenado.groupby(['nome_marca', 'nome_modelo']).first().reset_index()
    modelos_antigos = df_ordenado.groupby(['nome_marca', 'nome_modelo']).last().reset_index()

    relatorio = pd.merge(modelos_recentes, modelos_antigos, on=['nome_marca', 'nome_modelo'],
                         suffixes=('_novo', '_velho'))
    relatorio = relatorio[relatorio['ano_modelo_novo'] > relatorio['ano_modelo_velho']].copy()

    relatorio['anos_de_vida'] = relatorio['ano_modelo_novo'] - relatorio['ano_modelo_velho']
    relatorio['queda_total_pct'] = ((relatorio['preco_limpo_novo'] - relatorio['preco_limpo_velho']) / relatorio[
        'preco_limpo_novo']) * 100
    relatorio['queda_anual_media'] = relatorio['queda_total_pct'] / relatorio['anos_de_vida']

    return relatorio


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
    return session_id, sessions[session_id]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def plot_to_json(fig):
    return json.dumps(fig.to_plotly_json(), cls=plotly.utils.PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    session_id, session = get_or_create_session(request)

    lista_marcas = sorted(df_motos['nome_marca'].unique())
    restantes = max(0, 6 - session.consultas_feitas)

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
async def login(request: Request, senha: str = Form(...)):
    session_id, session = get_or_create_session(request)

    try:
        valido = auth_vip.validar_senha(senha)
    except Exception as e:
        print(f"Login validation error: {e}")
        valido = False

    session.usuario_vip = valido
    response = JSONResponse({"success": valido, "vip": valido})
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400 * 7)
    return response


@app.post("/api/analyze")
async def analyze(request: Request, marca: str = Form(...), modelo: str = Form(...)):
    session_id, session = get_or_create_session(request)

    if session.consultas_feitas >= 6 and not session.usuario_vip:
        raise HTTPException(status_code=403, detail="Limite gratuito atingido")

    session.consultas_feitas += 1

    df_filtrado = df_motos[df_motos['nome_marca'] == marca]
    df_final = df_filtrado[df_filtrado['nome_modelo'] == modelo].copy()
    df_final = df_final.sort_values(by='ano_modelo', ascending=False).reset_index(drop=True)

    df_final['perda_reais'] = df_final['preco_limpo'].diff(-1) * -1
    df_final['perda_pct'] = (df_final['perda_reais'] / df_final['preco_limpo'].shift(-1)) * 100

    preco_mais_novo = df_final['preco_limpo'].iloc[0]
    preco_mais_velho = df_final['preco_limpo'].iloc[-1]
    desvalorizacao_total_pct = ((preco_mais_novo - preco_mais_velho) / preco_mais_novo) * 100 if len(df_final) > 1 else 0

    tabela_data = []
    for idx, (_, row) in enumerate(df_final[['ano_modelo', 'preco_limpo']].iterrows()):
        tabela_data.append({
            "ano": int(row['ano_modelo']),
            "valor": f"R$ {row['preco_limpo']:,.2f}" if session.usuario_vip or idx >= 3 else "🔒 Exclusivo VIP"
        })

    df_grafico = df_final.dropna(subset=['perda_reais']).copy()
    df_grafico['periodo'] = df_grafico['ano_modelo'].astype(str) + " -> " + (df_grafico['ano_modelo'] - 1).astype(str)
    df_grafico['cor_barra'] = df_grafico['perda_pct'].apply(definir_cor_risco)
    df_grafico['texto_exibicao'] = df_grafico['perda_pct'].apply(lambda x: f"+{x:.1f}%" if x > 0 else f"{x:.1f}%")
    df_grafico['hover_exibicao'] = df_grafico['perda_reais'].apply(texto_dinamico_hover)

    if not session.usuario_vip and len(df_grafico) >= 2:
        media_falsa = df_grafico['perda_reais'].mean()
        df_grafico.loc[0:1, 'perda_reais'] = media_falsa
        df_grafico.loc[0:1, 'cor_barra'] = '#D3D3D3'
        df_grafico.loc[0:1, 'texto_exibicao'] = "🔒 VIP"
        df_grafico.loc[0:1, 'hover_exibicao'] = "🔒 Assine para ver"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_grafico['periodo'].tolist(),
        y=df_grafico['perda_reais'].tolist(),
        marker_color=df_grafico['cor_barra'].tolist(),
        text=df_grafico['texto_exibicao'].tolist(),
        textposition='outside',
        hovertemplate="<b>Período:</b> %{x}<br><b>%{customdata}</b><extra></extra>",
        customdata=df_grafico['hover_exibicao'].tolist()
    ))
    fig.update_layout(
        xaxis_title="Passagem dos Anos",
        yaxis_title="Impacto Financeiro (R$)",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis={'type': 'category'},
        showlegend=False
    )

    chart_json = plot_to_json(fig)

    from sklearn.linear_model import LinearRegression
    X = df_final[['ano_modelo']].values
    y = df_final['preco_limpo'].values

    previsao_2026 = "N/A"
    previsibilidade = 0
    tendencia_reais = 0

    if len(df_final) >= 3:
        reg_model = LinearRegression()
        reg_model.fit(X, y)
        r2 = reg_model.score(X, y)
        previsibilidade = r2 * 100
        tendencia_reais = reg_model.coef_[0]
        pred = reg_model.predict([[2026]])[0]
        previsao_2026 = f"R$ {max(0, pred):,.2f}"

    response = JSONResponse({
        "marca": marca,
        "modelo": modelo,
        "preco_novo": f"R$ {preco_mais_novo:,.2f}" if session.usuario_vip else "🔒 R$ *** (VIP)",
        "preco_velho": f"R$ {preco_mais_velho:,.2f}",
        "desvalorizacao": f"- {desvalorizacao_total_pct:.1f}%" if session.usuario_vip else "🔒 Oculto",
        "tabela": tabela_data,
        "grafico": chart_json,
        "consultas_restantes": max(0, 6 - session.consultas_feitas),
        "vip_stats": {
            "previsao_2026": previsao_2026 if session.usuario_vip else "🔒 VIP Only",
            "previsibilidade": f"{previsibilidade:.1f}%" if session.usuario_vip else "🔒 VIP Only",
            "tendencia_anual": f"R$ {tendencia_reais:,.2f}" if session.usuario_vip else "🔒 VIP Only"
        }
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=86400 * 7)
    return response


@app.get("/api/vip/reports")
async def get_vip_reports(request: Request):
    session_id, session = get_or_create_session(request)

    if not session.usuario_vip:
        return {
            "vip": False,
            "degustacao": [
                {"ranking": "1º", "marca": "H****", "modelo": "C* *** *****", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "2º", "marca": "Y*****", "modelo": "F***** ***", "preco": "R$ **.***,**", "perda": "🔒 VIP"},
                {"ranking": "3º", "marca": "B**", "modelo": "G *** *", "preco": "R$ **.***,**", "perda": "🔒 VIP"}
            ]
        }

    motos_recentes = df_relatorios[df_relatorios['ano_modelo_novo'] >= 2024].sort_values(
        by='queda_anual_media').head(10)
    motos_baratas = df_relatorios[
        (df_relatorios['preco_limpo_novo'] <= 15000) &
        (df_relatorios['ano_modelo_novo'] >= 2018)
    ].sort_values(by='queda_anual_media').head(10)
    motos_bombas = df_relatorios[df_relatorios['ano_modelo_novo'] >= 2022].sort_values(
        by='queda_anual_media', ascending=False).head(10)

    return {
        "vip": True,
        "recentes": motos_recentes[['nome_marca', 'nome_modelo', 'ano_modelo_novo', 'preco_limpo_novo', 'queda_anual_media']].to_dict('records'),
        "baratas": motos_baratas[['nome_marca', 'nome_modelo', 'ano_modelo_novo', 'preco_limpo_novo', 'queda_anual_media']].to_dict('records'),
        "bombas": motos_bombas[['nome_marca', 'nome_modelo', 'ano_modelo_novo', 'preco_limpo_novo', 'queda_anual_media']].to_dict('records'),
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

    df_a = df_motos[(df_motos['nome_marca'] == marca_a) & (df_motos['nome_modelo'] == modelo_a)].copy()
    df_b = df_motos[(df_motos['nome_marca'] == marca_b) & (df_motos['nome_modelo'] == modelo_b)].copy()

    df_a = df_a.sort_values('ano_modelo')
    df_b = df_b.sort_values('ano_modelo')
    df_a['Moto'] = modelo_a
    df_b['Moto'] = modelo_b
    df_duel = pd.concat([df_a, df_b])

    fig_duel = px.line(df_duel, x='ano_modelo', y='preco_limpo', color='Moto',
                       markers=True,
                       title=f"Evolução de Preço: {modelo_a} vs {modelo_b}",
                       labels={'preco_limpo': 'Preço FIPE (R$)', 'ano_modelo': 'Ano'})
    fig_duel.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    chart_json = plot_to_json(fig_duel)

    res_a = df_relatorios[(df_relatorios['nome_marca'] == marca_a) & (df_relatorios['nome_modelo'] == modelo_a)]
    res_b = df_relatorios[(df_relatorios['nome_marca'] == marca_b) & (df_relatorios['nome_modelo'] == modelo_b)]

    veredito = None
    if not res_a.empty and not res_b.empty:
        v1 = res_a['queda_anual_media'].values[0]
        v2 = res_b['queda_anual_media'].values[0]
        melhor = modelo_a if v1 < v2 else modelo_b
        diferenca = abs(v1 - v2)
        veredito = {"vencedor": melhor, "diferenca": diferenca}

    return {"grafico": chart_json, "veredito": veredito}


@app.get("/api/modelos/{marca}")
async def get_modelos(marca: str):
    modelos = sorted(df_motos[df_motos['nome_marca'] == marca]['nome_modelo'].unique())
    return {"modelos": modelos}
