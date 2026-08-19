# Samantah 💬

Um chatbot pessoal com interface de chat no navegador, com respostas geradas pela
API da Anthropic (Claude).

## O que tem aqui

- `app.py` — backend em Flask que serve a página e fala com a API da Anthropic.
- `templates/index.html`, `static/style.css`, `static/script.js` — interface de chat.
- `.env.example` — modelo do arquivo de configuração com sua chave de API.
- `requirements.txt` — dependências Python.

## Passo a passo para rodar

### 1. Tenha o Python instalado

Você precisa do Python 3.9 ou mais recente. Para checar, abra o terminal e rode:

```bash
python3 --version
```

### 2. Instale as dependências

Dentro da pasta do projeto:

```bash
python3 -m venv venv
source venv/bin/activate        # no Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Consiga sua chave da API da Anthropic

1. Acesse https://console.anthropic.com/ e crie uma conta (ou faça login).
2. Vá em **Settings → API Keys** e clique em **Create Key**.
3. Copie a chave gerada (começa com `sk-ant-...`). Guarde-a com cuidado — ela não
   é mostrada de novo depois.
4. A Anthropic cobra por uso da API (não é o mesmo plano do Claude.ai). Você vai
   precisar adicionar um método de pagamento ou créditos na sua conta de
   desenvolvedor para a chave funcionar.

### 4. Configure a chave no projeto

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Abra o `.env` em um editor de texto e cole sua chave na linha:

```
ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui
```

**Nunca compartilhe esse arquivo `.env` nem o suba para o GitHub** — ele já está
listado no `.gitignore` para evitar isso.

### 5. Rode o servidor

```bash
python3 app.py
```

Você vai ver algo como `Running on http://127.0.0.1:5000`. Abra esse endereço no
navegador e comece a conversar com a Samantah.

## Personalizando a Samantah

A personalidade dela está definida na variável `SYSTEM_PROMPT`, no início do
arquivo `app.py`. Edite esse texto para mudar o tom, o idioma padrão, ou dar a
ela mais contexto sobre você.

Para trocar o modelo usado (por exemplo, para um mais rápido/barato ou mais
avançado), altere `SAMANTAH_MODEL` no `.env`.

## Limitações desta versão

- O histórico da conversa fica **em memória** — se você reiniciar o servidor, a
  conversa recomeça do zero. Não há banco de dados.
- É pensado para uso local/pessoal (uma pessoa por vez). Para publicar na
  internet para várias pessoas usarem, seria necessário adicionar autenticação,
  um banco de dados para o histórico, e hospedar em um serviço como Render,
  Railway ou Fly.io.

## Próximos passos possíveis

- Guardar o histórico em um banco de dados (ex: SQLite) para não perder as
  conversas ao reiniciar.
- Adicionar memória de longo prazo (a Samantah lembrar de você entre sessões).
- Dar a ela uma voz, usando síntese de voz (text-to-speech) no navegador.
- Publicar o app em um serviço de hospedagem para acessar de qualquer lugar.
