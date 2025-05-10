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
    
    # Debug: Firebase-Status und Datenquelle deutlicher überprüfen
    import firebase_db_handler
    USE_FIREBASE = os.getenv('USE_FIREBASE', 'true').lower() == 'true'
    can_use_fb = firebase_db_handler.can_use_firebase() if USE_FIREBASE else False
    
    # Stärker gefiltertes Logging
    logger.info(f"Chat collection: Firebase enabled: {USE_FIREBASE}, Can use Firebase: {can_use_fb}, User ID: {g.user['id']}")
    
    # Force user into default chat
    try:
        if can_use_fb:
            firebase_db_handler.ensure_user_in_default_chat(g.user['id'])
            # Überprüfen, ob der Default-Chat erfolgreich erstellt wurde
            default_chat = firebase_db_handler.get_default_chat_id()
            logger.info(f"Default Firebase chat ID: {default_chat}")
        else:
            chat_db_handler.ensure_user_in_default_chat(g.user['id'])
    except Exception as e:
        logger.error(f"Error ensuring default chat: {e}", exc_info=True)
    
    # Chats aus der richtigen Datenquelle abrufen
    chat_data = []
    try:
        if can_use_fb:
            # Direkte Abfrage in Firebase
            user_id_str = str(g.user['id'])  # Firebase vergleicht mit Strings
            
            # Teilnahme direkt überprüfen
            from firebase_admin import db
            chat_participants_ref = db.reference("/chat_participants")
            all_participants = chat_participants_ref.get() or {}
            logger.info(f"All chat participants: {all_participants}")
            
            if isinstance(all_participants, dict):
                for chat_id, participants in all_participants.items():
                    logger.info(f"Checking chat {chat_id} for user {user_id_str} - participants: {participants}")
                    # Prüfen ob der User ein Teilnehmer ist
                    if isinstance(participants, dict) and user_id_str in participants:
                        logger.info(f"Found user {user_id_str} as participant in chat {chat_id}")
                        # Chat-Details abrufen
                        chat_ref = db.reference(f"/chats/{chat_id}")
                        chat_data_entry = chat_ref.get() or {}
                        
                        if chat_data_entry:
                            # Format und hinzufügen
                            chat_data.append({
                                "id": chat_id,
                                "name": chat_data_entry.get("name", "Unbenannt"),
                                "last_message": "",  # Können wir später noch auffüllen
                                "last_activity": "vor kurzem"
                            })
                            logger.info(f"Added chat {chat_id} with name {chat_data_entry.get('name')} to results")
                            
            # Falls keine Chats über direkte Methode gefunden wurden, Fallback auf normal
            if not chat_data:
                logger.warning(f"No chats found with direct Firebase access, trying normal function")
                chat_data = firebase_db_handler.get_user_chats(g.user['id'])
        else:
            chat_data = chat_db_handler.get_user_chats(g.user['id'])
    except Exception as e:
        logger.error(f"Error getting user chats: {e}", exc_info=True)
    
    logger.info(f"Returning {len(chat_data)} chats for display: {chat_data}")
    
    # Debug-Modus für Entwicklung
    debug_info = {
        "firebase_enabled": USE_FIREBASE,
        "can_use_firebase": can_use_fb,
        "user_id": g.user['id'],
        "user_id_str": str(g.user['id']),
        "chat_count": len(chat_data)
    }
    
    return render_template('chat_collection.html', 
                           user=g.user, 
                           darkmode=dark_mode_active, 
                           chat_rooms=chat_data,
                           debug_info=debug_info)  # Debug-Info an Template übergeben

@chat_bp.route('/<string:chat_id>')
@login_required
def chat_details(chat_id):
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    import firebase_db_handler
    USE_FIREBASE = os.getenv('USE_FIREBASE', 'true').lower() == 'true'
    can_use_fb = firebase_db_handler.can_use_firebase() if USE_FIREBASE else False

    # Chat laden
    chat = None
    if can_use_fb:
        try:
            chat = firebase_db_handler.get_chat_by_id(chat_id)
        except Exception:
            pass
    if not chat:
        chat = chat_db_handler.get_chat_by_id(chat_id)
    if not chat:
        flash('Der angeforderte Chat existiert nicht.', 'danger')
        return redirect(url_for('chat.chat_collection'))

    # Sicherstellen, dass der User Teilnehmer ist (immer join_chat, wenn nicht)
    is_participant = False
    if can_use_fb:
        try:
            is_participant = firebase_db_handler.is_chat_participant(chat_id, g.user['id'])
        except Exception:
            pass
    else:
        is_participant = chat_db_handler.is_chat_participant(chat_id, g.user['id'])

    if not is_participant:
        if can_use_fb:
            firebase_db_handler.join_chat(chat_id, g.user['id'])
        else:
            chat_db_handler.join_chat(chat_id, g.user['id'])
        # Nach join_chat() ist der User jetzt Teilnehmer

    # Jetzt Nachrichten laden (nach join_chat!)
    messages = []
    if can_use_fb:
        try:
            messages = firebase_db_handler.get_chat_messages(chat_id, limit=100)
        except Exception:
            pass
    if not messages:
        messages = chat_db_handler.get_chat_messages(chat_id, limit=100)

    return render_template('chat_details.html',
                           user=g.user,
                           darkmode=dark_mode_active,
                           chat=chat,
                           initial_messages=messages,
                           debug_info={
                               "chat_id": chat_id,
                               "firebase_enabled": can_use_fb,
                               "user_id": g.user['id'],
                               "message_count": len(messages)
                           })

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


@chat_bp.route('/<string:chat_id>/settings', methods=['GET', 'POST'])
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


@chat_bp.route('/<string:chat_id>/delete', methods=['POST'])
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


@chat_bp.route('/<string:chat_id>/messages', methods=['POST'])
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
    
    # Wir stellen sicher, dass wir einen String-Type für die Chat-ID haben
    chat_id_str = str(chat_id)
    user_id_str = str(user_id)
    
    logger.debug(f"[API_SEND_MESSAGE] Authenticated user_id: {user_id_str} to chat_id: {chat_id_str}")

    data = request.get_json()
    if not data:
        logger.warning("[API_SEND_MESSAGE] No JSON data received in request.")
        return jsonify({'error': 'Keine Daten empfangen.'}), 400
    
    message_text = (data.get('message_text') or '').strip()
    if not message_text:
        logger.warning("[API_SEND_MESSAGE] Message text is empty.")
        return jsonify({'error': 'Nachricht darf nicht leer sein.'}), 400

    # Import und Überprüfung der Firebase-Verfügbarkeit
    import firebase_db_handler
    USE_FIREBASE = os.getenv('USE_FIREBASE', 'true').lower() == 'true'
    can_use_fb = firebase_db_handler.can_use_firebase() if USE_FIREBASE else False
    
    # Überprüfung des Chats und der Teilnehmerstatus
    if can_use_fb:
        # Überprüfen, ob der Chat existiert
        chat_ref = firebase_db_handler.get_chat_by_id(chat_id_str)
        if not chat_ref:
            logger.warning(f"[API_SEND_MESSAGE] Chat {chat_id_str} does not exist.")
            return jsonify({'error': 'Chat existiert nicht.'}), 404
            
        # Sicherstellen, dass der Benutzer ein Teilnehmer ist
        is_participant = firebase_db_handler.is_chat_participant(chat_id_str, user_id_str)
        
        if not is_participant:
            logger.info(f"[API_SEND_MESSAGE] User {user_id_str} is not a participant of chat {chat_id_str}. Adding...")
            firebase_db_handler.join_chat(chat_id_str, user_id_str)
    else:
        # SQLite-Fallback
        chat_ref = chat_db_handler.get_chat_by_id(chat_id_str)
        if not chat_ref:
            logger.warning(f"[API_SEND_MESSAGE] Chat {chat_id_str} does not exist.")
            return jsonify({'error': 'Chat existiert nicht.'}), 404
            
        # Sicherstellen, dass der Benutzer ein Teilnehmer ist
        if not chat_db_handler.is_chat_participant(chat_id_str, user_id_str):
            logger.info(f"[API_SEND_MESSAGE] User {user_id_str} is not a participant of chat {chat_id_str}. Adding...")
            chat_db_handler.join_chat(chat_id_str, user_id_str)
    
    # Nachricht hinzufügen
    if can_use_fb:
        message_details = firebase_db_handler.add_message_and_get_details(chat_id_str, user_id_str, message_text)
    else:
        message_details = chat_db_handler.add_message_and_get_details(chat_id_str, user_id_str, message_text)
    
    if not message_details:
        logger.error("[API_SEND_MESSAGE] Failed to add message to DB.")
        return jsonify({'error': 'Fehler beim Speichern der Nachricht.'}), 500
    
    # Wichtiges Debug-Log
    logger.info(f"[API_SEND_MESSAGE] Message saved to chat {chat_id_str} with details: {message_details}")
    
    # SocketIO-Nachricht senden
    from flask import current_app
    socketio = current_app.extensions.get('socketio')
    if socketio:
        socketio.emit('new_message', message_details, room=str(chat_id_str), namespace='/chat')
    
    return jsonify({'success': True, 'message': message_details}), 201

def register_chat_events(socketio_instance):
    @socketio_instance.on('join', namespace='/chat')
    def handle_join(data):
        room_id = data.get('room_id')
        firebase_uid = session.get('firebase_uid')
        if not firebase_uid:
            emit('error', {'msg': 'Benutzer nicht angemeldet (Firebase UID fehlt).'})
            return
            
        from db_handler import get_user_by_firebase_uid
        user = get_user_by_firebase_uid(firebase_uid)
        if not user:
            emit('error', {'msg': 'Benutzer wurde nicht in der Datenbank gefunden.'})
            return
            
        user_id = user['id']
        
        if not room_id:
            emit('error', {'msg': 'Fehlende Raum-ID'})
            return

        join_room(str(room_id))
        emit('status', {'msg': f"{user['username']} ist dem Chat beigetreten."}, room=str(room_id))

    @socketio_instance.on('leave', namespace='/chat')
    def handle_leave(data):
        room_id = data.get('room_id')
        firebase_uid = session.get('firebase_uid')
        if not firebase_uid:
            emit('error', {'msg': 'Benutzer nicht angemeldet (Firebase UID fehlt).'})
            return
            
        from db_handler import get_user_by_firebase_uid
        user = get_user_by_firebase_uid(firebase_uid)
        if not user:
            emit('error', {'msg': 'Benutzer wurde nicht in der Datenbank gefunden.'})
            return
            
        user_id = user['id']

        if not room_id:
            emit('error', {'msg': 'Fehlende Raum-ID'})
            return

        leave_room(str(room_id))
        emit('status', {'msg': f"{user['username']} hat den Chat verlassen."}, room=str(room_id))

    @socketio_instance.on('send_message', namespace='/chat')
    def handle_send_message(data):
        message_text = data.get('message_text')
        chat_room_id = data.get('chat_room_id')
        firebase_uid = session.get('firebase_uid')
        if not firebase_uid:
            emit('error', {'msg': 'Benutzer nicht angemeldet (Firebase UID fehlt).'})
            return
            
        from db_handler import get_user_by_firebase_uid
        current_user = get_user_by_firebase_uid(firebase_uid)
        if not current_user:
            emit('error', {'msg': 'Benutzer wurde nicht in der Datenbank gefunden.'})
            return
            
        user_id = current_user['id']

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

@chat_bp.route('/admin/migrate-chat-data')
@login_required
def migrate_chat_data():
    # Prüfe, ob Benutzer Admin ist (ID 1)
    if g.user and g.user['id'] == 1:  # Einfacher Admin-Check, erweitern nach Bedarf
        import firebase_db_handler
        success = firebase_db_handler.migrate_chat_data_from_sqlite_to_firebase()
        
        if success:
            flash('Chat-Daten wurden erfolgreich zu Firebase migriert!', 'success')
        else:
            flash('Fehler bei der Migration der Chat-Daten.', 'danger')
    else:
        flash('Zugriff verweigert. Nur Administratoren können diese Funktion nutzen.', 'danger')
    
    return redirect(url_for('chat.chat_collection'))