import bcrypt

def hash_password(password):
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(hashed_password, password):
    """Checks a password against its hashed version."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
