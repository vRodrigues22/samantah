# Samantah 💬

Um chatbot pessoal com interface de chat no navegador, com respostas geradas
gratuitamente pela API do Gemini (Google AI), memória permanente e voz.

## Funcionalidades

- **Conversa natural** com a Samantah, com personalidade calorosa e conversacional.
- **Gratuita**: usa a API do Gemini, que tem um nível gratuito sem precisar de
  cartão de crédito.
- **Memória permanente**: o histórico de conversa e o "perfil" que você escreve
  sobre si mesma ficam salvos em um banco SQLite — sobrevivem a reinícios do
  servidor.
- **Perfil / memória de longo prazo**: um painel (ícone 👤) onde você escreve
  informações sobre você (nome, preferências, contexto) que são sempre lembradas
  pela Samantah, sem precisar repetir.
- **Voz**: clique no microfone (🎤) para ditar uma mensagem por voz, e ative o
  ícone de som (🔊) no topo para ela ler as respostas em voz alta. Usa a Web
  Speech API do navegador — funciona melhor no Chrome/Edge.

## O que tem aqui

- `app.py` — backend em Flask: serve a página, fala com a API do Gemini e
  gerencia as rotas de chat, histórico, perfil e reset.
- `db.py` — camada de banco de dados (SQLite) para histórico e perfil.
- `templates/index.html`, `static/style.css`, `static/script.js` — interface de
  chat, incluindo os recursos de voz e o modal de perfil.
- `.env.example` — modelo do arquivo de configuração com sua chave de API.
- `requirements.txt` — dependências Python.
- `Procfile` — comando de start usado por serviços de hospedagem (Render, etc).

## Passo a passo para rodar localmente

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

### 3. Consiga sua chave gratuita da API do Gemini

1. Acesse **https://aistudio.google.com/apikey** e faça login com uma conta
   Google.
2. Clique em **Create API key**.
3. Copie a chave gerada (começa com `AIza...`).
4. Não precisa de cartão de crédito — o nível gratuito tem limites de uso
   (quantidade de mensagens por minuto/dia), suficientes para uso pessoal.

**Sobre privacidade no nível gratuito:** segundo os termos da API do Gemini,
no uso gratuito o Google pode usar o conteúdo das conversas (e revisores
humanos podem ler amostras) para melhorar os produtos deles. Isso é diferente
do nível pago, onde isso não acontece. Vale ter isso em mente para o que você
conta pra Samantah e guarda no perfil dela. Se quiser mais privacidade, é
possível ativar o faturamento na sua conta do Google AI Studio para passar
para o nível pago (com custo por uso).

### 4. Configure a chave no projeto

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Abra o `.env` em um editor de texto e cole sua chave na linha:

```
GEMINI_API_KEY=AIza-sua-chave-aqui
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

A personalidade base dela está na variável `BASE_SYSTEM_PROMPT`, no início do
arquivo `app.py`. Edite esse texto para mudar o tom ou o idioma padrão.

Já as informações específicas sobre você (nome, preferências, contexto) não
precisam mexer em código — use o painel de perfil (ícone 👤) na própria
interface.

Para trocar o modelo usado, altere `SAMANTAH_MODEL` no `.env` (veja os modelos
disponíveis em aistudio.google.com).

## Limitações

- Pensado para uso pessoal (uma pessoa por vez, ou uma conversa por navegador —
  cada visitante tem seu próprio histórico e perfil, identificados por um cookie
  de sessão). Não há tela de login nem separação por conta de usuário.
- A leitura em voz alta e o ditado por voz dependem do navegador (funcionam bem
  no Chrome/Edge; o ditado pode não funcionar no Firefox/Safari).
- O nível gratuito da API do Gemini tem limites de uso (mensagens por minuto e
  por dia). Se a Samantah parar de responder com um erro de "limite excedido",
  espere um pouco ou considere ativar o faturamento no Google AI Studio.
- Ao publicar em um serviço de hospedagem gratuito, o banco SQLite pode não ser
  permanente (veja a seção de publicação abaixo) — para persistência garantida,
  rode localmente ou use um disco persistente pago no serviço de hospedagem.

## Publicando a Samantah online (Render)

1. Suba os arquivos deste projeto para um repositório no GitHub.
2. No Render (dashboard.render.com), crie um **Web Service** apontando para
   esse repositório.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
3. Nas variáveis de ambiente do serviço (**Environment**), adicione:
   - `GEMINI_API_KEY` — sua chave do Google AI Studio
   - `FLASK_SECRET_KEY` — uma string aleatória própria
   - `FLASK_DEBUG` — `false`
4. Espere o deploy terminar e acesse a URL pública gerada pelo Render.

**Nota sobre o banco de dados em produção:** no plano gratuito do Render, o
disco não é garantido como permanente entre reinícios/deploys — então a
memória da Samantah pode se perder de vez em quando nesse plano. Para memória
sempre persistente, é necessário um disco pago (Render Starter+) apontando
`SAMANTAH_DB_PATH` para dentro dele, ou trocar o SQLite por um banco de dados
hospedado.

## Próximos passos possíveis

- Adicionar login para várias pessoas usarem o mesmo app publicado sem
  misturar conversas.
- Trocar o SQLite por um banco de dados hospedado (Postgres) para garantir
  persistência total mesmo em hospedagem gratuita.
- Adicionar um avatar animado ou expressões visuais durante a fala.
