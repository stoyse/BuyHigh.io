from flask import Blueprint, render_template, g, request, flash, redirect, url_for
from utils import login_required
import db_handler
import logging  # Add logging import
import stock_news
from rich import print

# Configure basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('index.html', darkmode=dark_mode_active)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Import transactions_handler locally to avoid potential circular imports at top level
    import transactions_handler 
    portfolio_data = transactions_handler.show_user_portfolio(g.user['id'])
    recent_transactions_data = transactions_handler.get_recent_transactions(g.user['id'])
    
    # Generate a dog message based on portfolio or market conditions
    dog_message = generate_dog_message(g.user, portfolio_data)
    
    # Debug output
    logger.debug(f"Generated dog message: '{dog_message}'")
    logger.debug(f"User data: {g.user}")
    logger.debug(f"Portfolio data success: {portfolio_data.get('success', False)}")
    
    return render_template('dashboard.html', 
                           user=g.user, 
                           darkmode=dark_mode_active,
                           portfolio_data=portfolio_data,
                           recent_transactions=recent_transactions_data.get('transactions', []),
                           dog_message=dog_message)  # Pass the dog message to the template

# Generate a personalized dog message based on user data and portfolio
def generate_dog_message(user, portfolio_data):
    # Default message if we can't personalize
    default_message = "Woof! Willkommen zu deinem Dashboard!"
    
    # Check if user has any portfolio data
    if portfolio_data and portfolio_data.get('success') and portfolio_data.get('portfolio'):
        # User has portfolio items
        if len(portfolio_data['portfolio']) > 0:
            return f"Hey {user['username']}! Du hast {len(portfolio_data['portfolio'])} Assets in deinem Portfolio. Gute Arbeit!"
    
    # Check user's profit/loss
    if user.get('profit_loss', 0) > 0:
        return f"Toll gemacht! Du bist im Plus mit €{user['profit_loss']:.2f} Gewinn!"
    elif user.get('profit_loss', 0) < 0:
        return f"Kopf hoch! Dein aktueller Verlust ist €{abs(user['profit_loss']):.2f}. Das wird bald besser!"
    
    # Check if user is new (few or no trades)
    if user.get('total_trades', 0) < 5:
        return f"Willkommen bei BuyHigh.io! Starte deine ersten Trades und werde zum Trading-Profi!"
    
    return default_message

@main_bp.route('/trade')
@login_required
def trade():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('trade.html', user=g.user, darkmode=dark_mode_active)

@main_bp.route('/news')
@login_required
def news():  # Ändere den Funktionsnamen
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    news_data = stock_news.fetch_general_news("general")
    print(f'[cyan]General news data:', news_data)
    return render_template('news.html', user=g.user, darkmode=dark_mode_active, news_items=news_data)

@main_bp.route('/news/<symbol>')
@login_required
def company_news(symbol):
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    news_data = stock_news.fetch_company_news(symbol, "2025-01-01", "2025-01-02")
    print(f'[cyan]Symbol: {symbol} | News data:', news_data)
    return render_template('news.html', user=g.user, darkmode=dark_mode_active, news_items=news_data)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    # Import auth module locally for password checking if needed, or ensure it's imported at top
    import auth as auth_module


    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'theme_settings':
            new_theme = request.form.get('theme')
            if new_theme in ['light', 'dark']:
                if db_handler.update_user_theme(g.user['id'], new_theme):
                    flash('Theme erfolgreich aktualisiert.', 'success')
                    g.user = db_handler.get_user_by_id(g.user['id']) 
                    dark_mode_active = g.user and g.user.get('theme') == 'dark'
                else:
                    flash('Fehler beim Aktualisieren des Themes.', 'danger')
            else:
                flash('Ungültige Theme-Auswahl.', 'danger')

        elif form_type == 'password_settings':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            if not current_password or not new_password or not confirm_new_password:
                flash('Alle Passwortfelder müssen ausgefüllt sein.', 'danger')
            elif not auth_module.check_password(g.user['password_hash'], current_password):
                flash('Aktuelles Passwort ist nicht korrekt.', 'danger')
            elif new_password != confirm_new_password:
                flash('Die neuen Passwörter stimmen nicht überein.', 'danger')
            elif len(new_password) < 6:
                flash('Das neue Passwort muss mindestens 6 Zeichen lang sein.', 'danger')
            else:
                new_password_hash = auth_module.hash_password(new_password)
                if db_handler.update_user_password(g.user['id'], new_password_hash):
                    flash('Passwort erfolgreich geändert.', 'success')
                else:
                    flash('Fehler beim Ändern des Passworts.', 'danger')
        
        return redirect(url_for('main.settings'))

    return render_template('settings.html', user=g.user, darkmode=dark_mode_active)
