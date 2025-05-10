from flask import Blueprint, render_template, g, request, flash, redirect, url_for, jsonify, session
from flask_socketio import emit, join_room, leave_room
from utils import login_required
import logging
from datetime import datetime
import sqlite3
import dotenv
import os

import db_handler
import chat_db_handler

# Lade Umgebungsvariablen aus .env-Datei
dotenv.load_dotenv()
# Stelle sicher, dass die Umgebungsvariablen geladen sind

DATABASE_FILE_PATH = 'database/database.db' # Korrigierter relativer Pfad als Fallback

# Logger konfigurieren
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Blueprint erstellen
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Benutzerdefinierten Filter für datetime hinzufügen
@chat_bp.app_template_filter('datetime')
def format_datetime(value, format='%d.%m.%Y %H:%M'):
    """Formatiert ein Datetime-Objekt zu einem lesbaren String."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)

@chat_bp.route('/chats')
@login_required
def chat_collection():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Sicherstellen, dass der Benutzer am Standard-Chat teilnimmt
    chat_db_handler.ensure_user_in_default_chat(g.user['id'])
    
    # Chatrooms abrufen, an denen der Benutzer teilnimmt
    chat_data = chat_db_handler.get_user_chats(g.user['id'])
    
    logger.debug(f"Retrieved {len(chat_data)} chat rooms for user {g.user['id']}")
    
    return render_template('chat_collection.html', 
                           user=g.user, 
                           darkmode=dark_mode_active, 
                           chat_rooms=chat_data)

@chat_bp.route('/<int:chat_id>')
@login_required
def chat_details(chat_id):
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Überprüfen, ob der Chat existiert
    chat = chat_db_handler.get_chat_by_id(chat_id)
    
    if not chat:
        flash('Der angeforderte Chat existiert nicht.', 'danger')
        return redirect(url_for('chat.chat_collection'))
    
    # Überprüfen, ob der Benutzer Teilnehmer ist
    if not chat_db_handler.is_chat_participant(chat_id, g.user['id']):
        chat_db_handler.join_chat(chat_id, g.user['id'])
        flash(f'Du wurdest zum Chat "{chat["name"]}" hinzugefügt.', 'success')
    
    # Nachrichten des Chats laden
    messages = chat_db_handler.get_chat_messages(chat_id, limit=100)
    
    return render_template('chat_details.html', 
                           user=g.user, 
                           darkmode=dark_mode_active,
                           chat=chat,
                           initial_messages=messages)

@chat_bp.route('/new-chat', methods=['GET', 'POST'])
@login_required
def new_chat():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    if request.method == 'POST':
        chat_name = request.form.get('chat_name')
        
        if not chat_name or len(chat_name.strip()) == 0:
            flash('Der Chatname darf nicht leer sein.', 'danger')
            return render_template('new_chat.html', darkmode=dark_mode_active, user=g.user)
        
        # Stelle sicher, dass create_chat den User als created_by speichert!
        chat_id = chat_db_handler.create_chat(chat_name, g.user['id'])
        
        if chat_id:
            flash('Chat wurde erfolgreich erstellt!', 'success')
            return redirect(url_for('chat.chat_details', chat_id=chat_id))
        else:
            flash('Fehler beim Erstellen des Chats.', 'danger')
    
    return render_template('new_chat.html', darkmode=dark_mode_active, user=g.user)


@chat_bp.route('/chat/<int:chat_id>/settings', methods=['GET', 'POST'])
@login_required
def chat_settings(chat_id):
    import db_handler
    chat = db_handler.get_chat_room(chat_id)
    if not chat:
        flash("Chat nicht gefunden.", "danger")
        return redirect(url_for('chat.chat_collection'))

    members = db_handler.get_chat_members(chat_id)
    all_users = db_handler.get_all_users()
    member_ids = {m['id'] for m in members}

    # Debug: Zeige das Chat-Objekt im Log
    logger.debug(f"Chat-Objekt für Einstellungen: {chat}")

    # Sicherstellen, dass das Feld existiert und nicht None ist
    if 'created_by' in chat.keys() and chat['created_by'] is not None:
        try:
            is_admin = int(chat['created_by']) == int(g.user['id'])
        except Exception as e:
            logger.error(f"Fehler beim Admin-Check: {e}")
            is_admin = False
    else:
        logger.warning(f"Chat {chat_id} hat kein Feld 'created_by' oder Wert ist None. Admin-Check schlägt fehl.")
        is_admin = False

    if request.method == 'POST' and is_admin:
        # Mitglieder hinzufügen/entfernen
        add_ids = request.form.getlist('add_user')
        remove_ids = request.form.getlist('remove_user')
        for uid in add_ids:
            if int(uid) not in member_ids:
                db_handler.add_chat_member(chat_id, int(uid))
        for uid in remove_ids:
            if int(uid) in member_ids:
                db_handler.remove_chat_member(chat_id, int(uid))
        # members_can_invite setzen
        members_can_invite = request.form.get('members_can_invite') == 'on'
        db_handler.set_members_can_invite(chat_id, members_can_invite)
        flash("Chat-Einstellungen gespeichert.", "success")
        return redirect(url_for('chat.chat_settings', chat_id=chat_id))

    return render_template(
        'chat_settings.html',
        chat=chat,
        members=members,
        all_users=all_users,
        is_admin=is_admin,
        darkmode=g.user.get('theme') == 'dark'
    )


@chat_bp.route('/chat/<int:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    chat = chat_db_handler.get_chat_by_id(chat_id)
    if not chat:
        flash("Chat nicht gefunden.", "danger")
        return redirect(url_for('chat.chat_collection'))

    # Admin-Check
    if 'created_by' in chat.keys() and chat['created_by'] is not None:
        try:
            is_admin = int(chat['created_by']) == int(g.user['id'])
        except Exception as e:
            logger.error(f"Fehler beim Admin-Check: {e}")
            is_admin = False
    else:
        is_admin = False

    if not is_admin:
        flash("Nur der Chat-Admin kann den Chat löschen.", "danger")
        return redirect(url_for('chat.chat_settings', chat_id=chat_id))

    # Chat löschen
    try:
        chat_db_handler.delete_chat(chat_id)
        flash("Chat wurde gelöscht.", "success")
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Chats: {e}")
        flash("Fehler beim Löschen des Chats.", "danger")
    return redirect(url_for('chat.chat_collection'))


@chat_bp.route('/<int:chat_id>/messages', methods=['POST'])
@login_required
def api_send_message(chat_id):
    logger.debug(f"[API_SEND_MESSAGE] Received POST request for chat_id: {chat_id} (type: {type(chat_id)})")
    
    if not g.user:
        logger.error("[API_SEND_MESSAGE] g.user is not set. User not logged in or session issue.")
        return jsonify({'error': 'Benutzer nicht authentifiziert.'}), 401

    user_id = g.user.get('id')
    if not user_id:
        logger.error("[API_SEND_MESSAGE] user_id not found in g.user.")
        return jsonify({'error': 'Benutzer-ID nicht gefunden.'}), 400
    
    logger.debug(f"[API_SEND_MESSAGE] Authenticated user_id: {user_id} (type: {type(user_id)})")

    data = request.get_json()
    if not data:
        logger.warning("[API_SEND_MESSAGE] No JSON data received in request.")
        return jsonify({'error': 'Keine Daten empfangen.'}), 400
    
    logger.debug(f"[API_SEND_MESSAGE] Received JSON data: {data}")
    
    message_text = (data.get('message_text') or '').strip()
    logger.debug(f"[API_SEND_MESSAGE] Extracted message_text: '{message_text}'")

    if not message_text:
        logger.warning("[API_SEND_MESSAGE] Message text is empty.")
        return jsonify({'error': 'Nachricht darf nicht leer sein.'}), 400

    logger.debug(f"[API_SEND_MESSAGE] Checking if user {user_id} is participant in chat {chat_id}")
    if not chat_db_handler.is_chat_participant(chat_id, user_id):
        logger.warning(f"[API_SEND_MESSAGE] User {user_id} is not a participant of chat {chat_id}.")
        return jsonify({'error': 'Du bist kein Teilnehmer dieses Chats.'}), 403
    logger.debug(f"[API_SEND_MESSAGE] User {user_id} is a participant.")

    logger.debug(f"[API_SEND_MESSAGE] Attempting to add message to DB: chat_id={chat_id} (type: {type(chat_id)}), user_id={user_id} (type: {type(user_id)}), text='{message_text}'")
    message_details = chat_db_handler.add_message_and_get_details(chat_id, user_id, message_text)
    logger.debug(f"[API_SEND_MESSAGE] Raw return from add_message_and_get_details: {message_details}")
    
    if not message_details:
        logger.error(f"[API_SEND_MESSAGE] Failed to add message to DB. chat_db_handler.add_message_and_get_details returned: {message_details}")
        return jsonify({'error': 'Fehler beim Speichern der Nachricht.'}), 500
    
    logger.debug(f"[API_SEND_MESSAGE] Message supposedly added to DB. Details: {message_details}")

    # SocketIO: Nachricht an Raum senden
    from flask import current_app
    socketio = current_app.extensions.get('socketio')
    if socketio:
        logger.debug(f"[API_SEND_MESSAGE] Attempting to emit 'new_message' to room '{str(chat_id)}' with details: {message_details}")
        socketio.emit('new_message', message_details, room=str(chat_id), namespace='/chat')
        logger.debug(f"[API_SEND_MESSAGE] 'new_message' emit call completed for room '{str(chat_id)}'.")
    else:
        logger.error("[API_SEND_MESSAGE] SocketIO instance not found in current_app.extensions. Cannot emit message.")

    logger.info(f"[API_SEND_MESSAGE] Message successfully processed for user {user_id} to chat {chat_id}.")
    return jsonify({'success': True, 'message': message_details}), 201

def register_chat_events(socketio_instance):
    @socketio_instance.on('join', namespace='/chat')
    def handle_join(data):
        room_id = data.get('room_id')
        user_id = session.get('user_id')
        user = db_handler.get_user_by_id(user_id) if user_id else None

        if not room_id or not user:
            emit('error', {'msg': 'Fehlende Raum-ID oder Benutzer nicht angemeldet.'})
            return

        join_room(str(room_id))
        emit('status', {'msg': f"{user['username']} ist dem Chat beigetreten."}, room=str(room_id))

    @socketio_instance.on('leave', namespace='/chat')
    def handle_leave(data):
        room_id = data.get('room_id')
        user_id = session.get('user_id')
        user = db_handler.get_user_by_id(user_id) if user_id else None

        if not room_id or not user:
            emit('error', {'msg': 'Fehlende Raum-ID oder Benutzer nicht angemeldet.'})
            return

        leave_room(str(room_id))
        emit('status', {'msg': f"{user['username']} hat den Chat verlassen."}, room=str(room_id))

    @socketio_instance.on('send_message', namespace='/chat')
    def handle_send_message(data):
        message_text = data.get('message_text')
        chat_room_id = data.get('chat_room_id')
        user_id = session.get('user_id')

        if not user_id:
            emit('error', {'msg': 'Benutzer nicht angemeldet.'})
            return
        
        current_user = db_handler.get_user_by_id(user_id)
        if not current_user:
            emit('error', {'msg': 'Benutzer nicht gefunden.'})
            return

        if not message_text or len(message_text.strip()) == 0:
            emit('error', {'msg': 'Nachricht darf nicht leer sein.'})
            return
        
        if not chat_room_id:
            emit('error', {'msg': 'Chatraum-ID fehlt.'})
            return

        chat = chat_db_handler.get_chat_by_id(chat_room_id)
        if not chat:
            emit('error', {'msg': 'Chatraum nicht gefunden.'})
            return
        
        if not chat_db_handler.is_chat_participant(chat_room_id, user_id):
            emit('error', {'msg': 'Benutzer ist kein Teilnehmer dieses Chats.'})
            return

        message_details = chat_db_handler.add_message_and_get_details(chat_room_id, user_id, message_text)
        if message_details:
            emit('new_message', message_details, room=str(chat_room_id))
        else:
            emit('error', {'msg': 'Fehler beim Senden der Nachricht.'})
            return