from flask import Blueprint, render_template, g, request, flash, redirect, url_for
from utils import login_required
import database.handler.db_handler as db_handler
import logging  # Add logging import
import stock_news
from rich import print

# Configure basic logging
# logging.basicConfig(level=logging.DEBUG) # Wird jetzt in app.py global konfiguriert
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    logger.info(f"Index-Seite aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Nicht angemeldet'}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    logger.debug(f"Index: Dark Mode Active: {dark_mode_active}")
    return render_template('index.html', darkmode=dark_mode_active)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    logger.info(f"Dashboard aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'} (ID: {g.user.get('id') if g.user else 'N/A'})")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Import transactions_handler locally to avoid potential circular imports at top level
    import transactions_handler 
    logger.debug("Lade Portfolio-Daten...")
    portfolio_data = transactions_handler.show_user_portfolio(g.user['id'])
    logger.debug(f"Portfolio-Daten geladen: Erfolg={portfolio_data.get('success', False)}, Anzahl Items={len(portfolio_data.get('portfolio', []))}")
    
    logger.debug("Lade letzte Transaktionen...")
    recent_transactions_data = transactions_handler.get_recent_transactions(g.user['id'])
    logger.debug(f"Letzte Transaktionen geladen: Anzahl={len(recent_transactions_data.get('transactions', []))}")
    
    # Generate a dog message based on portfolio or market conditions
    logger.debug("Generiere Hundemeldung...")
    dog_message = generate_dog_message(g.user, portfolio_data)
    
    # Debug output
    logger.debug(f"Generierte Hundemeldung: '{dog_message}'")
    logger.debug(f"Benutzerdaten für Dashboard: {g.user}")
    logger.debug(f"Portfolio-Daten Erfolg: {portfolio_data.get('success', False)}")
    
    return render_template('dashboard.html', 
                           user=g.user, 
                           darkmode=dark_mode_active,
                           portfolio_data=portfolio_data,
                           recent_transactions=recent_transactions_data.get('transactions', []),
                           dog_message=dog_message)

# Generate a personalized dog message based on user data and portfolio
def generate_dog_message(user, portfolio_data):
    logger.debug(f"generate_dog_message aufgerufen für Benutzer: {user.get('username')}")
    # Default message if we can't personalize
    default_message = "Woof! Willkommen zu deinem Dashboard!"
    
    # Check if user has any portfolio data
    if portfolio_data and portfolio_data.get('success') and portfolio_data.get('portfolio'):
        # User has portfolio items
        if len(portfolio_data['portfolio']) > 0:
            message = f"Hey {user['username']}! Du hast {len(portfolio_data['portfolio'])} Assets in deinem Portfolio. Gute Arbeit!"
            logger.debug(f"Hundemeldung (Portfolio): {message}")
            return message
    
    # Check user's profit/loss
    profit_loss = user.get('profit_loss', 0)
    if profit_loss > 0:
        message = f"Toll gemacht! Du bist im Plus mit €{profit_loss:.2f} Gewinn!"
        logger.debug(f"Hundemeldung (Gewinn): {message}")
        return message
    elif profit_loss < 0:
        message = f"Kopf hoch! Dein aktueller Verlust ist €{abs(profit_loss):.2f}. Das wird bald besser!"
        logger.debug(f"Hundemeldung (Verlust): {message}")
        return message
    
    # Check if user is new (few or no trades)
    total_trades = user.get('total_trades', 0)
    if total_trades < 5:
        message = f"Willkommen bei BuyHigh.io! Starte deine ersten Trades und werde zum Trading-Profi!"
        logger.debug(f"Hundemeldung (Neuer Benutzer): {message}")
        return message
    
    logger.debug(f"Hundemeldung (Default): {default_message}")
    return default_message

@main_bp.route('/trade')
@login_required
def trade():
    logger.info(f"Trade-Seite aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('trade.html', user=g.user, darkmode=dark_mode_active)

@main_bp.route('/news')
@login_required
def news():
    logger.info(f"News-Seite (allgemein) aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    news_data = stock_news.fetch_general_news("general")
    logger.debug(f"Allgemeine Nachrichten abgerufen: {len(news_data) if news_data else 0} Artikel")
    # print(f'[cyan]General news data:', news_data) # Beibehalten für Rich-Print, falls gewünscht
    return render_template('news.html', user=g.user, darkmode=dark_mode_active, news_items=news_data)

@main_bp.route('/news/<symbol>')
@login_required
def company_news(symbol):
    logger.info(f"News-Seite für Symbol '{symbol}' aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    news_data = stock_news.fetch_company_news(symbol, "2025-01-01", "2025-01-02") # Daten sind statisch, ggf. anpassen
    logger.debug(f"Nachrichten für Symbol '{symbol}' abgerufen: {len(news_data) if news_data else 0} Artikel")
    # print(f'[cyan]Symbol: {symbol} | News data:', news_data) # Beibehalten für Rich-Print
    return render_template('news.html', user=g.user, darkmode=dark_mode_active, news_items=news_data)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    logger.info(f"Einstellungsseite aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'} (Methode: {request.method})")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    import auth as auth_module

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        logger.debug(f"POST-Anfrage an Einstellungen: form_type='{form_type}'")

        if form_type == 'theme_settings':
            new_theme = request.form.get('theme')
            logger.info(f"Benutzer {g.user['id']} versucht Theme zu ändern auf: {new_theme}")
            if new_theme in ['light', 'dark']:
                if db_handler.update_user_theme(g.user['id'], new_theme):
                    flash('Theme erfolgreich aktualisiert.', 'success')
                    logger.info(f"Theme für Benutzer {g.user['id']} erfolgreich auf {new_theme} aktualisiert.")
                    g.user = db_handler.get_user_by_id(g.user['id']) 
                    dark_mode_active = g.user and g.user.get('theme') == 'dark'
                else:
                    flash('Fehler beim Aktualisieren des Themes.', 'danger')
                    logger.error(f"Fehler beim Aktualisieren des Themes für Benutzer {g.user['id']} auf {new_theme}.")
            else:
                flash('Ungültige Theme-Auswahl.', 'danger')
                logger.warning(f"Ungültige Theme-Auswahl '{new_theme}' durch Benutzer {g.user['id']}.")

        elif form_type == 'password_settings':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')
            logger.info(f"Benutzer {g.user['id']} versucht Passwort zu ändern.")

            # Längen für Logging, nicht die Passwörter selbst
            logger.debug(f"Passwortänderung: Aktuelles PW Länge: {len(current_password) if current_password else 0}, Neues PW Länge: {len(new_password) if new_password else 0}")

            if not current_password or not new_password or not confirm_new_password:
                flash('Alle Passwortfelder müssen ausgefüllt sein.', 'danger')
                logger.warning(f"Passwortänderung für Benutzer {g.user['id']} fehlgeschlagen: Nicht alle Felder ausgefüllt.")
            elif not auth_module.check_password(g.user['password_hash'], current_password): # Annahme: Lokaler Hash für alte Logik, ggf. an Firebase anpassen
                flash('Aktuelles Passwort ist nicht korrekt.', 'danger')
                logger.warning(f"Passwortänderung für Benutzer {g.user['id']} fehlgeschlagen: Aktuelles Passwort falsch.")
            elif new_password != confirm_new_password:
                flash('Die neuen Passwörter stimmen nicht überein.', 'danger')
                logger.warning(f"Passwortänderung für Benutzer {g.user['id']} fehlgeschlagen: Neue Passwörter stimmen nicht überein.")
            elif len(new_password) < 6:
                flash('Das neue Passwort muss mindestens 6 Zeichen lang sein.', 'danger')
                logger.warning(f"Passwortänderung für Benutzer {g.user['id']} fehlgeschlagen: Neues Passwort zu kurz.")
            else:
                # Hier sollte die Firebase Passwortänderung implementiert sein, falls auth_module.hash_password und db_handler.update_user_password veraltet sind
                # Für dieses Beispiel wird der alte Flow beibehalten, aber mit Logging versehen
                logger.debug(f"Versuche Passwort-Hash für Benutzer {g.user['id']} zu aktualisieren (alter Flow).")
                new_password_hash = auth_module.hash_password(new_password) # Veraltet, wenn Firebase genutzt wird
                if db_handler.update_user_password(g.user['id'], new_password_hash): # Veraltet
                    flash('Passwort erfolgreich geändert.', 'success')
                    logger.info(f"Passwort für Benutzer {g.user['id']} erfolgreich geändert (alter Flow).")
                else:
                    flash('Fehler beim Ändern des Passworts.', 'danger')
                    logger.error(f"Fehler beim Ändern des Passworts für Benutzer {g.user['id']} (alter Flow).")
        
        return redirect(url_for('main.settings'))

    return render_template('settings.html', user=g.user, darkmode=dark_mode_active)

