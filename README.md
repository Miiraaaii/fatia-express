# 🍕 FatiaExpress - Sistema de Gestão e Pedidos de Pizzaria

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

## ⚙️ Como Executar Localmente

### 1. Pré-requisitos
* Ter o Python instalado (versão 3.10 ou superior).

### 2. Clonar ou Acessar a Pasta do Projeto
```bash
cd /home/abraaom/fatia-express
```

### 3. Ativar o Ambiente Virtual
```bash
# No Linux / macOS:
source .venv/bin/activate

# No Windows:
# .venv\Scripts\activate
```

### 4. Instalar as Dependências (caso não tenha instalado)
```bash
pip install -r requirements.txt
```

### 5. Iniciar a Aplicação

* **Modo Desktop (Janela nativa):**
  ```bash
  python3 main.py
  ```

* **Modo Web (no Navegador):**
  Você também pode rodar no navegador caso deseje testar a interface web:
  ```bash
  flet run main.py --web
  ```

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
