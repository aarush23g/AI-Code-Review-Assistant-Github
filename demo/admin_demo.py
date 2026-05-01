def delete_user(user_id):
    database.delete("users", user_id)
    return {"status": "deleted"}