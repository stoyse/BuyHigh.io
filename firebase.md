# Firebase Integration in BuyHigh.io

BuyHigh.io verwendet Firebase Realtime Database für Chat-Funktionen mit automatischem Fallback auf SQLite. Diese Dokumentation erklärt die Firebase-Integration und alle zugehörigen Funktionen.

## Übersicht

Die Firebase-Integration bietet:

- Echtzeitkommunikation für Chat-Funktionen
- Automatisches Failover auf SQLite wenn Firebase nicht verfügbar ist
- Synchronisation zwischen verschiedenen Clients
- Administrative Tools zur Verwaltung der Daten

## Konfiguration

Die Firebase-Integration wird über Umgebungsvariablen gesteuert:

- `FIREBASE_DATABASE_URL` - Firebase Realtime Database URL
- `GOOGLE_APPLICATION_CREDENTIALS` - Pfad zur Firebase-Anmeldedaten-JSON-Datei
- `USE_FIREBASE` - "true"/"false" zur Aktivierung/Deaktivierung von Firebase

Diese sollten in einer `.env`-Datei im Hauptverzeichnis oder als Umgebungsvariablen gesetzt sein.

## Datenstruktur

Die Firebase Realtime Database nutzt folgende Struktur:

```
/chats/                         # Chat-Räume
  /{chat_id}/                   # Individuelle Chat-IDs
    name: "Chat-Name"           # Name des Chats
    created_at: 1620000000000   # Zeitstempel (ms)
    created_by: "user_id"       # Ersteller (oder null für System-Chats)
    members_can_invite: false   # Berechtigungen

/chat_participants/             # Chat-Teilnehmer
  /{chat_id}/                   # Pro Chat
    /{user_id}/                 # Pro Benutzer im Chat
      chat_name: "Username"     # Anzeigename im Chat
      joined_at: 1620000000000  # Beitrittszeitpunkt (ms)

/messages/                      # Nachrichten
  /{chat_id}/                   # Pro Chat
    /{message_id}/              # Eindeutige Nachrichten-ID (Push-Key)
      user_id: "user_id"        # Absender
      message_text: "Nachricht" # Inhalt
      sent_at: 1620000000000    # Sendezeit (ms)
```

## Funktionen in `firebase_db_handler.py`

### Verbindungsfunktionen

| Funktion | Beschreibung |
|----------|--------------|
| `initialize_firebase_db()` | Initialisiert Firebase und gibt die DB-Referenz zurück. |
| `can_use_firebase()` | Überprüft, ob Firebase verwendet werden kann oder auf SQLite zurückgegriffen werden soll. |
| `handle_firebase_operation(operation_func, *args, **kwargs)` | Führt eine Firebase-Operation mit Wiederholungsversuchen aus. |

### Chat-Raum Operationen

| Funktion | Beschreibung |
|----------|--------------|
| `get_user_chats(user_id)` | Gibt alle Chat-Räume zurück, an denen ein Benutzer teilnimmt. |
| `get_chat_by_id(chat_id)` | Lädt Chat-Details anhand seiner ID. |
| `create_chat(chat_name, user_id)` | Erstellt einen neuen Chat und fügt den Ersteller als Teilnehmer hinzu. |
| `delete_chat(chat_id)` | Löscht einen Chat-Raum mit allen Nachrichten und Teilnehmern. |

### Chat-Teilnehmer Operationen

| Funktion | Beschreibung |
|----------|--------------|
| `is_chat_participant(chat_id, user_id)` | Prüft, ob ein Benutzer an einem Chat teilnimmt. |
| `join_chat(chat_id, user_id)` | Fügt einen Benutzer zu einem Chat hinzu. |

### Nachrichten-Operationen

| Funktion | Beschreibung |
|----------|--------------|
| `get_chat_messages(chat_id, limit=50, offset=0)` | Lädt Nachrichten eines Chats mit Paginierung. |
| `add_message_and_get_details(chat_id, user_id, message_text)` | Fügt eine neue Nachricht hinzu und gibt Details zurück. |

### Default-Chat Operationen

| Funktion | Beschreibung |
|----------|--------------|
| `get_default_chat_id()` | Findet die ID des Standard "General"-Chats. |
| `ensure_user_in_default_chat(user_id)` | Stellt sicher, dass ein Benutzer im Standard-Chat ist. |
| `setup_initial_firebase_chat_structure()` | Richtet den initialen "General"-Chat ein, wenn er noch nicht existiert. |

### Migrations- und Verwaltungsfunktionen

| Funktion | Beschreibung |
|----------|--------------|
| `migrate_chat_data_from_sqlite_to_firebase()` | Migriert alle Chat-Daten von SQLite nach Firebase. |
| `delete_all_firebase_chat_data()` | Löscht alle Chat-Daten aus Firebase (chats, messages, participants). |

### Hilfsfunktionen

| Funktion | Beschreibung |
|----------|--------------|
| `process_chat_details(chat_id, chat_data, messages)` | Verarbeitet Chat-Daten ins richtige Format. |

## Detaillierte Funktionsbeschreibungen

### `get_default_chat_id()`

Diese Funktion findet den Standard-"General"-Chat mit folgenden Strategien:

1. Überprüft zunächst direkt die bekannte Standard-Chat-ID (`-OPvLBJqVopKLHfHGPFF`)
2. Sucht nach einem Chat mit dem exakten Namen "General"
3. Sucht nach einem Chat mit dem Namen "general" (case-insensitive)
4. Nimmt den einzigen vorhandenen Chat, falls nur einer existiert

```python
def get_default_chat_id():
    # ...Check Firebase usability...
    try:
        # Zuerst bekannte Chat-ID prüfen
        known_general_chat_id = "-OPvLBJqVopKLHfHGPFF"
        known_chat_data = db_ref.child(f"chats/{known_general_chat_id}").get()
        if known_chat_data:
            return known_general_chat_id
            
        # Dann nach Namen "General" suchen
        chats_data = db_ref.child("chats").get() or {}
        for chat_id, chat_info in chats_data.items():
            if isinstance(chat_info, dict) and chat_info.get("name") == "General":
                return chat_id

        # Weitere Fallback-Strategien...
```

### `ensure_user_in_default_chat(user_id)`

Stellt sicher, dass ein Benutzer im Standard-Chat ist:

1. Ruft `get_default_chat_id()` auf, um den "General"-Chat zu finden
2. Falls kein "General"-Chat gefunden wird, gibt es eine Fehlermeldung zurück
3. Überprüft, ob der Benutzer bereits Teilnehmer ist
4. Fügt den Benutzer hinzu, falls erforderlich

### `setup_initial_firebase_chat_structure()`

Erzeugt den Standard-"General"-Chat, falls er noch nicht existiert:

```python
def setup_initial_firebase_chat_structure():
    # ...Check Firebase usability...
    try:
        # Existiert "General" bereits?
        general_chat_id = get_default_chat_id()
        if general_chat_id:
            return general_chat_id
        
        # Neuen "General"-Chat erstellen
        new_chat_ref = db_ref.child("chats").push()
        default_chat_id = new_chat_ref.key
        new_chat_ref.set({
            "name": "General",
            "created_at": int(time.time() * 1000),
            "created_by": None,  # System-Chat
            "members_can_invite": False
        })
        return default_chat_id
    # ...Error handling...
```

## Management-Befehle (`manage.py`)

### `python manage.py status`

Überprüft den Firebase-Verbindungsstatus und gibt Informationen zur Verwendung aus.

**Funktionsweise:**
```python
def check_firebase_status():
    # Initialize Firebase and check connection
    initialized = initialize_firebase_db()
    can_use = can_use_firebase()
    
    if can_use:
        logger.info("✅ Firebase connection successful.")
    else:
        logger.warning("⚠️ Firebase connection failed.")
```

### `python manage.py migrate`

Migriert Chat-Daten von SQLite nach Firebase.

**Funktionsweise:**
```python
def migrate_to_firebase():
    # Calls firebase_db_handler.migrate_chat_data_from_sqlite_to_firebase()
    result = firebase_db_handler.migrate_chat_data_from_sqlite_to_firebase()
```

**Migration-Prozess:**
1. Kopiert alle chat_rooms aus SQLite nach Firebase
2. Kopiert alle chat_room_participants 
3. Kopiert alle messages mit korrekter Zeitkonvertierung

### `python manage.py reset-firebase-chat`

Löscht alle Chat-Daten aus Firebase und erstellt den Standard-"General"-Chat neu.

**Funktionsweise:**
```python
def _reset_firebase_chat_data_interactive():
    # Ask for confirmation
    # Delete all Firebase chat data
    deleted = firebase_db_handler.delete_all_firebase_chat_data()
    
    # Set up initial structure (General chat)
    general_chat_id = firebase_db_handler.setup_initial_firebase_chat_structure()
```

### `python manage.py setup`

Initialisiert die Datenbankschemas für SQLite und Firebase.

**Funktionsweise:**
```python
def setup_database():
    # Set up SQLite database
    import db_handler
    db_handler.init_db()
    
    # Set up Firebase if enabled
    if firebase_enabled:
        initialize_firebase_db()
```

## Fehlerbehandlung und Fallback-Mechanismen

Jede Firebase-Operation in `firebase_db_handler.py` enthält eine Fehlerbehandlung und einen Fallback-Mechanismus:

1. Die Funktion prüft zuerst mit `can_use_firebase()`, ob Firebase verwendet werden kann
2. Falls nicht, erfolgt ein automatischer Fallback auf die entsprechende Funktion in `chat_db_handler.py`
3. Bei Fehlern während der Firebase-Operation erfolgt ein Fallback auf SQLite

```python
def example_operation(param):
    # Check if Firebase is usable
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.example_operation(param)
    
    try:
        # Firebase operation
        # ...
    except Exception as e:
        logger.error(f"Error in Firebase operation: {e}")
        import chat_db_handler
        return chat_db_handler.example_operation(param)
```

## Beispiele

### Benutzer zum General-Chat hinzufügen

```python
from firebase_db_handler import ensure_user_in_default_chat

# Füge Benutzer zum General-Chat hinzu (oder stelle sicher, dass er bereits teilnimmt)
success = ensure_user_in_default_chat(user_id)
```

### Chat-Nachrichten laden

```python
from firebase_db_handler import get_chat_messages

# Lade die letzten 50 Nachrichten
messages = get_chat_messages(chat_id, limit=50)
```

### Neue Nachricht senden

```python
from firebase_db_handler import add_message_and_get_details

# Nachricht hinzufügen und Details für Echtzeit-Updates zurückgeben
message_details = add_message_and_get_details(chat_id, user_id, "Hello world!")
```

## Fehlerbehandlung und Logging

Der Firebase-Code enthält umfangreiches Logging für Debugging- und Wartungszwecke:

- `DEBUG`-Level: Detaillierte Diagnose-Informationen
- `INFO`-Level: Erfolgreiche Operationen und wichtige Statusänderungen
- `WARNING`-Level: Probleme, die einen Fallback auslösen oder besondere Aufmerksamkeit benötigen
- `ERROR`-Level: Fehler, die Operationen verhindern

Die Logs können genutzt werden, um den Zustand der Firebase-Integration zu überwachen und Probleme zu diagnostizieren.
