from flask import Blueprint, render_template, g, request, flash, redirect, url_for, jsonify, session
from flask_socketio import emit, join_room, leave_room
from utils.utils import login_required
import logging
from datetime import datetime
import dotenv
import os

import database.handler.postgres.postgres_db_handler as db_handler
import database.handler.postgres.postgres_chat_db_handler as chat_db_handler

# Lade Umgebungsvariablen aus .env-Datei
dotenv.load_dotenv()
# Stelle sicher, dass die Umgebungsvariablen geladen sind

DATABASE_FILE_PATH = '../database.db' # Korrigierter relativer Pfad als Fallback

# Logger konfigurieren
logger = logging.getLogger(__name__)

# Blueprint erstellen
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')
logger.info("Chat Blueprint 'chat_bp' erstellt.")

# Benutzerdefinierten Filter für datetime hinzufügen
@chat_bp.app_template_filter('datetime')
def format_datetime(value, format='%d.%m.%Y %H:%M'):
    """Formatiert ein Datetime-Objekt zu einem lesbaren String."""
    logger.debug(f"format_datetime Filter aufgerufen mit Wert: {value}, Format: {format}")
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.warning(f"Konnte String '{value}' nicht in Datetime umwandeln im format_datetime Filter.")
            return value
    return value.strftime(format)

@chat_bp.route('/chats')
@login_required
def chat_collection():
    user_id = g.user['id'] if g.user else 'Unbekannt'
    logger.info(f"Chat-Sammlung aufgerufen von Benutzer ID: {user_id}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'

    try:
        logger.debug(f"Verwende chat_db_handler.get_user_chats für Benutzer {user_id}.")
        chat_data = chat_db_handler.get_user_chats(g.user['id'])
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Benutzer-Chats für {user_id}: {e}", exc_info=True)
        chat_data = []

    logger.info(f"Zeige {len(chat_data)} Chats an: {chat_data}")

    return render_template('chat_collection.html', 
                           user=g.user, 
                           darkmode=dark_mode_active, 
                           chat_rooms=chat_data)

@chat_bp.route('/<string:chat_id>')
@login_required
def chat_details(chat_id):
    user_id = g.user['id'] if g.user else 'Unbekannt'
    logger.info(f"Chat-Details für Chat ID '{chat_id}' aufgerufen von Benutzer ID: {user_id}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'

    chat = None
    logger.debug(f"Lade Chat '{chat_id}'...")
    chat = chat_db_handler.get_chat_by_id(chat_id)
    logger.info(f"Chat '{chat_id}' von SQLite geladen: {chat is not None}")

    if not chat:
        flash(f'Der angeforderte Chat ({chat_id}) existiert nicht.', 'danger')
        logger.warning(f"Chat '{chat_id}' nicht gefunden. Umleitung zur Chat-Sammlung.")
        return redirect(url_for('chat.chat_collection'))

    logger.debug(f"Überprüfe Teilnahme von Benutzer {user_id} in Chat '{chat_id}'.")
    is_participant = chat_db_handler.is_chat_participant(chat_id, g.user['id'])
    logger.info(f"Benutzer {user_id} ist Teilnehmer in Chat '{chat_id}' (SQLite): {is_participant}")

    if not is_participant:
        logger.info(f"Benutzer {user_id} ist kein Teilnehmer in Chat '{chat_id}'. Füge Benutzer hinzu.")
        chat_db_handler.join_chat(chat_id, g.user['id'])
        logger.info(f"Benutzer {user_id} zu Chat '{chat_id}' via SQLite hinzugefügt.")

    logger.debug(f"Lade Nachrichten für Chat '{chat_id}'.")
    messages = chat_db_handler.get_chat_messages(chat_id, limit=100)
    logger.info(f"{len(messages)} Nachrichten für Chat '{chat_id}' von SQLite geladen.")

    return render_template('chat_details.html',
                           user=g.user,
                           darkmode=dark_mode_active,
                           chat=chat,
                           initial_messages=messages)

@chat_bp.route('/new-chat', methods=['GET', 'POST'])
@login_required
def new_chat():
    user_id = g.user['id'] if g.user else 'Unbekannt'
    logger.info(f"Route /new-chat aufgerufen von Benutzer ID: {user_id}, Methode: {request.method}")
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    if request.method == 'POST':
        chat_name = request.form.get('chat_name', '').strip()
        logger.info(f"POST /new-chat: Benutzer {user_id} versucht Chat mit Namen '{chat_name}' zu erstellen.")
        
        if not chat_name:
            flash('Der Chatname darf nicht leer sein.', 'danger')
            logger.warning(f"Neuer Chat für Benutzer {user_id} fehlgeschlagen: Chatname leer.")
            return render_template('new_chat.html', darkmode=dark_mode_active, user=g.user)
        
        logger.debug(f"Versuche Chat '{chat_name}' für Benutzer {user_id} mit chat_db_handler zu erstellen.")
        chat_id = chat_db_handler.create_chat(chat_name, g.user['id'])
        
        if chat_id:
            flash('Chat wurde erfolgreich erstellt!', 'success')
            logger.info(f"Chat '{chat_name}' (ID: {chat_id}) erfolgreich von Benutzer {user_id} erstellt.")
            return redirect(url_for('chat.chat_details', chat_id=chat_id))
        else:
            flash('Fehler beim Erstellen des Chats.', 'danger')
            logger.error(f"Fehler beim Erstellen des Chats '{chat_name}' für Benutzer {user_id}.")
    
    return render_template('new_chat.html', darkmode=dark_mode_active, user=g.user)


@chat_bp.route('/<string:chat_id>/settings', methods=['GET', 'POST'])
@login_required
def chat_settings(chat_id):
    user_id = g.user['id'] if g.user else 'Unbekannt'
    logger.info(f"Chat-Einstellungen für Chat ID '{chat_id}' aufgerufen von Benutzer ID: {user_id}, Methode: {request.method}")
    
    chat = chat_db_handler.get_chat_by_id(chat_id)
    
    if not chat:
        flash("Chat nicht gefunden.", "danger")
        logger.warning(f"Chat-Einstellungen: Chat '{chat_id}' nicht gefunden.")
        return redirect(url_for('chat.chat_collection'))

    members = chat_db_handler.get_chat_members(chat_id)
    all_users = db_handler.get_all_users()
    member_ids = {m['id'] for m in members}

    logger.debug(f"Chat-Objekt für Einstellungen von Chat '{chat_id}': {chat}")

    is_admin = False
    if 'created_by' in chat.keys() and chat['created_by'] is not None:
        try:
            is_admin = int(chat['created_by']) == int(g.user['id'])
            logger.debug(f"Admin-Check für Chat '{chat_id}', Benutzer {user_id}: {is_admin} (Ersteller: {chat['created_by']})")
        except Exception as e:
            logger.error(f"Fehler beim Admin-Check für Chat '{chat_id}', Benutzer {user_id}: {e}", exc_info=True)
            is_admin = False
    else:
        logger.warning(f"Chat {chat_id} hat kein Feld 'created_by' oder Wert ist None. Admin-Check schlägt fehl.")
        is_admin = False

    if request.method == 'POST':
        logger.info(f"POST-Anfrage an Chat-Einstellungen für Chat '{chat_id}' von Benutzer {user_id}.")
        if not is_admin:
            flash("Nur der Chat-Admin kann Einstellungen ändern.", "danger")
            logger.warning(f"Nicht-Admin Benutzer {user_id} versuchte Einstellungen für Chat '{chat_id}' zu ändern.")
            return redirect(url_for('chat.chat_settings', chat_id=chat_id))

        add_ids = request.form.getlist('add_user')
        remove_ids = request.form.getlist('remove_user')
        logger.debug(f"Chat '{chat_id}': Hinzuzufügende Benutzer: {add_ids}, Zu entfernende Benutzer: {remove_ids}")

        for uid_to_add in add_ids:
            if int(uid_to_add) not in member_ids:
                chat_db_handler.add_chat_member(chat_id, int(uid_to_add))
                logger.info(f"Benutzer {uid_to_add} zu Chat '{chat_id}' hinzugefügt.")
        for uid_to_remove in remove_ids:
            if int(uid_to_remove) in member_ids:
                chat_db_handler.remove_chat_member(chat_id, int(uid_to_remove))
                logger.info(f"Benutzer {uid_to_remove} von Chat '{chat_id}' entfernt.")
        
        members_can_invite_form = request.form.get('members_can_invite') == 'on'
        chat_db_handler.set_members_can_invite(chat_id, members_can_invite_form)
        logger.info(f"Chat '{chat_id}': members_can_invite gesetzt auf {members_can_invite_form}.")
        
        flash("Chat-Einstellungen gespeichert.", "success")
        return redirect(url_for('chat.chat_settings', chat_id=chat_id))

    dark_mode_active_settings = g.user and g.user.get('theme') == 'dark'
    return render_template(
        'chat_settings.html',
        chat=chat,
        members=members,
        all_users=all_users,
        is_admin=is_admin,
        darkmode=dark_mode_active_settings
    )


@chat_bp.route('/<string:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    user_id = g.user['id'] if g.user else 'Unbekannt'
    logger.info(f"Versuch Chat '{chat_id}' von Benutzer ID {user_id} zu löschen.")
    
    chat = chat_db_handler.get_chat_by_id(chat_id)
    if not chat:
        flash("Chat nicht gefunden.", "danger")
        logger.warning(f"Löschversuch für nicht existierenden Chat '{chat_id}' durch Benutzer {user_id}.")
        return redirect(url_for('chat.chat_collection'))

    is_admin = False
    if 'created_by' in chat.keys() and chat['created_by'] is not None:
        try:
            is_admin = str(chat['created_by']) == str(g.user['id'])
            logger.debug(f"Admin-Check für Löschen von Chat '{chat_id}', Benutzer {user_id}: {is_admin} (Ersteller: {chat['created_by']})")
        except Exception as e:
            logger.error(f"Fehler beim Admin-Check für Löschen von Chat '{chat_id}': {e}", exc_info=True)
            is_admin = False
    else:
        logger.warning(f"Chat {chat_id} hat kein 'created_by' Feld für Admin-Check beim Löschen.")
        is_admin = False

    if not is_admin:
        flash("Nur der Chat-Admin kann den Chat löschen.", "danger")
        logger.warning(f"Nicht-Admin Benutzer {user_id} versuchte Chat '{chat_id}' zu löschen.")
        return redirect(url_for('chat.chat_settings', chat_id=chat_id))

    try:
        logger.debug(f"Admin {user_id} löscht Chat '{chat_id}'.")
        if chat_db_handler.delete_chat(chat_id):
            flash("Chat wurde gelöscht.", "success")
            logger.info(f"Chat '{chat_id}' erfolgreich von Admin {user_id} gelöscht.")
        else:
            flash("Fehler beim Löschen des Chats.", "danger")
            logger.error(f"Fehler beim Löschen des Chats '{chat_id}' durch Admin {user_id} (Handler gab False zurück).")
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Chats '{chat_id}': {e}", exc_info=True)
        flash("Fehler beim Löschen des Chats.", "danger")
    return redirect(url_for('chat.chat_collection'))


@chat_bp.route('/<string:chat_id>/messages', methods=['POST'])
@login_required
def api_send_message(chat_id):
    logger.info(f"[API_SEND_MESSAGE] POST-Anfrage für Chat-ID: {chat_id} (Typ: {type(chat_id)})")

    if not g.user:
        logger.error("[API_SEND_MESSAGE] g.user nicht gesetzt. Benutzer nicht angemeldet oder Sitzungsproblem.")
        return jsonify({'error': 'Benutzer nicht authentifiziert.'}), 401

    user_id = g.user.get('id')
    if not user_id:
        logger.error("[API_SEND_MESSAGE] user_id nicht in g.user gefunden.")
        return jsonify({'error': 'Benutzer-ID nicht gefunden.'}), 400

    chat_id_str = str(chat_id)
    user_id_str = str(user_id)

    logger.info(f"[API_SEND_MESSAGE] Authentifizierter Benutzer user_id: {user_id_str} sendet an chat_id: {chat_id_str}")

    data = request.get_json()
    if not data:
        logger.warning("[API_SEND_MESSAGE] Keine JSON-Daten in der Anfrage empfangen.")
        return jsonify({'error': 'Keine Daten empfangen.'}), 400

    message_text = (data.get('message_text') or '').strip()
    logger.debug(f"[API_SEND_MESSAGE] Empfangener Nachrichtentext (gekürzt): {message_text[:50] if message_text else 'LEER'}")
    if not message_text:
        logger.warning("[API_SEND_MESSAGE] Nachrichtentext ist leer.")
        return jsonify({'error': 'Nachricht darf nicht leer sein.'}), 400

    chat_exists = chat_db_handler.get_chat_by_id(chat_id_str) is not None
    if not chat_exists:
        logger.warning(f"[API_SEND_MESSAGE] Chat {chat_id_str} existiert nicht (laut chat_db_handler).")
        return jsonify({'error': 'Chat existiert nicht.'}), 404

    if not chat_db_handler.is_chat_participant(chat_id_str, user_id_str):
        logger.info(f"[API_SEND_MESSAGE] Benutzer {user_id_str} ist kein Teilnehmer von Chat {chat_id_str}. Füge hinzu...")
        if not chat_db_handler.join_chat(chat_id_str, user_id_str):
            logger.error(f"[API_SEND_MESSAGE] Konnte Benutzer {user_id_str} nicht zu Chat {chat_id_str} hinzufügen.")
            return jsonify({'error': 'Konnte Benutzer nicht zum Chat hinzufügen.'}), 500

    logger.debug(f"[API_SEND_MESSAGE] Füge Nachricht zu Chat {chat_id_str} von Benutzer {user_id_str} hinzu via chat_db_handler.")
    message_details = chat_db_handler.add_message_and_get_details(chat_id_str, user_id_str, message_text)

    if not message_details:
        logger.error("[API_SEND_MESSAGE] Fehler beim Hinzufügen der Nachricht zur DB über chat_db_handler.")
        return jsonify({'error': 'Fehler beim Speichern der Nachricht.'}), 500

    logger.info(f"[API_SEND_MESSAGE] Nachricht in Chat {chat_id_str} gespeichert mit Details: {message_details}")

    from flask import current_app
    socketio = current_app.extensions.get('socketio')
    if socketio:
        logger.debug(f"[API_SEND_MESSAGE] Sende SocketIO 'new_message' Event an Raum '{str(chat_id_str)}'.")
        socketio.emit('new_message', message_details, room=str(chat_id_str), namespace='/chat')
    else:
        logger.warning("[API_SEND_MESSAGE] SocketIO-Instanz nicht gefunden. Kann 'new_message' Event nicht senden.")

    return jsonify({'success': True, 'message': message_details}), 201

def register_chat_events(socketio_instance):
    logger.info("Registriere SocketIO Chat-Events...")

    @socketio_instance.on('join', namespace='/chat')
    def handle_join(data):
        room_id = data.get('room_id')
        firebase_uid_session = session.get('firebase_uid')
        logger.info(f"SocketIO 'join' Event: Raum '{room_id}', Firebase UID aus Session: {firebase_uid_session}")

        if not firebase_uid_session:
            logger.warning("SocketIO 'join': Benutzer nicht angemeldet (Firebase UID fehlt in Session).")
            emit('error', {'msg': 'Benutzer nicht angemeldet (Firebase UID fehlt).'})
            return
            
        from database.handler.postgres.postgres_db_handler import get_user_by_firebase_uid
        user = get_user_by_firebase_uid(firebase_uid_session)
        if not user:
            logger.warning(f"SocketIO 'join': Benutzer mit Firebase UID {firebase_uid_session} nicht in lokaler DB gefunden.")
            emit('error', {'msg': 'Benutzer wurde nicht in der Datenbank gefunden.'})
            return
            
        user_id_local = user['id']
        username_local = user.get('username', 'Unbekannt')
        logger.info(f"SocketIO 'join': Benutzer {username_local} (ID: {user_id_local}, Firebase UID: {firebase_uid_session}) tritt Raum '{room_id}' bei.")
        
        if not room_id:
            logger.warning("SocketIO 'join': Fehlende Raum-ID.")
            emit('error', {'msg': 'Fehlende Raum-ID'})
            return

        join_room(str(room_id))
        logger.info(f"SocketIO 'join': Benutzer {username_local} erfolgreich Raum '{str(room_id)}' beigetreten.")
        emit('status', {'msg': f"{username_local} ist dem Chat beigetreten."}, room=str(room_id))

    @socketio_instance.on('leave', namespace='/chat')
    def handle_leave(data):
        room_id = data.get('room_id')
        firebase_uid_session = session.get('firebase_uid')
        logger.info(f"SocketIO 'leave' Event: Raum '{room_id}', Firebase UID aus Session: {firebase_uid_session}")

        if not firebase_uid_session:
            logger.warning("SocketIO 'leave': Benutzer nicht angemeldet (Firebase UID fehlt in Session).")
            emit('error', {'msg': 'Benutzer nicht angemeldet (Firebase UID fehlt).'})
            return
            
        from database.handler.postgres.postgres_db_handler import get_user_by_firebase_uid
        user = get_user_by_firebase_uid(firebase_uid_session)
        if not user:
            logger.warning(f"SocketIO 'leave': Benutzer mit Firebase UID {firebase_uid_session} nicht in lokaler DB gefunden.")
            emit('error', {'msg': 'Benutzer wurde nicht in der Datenbank gefunden.'})
            return
            
        user_id_local = user['id']
        username_local = user.get('username', 'Unbekannt')
        logger.info(f"SocketIO 'leave': Benutzer {username_local} (ID: {user_id_local}, Firebase UID: {firebase_uid_session}) verlässt Raum '{room_id}'.")

        if not room_id:
            logger.warning("SocketIO 'leave': Fehlende Raum-ID.")
            emit('error', {'msg': 'Fehlende Raum-ID'})
            return

        leave_room(str(room_id))
        logger.info(f"SocketIO 'leave': Benutzer {username_local} erfolgreich Raum '{str(room_id)}' verlassen.")
        emit('status', {'msg': f"{username_local} hat den Chat verlassen."}, room=str(room_id))

    @socketio_instance.on('send_message', namespace='/chat')
    def handle_send_message(data):
        message_text = data.get('message_text', '').strip()
        chat_room_id = data.get('chat_room_id')
        firebase_uid_session = session.get('firebase_uid')
        logger.info(f"SocketIO 'send_message' Event: Raum '{chat_room_id}', Firebase UID: {firebase_uid_session}, Nachricht (gekürzt): {message_text[:50]}")

        if not firebase_uid_session:
            logger.warning("SocketIO 'send_message': Benutzer nicht angemeldet (Firebase UID fehlt).")
            emit('error', {'msg': 'Benutzer nicht angemeldet (Firebase UID fehlt).'})
            return
            
        from database.handler.postgres.postgres_db_handler import get_user_by_firebase_uid
        current_user = get_user_by_firebase_uid(firebase_uid_session)
        if not current_user:
            logger.warning(f"SocketIO 'send_message': Benutzer mit Firebase UID {firebase_uid_session} nicht in DB gefunden.")
            emit('error', {'msg': 'Benutzer wurde nicht in der Datenbank gefunden.'})
            return
            
        user_id_local = current_user['id']
        username_local = current_user.get('username', 'Unbekannt')
        logger.info(f"SocketIO 'send_message': Von Benutzer {username_local} (ID: {user_id_local}) an Raum '{chat_room_id}'.")

        if not message_text:
            logger.warning("SocketIO 'send_message': Nachrichtentext ist leer.")
            emit('error', {'msg': 'Nachricht darf nicht leer sein.'})
            return
        
        if not chat_room_id:
            logger.warning("SocketIO 'send_message': Chatraum-ID fehlt.")
            emit('error', {'msg': 'Chatraum-ID fehlt.'})
            return

        chat = chat_db_handler.get_chat_by_id(chat_room_id)
        if not chat:
            logger.warning(f"SocketIO 'send_message': Chatraum '{chat_room_id}' nicht gefunden.")
            emit('error', {'msg': 'Chatraum nicht gefunden.'})
            return
        
        if not chat_db_handler.is_chat_participant(chat_room_id, user_id_local):
            logger.warning(f"SocketIO 'send_message': Benutzer {user_id_local} ist kein Teilnehmer von Chat '{chat_room_id}'.")
            emit('error', {'msg': 'Benutzer ist kein Teilnehmer dieses Chats.'})
            return

        logger.debug(f"SocketIO 'send_message': Füge Nachricht zu Chat '{chat_room_id}' von Benutzer {user_id_local} hinzu via chat_db_handler.")
        message_details = chat_db_handler.add_message_and_get_details(chat_room_id, user_id_local, message_text)
        if message_details:
            logger.info(f"SocketIO 'send_message': Nachricht erfolgreich gespeichert, sende 'new_message' Event an Raum '{str(chat_room_id)}'. Details: {message_details}")
            emit('new_message', message_details, room=str(chat_room_id))
        else:
            logger.error(f"SocketIO 'send_message': Fehler beim Speichern der Nachricht für Chat '{chat_room_id}'.")
            emit('error', {'msg': 'Fehler beim Senden der Nachricht.'})
            return
    logger.info("SocketIO Chat-Events erfolgreich registriert.")

@chat_bp.route('/admin/migrate-chat-data')
@login_required
def migrate_chat_data():
    user_id = g.user['id'] if g.user else None
    username = g.user['username'] if g.user else 'Unbekannt'
    logger.info(f"Admin-Route /admin/migrate-chat-data aufgerufen von Benutzer: {username} (ID: {user_id})")

    if g.user and g.user['id'] == 1:
        logger.info(f"Admin-Benutzer {username} (ID: {user_id}) führt Chat-Datenmigration durch.")
        success = chat_db_handler.migrate_chat_data()
        
        if success:
            flash('Chat-Daten wurden erfolgreich migriert!', 'success')
            logger.info("Chat-Daten erfolgreich migriert.")
        else:
            flash('Fehler bei der Migration der Chat-Daten.', 'danger')
            logger.error("Fehler bei der Migration der Chat-Daten.")
    else:
        flash('Zugriff verweigert. Nur Administratoren können diese Funktion nutzen.', 'danger')
        logger.warning(f"Zugriffsversuch auf /admin/migrate-chat-data durch nicht-Admin Benutzer: {username} (ID: {user_id})")
    
    return redirect(url_for('chat.chat_collection'))