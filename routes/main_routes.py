from flask import Blueprint, render_template, g, request, flash, redirect, url_for
from utils import login_required
import database.handler.postgres.postgres_db_handler as db_handler
import logging  # Add logging import
import stock_news
from rich import print
import database.handler.postgres.postgre_education_handler as edu_handler
import datetime
import database.handler.postgres.postgre_market_mayhem_handler as market_mayhem_handler

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
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    logger.info(f"Dashboard aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'} (ID: {g.user.get('id') if g.user else 'N/A'})")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Import transactions_handler locally to avoid potential circular imports at top level
    import database.handler.postgres.postgre_transactions_handler as transactions_handler 
    logger.debug("Lade Portfolio-Daten...")
    portfolio_data = transactions_handler.show_user_portfolio(g.user['id'])
    logger.debug(f"Portfolio-Daten geladen: Erfolg={portfolio_data.get('success', False)}, Anzahl Items={len(portfolio_data.get('portfolio', []))}")
    user_assets = portfolio_data.get('portfolio', [])
    print(f'[cyan]User: Assets:', user_assets) 
    user_assets_types = [asset.get('type') for asset in user_assets]
    print(f'[cyan]User: Asset Types:', user_assets_types)  
    # Calculate percentage of each asset type in the portfolio
    logger.debug("Berechne prozentuale Verteilung der Asset-Typen...")
    asset_type_distribution = {}
    total_assets = sum(item.get('quantity', 0) for item in user_assets)
    #xp system
    user_xp = db_handler.get_user_xp(g.user['id'])
    print(f'[purple]User: XP:', user_xp)
    # Hole Level und Leveldaten VOR der XP-Prozent-Berechnung
    user_level = db_handler.get_user_level(g.user['id'])
    print(f'[purple]User: Level:', user_level)
    # Hole Leveldaten aus der DB und wandle sie in Dicts um
    levels_raw = db_handler.get_xp_levels()
    levels = [
        {'level': row[0], 'xp_required': row[1], 'bonus_percentage': row[2]}
        for row in levels_raw
    ]
    print(f'[purple]Levels:', levels)
    def calculate_xp_percentage(current_xp, current_level, levels):
        """
        Berechnet den prozentualen Fortschritt zum nächsten Level basierend auf aktuellem XP und XP-Anforderung des nächsten Levels.
        """
        current_level_data = next((lvl for lvl in levels if lvl['level'] == current_level), None)
        next_level_data = next((lvl for lvl in levels if lvl['level'] == current_level + 1), None)

        if not next_level_data:
            # Max-Level erreicht, immer 100%
            return 100.0

        xp_needed_for_next_level = next_level_data['xp_required']
        xp_in_level = current_xp
        percent = (xp_in_level / xp_needed_for_next_level) * 100
        # Clamp zwischen 0 und 100
        return max(0.0, min(percent, 100.0))
    
    # Calculate and print the user's XP percentage to the next level
    xp_percentage = calculate_xp_percentage(user_xp, user_level, levels)
    print(f'[purple]User percent to next level: {xp_percentage:.2f}%')
    if total_assets > 0:
        for asset in user_assets:
            asset_type = asset.get('type', 'Unknown')
            asset_quantity = asset.get('quantity', 0)
            if asset_type in asset_type_distribution:
                asset_type_distribution[asset_type] += asset_quantity
            else:
                asset_type_distribution[asset_type] = asset_quantity

        # Convert quantities to percentages
        for asset_type in asset_type_distribution:
            asset_type_distribution[asset_type] = (asset_type_distribution[asset_type] / total_assets) * 100


        print(f'[cyan]Asset Type Distribution:', asset_type_distribution)

    logger.debug(f"Asset-Typ-Verteilung berechnet: {asset_type_distribution}")
    print(f'[cyan]Asset Type Distribution: {asset_type_distribution}')
    # Calculate total portfolio value - this was missing
    portfolio_total_value = 0
    asset_values = []
    if portfolio_data and portfolio_data.get('success') and portfolio_data.get('portfolio'):
        for item in portfolio_data.get('portfolio', []):
            value = item.get('quantity', 0) * item.get('current_price', 0)
            portfolio_total_value += value
            # Füge den Wert auch explizit zum Item hinzu, falls er fehlt
            if 'value' not in item:
                item['value'] = value
            asset_values.append(item.get('value', 0))
    
    logger.debug("Lade letzte Transaktionen...")
    recent_transactions_data = transactions_handler.get_recent_transactions(g.user['id'])
    logger.debug(f"Letzte Transaktionen geladen: Anzahl={len(recent_transactions_data.get('transactions', []))}")
    
    
    # Debug output
    logger.debug(f"Benutzerdaten für Dashboard: {g.user}")
    logger.debug(f"Portfolio-Daten Erfolg: {portfolio_data.get('success', False)}")
    
    # Calculate profit_loss_percentage
    if g.user['balance'] > 0:  # Sicherstellen, dass Division durch 0 vermieden wird
        g.user['profit_loss_percentage'] = (g.user['profit_loss'] / g.user['balance']) * 100
    else:
        g.user['profit_loss_percentage'] = 0.0
    print(f'[cyan]Benutzer {g.user["username"]} hat eine Gewinn-/Verlustquote von {g.user["profit_loss_percentage"]:.2f}%')    
    # Calculate asset allocation (percentage of each asset in portfolio)
    asset_allocation = []
    if portfolio_total_value > 0:
        logger.debug("Berechne Asset-Allocation für das Portfolio...")
        for item in portfolio_data.get('portfolio', []):
            allocation = {
                'symbol': item.get('symbol'),
                'name': item.get('asset_name', item.get('name', item.get('symbol'))),
                'percentage': (item.get('value', 0) / portfolio_total_value) * 100
            }
            asset_allocation.append(allocation)
        logger.debug(f"Asset-Allocation berechnet: {len(asset_allocation)} Assets")
    print(f'[cyan]Asset-Allocation: {asset_allocation}')

    # Daily quiz

    today = datetime.date.today().strftime('%Y-%m-%d')
    quiz_data = edu_handler.get_daily_quiz(today)
    print(f'[red]user:', g.user)
    print(f'[red]today atempt: {edu_handler.get_dayly_quiz_attempt_day(g.user["id"], today)}')
    if quiz_data is None:
        quiz_data = {}
    if edu_handler.get_dayly_quiz_attempt_day(g.user['id'], today) is not None:
        quiz_data['attempted'] = True
    else:
        quiz_data['attempted'] = False
    print(f'[cyan]Quiz data:', quiz_data)


    # check for mayhem
    mayhem_data = market_mayhem_handler.check_if_mayhem()
    if mayhem_data:
        print(f'[red]Market Mayhem:', mayhem_data)
        for event_id, event_data in mayhem_data.items():
            if 'mayhem_scenarios' in event_data and 'description' in event_data['mayhem_scenarios']:
                flash(event_data['mayhem_scenarios']['description'], 'warning')
            else:
                logger.warning(f"Mayhem-Daten für Event-ID {event_id} enthalten keine 'mayhem_scenarios' oder 'description'.")
    else:
        print(f'[red]No market mayhem found for today.')


    return render_template('dashboard.html', 
                           user=g.user, 
                           darkmode=dark_mode_active,
                           portfolio_data=portfolio_data,
                           portfolio_total_value=portfolio_total_value,
                           recent_transactions=recent_transactions_data.get('transactions', []),
                           total_asset_values=asset_values,
                           asset_allocation=asset_allocation,
                           current_user_level=user_level,
                           current_user_xp=user_xp,
                           xp_percentage=xp_percentage,
                           levels=levels,
                           quiz=quiz_data)

# Generate a personalized dog message based on user data and portfolio
def generate_dog_message(user, portfolio_data):
    logger.debug(f"generate_dog_message called for user: {user.get('username')}")
    # Default message if we can't personalize
    default_message = "Woof! Welcome to your dashboard!"
    
    # Check if user has any portfolio data
    if portfolio_data and portfolio_data.get('success') and portfolio_data.get('portfolio'):
        # User has portfolio items
        if len(portfolio_data['portfolio']) > 0:
            message = f"Hey {user['username']}! You have {len(portfolio_data['portfolio'])} assets in your portfolio. Great job!"
            logger.debug(f"Dog message (Portfolio): {message}")
            return message
    
    # Check user's profit/loss
    profit_loss = user.get('profit_loss', 0)
    if profit_loss > 0:
        message = f"Well done! You're in profit with €{profit_loss:.2f} gain!"
        logger.debug(f"Dog message (Profit): {message}")
        return message
    elif profit_loss < 0:
        message = f"Cheer up! Your current loss is €{abs(profit_loss):.2f}. Things will get better soon!"
        logger.debug(f"Dog message (Loss): {message}")
        return message
    
    # Check if user is new (few or no trades)
    total_trades = user.get('total_trades', 0)
    if total_trades < 5:
        message = f"Welcome to BuyHigh.io! Start your first trades and become a trading expert!"
        logger.debug(f"Dog message (New User): {message}")
        return message
    
    logger.debug(f"Dog message (Default): {default_message}")
    return default_message

@main_bp.route('/trade')
@login_required
def trade():
    logger.info(f"Trade-Seite aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Hole Assets aus der Datenbank für die Seitenleiste
    import database.handler.postgres.postgre_transactions_handler as transactions_handler
    assets_data = transactions_handler.get_all_assets(active_only=True)
    assets = assets_data.get('assets', [])
    
    logger.debug(f"Geladene Assets für Trade-Seite: {len(assets)}")
    
    return render_template('trade.html', user=g.user, darkmode=dark_mode_active, assets=assets)

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


@main_bp.route('/profile')
@login_required
def profile():
    logger.info(f"Profilseite aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    print(f'[cyan]Profilseite aufgerufen von Benutzer: {g.user}')
    return render_template('profile.html', user=g.user, darkmode=dark_mode_active)

@main_bp.route('/transactions')
@login_required
def transactions():
    logger.info(f"Transaktionsseite aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Import transactions_handler locally to avoid potential circular imports at top level
    import database.handler.postgres.postgre_transactions_handler as transactions_handler 
    logger.debug("Lade Transaktionshistorie...")
    transactions_data = transactions_handler.get_transactions_by_user_id(g.user['id'])
    logger.debug(f"Transaktionshistorie geladen für Benutzer {g.user['id']}")
    
    return render_template('transactions.html', user=g.user, darkmode=dark_mode_active, transactions=transactions_data)


@main_bp.route('/trader_badges')
@login_required
def trader_badges():
    logger.info(f"Trader Badges-Seite aufgerufen von Benutzer: {g.user.get('username') if g.user else 'Unbekannt'}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Import badges handler locally to avoid potential circular imports
    try:
        import database.handler.postgres.postgres_badges_handler as badges_handler
        logger.debug(f"Lade Badges für Benutzer-ID: {g.user['id']}")
        badges_data = badges_handler.get_user_badges(g.user['id'])
        
        if badges_data['success']:
            badges_by_category = badges_data['badges_by_category']
            total_earned = badges_data['total_earned']
            total_available = badges_data['total_available']
            logger.debug(f"Badges erfolgreich geladen: {total_earned} von {total_available} erworben")
        else:
            logger.error(f"Fehler beim Laden der Badges: {badges_data.get('message', 'Unbekannter Fehler')}")
            badges_by_category = {}
            total_earned = 0
            total_available = 0
            flash(f"Badges konnten nicht geladen werden: {badges_data.get('message', 'Unbekannter Fehler')}", "danger")
    except ImportError:
        logger.error("Badge-Handler-Modul konnte nicht importiert werden")
        badges_by_category = {}
        total_earned = 0
        total_available = 0
        flash("Die Badge-Funktionalität ist nicht verfügbar", "warning")
    except Exception as e:
        logger.exception(f"Unerwarteter Fehler beim Laden der Badges: {e}")
        badges_by_category = {}
        total_earned = 0
        total_available = 0
        flash("Ein unerwarteter Fehler ist beim Laden der Badges aufgetreten", "danger")
    
    return render_template('trader_badges.html', 
                          user=g.user, 
                          darkmode=dark_mode_active,
                          badges_by_category=badges_by_category,
                          total_earned=total_earned,
                          total_available=total_available)

@main_bp.route('/daily-quiz', methods=['GET', 'POST'])
@login_required
def daily_quiz():
    possible_answer_1 = request.form.get("possible_answer_1")
    possible_answer_2 = request.form.get("possible_answer_2")
    possible_answer_3 = request.form.get("possible_answer_3")
    quiz_answer = request.form.get("quiz_answer")
    print(f'[red]Possible answer 1:', possible_answer_1)
    print(f'[red]Possible answer 2:', possible_answer_2)
    print(f'[red]Possible answer 3:', possible_answer_3)
    print(f'[red]Quiz answer:', quiz_answer)
    todays_quiz = edu_handler.get_daily_quiz(datetime.date.today().strftime('%Y-%m-%d'))
    print(f'[red]Quiz:', todays_quiz)
    if todays_quiz['correct_answer'] == quiz_answer:
        # Insert the quiz attempt into the database
        edu_handler.insert_daily_quiz_attempt(g.user['id'], todays_quiz['id'], quiz_answer, True)
        db_handler.manage_user_xp('daily_quiz', g.user['id'], 1)  # Beispiel: 10 XP für die richtige Antwort
        flash('Richtige Antwort! Gut gemacht!', 'success')
    if todays_quiz['correct_answer'] != quiz_answer:
        # Insert the quiz attempt into the database
        edu_handler.insert_daily_quiz_attempt(g.user['id'], todays_quiz['id'], quiz_answer, False)
        flash('Falsche Antwort!', 'danger')

    return redirect(url_for('main.dashboard'))