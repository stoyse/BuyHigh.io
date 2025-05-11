#!/usr/bin/env python3
"""
Management script for BuyHigh.io application.
"""
import argparse
import logging
import os
from dotenv import load_dotenv
import sys
from rich import print

# Configure logging (wird jetzt global in app.py konfiguriert, aber hier für Standalone-Nutzung)
# Wenn dieses Skript unabhängig von der Flask-App ausgeführt wird, benötigt es seine eigene Basiskonfiguration.
# Wenn es als Teil der App importiert wird, wird die App-Konfiguration verwendet.
# Für den Fall, dass es standalone läuft:
if not logging.getLogger().hasHandlers(): # Nur konfigurieren, wenn noch keine Handler da sind
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)] # Loggt auf stdout
    )
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Umgebungsvariablen aus .env geladen (falls vorhanden).")

# Import firebase_db_handler for specific commands
try:
    import database.handler.sqlite.firebase_db_handler as firebase_db_handler
    logger.debug("firebase_db_handler Modul erfolgreich importiert.")
except ImportError:
    firebase_db_handler = None
    logger.warning("firebase_db_handler Modul nicht gefunden. Einige Befehle sind möglicherweise nicht verfügbar.")

def migrate_to_firebase():
    """Migrate chat data from SQLite to Firebase."""
    print("[yellow]Starte Migration der Chat-Daten von SQLite zu Firebase...[/yellow]")
    logger.info("Starte Migration der Chat-Daten von SQLite zu Firebase...")
    
    if not firebase_db_handler:
        print("[red]firebase_db_handler Modul ist nicht verfügbar. Migration kann nicht fortgesetzt werden.[/red]")
        logger.error("firebase_db_handler Modul ist nicht verfügbar. Migration kann nicht fortgesetzt werden.")
        return

    try:
        logger.debug("Rufe firebase_db_handler.migrate_chat_data_from_sqlite_to_firebase() auf.")
        result = firebase_db_handler.migrate_chat_data_from_sqlite_to_firebase()
        
        if result:
            print("[green]Migration erfolgreich abgeschlossen![/green]")
            logger.info("Migration erfolgreich abgeschlossen!")
        else:
            print("[red]Migration fehlgeschlagen. Überprüfen Sie die Logs für Details.[/red]")
            logger.error("Migration fehlgeschlagen. Überprüfen Sie die Logs für Details.")
    except AttributeError:
        print("[red]Funktion 'migrate_chat_data_from_sqlite_to_firebase' nicht in firebase_db_handler gefunden.[/red]")
        logger.error("Funktion 'migrate_chat_data_from_sqlite_to_firebase' nicht in firebase_db_handler gefunden.", exc_info=True)
    except Exception as e:
        print(f"[red]Ein unerwarteter Fehler ist während der Migration aufgetreten: {e}[/red]")
        logger.error(f"Ein unerwarteter Fehler ist während der Migration aufgetreten: {e}", exc_info=True)

def check_firebase_status():
    """Check Firebase connection and status."""
    print("[yellow]Überprüfe Firebase Verbindungsstatus...[/yellow]")
    logger.info("Überprüfe Firebase Verbindungsstatus...")
    
    try:
        if not firebase_db_handler:
            print("[red]firebase_db_handler nicht verfügbar. Firebase-Status kann nicht geprüft werden.[/red]")
            logger.error("firebase_db_handler nicht verfügbar. Firebase-Status kann nicht geprüft werden.")
            return

        logger.debug("Initialisiere Firebase DB für Statusprüfung...")
        initialized = firebase_db_handler.initialize_firebase_db()
        if not initialized:
            print("[red]Firebase-Initialisierung fehlgeschlagen. Überprüfen Sie Ihre Anmeldeinformationen und Umgebungsvariablen.[/red]")
            logger.error("Firebase-Initialisierung fehlgeschlagen. Überprüfen Sie Ihre Anmeldeinformationen und Umgebungsvariablen.")
            return
            
        logger.debug("Prüfe, ob Firebase verwendet werden kann (can_use_firebase)...")
        can_use = firebase_db_handler.can_use_firebase()
        if can_use:
            print("[green]✅ Firebase-Verbindung erfolgreich. System kann Firebase Realtime Database verwenden.[/green]")
            logger.info("✅ Firebase-Verbindung erfolgreich. System kann Firebase Realtime Database verwenden.")
        else:
            print("[yellow]⚠️ Firebase-Verbindung fehlgeschlagen oder Firebase nicht nutzbar. System wird SQLite-Fallback verwenden (falls implementiert).[/yellow]")
            print("[yellow]Bitte überprüfen Sie Ihre Firebase-Konfiguration und Netzwerkverbindung.[/yellow]")
            logger.warning("⚠️ Firebase-Verbindung fehlgeschlagen oder Firebase nicht nutzbar. System wird SQLite-Fallback verwenden (falls implementiert).")
            logger.info("Bitte überprüfen Sie Ihre Firebase-Konfiguration und Netzwerkverbindung.")
            
    except ImportError:
        print("[red]Konnte Firebase-Module nicht importieren. Stellen Sie sicher, dass firebase_db_handler.py existiert.[/red]")
        logger.error("Konnte Firebase-Module nicht importieren. Stellen Sie sicher, dass firebase_db_handler.py existiert.")
    except Exception as e:
        print(f"[red]Ein unerwarteter Fehler ist beim Überprüfen von Firebase aufgetreten: {e}[/red]")
        logger.error(f"Ein unerwarteter Fehler ist beim Überprüfen von Firebase aufgetreten: {e}", exc_info=True)

def setup_database():
    """Initialize the database schema for both SQLite and Firebase."""
    print("[yellow]Richte Datenbanken ein...[/yellow]")
    logger.info("Richte Datenbanken ein...")
    
    # Setup SQLite database
    print("[yellow]Richte SQLite-Datenbank ein...[/yellow]")
    logger.info("Richte SQLite-Datenbank ein...")
    try:
        import database.handler.postgres.postgres_db_handler as db_handler
        db_handler.init_db()
        print("[green]SQLite-Datenbank erfolgreich initialisiert.[/green]")
        logger.info("SQLite-Datenbank erfolgreich initialisiert.")
    except ImportError:
        print("[red]db_handler Modul nicht gefunden. SQLite-Datenbank kann nicht eingerichtet werden.[/red]")
        logger.error("db_handler Modul nicht gefunden. SQLite-Datenbank kann nicht eingerichtet werden.")
    except Exception as e:
        print(f"[red]Fehler beim Initialisieren der SQLite-Datenbank: {e}[/red]")
        logger.error(f"Fehler beim Initialisieren der SQLite-Datenbank: {e}", exc_info=True)
    
    # Setup Firebase database structure (if enabled)
    print("[yellow]Richte Firebase-Datenbankstruktur ein (falls aktiviert)...[/yellow]")
    logger.info("Richte Firebase-Datenbankstruktur ein (falls aktiviert)...")
    try:
        firebase_enabled_env = os.environ.get('USE_FIREBASE', 'true').lower() == 'true'
        if firebase_enabled_env:
            if not firebase_db_handler:
                print("[red]firebase_db_handler nicht verfügbar. Firebase-Setup übersprungen.[/red]")
                logger.warning("firebase_db_handler nicht verfügbar. Firebase-Setup übersprungen.")
                return

            logger.debug("Initialisiere Firebase DB für Setup...")
            if firebase_db_handler.initialize_firebase_db():
                print("[green]Firebase-Datenbankverbindung erfolgreich initialisiert.[/green]")
                logger.info("Firebase-Datenbankverbindung erfolgreich initialisiert.")
                print("[yellow]Richte initiale Firebase Chat-Struktur ein (z.B. 'General' Chat)...[/yellow]")
                logger.info("Richte initiale Firebase Chat-Struktur ein (z.B. 'General' Chat)...")
                default_chat_id = firebase_db_handler.setup_initial_firebase_chat_structure()
                if default_chat_id:
                    print(f"[green]Initiale Firebase Chat-Struktur erfolgreich eingerichtet. 'General' Chat ID: {default_chat_id}[/green]")
                    logger.info(f"Initiale Firebase Chat-Struktur erfolgreich eingerichtet. 'General' Chat ID: {default_chat_id}")
                else:
                    print("[red]Fehler beim Einrichten der initialen Firebase Chat-Struktur.[/red]")
                    logger.error("Fehler beim Einrichten der initialen Firebase Chat-Struktur.")
            else:
                print("[red]Firebase-Datenbankinitialisierung fehlgeschlagen. Firebase-Setup übersprungen.[/red]")
                logger.warning("Firebase-Datenbankinitialisierung fehlgeschlagen. Firebase-Setup übersprungen.")
        else:
            print("[yellow]Firebase ist in .env deaktiviert. Firebase-Setup übersprungen.[/yellow]")
            logger.info("Firebase ist in .env deaktiviert. Firebase-Setup übersprungen.")
    except ImportError:
        print("[red]Firebase-Module nicht verfügbar. Firebase-Setup übersprungen.[/red]")
        logger.warning("Firebase-Module nicht verfügbar. Firebase-Setup übersprungen.")
    except Exception as e:
        print(f"[red]Fehler beim Einrichten der Firebase-Datenbank: {e}[/red]")
        logger.error(f"Fehler beim Einrichten der Firebase-Datenbank: {e}", exc_info=True)

def _reset_firebase_chat_data_interactive():
    """Handles the interactive Firebase chat data reset."""
    print("[yellow]Starte interaktiven Reset der Firebase Chat-Daten.[/yellow]")
    logger.info("Starte interaktiven Reset der Firebase Chat-Daten.")
    if not firebase_db_handler:
        print("[red]firebase_db_handler Modul ist nicht verfügbar. Reset kann nicht fortgesetzt werden.[/red]")
        logger.error("firebase_db_handler Modul ist nicht verfügbar. Reset kann nicht fortgesetzt werden.")
        return

    print("[red]DIES LÖSCHT ALLE Chaträume, Teilnehmer und Nachrichten aus Firebase.[/red]")
    logger.warning("DIES LÖSCHT ALLE Chaträume, Teilnehmer und Nachrichten aus Firebase.")
    confirm = input("Sind Sie sicher, dass Sie fortfahren möchten? (ja/nein): ")
    if confirm.lower() != 'ja':
        print("[yellow]Firebase Chat-Daten Reset vom Benutzer abgebrochen.[/yellow]")
        logger.info("Firebase Chat-Daten Reset vom Benutzer abgebrochen.")
        return

    print("[yellow]Fahre mit dem Löschen der Firebase Chat-Daten fort...[/yellow]")
    logger.info("Fahre mit dem Löschen der Firebase Chat-Daten fort...")
    deleted = firebase_db_handler.delete_all_firebase_chat_data()
    if not deleted:
        print("[red]Fehler beim Löschen aller Firebase Chat-Daten. Breche weiteres Setup ab.[/red]")
        logger.error("Fehler beim Löschen aller Firebase Chat-Daten. Breche weiteres Setup ab.")
        return
    
    print("[green]Firebase Chat-Daten erfolgreich gelöscht.[/green]")
    logger.info("Firebase Chat-Daten erfolgreich gelöscht.")
    print("[yellow]Richte initiale Firebase Chat-Struktur ein ('General' Chat)...[/yellow]")
    logger.info("Richte initiale Firebase Chat-Struktur ein ('General' Chat)...")
    general_chat_id = firebase_db_handler.setup_initial_firebase_chat_structure()
    if general_chat_id:
        print(f"[green]Initiale Firebase Chat-Struktur erfolgreich eingerichtet. 'General' Chat ID: {general_chat_id}[/green]")
        logger.info(f"Initiale Firebase Chat-Struktur erfolgreich eingerichtet. 'General' Chat ID: {general_chat_id}")
    else:
        print("[red]Fehler beim Einrichten der initialen Firebase Chat-Struktur nach dem Reset.[/red]")
        logger.error("Fehler beim Einrichten der initialen Firebase Chat-Struktur nach dem Reset.")
    
    print("[yellow]Firebase Chat-Daten Reset und Setup-Prozess beendet.[/yellow]")
    logger.info("Firebase Chat-Daten Reset und Setup-Prozess beendet.")
    print("[yellow]Sie möchten möglicherweise die Migration ausführen, wenn Sie Daten aus SQLite wiederherstellen möchten: ./manage.py migrate[/yellow]")
    logger.info("Sie möchten möglicherweise die Migration ausführen, wenn Sie Daten aus SQLite wiederherstellen möchten: ./manage.py migrate")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="BuyHigh.io Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Auszuführender Befehl", required=True)
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Migriere Chat-Daten von SQLite zu Firebase")
    
    # Check status command
    status_parser = subparsers.add_parser("status", help="Überprüfe Firebase Verbindungsstatus")
    
    # Setup database command
    setup_parser = subparsers.add_parser("setup", help="Initialisiere Datenbankschema (SQLite und grundlegende Firebase-Struktur)")

    # Reset Firebase chat data command
    reset_chat_parser = subparsers.add_parser("reset-firebase-chat", help="Lösche alle Chat-Daten aus Firebase und richte einen Standard-'General'-Chat ein.")
    
    args = parser.parse_args()
    print(f"[yellow]Management-Befehl '{args.command}' wird ausgeführt.[/yellow]")
    logger.info(f"Management-Befehl '{args.command}' wird ausgeführt.")
    
    if args.command == "migrate":
        migrate_to_firebase()
    elif args.command == "status":
        check_firebase_status()
    elif args.command == "setup":
        setup_database()
    elif args.command == "reset-firebase-chat":
        _reset_firebase_chat_data_interactive()
    else:
        parser.print_help()
    print(f"[yellow]Management-Befehl '{args.command}' beendet.[/yellow]")
    logger.info(f"Management-Befehl '{args.command}' beendet.")

if __name__ == "__main__":
    print("[yellow]manage.py Skript gestartet.[/yellow]")
    logger.info("manage.py Skript gestartet.")
    main()
    print("[yellow]manage.py Skript beendet.[/yellow]")
    logger.info("manage.py Skript beendet.")
