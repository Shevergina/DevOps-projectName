from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3
import pandas as pd

# Глобальные переменные для хранения состояния
user_data = {}
ADMIN_PASSWORD = "admin1212"  # Пароль администратора
authorized_users = set()  # Набор авторизованных пользователей

# Получаем книги по жанру и автору
def get_books(genre=None, author=None):
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    query = "SELECT title, author, genre, rating FROM books"
    params = ()
    if genre and author:
        query += " WHERE genre=? AND author=?"
        params = (genre, author)
    cursor.execute(query, params)
    books = cursor.fetchall()
    conn.close()
    return books

# Добавляем новую книгу в БД
def add_book_to_db(title, author, genre, rating):
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author, genre, rating) VALUES (?, ?, ?, ?)", (title, author, genre, rating))
    conn.commit()
    conn.close()

# Удаляем книгу из БД
def delete_book_by_title(title):
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE title=?", (title,))
    conn.commit()
    conn.close()

def get_unique_genres():
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT genre FROM books")
    genres = cursor.fetchall()
    conn.close()
    return [genre[0] for genre in genres]

# Получение авторов по выбранному жанру
def get_authors_by_genre(genre):
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT author FROM books WHERE genre=?", (genre,))
    authors = cursor.fetchall()
    conn.close()
    return [author[0] for author in authors]

# Начинаем беседу и задаем первый вопрос
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat.id] = {}
    genres = get_unique_genres()
    await update.message.reply_text("Какого жанра книга вам нужна?", reply_markup=genre_keyboard(genres))

# Клавиатура жанров
def genre_keyboard(genres, columns=3):
    keyboard = []
    for i in range(0, len(genres), columns):
        keyboard.append([InlineKeyboardButton(genre, callback_data=f"genre_{genre}") for genre in genres[i:i+columns]])
    return InlineKeyboardMarkup(keyboard)

# Обработка выбора жанра
async def genre_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    genre = query.data.split('_')[1]  # Извлекаем жанр из callback_data
    user_data[query.message.chat.id]['genre'] = genre  # Сохраняем выбранный жанр
    authors = get_authors_by_genre(genre)
    await query.edit_message_text(text=f"Вы выбрали жанр '{genre}'. Теперь какого автора вы предпочитаете?\n\nЕсли вы хотите выбрать другой жанр, нажмите /start ", reply_markup=author_keyboard(authors))

# Клавиатура авторов
def author_keyboard(authors, columns=2):
    keyboard = []
    for i in range(0, len(authors), columns):
        keyboard.append([InlineKeyboardButton(author, callback_data=f"author_{author}") for author in authors[i:i+columns]])
    return InlineKeyboardMarkup(keyboard)

# Обработка выбора автора
# Обработка выбора автора
async def author_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    author = query.data.split('_')[1]  # Извлекаем автора из callback_data
    chat_id = query.message.chat.id

    if 'genre' in user_data[chat_id]:
        genre = user_data[chat_id]['genre']  # Получаем сохраненный жанр
    else:
        await query.message.reply_text("Произошла ошибка, пожалуйста, начните заново /start.")
        return

    user_data[chat_id]['author'] = author  # Сохраняем выбранного автора

    books = get_books(genre, author)

    if books:
        books_message = f"Вы выбрали жанр '{genre}' и автора '{author}'.\n\nВот книги по вашему запросу:\n"
        books_message += "\n".join([f"{title} (Рейтинг: {rating}🌟)" for title, author, genre, rating in books])
        books_message += f"\n\nЧтобы начать поиск книг заново нажмите /start"
        await query.message.reply_text(books_message)
    else:
        await query.message.reply_text("Книг по вашему запросу не найдено.")

# Ввод пароля администратора
async def admin_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'enter_password'
    await update.message.reply_text("Введите пароль администратора:")

# Обработка текста для ввода пароля администратора
async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    password = update.message.text
    if context.user_data.get('state') == 'enter_password':
        if password == ADMIN_PASSWORD:
            authorized_users.add(chat_id)
            await update.message.reply_text("Вы успешно авторизованы как администратор.")
        else:
            await update.message.reply_text("Неверный пароль. Попробуйте снова.")
        context.user_data['state'] = None
async def addbook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id in authorized_users:
        context.user_data['state'] = 'adding_book'
        await update.message.reply_text("Введите название книги:")
    else:
        await update.message.reply_text("Эта команда доступна только администраторам. Введите /admin для авторизации.")

# Обработка текста для добавления книги
async def handle_addbook_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id

    if context.user_data.get('state') == 'adding_book':
        if 'book_title' not in context.user_data:
            context.user_data['book_title'] = update.message.text
            await update.message.reply_text("Введите автора книги:")
            return

        if 'book_author' not in context.user_data:
            context.user_data['book_author'] = update.message.text
            await update.message.reply_text("Введите жанр книги:")
            return

        if 'book_genre' not in context.user_data:
            context.user_data['book_genre'] = update.message.text
            await update.message.reply_text("Введите рейтинг книги (число через точку):")
            return

        if 'book_genre' in context.user_data:
            try:
                rating = float(update.message.text)
                title = context.user_data['book_title']
                author = context.user_data['book_author']
                genre = context.user_data['book_genre']

                # Добавляем книгу в базу данных
                add_book_to_db(title, author, genre, rating)
                await update.message.reply_text("Книга добавлена в базу данных!")
            except ValueError:
                await update.message.reply_text("Пожалуйста, введите корректный рейтинг (число через точку).")

            # Сбросим данные после добавления
            context.user_data.clear()

# Обработка команды для удаления книги
async def deletebook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id in authorized_users:
        context.user_data['state'] = 'deleting_book'
        await update.message.reply_text("Введите название книги, которую хотите удалить:")
        print("Состояние 'deleting_book' установлено")
    else:
        await update.message.reply_text("Эта команда доступна только администраторам. Введите /admin для авторизации.")
# Обработка текста для удаления книги
async def handle_deletebook_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'deleting_book':
        book_title = update.message.text
        print(f"Получено название книги для удаления: {book_title}")
        delete_book_by_title(book_title)
        await update.message.reply_text(f"Книга '{book_title}' была удалена из базы данных.")
        context.user_data.clear()
    else:
        await update.message.reply_text("Произошла ошибка, попробуйте снова.")
        print("Неверное состояние для удаления книги")

# Обработка команды выхода из администратора
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    if chat_id in authorized_users:
        authorized_users.remove(chat_id)
        await update.message.reply_text("Вы успешно вышли из режима администратора.")
    else:
        await update.message.reply_text("Вы не являетесь администратором.")

#Обработка команды помощи
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = ( "Я твой персональный помощник в мире книг!📕\n\nВот команды, которые я могу выполнить:\n"
                     "/start - Начать беседу и выбрать жанр и автора книги.\n" 
                     "/addbook - Добавить новую книгу в базу данных (доступно только администратору).\n"
                     "/deletebook - Удалить книгу из базы данных по названию (доступно только администратору).\n"
                     "/admin - Войти как администратор.\n"
                     "/logout - Выйти из режима администратора.\n"
                     "/help - Показать список доступных команд.\n"
                     "/books - Получить список всех книг в базе данных в формате Excel.\n"
                )
    await update.message.reply_text(help_message)

# Обработка команды для получения книг в формате Excel
async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
 # Получаем все книги из базы данных
    books = get_books()
 # Создаем DataFrame из данных книг
    df = pd.DataFrame(books, columns=["Название книги", "Автор", "Жанр", "Рейтинг"])
 # Сохраняем DataFrame в Excel файл
    file_path = "books.xlsx"
    df.to_excel(file_path, index=False)
 # Отправляем файл пользователю
    await update.message.reply_document(document=open(file_path, "rb"))
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    if context.user_data.get('state') == 'enter_password':
        await handle_password(update, context)
    elif context.user_data.get('state') == 'adding_book':
        await handle_addbook_text(update, context)
    elif context.user_data.get('state') == 'deleting_book':
        await handle_deletebook_text(update, context)
    else:
        await update.message.reply_text("Произошла ошибка, попробуйте снова.")

# Главная функция
def main():
    application = ApplicationBuilder().token("7903228169:AAEMsCkoTIJhL2HIw3flZGrFGepsbTEytOs").build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addbook", addbook))
    application.add_handler(CommandHandler("deletebook", deletebook))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_auth))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(CommandHandler("books", books_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(genre_selection, pattern='^genre_'))
    application.add_handler(CallbackQueryHandler(author_selection, pattern='^author_'))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
