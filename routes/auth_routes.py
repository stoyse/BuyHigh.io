from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, current_app
import database.handler.db_handler as db_handler
import auth as auth_module # Alias to avoid conflict with blueprint name
from utils import login_required # Import login_required
import logging # Hinzugefügt

logger = logging.getLogger(__name__) # Hinzugefügt

auth_bp = Blueprint('auth', __name__)
logger.info("Auth Blueprint 'auth_bp' erstellt.")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    logger.info(f"Registrierungsseite aufgerufen. Methode: {request.method}")
    if g.user:
        logger.info(f"Benutzer {g.user.get('username')} ist bereits angemeldet. Umleitung zum Index.")
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '') # Passwort nicht loggen!
        logger.info(f"Registrierungsversuch für Benutzername: {username}, E-Mail: {email}")
        
        error = None
        if not username:
            error = 'Benutzername ist erforderlich.'
            logger.warning("Registrierung fehlgeschlagen: Benutzername fehlt.")
        elif not email:
            error = 'E-Mail ist erforderlich.'
            logger.warning("Registrierung fehlgeschlagen: E-Mail fehlt.")
        elif not password: # Passwortlänge könnte hier geprüft werden, aber nicht das Passwort selbst loggen
            error = 'Passwort ist erforderlich.'
            logger.warning("Registrierung fehlgeschlagen: Passwort fehlt.")
        elif db_handler.get_user_by_username(username):
            error = f"Benutzer {username} ist bereits lokal registriert."
            logger.warning(f"Registrierung fehlgeschlagen: Benutzername '{username}' bereits vergeben (lokal).")
        elif db_handler.get_user_by_email(email):
            error = f"E-Mail {email} ist bereits lokal registriert."
            logger.warning(f"Registrierung fehlgeschlagen: E-Mail '{email}' bereits vergeben (lokal).")

        if error is None:
            try:
                logger.debug(f"Versuche Firebase-Benutzer für E-Mail {email} zu erstellen.")
                firebase_uid = auth_module.create_firebase_user(email, password, username)
                
                if firebase_uid:
                    logger.info(f"Firebase-Benutzer erfolgreich erstellt mit UID: {firebase_uid} für E-Mail: {email}.")
                    logger.debug(f"Füge Benutzer {username} (Firebase UID: {firebase_uid}) zur lokalen Datenbank hinzu.")
                    if db_handler.add_user(username, email, firebase_uid):
                        flash('Registrierung erfolgreich! Bitte melden Sie sich an.', 'success')
                        logger.info(f"Benutzer {username} (E-Mail: {email}, Firebase UID: {firebase_uid}) erfolgreich in lokaler DB registriert.")
                        return redirect(url_for('auth.login'))
                    else:
                        logger.error(f"Fehler beim Hinzufügen des Benutzers {username} (Firebase UID: {firebase_uid}) zur lokalen DB nach Firebase-Erstellung. Versuche Firebase-Benutzer zu löschen.")
                        auth_module.delete_firebase_user(firebase_uid)
                        logger.info(f"Firebase-Benutzer {firebase_uid} nach lokalem DB-Fehler gelöscht.")
                        error = "Registrierung fehlgeschlagen aufgrund eines lokalen Datenbankfehlers nach Firebase-Benutzererstellung."
                else:
                    # Sollte nicht passieren, wenn create_firebase_user Fehler wirft oder UID zurückgibt
                    error = "Registrierung fehlgeschlagen: Keine Firebase UID zurückgegeben."
                    logger.error(f"Registrierung für E-Mail {email} fehlgeschlagen: create_firebase_user gab keine UID zurück und keinen Fehler.")

            except ValueError as e:
                error = str(e)
                logger.error(f"ValueError während der Registrierung für E-Mail {email}: {e}", exc_info=True)
            except Exception as e:
                error = f"Ein unerwarteter Fehler ist während der Registrierung aufgetreten: {e}"
                logger.error(f"Unerwarteter Fehler während der Registrierung für E-Mail {email}: {e}", exc_info=True)
        
        if error:
            flash(error, 'danger')
            logger.warning(f"Registrierung für E-Mail {email} endgültig fehlgeschlagen mit Fehler: {error}")

    dark_mode_active = request.args.get('darkmode', 'False').lower() == 'true'
    return render_template('register.html', darkmode=dark_mode_active)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    logger.info(f"Login-Seite aufgerufen. Methode: {request.method}")
    if g.user: # Prüfen, ob Benutzer bereits angemeldet ist
        logger.info(f"Benutzer {g.user.get('username')} ist bereits angemeldet. Umleitung zum Dashboard.")
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '') # Passwort nicht loggen!
        
        logger.info(f"Login-Versuch für E-Mail: {email}")
        
        try:
            logger.debug(f"Versuche Firebase-Authentifizierung für E-Mail: {email} mit REST API.")
            firebase_uid, id_token = auth_module.login_firebase_user_rest(email, password)
            
            if not firebase_uid or not id_token:
                logger.warning(f"Firebase-Authentifizierung fehlgeschlagen für E-Mail: {email}. Keine UID oder Token zurückgegeben.")
                flash('Anmeldung fehlgeschlagen. Ungültige E-Mail oder Passwort.', 'danger')
                return render_template('login.html') # Darkmode hier ggf. auch übergeben
            
            logger.info(f"Firebase-Authentifizierung erfolgreich für E-Mail: {email}, Firebase UID: {firebase_uid}.")
            
            logger.debug(f"Suche lokalen Benutzer mit Firebase UID: {firebase_uid}.")
            local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
            
            if not local_user:
                logger.info(f"Kein lokaler Benutzer mit Firebase UID {firebase_uid} gefunden. Versuche Benutzer über E-Mail {email} zu finden.")
                local_user = db_handler.get_user_by_email(email)
                
                if not local_user:
                    logger.info(f"Kein lokaler Benutzer mit E-Mail {email} gefunden. Erstelle neuen lokalen Benutzer.")
                    username = email.split('@')[0] 
                    
                    logger.debug(f"Füge neuen lokalen Benutzer hinzu: Benutzername={username}, E-Mail={email}, Firebase UID={firebase_uid}")
                    success = db_handler.add_user(
                        username=username, 
                        email=email, 
                        firebase_uid=firebase_uid
                    )
                    
                    if not success:
                        logger.error(f"Fehler beim Erstellen des lokalen Benutzers für E-Mail: {email}, Firebase UID: {firebase_uid}.")
                        flash('Fehler beim Erstellen des Benutzerprofils.', 'danger')
                        return render_template('login.html')
                    
                    local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
                    logger.info(f"Neuer lokaler Benutzer erfolgreich erstellt für E-Mail: {email}, Lokale ID: {local_user.get('id') if local_user else 'N/A'}.")
                else:
                    logger.info(f"Lokaler Benutzer (ID: {local_user.get('id')}) mit E-Mail {email} gefunden. Aktualisiere Firebase UID auf {firebase_uid}.")
                    db_handler.update_firebase_uid(local_user['id'], firebase_uid)
                    local_user['firebase_uid'] = firebase_uid # Stelle sicher, dass das lokale Objekt aktuell ist
            
            if not local_user: # Sollte nach obiger Logik nicht passieren, aber als Sicherheitsnetz
                logger.critical(f"Kritischer Fehler: Konnte lokalen Benutzer für Firebase UID {firebase_uid} weder finden noch erstellen.")
                flash('Ein schwerwiegender Fehler ist bei der Benutzeranmeldung aufgetreten.', 'danger')
                return render_template('login.html')

            logger.debug(f"Aktualisiere Session für Benutzer: {local_user.get('username')}, Lokale ID: {local_user['id']}, Firebase UID: {firebase_uid}.")
            session.clear()
            session['logged_in'] = True
            session['user_id'] = local_user['id']
            session['firebase_uid'] = firebase_uid
            session['id_token'] = id_token # Token in Session speichern
            session.permanent = True
            
            logger.debug(f"Aktualisiere letzte Login-Zeit für Benutzer ID: {local_user['id']}.")
            db_handler.update_last_login(local_user['id'])
            
            # Alle verfügbaren Routen anzeigen (Debug) - kann bei Bedarf entfernt werden
            # for rule in current_app.url_map.iter_rules():
            #     logger.debug(f"Verfügbare Route: {rule.endpoint} -> {rule}")
            
            logger.info(f"Benutzer {email} (Lokale ID: {local_user['id']}) erfolgreich angemeldet. Umleitung zum Dashboard.")
            flash('Anmeldung erfolgreich!', 'success')
            return redirect(url_for('main.dashboard'))
        except ValueError as ve: # Spezifischer Fehler von login_firebase_user_rest
            logger.warning(f"ValueError während Login für E-Mail {email}: {str(ve)}")
            flash(str(ve), 'danger') # Zeige die spezifische Fehlermeldung dem Benutzer
            return render_template('login.html')
        except Exception as e:
            logger.error(f"Unerwarteter Fehler während Login für E-Mail {email}: {str(e)}", exc_info=True)
            flash(f'Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.', 'danger')
            return render_template('login.html')
    
    # Für GET-Anfrage
    dark_mode_active_login = request.args.get('darkmode', 'False').lower() == 'true' # Für den Fall, dass es als Parameter übergeben wird
    # Alternativ, falls Theme aus Session oder g.user geladen werden soll, hier anpassen
    # g.user ist hier None, wenn nicht angemeldet.
    # Wenn ein Cookie für Darkmode existiert, könnte man das hier auslesen.
    return render_template('login.html', darkmode=dark_mode_active_login)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    logger.info(f"Passwort vergessen Seite aufgerufen. Methode: {request.method}")
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        logger.info(f"Passwort zurücksetzen Anfrage für E-Mail: {email}")
        if not email:
            flash('E-Mail ist erforderlich.', 'danger')
            logger.warning("Passwort zurücksetzen fehlgeschlagen: E-Mail fehlt.")
            return render_template('forgot_password.html') # Darkmode?
        
        try:
            logger.debug(f"Sende Passwort-Reset-E-Mail an: {email} via Firebase.")
            auth_module.send_password_reset_email(email)
            flash('E-Mail zum Zurücksetzen des Passworts gesendet. Bitte überprüfen Sie Ihren Posteingang.', 'success')
            logger.info(f"Passwort-Reset-E-Mail erfolgreich an {email} gesendet.")
            return redirect(url_for('auth.login'))
        except ValueError as e: # Von Firebase erwarteter Fehler
            flash(str(e), 'danger')
            logger.error(f"ValueError beim Senden der Passwort-Reset-E-Mail an {email}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Fehler beim Senden der Passwort-Reset-E-Mail an {email}: {e}", exc_info=True)
            flash('Beim Senden der Passwort-Reset-E-Mail ist ein Fehler aufgetreten.', 'danger')
    
    return render_template('forgot_password.html') # Darkmode?

@auth_bp.route('/login-with-google')
def login_with_google():
    logger.info("Starte Google OAuth-Flow.")
    try:
        redirect_url = auth_module.get_google_auth_url()
        logger.debug(f"Google Auth Redirect URL erhalten: {redirect_url}")
        return redirect(redirect_url)
    except Exception as e:
        logger.error(f"Fehler beim Starten der Google-Anmeldung: {e}", exc_info=True)
        flash('Fehler beim Starten der Google-Anmeldung.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/auth/google/callback')
def google_auth_callback():
    logger.info("Google Auth Callback empfangen.")
    try:
        auth_code = request.args.get('code')
        if not auth_code:
            flash('Google-Authentifizierungscode fehlt.', 'danger')
            logger.warning("Google Auth Callback: Authentifizierungscode fehlt.")
            return redirect(url_for('auth.login'))
        
        logger.debug(f"Google Auth Code empfangen: {auth_code[:30]}...") # Gekürzt
        
        user_info = auth_module.exchange_google_code(auth_code)
        logger.info(f"Google Code ausgetauscht. Erhaltene Benutzerinfo: E-Mail='{user_info.get('email')}', Firebase UID='{user_info.get('firebase_uid')}'")
        
        if not user_info: # Sollte durch exchange_google_code abgedeckt sein, aber als Sicherheit
            flash('Fehler beim Verarbeiten der Google-Anmeldung.', 'danger')
            logger.error("Google Auth Callback: exchange_google_code gab keine Benutzerinfo zurück.")
            return redirect(url_for('auth.login'))
        
        email = user_info.get('email')
        firebase_uid = user_info.get('firebase_uid')
        
        if not email or not firebase_uid:
            flash('Unvollständige Benutzerinformationen von Google.', 'danger')
            logger.error(f"Google Auth Callback: Unvollständige Benutzerinfo. E-Mail: {email}, UID: {firebase_uid}")
            return redirect(url_for('auth.login'))
        
        logger.debug(f"Suche lokalen Benutzer mit Firebase UID: {firebase_uid} (von Google Auth).")
        local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
        
        if not local_user:
            logger.info(f"Kein lokaler Benutzer mit Firebase UID {firebase_uid} (Google Auth) gefunden. Suche nach E-Mail: {email}.")
            local_user = db_handler.get_user_by_email(email)
            
            if not local_user:
                logger.info(f"Kein lokaler Benutzer mit E-Mail {email} (Google Auth) gefunden. Erstelle neuen lokalen Benutzer.")
                username = user_info.get('name', email.split('@')[0])
                logger.debug(f"Neuer lokaler Benutzer (Google Auth): Benutzername='{username}', E-Mail='{email}', Firebase UID='{firebase_uid}', Provider='google'")
                success = db_handler.add_user(
                    username=username,
                    email=email,
                    firebase_uid=firebase_uid,
                    provider='google'
                )
                
                if not success:
                    flash('Fehler beim Erstellen des Benutzerprofils.', 'danger')
                    logger.error(f"Google Auth Callback: Fehler beim Erstellen des lokalen Benutzers für E-Mail {email}, UID {firebase_uid}.")
                    return redirect(url_for('auth.login'))
                
                local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
                logger.info(f"Neuer lokaler Benutzer (Google Auth) erfolgreich erstellt. Lokale ID: {local_user.get('id') if local_user else 'N/A'}")
            else:
                logger.info(f"Lokaler Benutzer (ID: {local_user.get('id')}) mit E-Mail {email} (Google Auth) gefunden. Aktualisiere Firebase UID auf {firebase_uid}.")
                db_handler.update_firebase_uid(local_user['id'], firebase_uid)
                local_user['firebase_uid'] = firebase_uid # Stelle sicher, dass das lokale Objekt aktuell ist
        
        if not local_user: # Sicherheitsnetz
            logger.critical(f"Google Auth Callback: Konnte lokalen Benutzer für Firebase UID {firebase_uid} (E-Mail: {email}) weder finden noch erstellen.")
            flash('Ein schwerwiegender Fehler ist bei der Google-Anmeldung aufgetreten.', 'danger')
            return redirect(url_for('auth.login'))

        logger.debug(f"Aktualisiere Session für Google Auth Benutzer: {local_user.get('username')}, Lokale ID: {local_user['id']}, Firebase UID: {firebase_uid}.")
        session.clear()
        session['logged_in'] = True
        session['user_id'] = local_user['id']
        session['firebase_uid'] = firebase_uid
        session['id_token'] = user_info.get('id_token', '') # ID Token von Google speichern
        session.permanent = True
        
        logger.debug(f"Aktualisiere letzte Login-Zeit für Benutzer ID: {local_user['id']} (Google Auth).")
        db_handler.update_last_login(local_user['id'])
        
        flash('Erfolgreich mit Google angemeldet!', 'success')
        logger.info(f"Benutzer {email} (Lokale ID: {local_user['id']}) erfolgreich mit Google angemeldet. Umleitung zum Dashboard.")
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        logger.error(f"Fehler während Google Auth Callback: {e}", exc_info=True)
        flash('Ein Fehler ist während der Google-Authentifizierung aufgetreten.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_id_local = g.user.get('id') if g.user else 'Unbekannt'
    username_local = g.user.get('username') if g.user else 'Unbekannt'
    logger.info(f"Konto löschen Anfrage von Benutzer: {username_local} (ID: {user_id_local}).")

    if request.method == 'POST': # Redundant wegen @login_required, aber schadet nicht
        current_password_for_delete = request.form.get('current_password_for_delete') # PW nicht loggen

        if not current_password_for_delete:
            flash('Passwort zur Bestätigung erforderlich.', 'danger')
            logger.warning(f"Konto löschen für {username_local}: Passwort zur Bestätigung fehlt.")
            return redirect(url_for('main.settings'))

        if not g.user or not g.user.get('email'): # Sollte durch @login_required abgedeckt sein
            flash('Benutzerdaten nicht gefunden oder E-Mail fehlt.', 'danger')
            logger.error(f"Konto löschen: Kritischer Fehler - g.user oder E-Mail fehlt für angemeldeten Benutzer {username_local}.")
            return redirect(url_for('auth.login')) # Zum Login umleiten, da etwas nicht stimmt

        user_email = g.user['email']
        logger.debug(f"Überprüfe aktuelles Passwort für Benutzer {user_email} (Konto löschen).")
        try:
            if not auth_module.verify_firebase_password_rest(user_email, current_password_for_delete):
                flash('Aktuelles Passwort ist nicht korrekt.', 'danger')
                logger.warning(f"Konto löschen für {user_email}: Aktuelles Passwort falsch.")
                return redirect(url_for('main.settings'))
            logger.info(f"Passwort für {user_email} (Konto löschen) erfolgreich verifiziert.")
        except ValueError as e:
            flash(f'Fehler bei der Passwortüberprüfung: {e}', 'danger')
            logger.error(f"ValueError bei Passwortüberprüfung für {user_email} (Konto löschen): {e}", exc_info=True)
            return redirect(url_for('main.settings'))
        except Exception as e:
            flash(f'Unerwarteter Fehler bei der Passwortüberprüfung: {e}', 'danger')
            logger.error(f"Unerwarteter Fehler bei Passwortüberprüfung für {user_email} (Konto löschen): {e}", exc_info=True)
            return redirect(url_for('main.settings'))

        firebase_uid_to_delete = g.user.get('firebase_uid')
        if not firebase_uid_to_delete: # Sollte nicht passieren, wenn Benutzer angemeldet ist
            flash('Firebase Benutzer-ID nicht gefunden. Löschvorgang abgebrochen.', 'danger')
            logger.error(f"Konto löschen für {user_email}: Firebase UID nicht in g.user gefunden.")
            return redirect(url_for('main.settings'))

        logger.info(f"Versuche Firebase-Konto mit UID {firebase_uid_to_delete} für Benutzer {user_email} zu löschen.")
        if not auth_module.delete_firebase_user(firebase_uid_to_delete):
            flash('Fehler beim Löschen des Firebase-Kontos. Das lokale Konto wurde nicht gelöscht.', 'danger')
            logger.error(f"Fehler beim Löschen des Firebase-Kontos UID {firebase_uid_to_delete} für {user_email}.")
            return redirect(url_for('main.settings'))
        logger.info(f"Firebase-Konto UID {firebase_uid_to_delete} für {user_email} erfolgreich gelöscht.")

        logger.info(f"Versuche lokales Konto ID {user_id_local} für Benutzer {user_email} zu löschen.")
        if db_handler.delete_user(user_id_local):
            logger.info(f"Lokales Konto ID {user_id_local} für {user_email} erfolgreich gelöscht.")
            session.clear()
            logger.info(f"Session für Benutzer {user_email} nach Kontolöschung geleert.")
            flash('Ihr Konto wurde erfolgreich gelöscht.', 'success')
            return redirect(url_for('main.index'))
        else:
            logger.critical(f"Kritischer Fehler: Firebase-Konto {firebase_uid_to_delete} gelöscht, aber lokales Konto {user_id_local} ({user_email}) konnte nicht gelöscht werden.")
            flash('Firebase-Konto gelöscht, aber Fehler beim Löschen des lokalen Kontos. Bitte kontaktieren Sie den Support.', 'danger')
            return redirect(url_for('main.settings'))
    
    # Sollte nicht erreicht werden, wenn POST und @login_required
    logger.warning("Konto löschen Route ohne POST erreicht, Umleitung zu Einstellungen.")
    return redirect(url_for('main.settings'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    user_email = g.user.get('email') if g.user else 'Unbekannt'
    logger.info(f"Passwort ändern Anfrage von Benutzer: {user_email}")

    current_password = request.form.get('current_password') # Nicht loggen
    new_password = request.form.get('new_password') # Nicht loggen
    confirm_new_password = request.form.get('confirm_new_password') # Nicht loggen
    
    # Längen loggen für Debugging
    logger.debug(f"Passwort ändern für {user_email}: Aktuelles PW Länge: {len(current_password) if current_password else 0}, Neues PW Länge: {len(new_password) if new_password else 0}")

    if not current_password:
        flash('Current password is required.', 'danger')
        logger.warning(f"Password change for {user_email}: Current password missing.")
        return redirect(url_for('main.settings'))
    
    if not auth_module.verify_firebase_password_rest(g.user['email'], current_password):
        flash('Current password is incorrect.', 'danger')
        logger.warning(f"Password change for {user_email}: Current password incorrect.")
        return redirect(url_for('main.settings'))
    
    if not new_password or not confirm_new_password:
        flash('All fields are required.', 'danger')
        logger.warning(f"Password change for {user_email}: Not all fields filled.")
        return redirect(url_for('main.settings'))
    
    if new_password != confirm_new_password:
        flash('New password and confirmation do not match.', 'danger')
        logger.warning(f"Password change for {user_email}: New password and confirmation do not match.")
        return redirect(url_for('main.settings'))
    
    # Zusätzliche Längenprüfung für neues Passwort (Beispiel)
    if len(new_password) < 6: # Synchron mit Registrierungsanforderung halten
        flash('The new password must be at least 6 characters long.', 'danger')
        logger.warning(f"Password change for {user_email}: New password too short (length {len(new_password)}).")
        return redirect(url_for('main.settings'))

    try:
        firebase_uid_for_pw_change = g.user.get('firebase_uid')
        if not firebase_uid_for_pw_change: # Sollte nicht passieren
            logger.error(f"Password change for {user_email}: Firebase UID not found in g.user.")
            flash('User identification failed.', 'danger')
            return redirect(url_for('main.settings'))

        logger.debug(f"Change Firebase password for UID: {firebase_uid_for_pw_change}.")
        auth_module.change_firebase_password(firebase_uid_for_pw_change, new_password)
        flash('Password successfully changed!', 'success')
        logger.info(f"Password for user {user_email} (UID: {firebase_uid_for_pw_change}) successfully changed in Firebase.")
    except ValueError as e: # Erwartete Fehler von Firebase-Operationen
        flash(str(e), 'danger')
        logger.error(f"ValueError while changing password for {user_email}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error while changing password for {user_email}: {e}", exc_info=True)
        flash('An unexpected error occurred.', 'danger')
    
    return redirect(url_for('main.settings'))

@auth_bp.route('/send-password-reset', methods=['POST'])
@login_required # Ist das sinnvoll hier? Normalerweise ist man nicht angemeldet, wenn man PW zurücksetzt.
                # Diese Route ist in settings.html, also ist der Benutzer angemeldet.
                # Es könnte sein, dass der Benutzer sein PW vergessen hat, aber noch eingeloggt ist und es proaktiv ändern will.
def send_password_reset():
    user_email = g.user.get('email') if g.user else 'Unbekannt' # E-Mail des angemeldeten Benutzers
    logger.info(f"Passwort-Reset-E-Mail senden Anfrage von angemeldetem Benutzer: {user_email}")
    
    # Das Formularfeld 'email' wird hier ignoriert, stattdessen wird die E-Mail des angemeldeten Benutzers verwendet.
    # email_form = request.form.get('email') # Aus Formular, falls benötigt, aber g.user['email'] ist sicherer.

    if not user_email: # Sollte durch @login_required und g.user nicht passieren
        flash('Benutzer-E-Mail nicht gefunden.', 'danger')
        logger.error("Passwort-Reset senden: E-Mail des angemeldeten Benutzers nicht in g.user gefunden.")
        return redirect(url_for('main.settings'))

    try:
        logger.debug(f"Sende Passwort-Reset-Link an E-Mail: {user_email} (aus g.user).")
        auth_module.send_password_reset_email(user_email)
        flash('Link zum Zurücksetzen des Passworts an Ihre E-Mail gesendet.', 'success')
        logger.info(f"Passwort-Reset-Link erfolgreich an {user_email} gesendet.")
    except ValueError as e: # Erwartete Fehler
        flash(str(e), 'danger')
        logger.error(f"ValueError beim Senden des Passwort-Reset-Links an {user_email}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Fehler beim Senden des Passwort-Reset-Links an {user_email}: {e}", exc_info=True)
        flash('Beim Senden des Passwort-Reset-Links ist ein Fehler aufgetreten.', 'danger')
    
    return redirect(url_for('main.settings'))

@auth_bp.route('/logout')
def logout():
    username = g.user.get('username') if g.user else 'Unbekannt'
    logger.info(f"Logout-Anfrage von Benutzer: {username}")
    session.clear()
    logger.info(f"Session für Benutzer {username} geleert.")
    flash('Sie wurden abgemeldet.', 'info')
    return redirect(url_for('auth.login'))
