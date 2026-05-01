def read_user_file(filename):
    with open("uploads/" + filename, "r", encoding="utf-8") as file:
        return file.read()