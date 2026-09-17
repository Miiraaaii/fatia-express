"""
FatiaExpress - Conexão e Inicialização do Banco de Dados SQLite.
"""

import os
import sqlite3
from pathlib import Path

# Localização do banco de dados na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "fatia_express.db"


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão configurada com o SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_database() -> None:
    """Inicializa as tabelas do banco de dados e dados padrão se necessário."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Categorias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT NOT NULL
        );
        """)

        # Tamanhos de Pizza
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pizza_sizes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slices INTEGER NOT NULL,
            price_multiplier REAL NOT NULL
        );
        """)

        # Opções de Bordas Recheadas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crust_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        );
        """)

        # Produtos (Pizzas, Bebidas, etc.)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price_base REAL NOT NULL,
            image_emoji TEXT NOT NULL DEFAULT '🍕',
            is_pizza INTEGER NOT NULL DEFAULT 1,
            available INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        );
        """)

        # Pedidos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            delivery_type TEXT NOT NULL, -- 'ENTREGA' ou 'BALCAO'
            address TEXT,
            payment_method TEXT NOT NULL, -- 'PIX', 'CARTAO_CREDITO', 'CARTAO_DEBITO', 'DINHEIRO'
            status TEXT NOT NULL, -- 'RECEBIDO', 'EM_PREPARO', 'NO_FORNO', 'SAIU_ENTREGA', 'ENTREGUE', 'CANCELADO'
            subtotal REAL NOT NULL,
            delivery_fee REAL NOT NULL DEFAULT 0.0,
            total REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Itens do Pedido
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            size_name TEXT,
            crust_name TEXT,
            product_name TEXT NOT NULL,
            unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        """)

        conn.commit()


def seed_data_if_empty() -> None:
    """Preenche dados iniciais no cardápio caso a base esteja vazia."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM products;")
        if cursor.fetchone()["count"] > 0:
            return  # Já existem dados cadastrados

        # Categorias
        cursor.executemany(
            "INSERT INTO categories (id, name, icon) VALUES (?, ?, ?);",
            [
                (1, "Pizzas Tradicionais", "local_pizza"),
                (2, "Pizzas Especiais", "stars"),
                (3, "Pizzas Doces", "cake"),
                (4, "Bebidas & Sucos", "local_bar"),
            ]
        )

        # Tamanhos
        cursor.executemany(
            "INSERT INTO pizza_sizes (id, name, slices, price_multiplier) VALUES (?, ?, ?, ?);",
            [
                (1, "Brotinho (4 fatias)", 4, 0.70),
                (2, "Média (6 fatias)", 6, 1.00),
                (3, "Grande (8 fatias)", 8, 1.35),
                (4, "Família (12 fatias)", 12, 1.65),
            ]
        )

        # Bordas
        cursor.executemany(
            "INSERT INTO crust_options (id, name, price) VALUES (?, ?, ?);",
            [
                (1, "Tradicional (Sem Borda Recheada)", 0.00),
                (2, "Catupiry Original", 8.00),
                (3, "Cheddar Cremoso", 8.00),
                (4, "Chocolate ao Leite", 9.50),
                (5, "Vulcão de Queijo", 12.00),
            ]
        )

        # Produtos
        products = [
            # Pizzas Tradicionais
            (1, "Calabresa Especial", "Molho de tomate pelado, mussarela, calabresa defumada fatiada, cebola roxa e orégano fresco.", 42.00, "🍕", 1),
            (1, "Marguerita Clássica", "Molho artesanal, mussarela de búfala, fatias de tomate selecionados, manjericão fresco e azeite extravirgem.", 45.00, "🍕", 1),
            (1, "Mussarela Tradicional", "Molho de tomate artesanal, generosa camada de mussarela de alta qualidade, azeitonas pretas e orégano.", 40.00, "🧀", 1),
            (1, "Frango com Catupiry", "Peito de frango desfiado temperado com ervas finas, requeijão Catupiry original e azeitonas.", 48.00, "🍗", 1),
            (1, "Portuguesa Completa", "Mussarela, presunto cozido magro, ovos picados, cebola, ervilhas frescas e azeitonas pretas.", 46.00, "🍕", 1),

            # Pizzas Especiais
            (2, "Quatro Queijos Nobres", "Combinação perfeita de mussarela, gorgonzola legítimo, provolone curado e Catupiry cremoso.", 52.00, "🧀", 1),
            (2, "Pepperoni Supremo", "Mussarela, fatias crocantes de pepperoni especial levemente picante e orégano fresco.", 54.00, "🍕", 1),
            (2, "Bacon & Barbecue", "Mussarela, tiras crocantes de bacon premium, cebola caramelizada e redução de barbecue artesanal.", 50.00, "🥓", 1),
            (2, "Camarão com Alho Poró", "Mussarela, camarões médios refogados no azeite, alho poró crocante e toque de requeijão.", 68.00, "🍤", 1),

            # Pizzas Doces
            (3, "Chocolate com Morango", "Base de chocolate ao leite nobre forneável, coberta com morangos frescos fatiados.", 46.00, "🍓", 1),
            (3, "Romeu e Julieta", "Mussarela especial coberta com fatias de goiabada cascão cremosa e queijo minas curado.", 42.00, "🧀", 1),
            (3, "Banana Nevada", "Banana caramelizada, canela em pó, leite condensado e cobertura de chocolate branco gratinado.", 44.00, "🍌", 1),

            # Bebidas
            (4, "Coca-Cola 2 Litros", "Refrigerante Coca-Cola garrafa 2L gelada.", 14.00, "🥤", 0),
            (4, "Coca-Cola Lata 350ml", "Refrigerante Coca-Cola lata 350ml original gelada.", 6.50, "🥤", 0),
            (4, "Guaraná Antarctica 2L", "Refrigerante Guaraná Antarctica garrafa 2L bem gelada.", 13.00, "🥤", 0),
            (4, "Suco Natural de Laranja 500ml", "Suco 100% natural de laranja, espremido na hora.", 9.00, "🍊", 0),
            (4, "Água Mineral sem Gás 500ml", "Água mineral pura e refrescante.", 4.50, "💧", 0),
        ]

        cursor.executemany(
            """
            INSERT INTO products (category_id, name, description, price_base, image_emoji, is_pizza)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            products
        )

        # Inserir pedidos de demonstração se a tabela estiver vazia
        cursor.execute("SELECT COUNT(*) AS count FROM orders;")
        if cursor.fetchone()["count"] == 0:
            cursor.execute(
                """
                INSERT INTO orders (
                    customer_name, customer_phone, delivery_type, address,
                    payment_method, status, subtotal, delivery_fee, total, notes, created_at
                ) VALUES 
                ('Ana Paula Souza', '(11) 98765-4321', 'ENTREGA', 'Av. Paulista, 1578, Apto 82 - Bela Vista', 'PIX', 'RECEBIDO', 64.70, 7.00, 71.70, 'Campainha está com defeito, bater no portão', datetime('now', '-25 minutes')),
                ('Lucas Fernandes', '(11) 99123-4567', 'BALCAO', NULL, 'CARTAO_CREDITO', 'EM_PREPARO', 52.00, 0.00, 52.00, 'Massa bem fina', datetime('now', '-40 minutes')),
                ('Mariana Oliveira', '(11) 97654-3210', 'ENTREGA', 'Rua Augusta, 920, Bloco B - Consolação', 'DINHEIRO', 'NO_FORNO', 78.50, 7.00, 85.50, 'Troco para R$ 100', datetime('now', '-55 minutes')),
                ('Roberto Mendes', '(11) 98888-7777', 'ENTREGA', 'Rua Oscar Freire, 300 - Jardins', 'CARTAO_DEBITO', 'ENTREGUE', 110.00, 7.00, 117.00, NULL, datetime('now', '-3 hours'));
                """
            )

            # Itens dos pedidos de demonstração
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, size_name, crust_name, product_name, unit_price, quantity, subtotal, notes)
                VALUES 
                (1, 1, 'Grande (8 fatias)', 'Catupiry Original', 'Calabresa Especial', 64.70, 1, 64.70, 'Sem cebola'),
                (2, 6, 'Média (6 fatias)', 'Tradicional (Sem Borda Recheada)', 'Quatro Queijos Nobres', 52.00, 1, 52.00, NULL),
                (3, 7, 'Grande (8 fatias)', 'Cheddar Cremoso', 'Pepperoni Supremo', 64.50, 1, 64.50, 'Bem assada'),
                (3, 14, NULL, NULL, 'Coca-Cola 2 Litros', 14.00, 1, 14.00, 'Gelada'),
                (4, 4, 'Família (12 fatias)', 'Vulcão de Queijo', 'Frango com Catupiry', 91.20, 1, 91.20, NULL),
                (4, 16, NULL, NULL, 'Guaraná Antarctica 2L', 13.00, 1, 13.00, NULL),
                (4, 10, 'Brotinho (4 fatias)', 'Chocolate ao Leite', 'Chocolate com Morango', 41.70, 1, 41.70, NULL);
                """
            )

        conn.commit()
