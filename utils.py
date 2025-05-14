import functools
from flask import g, flash, redirect, url_for, request, session
from rich import print
from database.handler.postgres.postgres_db_handler import get_db_connection

# Decorator for routes that require login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            # load_logged_in_user (in app.py @before_request) is responsible for populating g.user
            # If g.user is None here, it means the user is not logged in or session is invalid.
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return view(**kwargs)
    return wrapped_view

# Decorator for routes that require developer access
def dev_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("You need to be logged in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.path))

        is_developer = False

        # 1. Prüfe direkt im g.user-Objekt auf das Feld 'is_dev'
        if isinstance(g.user, dict) and g.user.get('is_dev'):
            is_developer = True
        elif hasattr(g.user, 'is_dev') and getattr(g.user, 'is_dev'):
            is_developer = True

        # 2. Falls nicht, prüfe in der developers-Tabelle (DB)
        if not is_developer:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        # Wichtig: user_id als INT vergleichen, nicht als STRING!
                        cur.execute("SELECT 1 FROM developers WHERE user_id = %s", (int(g.user['id']),))
                        row = cur.fetchone()
                        print(f'[dark orange3]SQL: SELECT 1 FROM developers WHERE user_id = {g.user["id"]} -> {row}[/]')
                        is_developer = row is not None
            except Exception as e:
                print(f'[red]Fehler bei dev_required DB-Check: {e}[/]')

        if not is_developer:
            flash("You don't have developer access to this page.", "error")
            return redirect(url_for('main.index'))

        return view(**kwargs)
    return wrapped_view
