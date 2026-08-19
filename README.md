# Samantah 💬

Um chatbot pessoal com interface de chat no navegador, com respostas geradas
gratuitamente pela API do Gemini (Google AI), memória permanente e voz.

## Funcionalidades

- **Login com email e senha**: sua conta guarda tudo — histórico, perfil e
  tarefas — então você pode entrar de qualquer computador ou celular e
  encontrar a Samantah do jeito que deixou.
- **Conversa natural** com a Samantah, com personalidade calorosa e conversacional.
- **Gratuita**: usa a API do Gemini, que tem um nível gratuito sem precisar de
  cartão de crédito. Em produção, o banco de dados também pode ser 100%
  gratuito usando o Turso (veja a seção de publicação abaixo).
- **Memória permanente de verdade**: o histórico de conversa, o "perfil" e as
  tarefas ficam salvos num banco de dados. Rodando localmente, é um arquivo
  SQLite; em produção, recomendamos o Turso (banco hospedado, gratuito),
  para que os dados sobrevivam a deploys e aos períodos em que o servidor
  "dorme" por inatividade em hospedagens gratuitas.
- **Perfil / memória de longo prazo**: um painel (ícone 👤) onde você escreve
  informações sobre você (nome, preferências, contexto) que são sempre lembradas
  pela Samantah, sem precisar repetir.
- **Tarefas e agenda**: um painel (ícone 📋) com sua lista de tarefas. Você pode
  adicionar por lá ou simplesmente pedir no chat ("adiciona uma tarefa pra
  amanhã: pagar a conta de luz") — a própria Samantah cria, lista, marca como
  concluída ou apaga tarefas durante a conversa.
- **Documentos e imagens**: clique no clipe (📎) para anexar um PDF, imagem ou
  outro arquivo — a Samantah lê o conteúdo e comenta sobre ele.
- **Voz**: clique no microfone (🎤) para ditar uma mensagem por voz, e ative o
  ícone de som (🔊) no topo para ela ler as respostas em voz alta. Usa a Web
  Speech API do navegador — funciona melhor no Chrome/Edge.
- **Funciona no celular**: interface responsiva, e dá para "Adicionar à tela
  inicial" no Android/iPhone para abrir como um app.

## O que tem aqui

- `app.py` — backend em Flask: login/cadastro, serve a página, fala com a API
  do Gemini (incluindo as ferramentas de tarefas e upload de arquivos) e
  gerencia as rotas de chat, histórico, perfil, tarefas e reset.
- `db.py` — camada de banco de dados para contas, histórico, perfil e tarefas.
  Usa SQLite local por padrão, ou o Turso (banco hospedado gratuito) se as
  variáveis `TURSO_DATABASE_URL`/`TURSO_AUTH_TOKEN` estiverem configuradas.
- `templates/login.html`, `templates/register.html` — telas de entrar/criar conta.
- `templates/index.html`, `static/style.css`, `static/script.js` — interface de
  chat, incluindo voz, anexos e os painéis de perfil e tarefas.
- `static/manifest.webmanifest`, `static/sw.js`, `static/icon-*.png` — arquivos
  que permitem "Adicionar à tela inicial" no celular.
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
navegador — a primeira tela vai pedir para você criar uma conta (email e
senha). Depois de criar, é essa mesma conta que você usa para entrar em
qualquer outro aparelho e continuar de onde parou.

**Sobre a senha:** não existe ainda um "esqueci minha senha" nesta versão —
guarde bem sua senha, porque se esquecer não tem como recuperar a conta sem
mexer direto no banco de dados.

## Personalizando a Samantah

A personalidade base dela está na variável `BASE_SYSTEM_PROMPT`, no início do
arquivo `app.py`. Edite esse texto para mudar o tom ou o idioma padrão.

Já as informações específicas sobre você (nome, preferências, contexto) não
precisam mexer em código — use o painel de perfil (ícone 👤) na própria
interface.

Para trocar o modelo usado, altere `SAMANTAH_MODEL` no `.env` (veja os modelos
disponíveis em aistudio.google.com).

## Limitações

- Cada conta é isolada (seu histórico, perfil e tarefas não aparecem para
  outra conta), mas não existe recuperação de senha nem verificação de email
  ainda — qualquer pessoa pode criar uma conta com qualquer email (mesmo que
  não seja dela). Para uso pessoal isso não costuma ser problema, mas não é
  adequado como está para um público maior.
- A leitura em voz alta e o ditado por voz dependem do navegador (funcionam bem
  no Chrome/Edge; o ditado pode não funcionar no Firefox/Safari).
- Arquivos enviados para a Samantah ficam guardados nos servidores do Google
  por até 48 horas (limite da API do Gemini) — depois desse prazo, se você
  perguntar de novo sobre um arquivo antigo, ela não vai mais conseguir acessá-lo.
- O nível gratuito da API do Gemini tem limites de uso (mensagens por minuto e
  por dia). Se a Samantah parar de responder com um erro de "limite excedido",
  espere um pouco ou considere ativar o faturamento no Google AI Studio.
- Se você publicar em um serviço de hospedagem gratuito **sem** configurar o
  Turso (veja abaixo), o banco fica só no disco do servidor, que costuma ser
  apagado a cada deploy e a cada vez que o servidor "dorme" por inatividade —
  ou seja, login e memória se perdem de vez em quando. Configurando o Turso,
  isso deixa de ser um problema.

## Publicando a Samantah online (Render)

### 1. Crie um banco de dados gratuito no Turso (recomendado)

Isso garante que login, histórico, perfil e tarefas sobrevivam a deploys e
aos períodos em que o Render "dorme" por inatividade.

1. Acesse **https://turso.tech**, clique em algo como "Get Started" / "Sign
   up" e crie uma conta gratuita (dá para entrar com GitHub ou email — não
   pede cartão de crédito).
2. No painel, crie um banco de dados novo (ex: botão "Create Database"),
   escolha um nome (ex: `samantah`) e uma região.
3. Abra o banco criado e procure a área de conexão ("Connect" / "Connection
   info"): copie a **Database URL** (começa com `libsql://...`).
4. Ainda no painel do banco, gere um **token de autenticação** (algo como
   "Create Token" / "Auth Tokens") e copie o token gerado (uma string longa).
5. Guarde os dois valores — você vai usá-los como variáveis de ambiente no
   Render no próximo passo (`TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN`).

Se preferir não usar o Turso, pode pular essa parte — a Samantah funciona do
mesmo jeito, só que com o risco de perda de dados descrito na seção de
Limitações.

### 2. Publique no Render

1. Suba os arquivos deste projeto para um repositório no GitHub.
2. No Render (dashboard.render.com), crie um **Web Service** apontando para
   esse repositório.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --timeout 120`
3. Nas variáveis de ambiente do serviço (**Environment**), adicione:
   - `GEMINI_API_KEY` — sua chave do Google AI Studio
   - `FLASK_SECRET_KEY` — uma string aleatória própria
   - `FLASK_DEBUG` — `false`
   - `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN` — se você criou o banco no
     Turso no passo anterior
4. Espere o deploy terminar e acesse a URL pública gerada pelo Render.

## Sobre esta atualização (Turso)

Antes desta versão, o banco de dados vivia só no disco do servidor do
Render, que é apagado com frequência no plano gratuito (a cada deploy e a
cada vez que o app "dorme" por inatividade) — por isso o login e a memória
estavam se perdendo sozinhos. Agora, se `TURSO_DATABASE_URL` estiver
configurada, os dados ficam guardados num banco separado, fora do disco do
Render, e não são mais afetados por isso.

**Importante:** se você já tinha criado uma conta antes desta atualização,
ela estava guardada no disco antigo do Render e provavelmente já foi
apagada — será preciso criar a conta de novo depois de configurar o Turso.

## Próximos passos possíveis

- Recuperação de senha (por email) e verificação de email no cadastro.
- Adicionar um avatar animado ou expressões visuais durante a fala.
