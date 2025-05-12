import psycopg2
import psycopg2.extras
import logging
import os

logger = logging.getLogger(__name__)

def get_db_connection():
    """Stellt eine Verbindung zur PostgreSQL-Datenbank her."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            dbname=os.getenv('POSTGRES_DB')
        )
        return conn
    except Exception as e:
        logger.error(f"Fehler beim Öffnen der PostgreSQL-Verbindung: {e}", exc_info=True)
        raise

def get_user_badges(user_id):
    """
    Ruft alle Abzeichen ab, die ein bestimmter Benutzer erhalten hat.
    
    Args:
        user_id (int): Die ID des Benutzers
        
    Returns:
        dict: Erfolgsstatus und nach Kategorie gruppierte Abzeichen
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Alle vom Benutzer erworbenen Abzeichen abrufen
                query = """
                    SELECT b.id, b.name, b.description, b.category, b.icon_name, b.color, b.level, 
                           ub.earned_at
                    FROM badges b
                    JOIN user_badges ub ON b.id = ub.badge_id
                    WHERE ub.user_id = %s
                    ORDER BY b.category, b.level DESC
                """
                cur.execute(query, (user_id,))
                user_badges = cur.fetchall()
                
                # Alle verfügbaren Abzeichen abrufen
                cur.execute("SELECT id, name, description, category, icon_name, color, level FROM badges ORDER BY category, level DESC")
                all_badges = cur.fetchall()
                
                # Abzeichen nach Kategorien gruppieren
                badges_by_category = {}
                
                # Zuerst alle verfügbaren Abzeichen nach Kategorie organisieren
                for badge in all_badges:
                    category = badge['category']
                    if category not in badges_by_category:
                        badges_by_category[category] = {
                            'earned': [],
                            'available': []
                        }
                    
                    # Prüfen, ob dieses Abzeichen vom Benutzer erworben wurde
                    is_earned = False
                    for user_badge in user_badges:
                        if user_badge['id'] == badge['id']:
                            # Erworbenes Abzeichen mit earned_at-Zeitstempel hinzufügen
                            badge_copy = dict(badge)
                            badge_copy['earned_at'] = user_badge['earned_at']
                            badges_by_category[category]['earned'].append(badge_copy)
                            is_earned = True
                            break
                    
                    # Wenn nicht erworben, zu verfügbaren Abzeichen hinzufügen
                    if not is_earned:
                        badges_by_category[category]['available'].append(badge)
                
                return {
                    "success": True,
                    "badges_by_category": badges_by_category,
                    "total_earned": len(user_badges),
                    "total_available": len(all_badges)
                }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Abzeichen für Benutzer {user_id}: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Datenbankfehler: {e}",
            "badges_by_category": {}
        }

def award_badge_to_user(user_id, badge_id):
    """
    Verleiht einem Benutzer ein Abzeichen.
    
    Args:
        user_id (int): Die ID des Benutzers
        badge_id (int): Die ID des zu verleihenden Abzeichens
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Prüfen, ob der Benutzer dieses Abzeichen bereits besitzt
                cur.execute("SELECT 1 FROM user_badges WHERE user_id = %s AND badge_id = %s", 
                           (user_id, badge_id))
                if cur.fetchone():
                    logger.info(f"Benutzer {user_id} hat Abzeichen {badge_id} bereits")
                    return True  # Bereits verliehen
                
                # Abzeichen verleihen
                cur.execute("INSERT INTO user_badges (user_id, badge_id) VALUES (%s, %s)",
                           (user_id, badge_id))
                conn.commit()
                
                logger.info(f"Abzeichen {badge_id} an Benutzer {user_id} verliehen")
                return True
    except Exception as e:
        logger.error(f"Fehler beim Verleihen von Abzeichen {badge_id} an Benutzer {user_id}: {e}", exc_info=True)
        return False

def revoke_badge_from_user(user_id, badge_id):
    """
    Entzieht einem Benutzer ein Abzeichen.
    
    Args:
        user_id (int): Die ID des Benutzers
        badge_id (int): Die ID des zu entziehenden Abzeichens
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_badges WHERE user_id = %s AND badge_id = %s",
                           (user_id, badge_id))
                conn.commit()
                
                # Prüfen, ob Zeilen betroffen waren
                if cur.rowcount > 0:
                    logger.info(f"Abzeichen {badge_id} von Benutzer {user_id} entzogen")
                    return True
                else:
                    logger.info(f"Benutzer {user_id} hatte Abzeichen {badge_id} nicht zum Entziehen")
                    return False
    except Exception as e:
        logger.error(f"Fehler beim Entziehen von Abzeichen {badge_id} von Benutzer {user_id}: {e}", exc_info=True)
        return False

def get_badge_by_id(badge_id):
    """
    Ruft ein Abzeichen anhand seiner ID ab.
    
    Args:
        badge_id (int): Die ID des Abzeichens
        
    Returns:
        dict: Abzeichendetails oder None, wenn nicht gefunden
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM badges WHERE id = %s", (badge_id,))
                return cur.fetchone()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Abzeichens {badge_id}: {e}", exc_info=True)
        return None
