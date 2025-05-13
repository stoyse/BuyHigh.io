import database.handler.postgres.postgres_db_handler as db_handler



print(db_handler.get_user_xp("1"))

print(db_handler.get_user_level("1"))

def check_user_level(user_id, user_xp):