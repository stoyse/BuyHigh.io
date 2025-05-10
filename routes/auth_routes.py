from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, current_app
import db_handler
import auth as auth_module # Alias to avoid conflict with blueprint name
from utils import login_required # Import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        error = None
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        # Local DB checks for username/email uniqueness before attempting Firebase creation
        elif db_handler.get_user_by_username(username):
            error = f"User {username} is already registered locally."
        elif db_handler.get_user_by_email(email): # Check local DB first
            error = f"Email {email} is already registered locally."

        if error is None:
            try:
                # 1. Create user in Firebase
                firebase_uid = auth_module.create_firebase_user(email, password, username)
                
                # 2. If Firebase creation is successful, add user to local database
                if firebase_uid:
                    if db_handler.add_user(username, email, firebase_uid):
                        flash('Registration successful! Please log in.', 'success')
                        return redirect(url_for('auth.login'))
                    else:
                        # This case is tricky: user in Firebase, but not in local DB.
                        # Should ideally have a cleanup mechanism or retry.
                        # For now, inform user and potentially delete from Firebase.
                        auth_module.delete_firebase_user(firebase_uid) # Attempt to clean up Firebase user
                        error = "Registration failed due to a local database error after Firebase user creation."
                else:
                    # This should not happen if create_firebase_user throws an error or returns UID
                    error = "Registration failed: No Firebase UID returned."

            except ValueError as e: # Catch errors from create_firebase_user or local checks
                error = str(e)
            except Exception as e:
                error = f"An unexpected error occurred during registration: {e}"
        
        if error:
            flash(error, 'danger')

    dark_mode_active = request.args.get('darkmode', 'False').lower() == 'true'
    return render_template('register.html', darkmode=dark_mode_active)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Erweiterte Debug-Ausgaben
        current_app.logger.debug(f"Login attempt for email: {email}")
        
        try:
            # Firebase-Authentifizierung - KORRIGIERT: Verwende die richtige Funktion
            # Die Funktion gibt ein Tupel (uid, token) zurück, kein Dictionary
            firebase_uid, id_token = auth_module.login_firebase_user_rest(email, password)
            
            if not firebase_uid or not id_token:
                current_app.logger.error(f"Firebase authentication failed for email: {email}")
                flash('Anmeldung fehlgeschlagen. Ungültige E-Mail oder Passwort.', 'danger')
                return render_template('login.html')
            
            # Lokale Benutzerüberprüfung
            local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
            
            if not local_user:
                current_app.logger.debug(f"User not found by Firebase UID, trying to find by email: {email}")
                # Benutzer über E-Mail finden
                local_user = db_handler.get_user_by_email(email)
                
                if not local_user:
                    current_app.logger.debug(f"User not found in local DB, attempting to create: {email}")
                    # Firebase-Benutzerdetails abrufen - Vereinfacht, da wir keine get_user_info haben
                    username = email.split('@')[0]  # E-Mail-Präfix als Benutzernamen verwenden
                    
                    # Lokalen Benutzer erstellen
                    success = db_handler.add_user(
                        username=username, 
                        email=email, 
                        firebase_uid=firebase_uid
                    )
                    
                    if not success:
                        current_app.logger.error(f"Failed to create local user for: {email}")
                        flash('Fehler beim Erstellen des Benutzerprofils.', 'danger')
                        return render_template('login.html')
                    
                    local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
                    current_app.logger.info(f"New local user created for: {email}")
                else:
                    current_app.logger.debug(f"User found by email, updating Firebase UID: {email}")
                    # Firebase UID aktualisieren
                    db_handler.update_firebase_uid(local_user['id'], firebase_uid)
            
            # Session aktualisieren
            session.clear()  # Vorherige Session-Daten löschen
            session['logged_in'] = True
            session['user_id'] = local_user['id']
            session['firebase_uid'] = firebase_uid
            session['id_token'] = id_token
            
            # Login-Zeit aktualisieren
            db_handler.update_last_login(local_user['id'])
            
            # Alle verfügbaren Routen anzeigen (Debug)
            for rule in current_app.url_map.iter_rules():
                current_app.logger.debug(f"Available route: {rule.endpoint} -> {rule}")
            
            current_app.logger.info(f"User {email} successfully logged in")
            flash('Anmeldung erfolgreich!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            current_app.logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
            flash(f'Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.', 'danger')
            return render_template('login.html')
    
    return render_template('login.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Email is required.', 'danger')
            return render_template('forgot_password.html')
        
        try:
            # Verwenden Sie die Firebase-API, um einen Passwort-Reset-Link zu senden
            auth_module.send_password_reset_email(email)
            flash('Password reset email sent. Please check your inbox.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            current_app.logger.error(f"Error sending password reset: {e}")
            flash('An error occurred while sending the password reset email.', 'danger')
    
    return render_template('forgot_password.html')

@auth_bp.route('/login-with-google')
def login_with_google():
    """Startet den Google OAuth-Flow für die Anmeldung"""
    try:
        # Redirect URL für die Google OAuth-Anmeldung
        redirect_url = auth_module.get_google_auth_url()
        return redirect(redirect_url)
    except Exception as e:
        current_app.logger.error(f"Error initiating Google login: {e}")
        flash('Fehler beim Starten der Google-Anmeldung.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/auth/google/callback')
def google_auth_callback():
    """Callback-Handler für die Google OAuth-Authentifizierung"""
    try:
        # OAuth-Code aus der Anfrage extrahieren
        auth_code = request.args.get('code')
        if not auth_code:
            flash('Google-Authentifizierungscode fehlt.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Code gegen Token und Profildaten austauschen
        user_info = auth_module.exchange_google_code(auth_code)
        
        if not user_info:
            flash('Fehler beim Verarbeiten der Google-Anmeldung.', 'danger')
            return redirect(url_for('auth.login'))
        
        # E-Mail und Firebase-UID aus den Google-Profildaten extrahieren
        email = user_info.get('email')
        firebase_uid = user_info.get('firebase_uid')
        
        if not email or not firebase_uid:
            flash('Unvollständige Benutzerinformationen von Google.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Überprüfen, ob der Benutzer bereits in der lokalen DB existiert
        local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
        
        if not local_user:
            # Prüfen, ob ein Benutzer mit dieser E-Mail existiert
            local_user = db_handler.get_user_by_email(email)
            
            if not local_user:
                # Neuen Benutzer anlegen, wenn keiner existiert
                username = user_info.get('name', email.split('@')[0])
                success = db_handler.add_user(
                    username=username,
                    email=email,
                    firebase_uid=firebase_uid,
                    provider='google'  # Anbieter als 'google' markieren
                )
                
                if not success:
                    flash('Fehler beim Erstellen des Benutzerprofils.', 'danger')
                    return redirect(url_for('auth.login'))
                
                local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
            else:
                # Bestehenden Benutzer mit Firebase UID verknüpfen
                db_handler.update_firebase_uid(local_user['id'], firebase_uid)
        
        # Benutzer in die Session setzen
        session.clear()
        session['logged_in'] = True
        session['user_id'] = local_user['id']
        session['firebase_uid'] = firebase_uid
        session['id_token'] = user_info.get('id_token', '')
        
        # Login-Zeit aktualisieren
        db_handler.update_last_login(local_user['id'])
        
        flash('Erfolgreich mit Google angemeldet!', 'success')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        current_app.logger.error(f"Error during Google auth callback: {e}", exc_info=True)
        flash('Ein Fehler ist während der Google-Authentifizierung aufgetreten.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    # g.user is already loaded by @login_required and load_logged_in_user
    # It contains the local user record, including 'firebase_uid' and 'email'
    if request.method == 'POST':
        current_password = request.form.get('current_password_for_delete')

        if not current_password:
            flash('Passwort zur Bestätigung erforderlich.', 'danger')
            return redirect(url_for('main.settings'))

        if not g.user or not g.user.get('email'):
            flash('Benutzerdaten nicht gefunden oder E-Mail fehlt.', 'danger')
            return redirect(url_for('auth.login'))

        # 1. Verify current password against Firebase
        try:
            if not auth_module.verify_firebase_password_rest(g.user['email'], current_password):
                flash('Aktuelles Passwort ist nicht korrekt.', 'danger')
                return redirect(url_for('main.settings'))
        except ValueError as e: # Catch issues from verify_firebase_password_rest
            flash(f'Fehler bei der Passwortüberprüfung: {e}', 'danger')
            return redirect(url_for('main.settings'))
        except Exception as e:
            flash(f'Unerwarteter Fehler bei der Passwortüberprüfung: {e}', 'danger')
            return redirect(url_for('main.settings'))


        # 2. Proceed with deletion from Firebase
        firebase_uid_to_delete = g.user.get('firebase_uid')
        if not firebase_uid_to_delete:
            flash('Firebase Benutzer-ID nicht gefunden. Löschvorgang abgebrochen.', 'danger')
            return redirect(url_for('main.settings'))

        if not auth_module.delete_firebase_user(firebase_uid_to_delete):
            flash('Fehler beim Löschen des Firebase-Kontos. Das lokale Konto wurde nicht gelöscht.', 'danger')
            return redirect(url_for('main.settings'))

        # 3. Delete from local database
        if db_handler.delete_user(g.user['id']): # Use local DB user ID
            session.clear() # Log out the user
            flash('Ihr Konto wurde erfolgreich gelöscht.', 'success')
            return redirect(url_for('main.index'))
        else:
            # This is problematic: Firebase user deleted, local user not.
            # Needs robust error handling/logging.
            flash('Firebase-Konto gelöscht, aber Fehler beim Löschen des lokalen Kontos. Bitte kontaktieren Sie den Support.', 'danger')
            return redirect(url_for('main.settings'))
    
    return redirect(url_for('main.settings'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')
    
    if not current_password or not new_password or not confirm_new_password:
        flash('All fields are required.', 'danger')
        return redirect(url_for('main.settings'))
    
    if new_password != confirm_new_password:
        flash('New password and confirmation do not match.', 'danger')
        return redirect(url_for('main.settings'))
    
    try:
        # Verify current password with Firebase
        if not auth_module.verify_firebase_password_rest(g.user['email'], current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('main.settings'))
        
        # Change password with Firebase
        auth_module.change_firebase_password(g.user['firebase_uid'], new_password)
        flash('Password changed successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        current_app.logger.error(f"Error changing password: {e}")
        flash('An unexpected error occurred.', 'danger')
    
    return redirect(url_for('main.settings'))

@auth_bp.route('/send-password-reset', methods=['POST'])
@login_required
def send_password_reset():
    email = request.form.get('email')
    
    try:
        auth_module.send_password_reset_email(email)
        flash('Password reset link sent to your email.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        current_app.logger.error(f"Error sending password reset: {e}")
        flash('An error occurred while sending the password reset email.', 'danger')
    
    return redirect(url_for('main.settings'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
