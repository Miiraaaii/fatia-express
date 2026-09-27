# 🍕 FatiaExpress - Sistema de Gestão e Pedidos de Pizzaria

## Nova interface web responsiva

A versão web usa **HTML, CSS e JavaScript**, com **Flask/Python e SQLite** no servidor. Funciona sem npm ou etapa de build e preserva o aplicativo Flet original. Os pedidos web usam as mesmas tabelas da cozinha existente.

### Executar no Windows

Na pasta do repositório, com Python 3.10 ou superior:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-web.txt
.venv\Scripts\python.exe web_app.py
```

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000). No Linux/macOS, use `.venv/bin/python` nos dois últimos comandos. Não abra `web/index.html` diretamente: a página precisa da API local.

### Recursos da versão web

- Layout adaptável, carrinho lateral no computador e acesso fixo ao carrinho em telas pequenas.
- Busca por nome e ingredientes sem depender de acentos, categorias e ordenação por preço ou nome.
- Personalização por tamanho, borda, quantidade e observações; bebidas usam preço unitário.
- Carrinho salvo no navegador, entrega com taxa de R$ 7,00 e retirada sem taxa.
- Checkout com validação no servidor, preços recalculados a partir do catálogo e proteção contra duplicação ao repetir o mesmo envio.
- Acompanhamento em **Meus pedidos**, protegido por um token por pedido. As atualizações da equipe aparecem na consulta; o navegador consulta a cada 20 segundos enquanto esse painel está aberto.
- Imagens ilustrativas geradas por IA; prompts e origem em [web/assets/IMAGE_SOURCES.md](web/assets/IMAGE_SOURCES.md).

O pagamento é **no recebimento**. Não há cobrança online, integração Pix bancária ou envio por WhatsApp. A seleção da forma de pagamento registra a preferência do cliente.

### Dados e execução

O banco padrão é `fatia_express.db`, na raiz. A variável `FATIA_DB_PATH` permite escolher outro arquivo; para compartilhar os pedidos, web e desktop devem usar o mesmo banco. A inicialização web cria o cardápio original, sem inserir pedidos fictícios. A inicialização desktop conserva o comportamento anterior de demonstração em bancos novos.

O navegador guarda o carrinho e os tokens dos últimos 20 pedidos. Limpar os dados do navegador remove esse acesso; não existe conta ou recuperação de histórico nesta versão. O endereço e o telefone são gravados no banco para atendimento do pedido.

### Validação

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

São 20 testes de integração, incluindo preços, retirada, disponibilidade, transações, concorrência, repetição de envio e acesso aos pedidos. Também foram verificados no navegador a personalização, a persistência do carrinho após recarregar, a validação de telefone, um pedido com retirada e a busca no layout móvel. A interface Flet original não foi revalidada nesta alteração.

### Estrutura adicionada

```text
web_app.py                    # Servidor Flask e rotas HTTP
services/web_order_service.py # Validação, preços, persistência e acompanhamento
requirements-web.txt          # Dependência independente do Flet
web/index.html                # Interface em português
web/styles.css                # Layout responsivo e estados de interação
web/app.js                    # Cardápio, carrinho, checkout e acompanhamento
web/assets/                   # Fotos ilustrativas e identidade visual
tests/test_web_app.py         # Testes com bancos temporários
```

### Uso em produção

`python web_app.py` abre um servidor **local de desenvolvimento**. O envio deste código ao GitHub não publica um site. Antes de atender clientes, confirme catálogo, preços, taxa, área de entrega, endereço e horários da loja; configure hospedagem WSGI com HTTPS e operação administrativa autenticada. Não há integração de pagamento nem prazo de entrega automático. Consulte a [documentação oficial do Flask](https://flask.palletsprojects.com/en/stable/quickstart/).

## Aplicativo Flet original

As instruções e a descrição abaixo se referem à interface original. Para executá-la, use `requirements.txt` e `main.py`. Recursos descritos para o desktop não implicam implementação na nova interface web; por exemplo, não foi adicionado pedido meio a meio ou cadastro de adicionais.

> **Aplicação Multiplataforma (Desktop e Mobile/Web) desenvolvida em Python com Flet e SQLite.**
> Projeto projetado com foco em boas práticas de engenharia de software, arquitetura limpa em camadas (Layered Architecture) e padrões de projeto (Repository Pattern).

---

## 🎯 Sobre o Projeto

O **FatiaExpress** é um sistema completo para pizzarias e serviços de delivery, cobrindo o fluxo de ponta a ponta:
1. **Atendimento / Cardápio:** Seleção de pizzas com tamanhos (Brotinho a Família), bordas recheadas, adicionais, observações e bebidas.
2. **Carrinho & Checkout:** Validações de pedidos, cálculo dinâmico de taxas de entrega e escolha da forma de pagamento.
3. **Cozinha & Gestão Operacional (Kanban):** Controle em tempo real do status dos pedidos (`Recebido` ➔ `Em Preparo` ➔ `No Forno 🔥` ➔ `Saiu para Entrega 🛵` ➔ `Entregue ✅`).
4. **Relatórios & Dashboard:** Métricas consolidadas de faturamento diário, pedidos totais, distribuição de status e ranking de produtos mais vendidos.

---

## 🚀 Tecnologias Utilizadas

* **Linguagem:** [Python 3.10+](https://www.python.org/)
* **Interface Gráfica:** [Flet](https://flet.dev/) (Framework moderno baseado no Flutter da Google, oferecendo visual nativo e responsivo)
* **Banco de Dados:** [SQLite3](https://sqlite.org/) (Embutido, nativo, com suporte a transações atômicas ACID e modo WAL ativado)
* **Arquitetura:** Padrão em camadas (UI $\leftrightarrow$ Services $\leftrightarrow$ Repositories $\leftrightarrow$ Database)

---

## 🏗️ Estrutura do Projeto

```text
fatia-express/
├── database/
│   ├── __init__.py
│   └── connection.py       # Gerenciamento de conexões SQLite, schema DDL e seed inicial
├── models/
│   ├── __init__.py
│   ├── product.py          # Modelos de Domínio: Produto, Categoria, Tamanho, Borda
│   └── order.py            # Modelos de Domínio: Pedido, Item do Pedido, Status, Pagamento
├── repositories/
│   ├── __init__.py
│   ├── product_repo.py     # Repositório de consulta e persistência do cardápio
│   └── order_repo.py       # Repositório de pedidos, transações atômicas e métricas
├── services/
│   ├── __init__.py
│   ├── catalog_service.py  # Regras de negócio de catálogo e filtros
│   └── order_service.py    # Regras de negócio do carrinho, checkout e avanço de status
├── ui/
│   ├── theme.py            # Paleta de cores, tipografia e formatadores
│   ├── components/
│   │   ├── product_card.py    # Card visual do produto
│   │   ├── product_dialog.py  # Modal interativo de customização de pizza
│   │   ├── cart_view.py       # Painel do carrinho com checkout
│   │   └── order_card.py      # Card operacional para o painel de pedidos
│   └── views/
│       ├── catalog_view.py    # Tela de cardápio e seleção de pedidos
│       ├── orders_view.py     # Tela de fluxo e gestão da cozinha/delivery
│       └── dashboard_view.py  # Tela de métricas e gráficos de desempenho
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do projeto
└── README.md               # Documentação completa
```

---

## 🏠 Guia Rápido: Como Continuar o Desenvolvimento em Casa

Se você for rodar este projeto em outro computador (Windows, macOS ou Linux), siga este passo a passo:

### 1. Clonar o Repositório
```bash
# Via SSH (se já configurou a chave SSH no GitHub):
git clone git@github.com:Miiraaaii/fatia-express.git

# OU via HTTPS:
git clone https://github.com/Miiraaaii/fatia-express.git

cd fatia-express
```

### 2. Criar e Ativar o Ambiente Virtual (Virtualenv)

* **No Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

* **No Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
  *(Se houver erro de permissão de script no PowerShell, execute `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

* **No Windows (Prompt de Comando / CMD):**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate.bat
  ```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a Aplicação
O banco de dados SQLite (`fatia_express.db`) será **criado e semeado com dados automaticamente** na primeira inicialização!

* **Modo Janela Desktop (Nativo):**
  ```bash
  python main.py
  # ou python3 main.py
  ```

* **Modo Web (Navegador com Hot-Reload):**
  ```bash
  flet run main.py --web --port 8550
  ```
  Depois abra no seu navegador em: `http://localhost:8550`.

---

## 📌 Status Atual & Sugestões para Continuar

### ✅ O que já está pronto e funcionando:
* **Banco de Dados:** Schema SQLite completo (categorias, produtos, tamanhos, bordas, adicionais, pedidos e itens do pedido) com migração e seed automático.
* **Arquitetura em Camadas:** Modelos desacoplados (`models/`), repositórios com suporte a transações atômicas (`repositories/`) e regras de negócio (`services/`).
* **Cardápio e Customização:** Modal de montagem de pizza (escolha de massa, bordas, adicionais e observações), cálculo de preços e carrinho reativo.
* **Painel da Cozinha (Kanban Operacional):** Visualização dos pedidos com filtros por status e botão para avançar etapas (`Recebido` ➔ `Em Preparo` ➔ `No Forno` ➔ `Saiu para Entrega` ➔ `Entregue`).
* **Dashboard Analítico:** Indicadores de faturamento, pedidos entregues, taxa de entrega acumulada, gráficos e ranking de produtos mais vendidos.

### 💡 Ideias de Próximas Features para Desenvolver em Casa:
1. **Impressão de Comanda / PDF:** Gerar um comprovante ou PDF formatado para envio para a impressora térmica da cozinha.
2. **Pagamento PIX Simulado:** Exibir um modal com QR Code e código Copia e Cola ao selecionar pagamento via PIX no checkout.
3. **Notificação Sonora:** Tocar um alerta sonoro quando um novo pedido for criado no painel da cozinha.
4. **Filtros e Busca no Cardápio:** Adicionar barra de pesquisa de produtos por nome ou ingredientes.
5. **Exportação de Relatórios:** Botão no Dashboard para exportar o histórico de vendas para arquivo `.csv` ou `.xlsx`.

---

---

## 💼 Destaques de Engenharia para Currículo e Entrevistas

Ao apresentar este projeto em entrevistas de emprego ou no LinkedIn/GitHub, você pode enfatizar:

1. **Separação de Responsabilidades (SoC):**
   A camada de interface (`ui`) nunca conversa diretamente com o banco de dados. Todas as ações passam por regras de negócio (`services`) e persistência isolada (`repositories`).
2. **Padrão Repository (Desacoplamento de Banco de Dados):**
   O sistema utiliza SQLite local para custo zero e execução imediata, mas a camada de repositório permite substituir o SQLite por PostgreSQL, Supabase ou uma API REST sem modificar uma única linha das telas.
3. **Transações Atômicas:**
   A gravação de novos pedidos no banco de dados insere tanto o cabeçalho quanto os itens em uma transação única (garantindo consistência caso ocorra qualquer falha).
4. **Interface Reativa Multiplataforma:**
   Desenvolvida com componentes visuais reativos em Flet/Flutter, garantindo que o mesmo código funcione em Desktop (Linux, Windows, macOS) e navegadores/Mobile.
