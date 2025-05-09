import functools
from flask import g, flash, redirect, url_for, request

def login_required(view):
    """
    Decorator that redirects to the login page if the user is not logged in.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view
