# vulnerable_code.py

password = "admin123"

user_id = input()

query = (
    f"SELECT * FROM users "
    f"WHERE id={user_id}"
)

print(query)