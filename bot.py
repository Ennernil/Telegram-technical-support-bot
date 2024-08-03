import sqlite3
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import *
from logic import *

bot = telebot.TeleBot(API_TOKEN)
	


@bot.message_handler(commands=['start'])
def welcome(message):
    chat_id = message.chat.id
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = telebot.types.KeyboardButton(text="/start")
    button2 = telebot.types.KeyboardButton(text="/faq")
    button3 = telebot.types.KeyboardButton(text="/helptech")
    button4 = telebot.types.KeyboardButton(text="/answer_my_questions")
    keyboard.add(button1, button2, button3,
				 button4)
    bot.send_message(chat_id,
'''Здравствуйте, я бот техподдержки магазина "Продаем все на свете"
Чем могу помочь?:
	/start - Просмотреть команды еще раз
	/faq - Часто задаваемые вопросы
	/helptech - Написать вопрос техподдержке через бота
	/answer_my_questions - Получить ответы на вопросы заданные через /helptech''',reply_markup=keyboard)

@bot.message_handler(commands=['faq'])
def faq_handler(message):
	bot.reply_to(message, '''Напечатайте ваш вопрос:
		-Как оформить заказ?
		-Как узнать статус моего заказа?
		-Как отменить заказ?
		-Что делать, если товар пришел поврежденным?л
		-Как связаться с вашей технической поддержкой?
		-Как узнать информацию о доставке?
Для связи с техподдержкой используйте /helptech чтобы задать вопрос которого здесь нету.''')
	
@bot.message_handler(commands=['helptech'])
def tech_handler(message):
	con = sqlite3.connect("blacklist.db")
	cur = con.cursor()
	cur.execute("SELECT USER_ID FROM user_blacklist")
	res = cur.fetchall()
	con.close()
	if message.from_user.id in res:
		bot.reply_to(message, f'''Ваш аккаунт находится в blacklist и использовать эту комаду запрещено
Если вы считаете что это ошибка то отправьте ваш user_id({(message.from_user.id)}) администратору''')	
	else:
		bot.reply_to(message, '''Напечатайте ваш вопрос который мы отправим нашим специалистам
PS: Если вы будете злоупотреблять этой командой то вас добавят в blacklist и вы больше не сможете использовать /helptech''')
		bot.register_next_step_handler(message, add_question)

def add_question(message):
	if message.content_type == "text":
		bot.reply_to(message, f'Хорошо, ваш вопрос "{message.text}" был сохранен')
		con = sqlite3.connect("questions.db")
		cur = con.cursor()
		cur.execute(f"INSERT INTO user_questions (QUESTION, USER, USER_ID) VALUES ('{message.text}', '{message.from_user.username}', {message.from_user.id})")
		con.commit()
		con.close()
	else:
		bot.reply_to(message, "Весь вопрос должен являться текстом")



@bot.message_handler(commands=['admin_commands'])
def admin_handler(message):
	if message.from_user.id in admins:
		bot.reply_to(message, '''/admin_commands - просмотреть все команды доступные только для администратора
/answer_questions - благодаря этой команде вы сможете отвечать на вопросы пользователей заданных с помощью /helptech
/remove_blacklist - убирает пользователя из черного списка
Пользователи находящиеся в черном списке не смогут использовать команду /helptech''')
	else:
		bot.reply_to(message,"Вы не являетесь админом и использование данной команды запрещено")


@bot.message_handler(commands=['answer_questions'])
def answer_questions_handler(message):
	if message.from_user.id in admins:
		bot.reply_to(message,'''В любой момент времени вы можете ввести /stop чтобы остановиться отвечать на вопросы.
Если вопрос является спамом введите команду /spam чтобы удалить все вопросы от данного пользователя и заблокировать команду /helptech для него''')
		questions_handler(message)
	else:
		bot.reply_to(message,"Вы не являетесь админом и использование данной команды запрещено")

def questions_handler(message):
	con = sqlite3.connect("questions.db")
	cur = con.cursor()

	cur.execute("SELECT * FROM user_questions WHERE ANSWER IS NULL")
	res = cur.fetchone()
	con.close()
	if res:
		bot.reply_to(message, f'''Этот вопрос был задан {res[2]} его user_id является "{res[3]}": 
		"{res[1]}"''')
		bot.register_next_step_handler(message, answer_handler, answer_id = res[0],username = res[2], user_id = res[3])
	else:
		bot.reply_to(message, "На данный момент вопросов больше нету")

def answer_handler(message, answer_id, username, user_id):
	answer_save = message.text
	if answer_save == "/stop":
		bot.reply_to(message, "Вы остановились отвечать на вопросы")
	elif answer_save == "/spam":
		con = sqlite3.connect("questions.db")
		cur = con.cursor()
		cur.execute("DELETE FROM user_questions WHERE USER_ID = ?", (user_id, ))
		con.commit()
		con.close()
		con = sqlite3.connect("blacklist.db")
		cur = con.cursor()
		cur.execute("INSERT INTO user_blacklist VALUES(?,?)", (username, user_id))
		con.commit()
		con.close()
		bot.reply_to(message, "Вопросы от этого пользователя были удалены и он был добавлен в черный список")
		questions_handler(message)
	else:
		con = sqlite3.connect("questions.db")
		cur = con.cursor()
		cur.execute("UPDATE user_questions SET ANSWER = ? WHERE ID = ?", (answer_save, answer_id))
		con.commit()
		con.close()
		bot.reply_to(message, "Ответ сохранен")
		questions_handler(message)
		
@bot.message_handler(commands=['answer_my_questions'])
def answer_my_questions_handler(message):
	user_id = message.from_user.id
	con = sqlite3.connect("questions.db")
	cur = con.cursor()

	cur.execute("SELECT * FROM user_questions WHERE USER_ID = ?", (user_id, ))
	res = cur.fetchall()
	con.close()
	for r in res:
		if r[4]:
			bot.reply_to(message, f'''Ваш вопрос был: "{r[1]}", 
	Специалист выдал ответ: "{r[4]}''')
		else:
			bot.reply_to(message, f'Специалист еще не ответил на "{r[1]}"')
	bot.reply_to(message, "Вопросов больше нету")



@bot.message_handler(commands=['remove_blacklist'])
def remove_blacklist_handler(message):
	if message.from_user.id in admins:
		bot.reply_to(message,'''Введите user_id пользователя которого вы хотите убрать из черного списка''')
		bot.register_next_step_handler(message, blacklist_remove_user_handler)
	else:
		bot.reply_to(message,"Вы не являетесь админом и использование данной команды запрещеноы")

def blacklist_remove_user_handler(message):
	con = sqlite3.connect("blacklist.db")
	cur = con.cursor()
	cur.execute("DELETE FROM user_blacklist WHERE USER_ID = ?", (message.text, ))
	con.commit()
	con.close()
	bot.reply_to(message, f'Данный user_id({message.text}) был удален из черного списка')





@bot.message_handler(func=lambda message: True)
def echo_all(message):
	if faq.get(message.text) != None:
		bot.reply_to(message, faq.get(message.text))
	else:
		pass

bot.infinity_polling()


