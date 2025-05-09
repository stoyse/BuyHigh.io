import sqlite3
import os

DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'database.db')

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
    
    Args:
        user_id: ID of the user making the purchase
        asset_symbol: Symbol of the asset being purchased (e.g., 'AAPL')
        quantity: Number of shares to buy
        price_per_unit: Price per share
        
    Returns:
        Dictionary with success status and message
    """
    conn = None
    try:
        conn = get_db_connection()
        asset_type_id = get_asset_type_id(conn, 'stock')
        
        # Check if user has enough balance
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return {"success": False, "message": "User not found."}
        
        current_balance = user_data['balance']
        total_cost = quantity * price_per_unit
        
        if current_balance < total_cost:
            return {"success": False, "message": "Insufficient balance."}
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Update user's balance
        new_balance = current_balance - total_cost
        cursor.execute(
            "UPDATE users SET balance = ?, total_trades = total_trades + 1 WHERE id = ?", 
            (new_balance, user_id)
        )
        
        # Record the transaction
        cursor.execute("""
            INSERT INTO transactions 
            (user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type)
            VALUES (?, ?, ?, ?, ?, 'buy')
        """, (user_id, asset_type_id, asset_symbol, quantity, price_per_unit))
        
        conn.commit()
        return {"success": True, "message": f"Successfully purchased {quantity} shares of {asset_symbol}."}
        
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
    Execute a stock sale transaction.
    
    Args:
        user_id: ID of the user selling the stock
        asset_symbol: Symbol of the asset being sold (e.g., 'AAPL')
        quantity: Number of shares to sell
        price_per_unit: Price per share
        
    Returns:
        Dictionary with success status and message
    """
    conn = None
    try:
        conn = get_db_connection()
        asset_type_id = get_asset_type_id(conn, 'stock')
        
        # Check if user has enough stocks to sell
        cursor = conn.cursor()
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
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Update user's balance
        total_sale_amount = quantity * price_per_unit
        cursor.execute(
            "UPDATE users SET balance = balance + ?, total_trades = total_trades + 1 WHERE id = ?", 
            (total_sale_amount, user_id)
        )
        
        # Record the transaction
        cursor.execute("""
            INSERT INTO transactions 
            (user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type)
            VALUES (?, ?, ?, ?, ?, 'sell')
        """, (user_id, asset_type_id, asset_symbol, quantity, price_per_unit))
        
        conn.commit()
        return {"success": True, "message": f"Successfully sold {quantity} shares of {asset_symbol}."}
        
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
