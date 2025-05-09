import sqlite3
import os

DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'database.db')

# HINWEIS: Dies ist ein Platzhalter. In einer echten Anwendung sollte dieser Kurs dynamisch abgerufen werden.
USD_TO_EUR_EXCHANGE_RATE = 0.92  # Beispiel: 1 USD = 0.92 EUR

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_asset_type_id(conn, asset_type_name):
    """Gets the ID for a given asset type name."""
    cursor = conn.execute("SELECT id FROM asset_types WHERE name = ?", (asset_type_name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    else:
        raise ValueError(f"Asset type '{asset_type_name}' not found in database.")

def buy_stock(user_id, asset_symbol, quantity, price_per_unit):
    """
    Execute a stock purchase transaction.
    User balance is in EUR, stock price is in USD.
    """
    conn = None
    try:
        conn = get_db_connection()
        asset_type_id = get_asset_type_id(conn, 'stock')
        
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return {"success": False, "message": "User not found."}
        
        current_balance_eur = user_data['balance']
        total_cost_usd = quantity * price_per_unit
        total_cost_eur = total_cost_usd * USD_TO_EUR_EXCHANGE_RATE
        
        if current_balance_eur < total_cost_eur:
            return {"success": False, "message": "Insufficient balance."}
        
        conn.execute("BEGIN TRANSACTION")
        
        new_balance_eur = current_balance_eur - total_cost_eur
        cursor.execute(
            "UPDATE users SET balance = ?, total_trades = total_trades + 1 WHERE id = ?", 
            (new_balance_eur, user_id)
        )
        
        # Store transaction price_per_unit in USD (actual asset price)
        cursor.execute("""
            INSERT INTO transactions 
            (user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type)
            VALUES (?, ?, ?, ?, ?, 'buy')
        """, (user_id, asset_type_id, asset_symbol, quantity, price_per_unit))
        
        conn.commit()
        return {"success": True, "message": f"Successfully purchased {quantity} shares of {asset_symbol} for ${total_cost_usd:.2f} (approx. €{total_cost_eur:.2f})."}
        
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return {"success": False, "message": f"Database error: {e}"}
    except ValueError as e:
        if conn:
            conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        if conn:
            conn.close()

def sell_stock(user_id, asset_symbol, quantity, price_per_unit):
    """
    Execute a stock sale transaction and update realized profit/loss.
    User balance and profit_loss are in EUR. Stock prices are in USD.
    """
    conn = None
    try:
        conn = get_db_connection()
        asset_type_id = get_asset_type_id(conn, 'stock')
        
        cursor = conn.cursor()
        
        # Check if user has enough stocks to sell (this logic remains based on quantity)
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN transaction_type = 'sell' THEN quantity ELSE 0 END), 0) as current_holding
            FROM transactions
            WHERE user_id = ? AND asset_symbol = ? AND asset_type_id = ?
        """, (user_id, asset_symbol, asset_type_id))
        
        holding_data = cursor.fetchone()
        current_holding = holding_data['current_holding'] if holding_data else 0
        
        if current_holding < quantity:
            return {"success": False, "message": f"Insufficient shares of {asset_symbol} to sell."}

        # --- FIFO Profit/Loss Calculation (in USD first) ---
        cursor.execute("""
            SELECT quantity, price_per_unit 
            FROM transactions
            WHERE user_id = ? AND asset_symbol = ? AND asset_type_id = ? AND transaction_type = 'buy'
            ORDER BY timestamp ASC
        """, (user_id, asset_symbol, asset_type_id))
        buy_transactions = cursor.fetchall()

        # Get total bought and sold quantities to find remaining buy lots
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE 0 END) as total_bought,
                SUM(CASE WHEN transaction_type = 'sell' THEN quantity ELSE 0 END) as total_sold
            FROM transactions
            WHERE user_id = ? AND asset_symbol = ? AND asset_type_id = ?
        """, (user_id, asset_symbol, asset_type_id))
        all_tx_summary = cursor.fetchone()
        
        temp_quantity_sold_previously = all_tx_summary['total_sold'] if all_tx_summary else 0
        
        effective_buy_lots = []
        for bt in buy_transactions:
            bt_quantity = float(bt['quantity'])
            bt_price = float(bt['price_per_unit']) # USD
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
            cost_for_current_sale_usd += sell_from_this_lot * lot['price_per_unit'] # USD
            quantity_for_current_sale_calc -= sell_from_this_lot
            
        if quantity_for_current_sale_calc > 0.0001:
            conn.rollback()
            return {"success": False, "message": f"Error in cost basis calculation for {asset_symbol}. Not enough purchase history for sale."}

        total_sale_value_usd = float(quantity) * float(price_per_unit) # price_per_unit ist USD
        realized_profit_or_loss_usd = total_sale_value_usd - cost_for_current_sale_usd
        
        # Convert to EUR for updating user's profit_loss
        realized_profit_or_loss_eur = realized_profit_or_loss_usd * USD_TO_EUR_EXCHANGE_RATE
        # --- End FIFO Profit/Loss Calculation ---
        
        conn.execute("BEGIN TRANSACTION")
        
        total_sale_amount_usd = float(quantity) * float(price_per_unit)
        total_sale_amount_eur = total_sale_amount_usd * USD_TO_EUR_EXCHANGE_RATE
        
        cursor.execute(
            """UPDATE users 
               SET balance = balance + ?, 
                   total_trades = total_trades + 1,
                   profit_loss = profit_loss + ? 
               WHERE id = ?""", 
            (total_sale_amount_eur, realized_profit_or_loss_eur, user_id)
        )
        
        # Store transaction price_per_unit in USD
        cursor.execute("""
            INSERT INTO transactions 
            (user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type)
            VALUES (?, ?, ?, ?, ?, 'sell')
        """, (user_id, asset_type_id, asset_symbol, quantity, price_per_unit))
        
        conn.commit()
        return {"success": True, "message": f"Successfully sold {quantity} shares of {asset_symbol} for ${total_sale_value_usd:.2f} (approx. €{total_sale_amount_eur:.2f}). Realized P/L: ${realized_profit_or_loss_usd:.2f} (approx. €{realized_profit_or_loss_eur:.2f})"}
        
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return {"success": False, "message": f"Database error: {e}"}
    except ValueError as e:
        if conn:
            conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        if conn:
            conn.close()

def show_user_portfolio(user_id):
    """
    Show the current portfolio for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with portfolio data and user's current balance from users table
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        asset_types_map = {}
        cursor.execute("SELECT id, name FROM asset_types")
        for row in cursor.fetchall():
            asset_types_map[row['id']] = row['name']
        
        cursor.execute("""
            SELECT 
                asset_symbol,
                asset_type_id,
                SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) as net_quantity
            FROM transactions
            WHERE user_id = ?
            GROUP BY asset_symbol, asset_type_id
            HAVING net_quantity > 0
        """, (user_id,))
        
        portfolio = []
        for row in cursor.fetchall():
            portfolio.append({
                "symbol": row['asset_symbol'],
                "type": asset_types_map.get(row['asset_type_id'], 'unknown'),
                "quantity": row['net_quantity']
            })
        
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        balance = user_data['balance'] if user_data else None
        
        return {
            "success": True,
            "portfolio": portfolio,
            "balance": balance
        }
        
    except sqlite3.Error as e:
        return {"success": False, "message": f"Database error: {e}", "portfolio": [], "balance": None}
    finally:
        if conn:
            conn.close()

def get_recent_transactions(user_id, limit=5):
    """Fetches the most recent transactions for a user."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT asset_symbol, quantity, price_per_unit, transaction_type, timestamp
            FROM transactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append(dict(row))
        return {"success": True, "transactions": transactions}
    except sqlite3.Error as e:
        return {"success": False, "message": f"Database error: {e}", "transactions": []}
    finally:
        if conn:
            conn.close()

def init_asset_types():
    """Initialize the asset_types table with basic types if empty."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM asset_types")
        count_data = cursor.fetchone()
        count = count_data['count'] if count_data else 0
        
        if count == 0:
            asset_types_to_insert = ['stock', 'crypto', 'forex']
            for asset_type in asset_types_to_insert:
                cursor.execute("INSERT INTO asset_types (name) VALUES (?)", (asset_type,))
            conn.commit()
            print("Asset types initialized.")
    except sqlite3.Error as e:
        print(f"Error initializing asset types: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_asset_types()
