import functools
from flask import g, flash, redirect, url_for, request, session

# Decorator for routes that require login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            # load_logged_in_user (in app.py @before_request) is responsible for populating g.user
            # If g.user is None here, it means the user is not logged in or session is invalid.
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view
