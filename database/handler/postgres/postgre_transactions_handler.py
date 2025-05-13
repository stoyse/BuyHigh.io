import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import stock_data  # Import des stock_data Moduls für aktuelle Kurse
import database.handler.postgres.postgres_db_handler as db_handler  # Import des PostgreSQL DB Handlers

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

def get_asset_id_by_symbol(cursor, symbol):
    """
    Findet die Asset-ID für ein bestimmtes Symbol.
    """
    cursor.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
    asset = cursor.fetchone()
    if not asset:
        raise ValueError(f"Asset with symbol '{symbol}' not found.")
    return asset['id'] if isinstance(asset, dict) else asset[0]

def update_portfolio_on_buy(cursor, user_id, asset_symbol, quantity, price_per_unit):
    """
    Aktualisiert das Portfolio beim Kauf von Assets.
    """
    # Asset ID abrufen
    asset_id = get_asset_id_by_symbol(cursor, asset_symbol)
    
    # Prüfen, ob das Asset bereits im Portfolio des Benutzers ist
    cursor.execute("""
        SELECT quantity, average_buy_price FROM portfolio 
        WHERE user_id = %s AND asset_id = %s
    """, (user_id, asset_id))
    
    portfolio_entry = cursor.fetchone()
    
    if portfolio_entry:
        # Asset bereits vorhanden, Update durchführen
        current_quantity = float(portfolio_entry['quantity']) if isinstance(portfolio_entry, dict) else float(portfolio_entry[0])
        current_avg_price = float(portfolio_entry['average_buy_price']) if isinstance(portfolio_entry, dict) else float(portfolio_entry[1])
        
        # Neue Durchschnittskosten berechnen
        new_quantity = current_quantity + quantity
        new_avg_price = ((current_quantity * current_avg_price) + (quantity * price_per_unit)) / new_quantity
        
        # Portfolio aktualisieren
        cursor.execute("""
            UPDATE portfolio 
            SET quantity = %s, average_buy_price = %s, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = %s AND asset_id = %s
        """, (new_quantity, new_avg_price, user_id, asset_id))
    else:
        # Neuer Eintrag im Portfolio
        cursor.execute("""
            INSERT INTO portfolio (user_id, asset_id, quantity, average_buy_price)
            VALUES (%s, %s, %s, %s)
        """, (user_id, asset_id, quantity, price_per_unit))

def update_portfolio_on_sell(cursor, user_id, asset_symbol, quantity):
    """
    Aktualisiert das Portfolio beim Verkauf von Assets.
    """
    # Asset ID abrufen
    asset_id = get_asset_id_by_symbol(cursor, asset_symbol)
    
    # Aktuelle Portfolio-Position abrufen
    cursor.execute("""
        SELECT quantity FROM portfolio 
        WHERE user_id = %s AND asset_id = %s
    """, (user_id, asset_id))
    
    portfolio_entry = cursor.fetchone()
    
    if not portfolio_entry:
        raise ValueError(f"Asset {asset_symbol} not found in user's portfolio.")
    
    current_quantity = float(portfolio_entry['quantity']) if isinstance(portfolio_entry, dict) else float(portfolio_entry[0])
    new_quantity = current_quantity - quantity
    
    if abs(new_quantity) < 0.000001:  # Praktisch 0
        # Wenn keine Einheiten mehr übrig sind, den Eintrag löschen
        cursor.execute("""
            DELETE FROM portfolio 
            WHERE user_id = %s AND asset_id = %s
        """, (user_id, asset_id))
    elif new_quantity > 0:
        # Menge aktualisieren
        cursor.execute("""
            UPDATE portfolio 
            SET quantity = %s, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = %s AND asset_id = %s
        """, (new_quantity, user_id, asset_id))
    else:
        raise ValueError(f"Insufficient quantity of {asset_symbol} in portfolio.")

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
                
                # Portfolio aktualisieren
                update_portfolio_on_buy(cur, user_id, asset_symbol, quantity, price_per_unit)
                
                conn.commit()
                db_handler.manage_user_xp("buy", user_id, quantity=quantity)
                db_handler.check_user_level(user_id, db_handler.get_user_xp(user_id))
                
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
                
                # Portfolio aktualisieren
                update_portfolio_on_sell(cur, user_id, asset_symbol, quantity)
                
                conn.commit()
                db_handler.manage_user_xp("buy", user_id, quantity=quantity)
                db_handler.check_user_level(user_id, db_handler.get_user_xp(user_id))
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
    Verwendet aktuelle Marktdaten für die Preise, ansonsten default_price aus der DB.
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT p.quantity, p.average_buy_price, 
                           a.symbol, a.name, a.asset_type, a.sector, a.default_price
                    FROM portfolio p
                    JOIN assets a ON p.asset_id = a.id
                    WHERE p.user_id = %s
                """, (user_id,))
                
                portfolio = []
                for row in cur.fetchall():
                    symbol = row['symbol']
                    current_price = None # Wird später gesetzt
                    
                    # Versuche, den aktuellen Kurs von der API zu holen (für 1D Ansicht)
                    try:
                        df = stock_data.get_cached_or_live_data(symbol, '1D') # '1D' für den aktuellsten Schlusskurs
                        if df is not None and not df.empty and not getattr(df, 'is_demo', True): # Nur echte API-Daten verwenden
                            current_price = float(df['Close'].iloc[-1])
                        else:
                            print(f"API lieferte Demo-Daten oder keine Daten für {symbol} im Portfolio. Nutze DB Fallback.")
                    except Exception as e:
                        print(f"Fehler beim Abrufen des API-Kurses für {symbol} im Portfolio: {e}. Nutze DB Fallback.")

                    # Fallback-Logik, wenn current_price nicht durch echte API-Daten gesetzt wurde
                    if current_price is None:
                        if row['default_price'] is not None:
                            current_price = float(row['default_price'])
                        else:
                            # Allerletzter Fallback, wenn auch default_price fehlt
                            current_price = float(row['average_buy_price'])
                            print(f"Warnung: Weder API-Preis noch default_price für {symbol} verfügbar. Nutze average_buy_price.")
                    
                    avg_price = float(row['average_buy_price'])
                    performance = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
                    quantity = float(row['quantity'])
                    
                    # Stelle sicher, dass asset_type nicht null ist
                    asset_type = row['asset_type'] 
                    if asset_type is None or asset_type.strip() == '':
                        asset_type = 'stock'  # Standardwert, falls asset_type fehlt
                    
                    # Berechne den aktuellen Wert des Assets
                    item_value = quantity * current_price
                    
                    portfolio.append({
                        "symbol": symbol,
                        "name": row['name'],
                        "type": asset_type,
                        "quantity": quantity,
                        "average_price": avg_price,
                        "current_price": current_price,
                        "performance": performance,
                        "sector": row['sector'],
                        "value": item_value  # Wert des Assets für Asset Allocation
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

def get_asset_value(user_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT SUM(quantity * price_per_unit) AS total_value
                FROM transactions
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()
            return result['total_value'] if result else 0.0

def get_all_assets(active_only=True, asset_type=None):
    """
    Ruft alle Assets aus der Datenbank ab.
    
    Args:
        active_only (bool): Wenn True, werden nur aktive Assets zurückgegeben
        asset_type (str): Optional Filter für Asset-Typ (stock, crypto, forex, etc.)
        
    Returns:
        List[dict]: Liste aller Assets als Dictionary-Objekte
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM assets"
                where_clauses = []
                params = []
                
                if active_only:
                    where_clauses.append("is_active = %s")
                    params.append(True)
                
                if asset_type:
                    where_clauses.append("asset_type = %s")
                    params.append(asset_type)
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                query += " ORDER BY symbol"
                cur.execute(query, params)
                assets = cur.fetchall()
                return {"success": True, "assets": assets}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "assets": []}

def get_asset_by_symbol(symbol):
    """
    Ruft ein Asset anhand seines Symbols ab.
    Gibt default_price zurück, aber NICHT last_price.
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description, is_active, created_at, default_price
                    FROM assets WHERE symbol = %s
                """, (symbol,))
                asset = cur.fetchone()
                if asset:
                    return {"success": True, "asset": asset}
                else:
                    return {"success": False, "message": f"Asset with symbol '{symbol}' not found."}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}

def create_asset(symbol, name, asset_type, exchange=None, currency="USD", 
                sector=None, industry=None, logo_url=None, description=None):
    """
    Erstellt ein neues Asset in der Datenbank.
    
    Returns:
        dict: Erstelltes Asset oder Fehlermeldung
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO assets 
                    (symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description))
                conn.commit()
                return {"success": True, "asset": cur.fetchone()}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}

def get_default_price_for_symbol(symbol):
    """
    Holt den default_price für ein Asset aus der Datenbank.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT default_price FROM assets WHERE symbol = %s", (symbol,))
            row = cur.fetchone()
            if row and row.get('default_price') is not None:
                return float(row['default_price'])
            return None

def get_user_assets(user_id):
    """
    Holt alle Assets eines Benutzers aus der Datenbank.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.symbol, a.name, a.asset_type, a.sector, a.industry, a.logo_url, a.description, p.quantity, p.average_buy_price
                FROM portfolio p
                JOIN assets a ON p.asset_id = a.id
                WHERE p.user_id = %s
            """, (user_id,))
            return cur.fetchall()