import sqlite3
from pathlib import Path


# =====================================================
# DATABASE CONFIGURATION
# =====================================================

DATABASE_PATH = Path(__file__).parent / "database.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# =====================================================
# CREATE ALL DATABASE TABLES
# =====================================================

def create_tables():
    connection = get_connection()

    try:
        connection.executescript("""

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL CHECK(price >= 0),
                category TEXT NOT NULL,
                image_filename TEXT NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0
                    CHECK(stock_quantity >= 0),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                phone TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (customer_id)
                    REFERENCES customers(id)
                    ON DELETE CASCADE
            );


            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,

                delivery_name TEXT NOT NULL,
                delivery_phone TEXT NOT NULL,
                delivery_address TEXT NOT NULL,
                delivery_city TEXT NOT NULL,
                delivery_state TEXT NOT NULL,

                subtotal INTEGER NOT NULL CHECK(subtotal >= 0),
                delivery_fee INTEGER NOT NULL DEFAULT 0
                    CHECK(delivery_fee >= 0),
                total_amount INTEGER NOT NULL CHECK(total_amount >= 0),

                status TEXT NOT NULL DEFAULT 'Pending',
                payment_status TEXT NOT NULL DEFAULT 'Unpaid',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (customer_id)
                    REFERENCES customers(id)
            );


            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER,

                product_name TEXT NOT NULL,
                product_image TEXT,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price INTEGER NOT NULL CHECK(unit_price >= 0),
                total_price INTEGER NOT NULL CHECK(total_price >= 0),

                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE SET NULL
            );


            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount INTEGER NOT NULL CHECK(amount >= 0),
                payment_method TEXT NOT NULL,
                payment_reference TEXT UNIQUE,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
            );


            CREATE INDEX IF NOT EXISTS idx_products_category
                ON products(category);

            CREATE INDEX IF NOT EXISTS idx_products_active
                ON products(is_active);

            CREATE INDEX IF NOT EXISTS idx_orders_customer
                ON orders(customer_id);

            CREATE INDEX IF NOT EXISTS idx_order_items_order
                ON order_items(order_id);

            CREATE INDEX IF NOT EXISTS idx_payments_order
                ON payments(order_id);

        """)

        connection.commit()

    finally:
        connection.close()


# =====================================================
# PRODUCT FUNCTIONS
# =====================================================

def add_product(
    name,
    description,
    price,
    category,
    image_filename,
    stock_quantity
):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO products (
                name,
                description,
                price,
                category,
                image_filename,
                stock_quantity
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            description,
            price,
            category,
            image_filename,
            stock_quantity
        ))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_all_products():
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM products
            WHERE is_active = 1
            ORDER BY created_at DESC
        """).fetchall()

    finally:
        connection.close()


def get_product_by_id(product_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM products
            WHERE id = ?
        """, (product_id,)).fetchone()

    finally:
        connection.close()


def get_products_by_category(category):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM products
            WHERE category = ?
            AND is_active = 1
            ORDER BY created_at DESC
        """, (category,)).fetchall()

    finally:
        connection.close()


def search_products(search_term):
    connection = get_connection()

    try:
        search = f"%{search_term}%"

        return connection.execute("""
            SELECT *
            FROM products
            WHERE is_active = 1
            AND (
                name LIKE ?
                OR description LIKE ?
                OR category LIKE ?
            )
            ORDER BY name
        """, (search, search, search)).fetchall()

    finally:
        connection.close()


def update_product(product_id, **updates):
    allowed_fields = {
        "name",
        "description",
        "price",
        "category",
        "image_filename",
        "stock_quantity",
        "is_active"
    }

    if not updates:
        return False

    if not set(updates).issubset(allowed_fields):
        raise ValueError("Invalid product field.")

    fields = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values())
    values.append(product_id)

    connection = get_connection()

    try:
        cursor = connection.execute(
            f"UPDATE products SET {fields} WHERE id = ?",
            values
        )

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


def deactivate_product(product_id):
    return update_product(product_id, is_active=0)


def delete_product(product_id):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            DELETE FROM products
            WHERE id = ?
        """, (product_id,))

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


# =====================================================
# CUSTOMER FUNCTIONS
# =====================================================

def add_customer(full_name, email, phone, password_hash):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO customers (
                full_name,
                email,
                phone,
                password_hash
            )
            VALUES (?, ?, ?, ?)
        """, (
            full_name,
            email.strip().lower(),
            phone,
            password_hash
        ))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_customer_by_email(email):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM customers
            WHERE email = ?
        """, (email.strip().lower(),)).fetchone()

    finally:
        connection.close()


def get_customer_by_id(customer_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT id, full_name, email, phone, created_at
            FROM customers
            WHERE id = ?
        """, (customer_id,)).fetchone()

    finally:
        connection.close()


# =====================================================
# ADMIN FUNCTIONS
# =====================================================

def add_admin(full_name, email, password_hash):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO admins (
                full_name,
                email,
                password_hash
            )
            VALUES (?, ?, ?)
        """, (
            full_name,
            email.strip().lower(),
            password_hash
        ))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_admin_by_email(email):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM admins
            WHERE email = ?
        """, (email.strip().lower(),)).fetchone()

    finally:
        connection.close()


# =====================================================
# CUSTOMER DELIVERY ADDRESS FUNCTIONS
# =====================================================

def add_address(
    customer_id,
    full_name,
    phone,
    address,
    city,
    state
):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO addresses (
                customer_id,
                full_name,
                phone,
                address,
                city,
                state
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            full_name,
            phone,
            address,
            city,
            state
        ))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_customer_addresses(customer_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM addresses
            WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,)).fetchall()

    finally:
        connection.close()


# =====================================================
# ORDER FUNCTIONS
# =====================================================

def create_order(
    customer_id,
    delivery_name,
    delivery_phone,
    delivery_address,
    delivery_city,
    delivery_state,
    items,
    delivery_fee=0
):
    """
    items must be a list of dictionaries:

    [
        {"product_id": 1, "quantity": 2},
        {"product_id": 3, "quantity": 1}
    ]

    Product prices are read from the database,
    not trusted from the customer's browser.
    """

    if not items:
        raise ValueError("Your shopping cart is empty.")

    if delivery_fee < 0:
        raise ValueError("Invalid delivery fee.")

    connection = get_connection()

    try:
        subtotal = 0
        order_products = []

        for item in items:
            product = connection.execute("""
                SELECT *
                FROM products
                WHERE id = ?
                AND is_active = 1
            """, (item["product_id"],)).fetchone()

            if product is None:
                raise ValueError("A product in your cart is unavailable.")

            quantity = int(item["quantity"])

            if quantity <= 0:
                raise ValueError("Invalid product quantity.")

            if product["stock_quantity"] < quantity:
                raise ValueError(
                    f"Not enough stock for {product['name']}."
                )

            total_price = product["price"] * quantity
            subtotal += total_price

            order_products.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "product_image": product["image_filename"],
                "quantity": quantity,
                "unit_price": product["price"],
                "total_price": total_price
            })

        total_amount = subtotal + delivery_fee

        cursor = connection.execute("""
            INSERT INTO orders (
                customer_id,
                delivery_name,
                delivery_phone,
                delivery_address,
                delivery_city,
                delivery_state,
                subtotal,
                delivery_fee,
                total_amount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            delivery_name,
            delivery_phone,
            delivery_address,
            delivery_city,
            delivery_state,
            subtotal,
            delivery_fee,
            total_amount
        ))

        order_id = cursor.lastrowid

        for item in order_products:

            connection.execute("""
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    product_name,
                    product_image,
                    quantity,
                    unit_price,
                    total_price
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                item["product_id"],
                item["product_name"],
                item["product_image"],
                item["quantity"],
                item["unit_price"],
                item["total_price"]
            ))

            stock_update = connection.execute("""
                UPDATE products
                SET stock_quantity = stock_quantity - ?
                WHERE id = ?
                AND stock_quantity >= ?
            """, (
                item["quantity"],
                item["product_id"],
                item["quantity"]
            ))

            if stock_update.rowcount != 1:
                raise ValueError(
                    f"Stock changed for {item['product_name']}. "
                    "Please review your cart."
                )

        connection.commit()
        return order_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_order_by_id(order_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM orders
            WHERE id = ?
        """, (order_id,)).fetchone()

    finally:
        connection.close()


def get_order_items(order_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = ?
        """, (order_id,)).fetchall()

    finally:
        connection.close()


def get_customer_orders(customer_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM orders
            WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,)).fetchall()

    finally:
        connection.close()


def get_all_orders():
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT
                orders.*,
                customers.full_name,
                customers.email
            FROM orders
            JOIN customers
                ON orders.customer_id = customers.id
            ORDER BY orders.created_at DESC
        """).fetchall()

    finally:
        connection.close()


def update_order_status(order_id, status):
    allowed_statuses = {
        "Pending",
        "Confirmed",
        "Processing",
        "Shipped",
        "Delivered",
        "Cancelled"
    }

    if status not in allowed_statuses:
        raise ValueError("Invalid order status.")

    connection = get_connection()

    try:
        cursor = connection.execute("""
            UPDATE orders
            SET status = ?
            WHERE id = ?
        """, (status, order_id))

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


# =====================================================
# PAYMENT FUNCTIONS
# =====================================================

def add_payment(
    order_id,
    amount,
    payment_method,
    payment_reference=None
):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO payments (
                order_id,
                amount,
                payment_method,
                payment_reference
            )
            VALUES (?, ?, ?, ?)
        """, (
            order_id,
            amount,
            payment_method,
            payment_reference
        ))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def update_payment_status(payment_id, status):
    allowed_statuses = {
        "Pending",
        "Successful",
        "Failed",
        "Refunded"
    }

    if status not in allowed_statuses:
        raise ValueError("Invalid payment status.")

    connection = get_connection()

    try:
        payment = connection.execute("""
            SELECT order_id
            FROM payments
            WHERE id = ?
        """, (payment_id,)).fetchone()

        if payment is None:
            return False

        connection.execute("""
            UPDATE payments
            SET status = ?
            WHERE id = ?
        """, (status, payment_id))

        if status == "Successful":
            order_payment_status = "Paid"
        elif status == "Refunded":
            order_payment_status = "Refunded"
        elif status == "Failed":
            order_payment_status = "Failed"
        else:
            order_payment_status = "Unpaid"

        connection.execute("""
            UPDATE orders
            SET payment_status = ?
            WHERE id = ?
        """, (order_payment_status, payment["order_id"]))

        connection.commit()
        return True

    finally:
        connection.close()


def get_order_payments(order_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM payments
            WHERE order_id = ?
            ORDER BY created_at DESC
        """, (order_id,)).fetchall()

    finally:
        connection.close()


# =====================================================
# INITIALIZE DATABASE
# =====================================================

if __name__ == "__main__":
    create_tables()
    print("Grace Luxury database is ready!")