import sqlite3
from datetime import datetime


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('data/warehouse.db')
    cursor = conn.cursor()

    # Таблица товаров
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS products
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       category
                       TEXT,
                       quantity
                       INTEGER
                       DEFAULT
                       0,
                       price
                       REAL
                   )
                   ''')

    # Таблица заявок
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS orders
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       user_name
                       TEXT,
                       product_id
                       INTEGER,
                       quantity
                       INTEGER,
                       status
                       TEXT
                       DEFAULT
                       'Новая',
                       created_at
                       TEXT,
                       updated_at
                       TEXT,
                       FOREIGN
                       KEY
                   (
                       product_id
                   ) REFERENCES products
                   (
                       id
                   )
                       )
                   ''')

    # Добавление тестовых данных, если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        test_products = [
            ('Подшипники шариковые', 'Метизы', 500, 150),
            ('Болты М10х50', 'Крепеж', 1000, 25),
            ('Электроды сварочные', 'Расходные материалы', 300, 80),
            ('Масло индустриальное', 'Смазочные материалы', 200, 450),
            ('Перчатки рабочие', 'СИЗ', 1000, 35),
            ('Кабель ВВГ 3х2.5', 'Электротовары', 500, 120),
            ('Краска акриловая', 'Лакокрасочные материалы', 150, 300)
        ]
        cursor.executemany(
            "INSERT INTO products (name, category, quantity, price) VALUES (?, ?, ?, ?)",
            test_products
        )

    conn.commit()
    conn.close()
    print("База данных инициализирована")


def get_products():
    """Получить список всех товаров"""
    conn = sqlite3.connect('data/warehouse.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, quantity, price FROM products")
    products = cursor.fetchall()
    conn.close()
    return products


def create_order(user_id, user_name, product_id, quantity):
    """Создать новую заявку"""
    conn = sqlite3.connect('data/warehouse.db')
    cursor = conn.cursor()

    # Проверка наличия товара
    cursor.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return False, "Товар не найден"

    available = result[0]
    if available < quantity:
        conn.close()
        return False, f"Недостаточно товара на складе. Доступно: {available}"

    # Создание заявки
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
                   INSERT INTO orders (user_id, user_name, product_id, quantity, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ''', (user_id, user_name, product_id, quantity, 'Новая', now, now))

    # Обновление остатков
    cursor.execute(
        "UPDATE products SET quantity = quantity - ? WHERE id = ?",
        (quantity, product_id)
    )

    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return True, f"Заявка N{order_id} успешно создана"


def get_order_status(user_id):
    """Получить статус заявок пользователя"""
    conn = sqlite3.connect('data/warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''
                   SELECT o.id, p.name, o.quantity, o.status, o.created_at
                   FROM orders o
                            JOIN products p ON o.product_id = p.id
                   WHERE o.user_id = ?
                   ORDER BY o.created_at DESC LIMIT 10
                   ''', (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_all_orders():
    """Получить все заявки для дашборда"""
    conn = sqlite3.connect('data/warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''
                   SELECT o.id, o.user_name, p.name, o.quantity, o.status, o.created_at
                   FROM orders o
                            JOIN products p ON o.product_id = p.id
                   ORDER BY o.created_at DESC
                   ''')
    orders = cursor.fetchall()
    conn.close()
    return orders