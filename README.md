# Samantah 💬

Um chatbot pessoal com interface de chat no navegador, com respostas geradas
gratuitamente pela API do Gemini (Google AI), memória permanente e voz.

## Funcionalidades

- **Login com email e senha**: sua conta guarda tudo — histórico, perfil e
  tarefas — então você pode entrar de qualquer computador ou celular e
  encontrar a Samantah do jeito que deixou.
- **Conversa natural** com a Samantah, com personalidade calorosa e conversacional.
- **Gratuita**: usa a API do Gemini, que tem um nível gratuito sem precisar de
  cartão de crédito.
- **Memória permanente**: o histórico de conversa, o "perfil" e as tarefas ficam
  salvos em um banco SQLite — sobrevivem a reinícios do servidor.
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
- `db.py` — camada de banco de dados (SQLite) para contas, histórico, perfil e
  tarefas.
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

## Sobre esta atualização (login)

Antes desta versão, os dados eram identificados por um cookie de navegador
aleatório. Agora passaram a ser identificados pela sua conta. Isso significa
que qualquer conversa/tarefa salva antes de existir login não vai aparecer
depois de criar sua conta — é preciso criar a conta e começar a usar dali
para frente.

## Próximos passos possíveis

- Recuperação de senha (por email) e verificação de email no cadastro.
- Trocar o SQLite por um banco de dados hospedado (Postgres) para garantir
  persistência total mesmo em hospedagem gratuita.
- Adicionar um avatar animado ou expressões visuais durante a fala.
