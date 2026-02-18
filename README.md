# Cartas de Amor

Aplicação web mobile-first para criar, personalizar, pagar e compartilhar cartas românticas digitais.

## Stack
- Django 5.2 (LTS mais recente)
- Django Templates + Django Forms
- Pillow + qrcode
- Mercado Pago SDK + Stripe SDK
- python-decouple
- django-cleanup
- Tailwind CSS (pipeline de build disponível)
- Animate.css
- WOW.js

## Paletas de cores
- Base: `#111111`, `#333333`, `#555555`, `#777777`, `#999999`
- Emocional: `#f2c0c0`, `#e37979`, `#e76464`, `#b65e5e`, `#983434`

## Como rodar
1. Criar venv (opcional) e instalar dependências:

```bash
python -m pip install -r requirements.txt
```

2. Configurar variáveis de ambiente:

```bash
copy .env.example .env
```

3. Rodar migrações:

```bash
python manage.py migrate
```

4. Executar servidor:

```bash
python manage.py runserver
```

## Deploy na Render (pronto)
Este repositório já inclui configuração para Render:
- `render.yaml`
- `build.sh`
- suporte a `DATABASE_URL` (PostgreSQL)
- Gunicorn + WhiteNoise para produção

### Opção A: Blueprint (recomendado)
1. Suba o código para GitHub.
2. Na Render, clique em **New +** -> **Blueprint**.
3. Selecione o repositório e confirme.
4. A Render criará:
   - Web Service (`cartas-de-amor`)
   - Banco PostgreSQL (`cartas-de-amor-db`)

### Opção B: Web Service manual
1. Em `render.com/web/new`, conecte o repositório.
2. Configure:
   - Root Directory: `cartas_de_amor`
   - Build Command: `bash build.sh`
   - Start Command: `gunicorn config.wsgi:application`
   - Health Check Path: `/health/`
3. Crie um PostgreSQL na Render e adicione `DATABASE_URL` nas env vars.

### Variáveis de ambiente mínimas (produção)
- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=seu-app.onrender.com`
- `DATABASE_URL` (PostgreSQL da Render)
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`

### Uploads de fotos em produção
Atualmente as fotos vão para `media/`. Em produção, o ideal é:
- usar **Persistent Disk** na Render, ou
- mover para storage externo (S3/Cloudinary).

## Tailwind
O projeto já funciona com Tailwind via CDN e também inclui pipeline de build local.

Instalar dependências de frontend:

```bash
npm install
```

Gerar CSS:

```bash
npm run build:css
```

Modo watch:

```bash
npm run watch:css
```

Arquivo de entrada: `src/input.css`  
Saída: `static/css/output.css`

## Fluxo principal
1. Home (`/`)
2. Wizard mobile-first (`/criar/etapa/<n>/`)
3. Preview (`/preview/<uuid>/`)
4. Pagamento (`/pagamento/<uuid>/`)
5. Carta pública (`/carta/<uuid>/`)
6. Unlock por senha (`/carta/<uuid>/unlock/`)
7. QR da carta (`/carta/<uuid>/qr/`)

## Pagamentos
Valor fixo: **R$ 3,99** (pagamento único)

### PIX
- Chave: `11948587422`
- Tipo: telefone
- Geração de payload + QR Code
- Botão de copiar código PIX
- Endpoint de simulação para desenvolvimento: `POST /pagamento/<uuid>/simular/pix/`

### Mercado Pago
- Criação de preferência via SDK quando `MERCADO_PAGO_ACCESS_TOKEN` está configurado
- Fallback de simulação quando token não está configurado
- Webhook: `POST /webhooks/mercadopago/`

### Stripe
- Checkout Session (pagamento único) quando `STRIPE_SECRET_KEY` está configurado
- Fallback de simulação sem chave
- Webhook: `POST /webhooks/stripe/`

## Privacidade
- Carta pode ser protegida por senha
- Senha armazenada com hash (`make_password`)
- Desbloqueio via tela dedicada

## Segurança
- CSRF ativo em todos os formulários
- IDs UUID imprevisíveis
- Upload validado (quantidade e tamanho)
- Webhooks com validação de assinatura quando segredo está configurado

## Estrutura de app
- `letters/models.py`: `LoveLetter`, `LovePhoto`, `PaymentRecord`
- `letters/forms.py`: formulários por etapa + upload + senha
- `letters/views.py`: wizard, preview, pagamento, webhooks, unlock e compartilhamento
- `letters/utils.py`: QR, payload PIX e parser de música
- `templates/letters/`: todas as telas mobile-first

## Observações
- Em desenvolvimento, o botão de simulação permite concluir pagamentos sem gateways reais.
- Para produção, configure HTTPS, segredos reais e URLs públicas de webhook.
