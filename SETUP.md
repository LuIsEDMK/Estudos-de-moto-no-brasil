# 🚀 Guia de Configuração - MotoExpert AI

## 1. Configurar Google Cloud (Service Account)

### Criar Service Account
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto (ou use existente)
3. Vá em **IAM & Admin** > **Service Accounts**
4. Clique **Create Service Account**
5. Dê um nome (ex: "motoexpert-sheets")
6. Em **Roles**, adicione: `Google Sheets API > Editor`

### Criar Chave JSON
1. Clique na service account criada
2. Vá em **Keys** > **Add Key** > **Create New Key**
3. Escolha **JSON** e faça o download
4. Anote o `client_email` e a `private_key`

### Compartilhar Planilha
1. Abra sua planilha Google Sheets
2. Clique em **Share**
3. Adicione o `client_email` da service account
4. Dê permissão de **Editor**

### Criar Aba "Assinantes"
Na planilha, crie uma aba chamada `Assinantes` com as colunas:
```
A: Email_Pagador
B: Plano
C: Status
D: Validade
E: Data_Pagamento
F: Vendedor_1
G: Vendedor_2
H: Vendedor_3
```

---

## 2. Configurar Google Identity Services (Login)

### Criar OAuth 2.0 Credentials
1. No [Google Cloud Console](https://console.cloud.google.com/)
2. Vá em **APIs & Services** > **Credentials**
3. Clique **Create Credentials** > **OAuth client ID**
4. Tipo: **Web application**
5. Nome: "MotoExpert Login"
6. **Authorized JavaScript origins**:
   - `http://localhost:5173` (dev)
   - `https://seudominio.com` (produção)
7. **Authorized redirect URIs**: (deixe vazio para popup)
8. Clique **Create** e anote o **Client ID**

---

## 3. Configurar Mercado Pago

### Criar Aplicação
1. Acesse [Mercado Pago Developers](https://www.mercadopago.com.br/developers)
2. Vá em **Suas Aplicações** > **Criar Aplicação**
3. Nome: "MotoExpert AI"
4. Tipo: **Checkout API**

### Credenciais
1. Na aplicação, vá em **Credenciais de Produção**
2. Copie o **Access Token**
3. (Opcional) Gere o **Webhook Secret** para validação

### Configurar Webhook
1. Em **Webhooks** > **Configurar notificações**
2. URL: `https://seudominio.com/api/webhooks/mercado-pago`
3. Events: `payment` (payment.created, payment.updated)

---

## 4. Configurar Cloudflare Workers

### Instalar Wrangler
```bash
npm install -g wrangler
```

### Login no Cloudflare
```bash
npx wrangler login
```

### Configurar Variáveis de Ambiente
```bash
# Google Sheets
npx wrangler secret put GOOGLE_SERVICE_ACCOUNT_EMAIL
# Cole o email da service account

npx wrangler secret put GOOGLE_PRIVATE_KEY
# Cole a chave privada (com \n para quebras de linha)

npx wrangler secret put GOOGLE_SPREADSHEET_ID
# Cole o ID da planilha (da URL: .../d/ID/edit)

# Google Login
npx wrangler secret put VITE_GOOGLE_CLIENT_ID
# Cole o Client ID do OAuth

# Mercado Pago
npx wrangler secret put MERCADO_PAGO_ACCESS_TOKEN
# Cole o Access Token

npx wrangler secret put MERCADO_PAGO_WEBHOOK_SECRET
# (Opcional) Para validar webhooks
```

---

## 5. Deploy

### Build e Deploy
```bash
# Instalar dependências
npm install

# Build
npm run build

# Deploy
npx wrangler deploy
```

---

## 6. Configurar Domínio (Opcional)

1. No [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Selecione seu Worker
3. Vá em **Triggers** > **Custom Domains**
4. Adicione seu domínio

---

## 📋 Resumo das Variáveis

| Variável | Origem | Obrigatório |
|----------|--------|-------------|
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | Google Cloud IAM | ✅ |
| `GOOGLE_PRIVATE_KEY` | Google Cloud IAM | ✅ |
| `GOOGLE_SPREADSHEET_ID` | URL da planilha | ✅ |
| `VITE_GOOGLE_CLIENT_ID` | Google Cloud OAuth | ✅ |
| `MERCADO_PAGO_ACCESS_TOKEN` | Dashboard MP | ✅ |
| `MERCADO_PAGO_WEBHOOK_SECRET` | Dashboard MP | ❌ |

---

## 🧪 Testar Localmente

```bash
# Criar .env.local
VITE_GOOGLE_CLIENT_ID=seu_client_id

# Rodar dev server
npm run dev
```

Acesse: http://localhost:5173

---

## ❌ Troubleshooting

### "Access denied" no Google Sheets
- Verifique se compartilhou a planilha com o `client_email`
- Confirme que a service account tem papel de Editor

### Webhook não funciona
- Verifique se a URL está acessível publicamente
- Confirme o Access Token do Mercado Pago
- Teste com `npm run preview` e ngrok

### Login Google não aparece
- Verifique se o Client ID está correto
- Confirme se o domínio está nos "Authorized origins"
- Abra o console do navegador (F12) para ver erros
