import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

USD_TO_EUR_EXCHANGE_RATE = 0.92  # Beispielkurs, wie im SQLite-Handler

def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

def create_transactions_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    asset_type_id INTEGER,
                    asset_symbol VARCHAR(20) NOT NULL,
                    quantity FLOAT NOT NULL,
                    price_per_unit FLOAT,
                    transaction_type VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

def init_asset_types():
    """
    Initialisiert die Tabelle asset_types, falls sie nicht existiert und fügt Standardwerte ein.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS asset_types (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL
                );
            """)
            # Prüfe, ob schon Werte existieren
            cur.execute("SELECT COUNT(*) FROM asset_types")
            count = cur.fetchone()[0]
            if count == 0:
                for asset_type in ['stock', 'crypto', 'forex']:
                    cur.execute("INSERT INTO asset_types (name) VALUES (%s) ON CONFLICT DO NOTHING", (asset_type,))
            conn.commit()

def get_asset_type_id(asset_type_name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM asset_types WHERE name = %s", (asset_type_name,))
            row = cur.fetchone()
            if row:
                return row[0]
            else:
                raise ValueError(f"Asset type '{asset_type_name}' not found in database.")

def buy_stock(user_id, asset_symbol, quantity, price_per_unit):
    """
    Führt einen Aktienkauf für den Benutzer durch (PostgreSQL).
    User balance ist in EUR, price_per_unit in USD.
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                asset_type_id = get_asset_type_id('stock')
                cur.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                if not user:
                    return {"success": False, "message": "User not found."}
                current_balance_eur = user['balance']
                total_cost_usd = quantity * price_per_unit
                total_cost_eur = total_cost_usd * USD_TO_EUR_EXCHANGE_RATE
                if current_balance_eur < total_cost_eur:
                    return {"success": False, "message": "Insufficient balance."}
                cur.execute("BEGIN;")
                new_balance_eur = current_balance_eur - total_cost_eur
                cur.execute(
                    "UPDATE users SET balance = %s, total_trades = total_trades + 1 WHERE id = %s",
                    (new_balance_eur, user_id)
                )
                cur.execute("""
                    INSERT INTO transactions 
                    (user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type)
                    VALUES (%s, %s, %s, %s, %s, 'buy')
                    RETURNING id, user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type, timestamp;
                """, (user_id, asset_type_id, asset_symbol, quantity, price_per_unit))
                transaction = cur.fetchone()
                conn.commit()
                return {"success": True, "transaction": transaction, "message": f"Successfully purchased {quantity} shares of {asset_symbol} for ${total_cost_usd:.2f} (approx. €{total_cost_eur:.2f})."}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}

def sell_stock(user_id, asset_symbol, quantity, price_per_unit):
    """
    Führt einen Aktienverkauf für den Benutzer durch (PostgreSQL) und berechnet realisierten Gewinn/Verlust (FIFO).
    User balance und profit_loss sind in EUR, price_per_unit in USD.
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                asset_type_id = get_asset_type_id('stock')
                # Prüfe, ob genug Aktien vorhanden sind
                cur.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE 0 END), 0) -
                        COALESCE(SUM(CASE WHEN transaction_type = 'sell' THEN quantity ELSE 0 END), 0) as current_holding
                    FROM transactions
                    WHERE user_id = %s AND asset_symbol = %s AND asset_type_id = %s
                """, (user_id, asset_symbol, asset_type_id))
                holding_data = cur.fetchone()
                current_holding = holding_data['current_holding'] if holding_data else 0
                if current_holding < quantity:
                    return {"success": False, "message": f"Insufficient shares of {asset_symbol} to sell."}
                # FIFO Profit/Loss Calculation
                cur.execute("""
                    SELECT quantity, price_per_unit 
                    FROM transactions
                    WHERE user_id = %s AND asset_symbol = %s AND asset_type_id = %s AND transaction_type = 'buy'
                    ORDER BY timestamp ASC
                """, (user_id, asset_symbol, asset_type_id))
                buy_transactions = cur.fetchall()
                cur.execute("""
                    SELECT 
                        SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE 0 END) as total_bought,
                        SUM(CASE WHEN transaction_type = 'sell' THEN quantity ELSE 0 END) as total_sold
                    FROM transactions
                    WHERE user_id = %s AND asset_symbol = %s AND asset_type_id = %s
                """, (user_id, asset_symbol, asset_type_id))
                all_tx_summary = cur.fetchone()
                temp_quantity_sold_previously = all_tx_summary['total_sold'] if all_tx_summary else 0
                effective_buy_lots = []
                for bt in buy_transactions:
                    bt_quantity = float(bt['quantity'])
                    bt_price = float(bt['price_per_unit'])
                    if temp_quantity_sold_previously >= bt_quantity:
                        temp_quantity_sold_previously -= bt_quantity
                    else:
                        remaining_in_lot = bt_quantity - temp_quantity_sold_previously
                        temp_quantity_sold_previously = 0
                        if remaining_in_lot > 0:
                            effective_buy_lots.append({'quantity': remaining_in_lot, 'price_per_unit': bt_price})
                quantity_for_current_sale_calc = float(quantity)
                cost_for_current_sale_usd = 0.0
                for lot in effective_buy_lots:
                    if quantity_for_current_sale_calc == 0:
                        break
                    sell_from_this_lot = min(quantity_for_current_sale_calc, lot['quantity'])
                    cost_for_current_sale_usd += sell_from_this_lot * lot['price_per_unit']
                    quantity_for_current_sale_calc -= sell_from_this_lot
                if quantity_for_current_sale_calc > 0.0001:
                    conn.rollback()
                    return {"success": False, "message": f"Error in cost basis calculation for {asset_symbol}. Not enough purchase history for sale."}
                total_sale_value_usd = float(quantity) * float(price_per_unit)
                realized_profit_or_loss_usd = total_sale_value_usd - cost_for_current_sale_usd
                realized_profit_or_loss_eur = realized_profit_or_loss_usd * USD_TO_EUR_EXCHANGE_RATE
                # Verkaufserlös in EUR
                total_sale_amount_eur = total_sale_value_usd * USD_TO_EUR_EXCHANGE_RATE
                cur.execute("SELECT balance, profit_loss FROM users WHERE id = %s", (user_id,))
                user_data = cur.fetchone()
                if not user_data:
                    return {"success": False, "message": "User not found."}
                cur.execute("BEGIN;")
                cur.execute(
                    """UPDATE users 
                       SET balance = balance + %s, 
                           total_trades = total_trades + 1,
                           profit_loss = profit_loss + %s 
                       WHERE id = %s""", 
                    (total_sale_amount_eur, realized_profit_or_loss_eur, user_id)
                )
                cur.execute("""
                    INSERT INTO transactions 
                    (user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type)
                    VALUES (%s, %s, %s, %s, %s, 'sell')
                    RETURNING id, user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type, timestamp;
                """, (user_id, asset_type_id, asset_symbol, quantity, price_per_unit))
                transaction = cur.fetchone()
                conn.commit()
                return {
                    "success": True,
                    "transaction": transaction,
                    "message": f"Successfully sold {quantity} shares of {asset_symbol} for ${total_sale_value_usd:.2f} (approx. €{total_sale_amount_eur:.2f}). Realized P/L: ${realized_profit_or_loss_usd:.2f} (approx. €{realized_profit_or_loss_eur:.2f})"
                }
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}

def show_user_portfolio(user_id):
    """
    Zeigt das aktuelle Portfolio für einen Benutzer (PostgreSQL).
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name FROM asset_types")
                asset_types_map = {row['id']: row['name'] for row in cur.fetchall()}
                cur.execute("""
                    SELECT 
                        asset_symbol,
                        asset_type_id,
                        SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) as net_quantity
                    FROM transactions
                    WHERE user_id = %s
                    GROUP BY asset_symbol, asset_type_id
                    HAVING SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) > 0
                """, (user_id,))
                portfolio = []
                for row in cur.fetchall():
                    portfolio.append({
                        "symbol": row['asset_symbol'],
                        "type": asset_types_map.get(row['asset_type_id'], 'unknown'),
                        "quantity": row['net_quantity']
                    })
                cur.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
                user_data = cur.fetchone()
                balance = user_data['balance'] if user_data else None
                return {
                    "success": True,
                    "portfolio": portfolio,
                    "balance": balance
                }
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "portfolio": [], "balance": None}

def get_recent_transactions(user_id, limit=5):
    """
    Holt die letzten Transaktionen für einen Benutzer (PostgreSQL).
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT asset_symbol, quantity, price_per_unit, transaction_type, timestamp
                    FROM transactions
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (user_id, limit))
                transactions = [dict(row) for row in cur.fetchall()]
                return {"success": True, "transactions": transactions}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "transactions": []}

def create_transaction(user_id, asset_type, asset_symbol, quantity, price, transaction_type):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            asset_type_id = get_asset_type_id(asset_type)
            cur.execute("""
                INSERT INTO transactions (user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *;
            """, (user_id, asset_type_id, asset_symbol, quantity, price, transaction_type))
            transaction = cur.fetchone()
            conn.commit()
            return transaction

def get_transaction_by_id(transaction_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM transactions WHERE id = %s;", (transaction_id,))
            return cur.fetchone()

def get_transactions_by_user_id(user_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM transactions WHERE user_id = %s ORDER BY timestamp DESC;", (user_id,))
            return cur.fetchall()

def delete_transaction(transaction_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM transactions WHERE id = %s;", (transaction_id,))
            conn.commit()
