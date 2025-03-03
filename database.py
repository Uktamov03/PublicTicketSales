import psycopg2
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse

def get_db_connection():
    """Database connection string from environment variable"""
    db_url = os.getenv('postgresql://postgres:kswjfmPjCelLAMRbhGpKIzAxeXdlLWvU@postgres.railway.internal:5432/railway')
    if db_url:
        # To'g'ridan-to'g'ri URL bilan ulanish
        connection = psycopg2.connect(db_url)
    else:
        # URL mavjud emas bo'lsa eski usul bilan ulanish
        url = urlparse(os.getenv('postgresql://postgres:kswjfmPjCelLAMRbhGpKIzAxeXdlLWvU@postgres.railway.internal:5432/railway'))
        connection = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    return connection

# Ulanishni tekshirish
conn = get_db_connection()
if conn:
    conn.close()
    print("🔌 Ulanish yopildi.")


def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Customers table
    cur.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id SERIAL PRIMARY KEY,
                  name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  workplace TEXT,
                  registration_date DATE)''')

    # Orders table
    cur.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id SERIAL PRIMARY KEY,
                  customer_id INTEGER REFERENCES customers(id),
                  square_meters REAL,
                  price_per_meter REAL,
                  banner_price REAL,
                  delivery_price REAL,
                  total_price REAL,
                  banner_dimensions TEXT,
                  delivery_status TEXT,
                  installation_status TEXT,
                  order_date DATE)''')

    # Payments table
    cur.execute('''CREATE TABLE IF NOT EXISTS payments
                 (id SERIAL PRIMARY KEY,
                  order_id INTEGER REFERENCES orders(id),
                  amount REAL,
                  payment_date DATE)''')

    conn.commit()
    cur.close()
    conn.close()

def add_customer(name, phone, workplace):
    """Add new customer"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''INSERT INTO customers (name, phone, workplace, registration_date)
                   VALUES (%s, %s, %s, %s)''', 
                (name, phone, workplace, datetime.now().date()))
    conn.commit()
    cur.close()
    conn.close()

def get_customers():
    """Get all customers"""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df

def add_order(customer_id, square_meters, price_per_meter, banner_dimensions, 
              delivery_status, installation_status, banner_price=0, delivery_price=0):
    """Add new order"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure all values are float for calculation
    square_meters = float(square_meters)
    price_per_meter = float(price_per_meter)
    banner_price = float(banner_price)
    delivery_price = float(delivery_price)

    # Calculate total price - faqat banner narxi va yetkazib berish narxini qo'shamiz
    total_price = banner_price + delivery_price

    try:
        cur.execute('''INSERT INTO orders 
                       (customer_id, square_meters, price_per_meter, banner_price,
                        delivery_price, total_price, banner_dimensions,
                        delivery_status, installation_status, order_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (customer_id, square_meters, price_per_meter, banner_price,
                     delivery_price, total_price, banner_dimensions,
                     delivery_status, installation_status, datetime.now().date()))
        conn.commit()
    except Exception as e:
        print(f"Error in add_order: {str(e)}")
        raise e
    finally:
        cur.close()
        conn.close()

def get_orders():
    """Get all orders with customer names"""
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT 
            o.*,
            c.name as customer_name,
            o.banner_price + o.delivery_price as total_amount
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        ORDER BY o.order_date DESC
    """, conn)
    conn.close()
    return df

def add_payment(order_id, amount):
    """Add new payment"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''INSERT INTO payments (order_id, amount, payment_date)
                   VALUES (%s, %s, %s)''', 
                (order_id, float(amount), datetime.now().date()))
    conn.commit()
    cur.close()
    conn.close()

def get_payments():
    """Get all payments with order and customer details"""
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT p.*, o.total_price, c.name as customer_name
        FROM payments p
        JOIN orders o ON p.order_id = o.id
        JOIN customers c ON o.customer_id = c.id
        ORDER BY p.payment_date DESC
    """, conn)
    conn.close()
    return df
