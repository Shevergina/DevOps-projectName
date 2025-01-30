import sqlite3


# Пример создания базы данных и таблицы
def create_database():
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS books (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT,
                      author TEXT,
                      genre TEXT,
                      rating TEXT)''')

    # Пример данных, добавьте свои
    cursor.execute("INSERT INTO books (title, author, genre, rating) VALUES ('Джунгли', 'Рудьярд Киплинг', 'Приключения' , '4,7')")
    cursor.execute(
        "INSERT INTO books (title, author, genre, rating) VALUES ('451 градус по Фаренгейту', 'Рэй Брэдбери', 'Фантастика', '4,6')")
    cursor.execute(
        "INSERT INTO books (title, author, genre, rating) VALUES ('Убийство в Восточном экспрессе', 'Агата Кристи', 'Детектив', '4,8')")
    cursor.execute(
        "INSERT INTO books (title, author, genre, rating) VALUES ('Десять негритят', 'Агата Кристи', 'Детектив', '4,8')")

    conn.commit()
    conn.close()


create_database()