import functools
from flask import g, flash, redirect, url_for, request, session

# Decorator for routes that require login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            user_id = session.get('user_id')
            if user_id is None: # Double check if g.user was not loaded by before_request
                flash("You need to be logged in to view this page.", "warning")
                return redirect(url_for('auth.login', next=request.url)) # Assuming auth_bp is named 'auth'
            # If user_id is in session but g.user is None, it implies an issue or specific state.
            # For robustness, one might reload g.user here if necessary,
            # but typically app.before_request should handle g.user loading.
            # The primary check remains g.user.
            # If g.user is still None after before_request and session check, then redirect.
            # This part of the logic might need refinement based on how g.user is managed if session exists but g.user is not set.
            # However, the original logic in app.py's login_required only checked g.user.
            # The provided route files already use this decorator assuming it handles redirection.
            # The key is that g.user must be populated by @app.before_request.
            # If g.user is None, it means no user is logged in.
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('auth.login', next=request.url)) # Ensure 'auth.login' is the correct endpoint
        return view(**kwargs)
    return wrapped_view
