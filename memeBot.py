from types import TracebackType
from dns.rdatatype import UNSPEC
from dns.resolver import query
import mysql.connector
import logging
from datetime import datetime
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, CallbackContext, ConversationHandler, InlineQueryHandler)
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, message, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedPhoto, InputTextMessageContent
import time
from emoji import emojize
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.inline.inlinequeryresultarticle import InlineQueryResultArticle
from telegram.inline.inlinequeryresultphoto import InlineQueryResultPhoto

import base64
import requests


def uploadPhoto(photo):
    print("Uploading...")
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": "imgbbApiToken",
        "image": base64.b64encode(photo),
    }
    response = requests.post(url, payload)
    print(response.status_code)
    if response.status_code == 200:
        return {"photo_url": response.json()["data"]["url"], "thumb_url": response.json()["data"]["thumb"]["url"]}
    return None


updater = Updater(
    token="Bot token",
    use_context=True)

dispathcer = updater.dispatcher

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData


def writeImage(image, user_id):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = "INSERT INTO files (file,user_id) VALUES (%s, %s)"
        binatyPhoto = convertToBinaryData(image)
        cursor.execute(query, (binatyPhoto, user_id))
        connection.commit()
        return cursor.lastrowid
    except mysql.connector.Error as error:
        logger.info("Error at writing to db " + error)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def readImage(file_id):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = "SELECT file FROM files WHERE file_id = %s"
        cursor.execute(query, (file_id,))
        record = cursor.fetchone()
        return record[0]
    except mysql.connector.Error as error:
        logger.info("Error at reading from db " + error)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


START_SEARCH, SEARCH = range(2)


def create_user(name, telegram_id):
    try:
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = """INSERT INTO users (user_name,reg_date,telegram_id)
                 VALUES (%s, %s, %s)"""
        cursor.execute(query, (name, formatted_date, telegram_id))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        logger.info("Error at writing to db ")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def add_tag(text):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = """INSERT INTO tags (text)
                 VALUES (%s)"""
        cursor.execute(query, (text, ))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        logger.info("Error at writing to db ")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_user_id(telegram_id):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = "SELECT user_id FROM users WHERE telegram_id = %s"
        cursor.execute(query, (telegram_id,))
        record = cursor.fetchone()
        return record[0]
    except mysql.connector.Error as error:
        logger.info("Error at reading from db " + error)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def createMeme(file_id, tags):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = "INSERT INTO memes (file_id,tag_id) VALUES (%s, %s)"
        values = []
        for tag in tags:
            values.append((file_id, tag))
        cursor.executemany(query, values)
        connection.commit()
        return True
    except mysql.connector.Error as error:
        logger.info("Error at writing to db " + error)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def getTagIds(tags):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        ids = []
        for tag in tags:
            cursor = connection.cursor()
            query = "SELECT tag_id FROM tags WHERE text = %s"
            cursor.execute(query, (tag,))
            record = cursor.fetchone()
            ids.append(record[0])
            cursor.close()
        return ids
    except mysql.connector.Error as error:
        logger.info("Error at reading from db " + error)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def tagExists(text):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = "SELECT tag_id FROM tags WHERE text = %s"
        cursor.execute(query, (text,))
        record = cursor.fetchone()
        cursor.close()
        if (record != None):
            return True
        else:
            return False

    except mysql.connector.Error as error:
        logger.info("Error at reading from db " + error)
        return False

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def createMeme(file_id, tag_ids):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        for tag in tag_ids:
            cursor = connection.cursor()
            query = """INSERT INTO memes (file_id,tag_id)
                 VALUES (%s, %s)"""
            cursor.execute(query, (file_id, tag))
            connection.commit()
            cursor.close()

        return True
    except mysql.connector.Error as error:
        logger.info("Error at writing to db ")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def searchMeme(keyword):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = """
        SELECT DISTINCT(f.file_id), MATCH(text) AGAINST(%s) AS accuracy,f.file_id
        FROM tags
        LEFT JOIN memes m USING(tag_id)
        LEFT JOIN files f USING(file_id)
        WHERE MATCH(text) AGAINST(%s)
        ORDER BY accuracy DESC;
        """
        cursor.execute(query, (keyword, keyword))
        record = cursor.fetchall()
        if (record != None):
            return record
        else:
            return False

    except mysql.connector.Error as error:
        logger.info("Error at reading from db " + error)
        return False

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def likeFile(file_id):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')

        cursor = connection.cursor()
        query = "UPDATE files SET `like` =`like` + 1 WHERE file_id = %s"
        cursor.execute(query, (file_id,))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        logger.info("Error at reading from db " + error)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def addReport(user_id, report_status_id, discription):
    try:
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = "INSERT INTO reports (report_status_id,user_id,date,discription) VALUES (%s, %s,%s,%s)"
        cursor.execute(query, (report_status_id, user_id, formatted_date, discription))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        logger.info("Error at writing to db " + error)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def getMostLiked():
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='sql_meme',
                                             user='databaseUserName',
                                             password='DatabasePassword')
        cursor = connection.cursor()
        query = """
        SELECT file_id,`like`
        FROM files
        WHERE `like` > 0
        ORDER BY `like` DESC
        LIMIT 10;
        """
        cursor.execute(query)
        record = cursor.fetchall()
        if (record != None):
            return record
        else:
            return False

    except mysql.connector.Error as error:
        logger.info("Error at reading from db " + error)
        return False

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
# Finish database section


def start(update: Update, _: CallbackContext):
    serachEmojy = emojize(":mag:", use_aliases=True)
    addEmojy = emojize(":heavy_plus_sign:", use_aliases=True)
    helpEmojy = emojize(":question:", use_aliases=True)
    keyboard = [
        [f"جستجو میم {serachEmojy}", f'افزودن میم {addEmojy}'],
        [f"راهنما استفاده {helpEmojy}"]
    ]
    user = update.message.from_user
    user_full_name = user.first_name + (", " + user.last_name if user.last_name else "")
    telegram_id = user.id
    create_user(user_full_name, telegram_id)
    update.message.reply_text(
        f"به میم فایندر خوش آمدید",
        reply_markup=ReplyKeyboardMarkup(keyboard,
                                         resize_keyboard=True,
                                         one_time_keyboard=True)
    )


def addMeme(update: Update, _: CallbackContext):
    MAX_FILE_SIZE = 2000000  # 2MB
    user = update.message.from_user
    if(update.message.caption == None):
        update.message.reply_text("باید تو کپشن عکس حداقل ی کلیدواژه با طول ۳ تا حرف باشه")
        return
    if(len(update.message.caption) < 3):
        update.message.reply_text("باید تو کپشن عکس حداقل ی کلیدواژه با طول ۳ تا حرف باشه")
        return
    photo_file = update.message.photo[-1].get_file()
    if (photo_file.file_size > MAX_FILE_SIZE):
        update.message.reply_text("حجم میمی که فرستادی خیلی بود نمیتونم سیوش کنم :((")
    photo_file.download('cash.jpg')
    file_id = writeImage('cash.jpg', get_user_id(user.id))
    tags = update.message.caption.split('/')
    for tag in tags:
        state = tagExists(tag.strip())
        if state == False:
            add_tag(tag.strip())
    ids = getTagIds(tags)
    createMeme(file_id, ids)
    update.message.reply_text("میم اضافه شد :)))")


def startSearch(update: Update, context: CallbackContext):
    update.message.reply_text(
        """کلید واژه میمی که دنبالشی رو برام بفرست تا پیداش کنم برات :‌)) \n
        اگه بیخیال شدی هم /cancelSearch رو برام بفرست
        """,
        reply_markup=ReplyKeyboardRemove())
    return SEARCH


def search(update: Update, context: CallbackContext):
    finalKeyboard = [[
        InlineKeyboardButton('میمی که میخواستم نبود :((', callback_data='memeNotFound' + update.message.text),
        InlineKeyboardButton('میم بی ربط فرستادم برات؟', callback_data='irrelevantMeme' + update.message.text)
    ]]
    homeEmoji = emojize(":house:", use_aliases=True)
    keyboard = [[f"صفحه اصلی {homeEmoji}"]]
    notFoundKeyboard = [[InlineKeyboardButton(
        'درخواست میم', callback_data="addMemeRequest" + update.message.text)]]
    results = searchMeme(update.message.text)
    if (len(results) < 1):
        update.message.reply_text("""هیچ میمی پیدا نکردم :( \n
         با کلید واژه های دیگه امتحان کن یا گزارش درخواست میم برام بفرست""",
                                  reply_markup=InlineKeyboardMarkup(notFoundKeyboard)

                                  )
        home(update, context)
        return ConversationHandler.END
    startTime = time.time()
    for item in results:
        likeKeyboard = [[InlineKeyboardButton(
            "همینی بود که میخواستم", callback_data="LikeFile"+str(item[2]))]]
        image = readImage(item[0])
        relevence = item[1]
        if (relevence > 1):
            relevence = round(relevence)
        update.message.reply_photo(
            image, f"میزان شباهت : {relevence}", reply_markup=InlineKeyboardMarkup(likeKeyboard))
    endTime = time.time()
    update.message.reply_text(
        f"""{len(results)} میم پیدا کردم و فرستادمشون :)) \n
         مدت زمان جستجو {int(endTime - startTime)} میلی ثانیه""",
        reply_markup=InlineKeyboardMarkup(finalKeyboard)
    )
    home(update, context)
    return ConversationHandler.END


def cancellSearch(update: Update, _: CallbackContext):
    homeEmoji = emojize(":house:", use_aliases=True)
    keyboard = [[f"صفحه اصلی {homeEmoji}"]]
    update.message.reply_text("اوکی بیخیالش :))", reply_markup=ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True))
    return ConversationHandler.END


def help(update: Update, _: CallbackContext):
    homeEmoji = emojize(":house:", use_aliases=True)
    keyboard = [[f"صفحه اصلی {homeEmoji}"]]
    update.message.reply_text(
        """
        من میم فایندم حالت چطوره؟ سر کیفی عزیز :) \n
        مشکلت چیه عزیزم همه چی خیلی ساده و شفافه الکی ادا حال بدا رو در نیار :))
        """,
        reply_markup=ReplyKeyboardMarkup(keyboard,
                                         resize_keyboard=True,
                                         one_time_keyboard=True)
    )


def addMemeHelp(update: Update, _: CallbackContext):
    homeEmoji = emojize(":house:", use_aliases=True)
    keyboard = [[f"صفحه اصلی {homeEmoji}"]]
    update.message.reply_text(
        """
        برای اضافه کردن میم میتونی عکس رو برام بفرستی و توی توضیحاتش کلیدواژه(ها)ش رو برام بفرستی\n
        فقط یادت نره که هر کلید واژه ای رو با استفاده از / از هم دیگه جدا کنی :)
        """,
        reply_markup=ReplyKeyboardMarkup(keyboard,
                                         resize_keyboard=True,
                                         one_time_keyboard=True)
    )


def mostLiked(update: Update, _: CallbackContext):
    homeEmoji = emojize(":house:", use_aliases=True)
    keyboard = [[f"صفحه اصلی {homeEmoji}"]]
    results = getMostLiked()
    for item in results:
        image = readImage(item[0])
        update.message.reply_photo(image, f"تعداد دانلود : {item[1]}")
    update.message.reply_text(
        "همشو برات فرستادم",
        reply_markup=ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True))


def inlineSearch(update: Update, context: CallbackContext):
    query = update.inline_query.query
    if not query:
        return
    sqlResults = searchMeme(query)
    results = list()
    for item in sqlResults:
        image = readImage(item[0])
        url = uploadPhoto(image)
        print(url)
        relevence = item[1]
        if (relevence > 1):
            relevence = round(relevence)
        results.append(
            InlineQueryResultPhoto(
                id=url["photo_url"],
                photo_url=url["photo_url"],
                thumb_url=url["thumb_url"],
                title=f"میزان شباهت : {relevence}",
                description=f"میزان شباهت : {relevence}",
                caption=f"میزان شباهت : {relevence}",

            )
        ),
    print(len(results))
    update.inline_query.answer(results)
    # context.bot.answer_inline_query(update.inline_query.id, results)


def home(update: Update, _: CallbackContext):
    serachEmojy = emojize(":mag:", use_aliases=True)
    addEmojy = emojize(":heavy_plus_sign:", use_aliases=True)
    helpEmojy = emojize(":question:", use_aliases=True)
    mostEmojy = emojize(":inbox_tray:", use_aliases=True)
    keyboard = [
        [f"جستجو میم {serachEmojy}", f'افزودن میم {addEmojy}'],
        [f'میم های پردانلود هفته {mostEmojy}'],
        [f"راهنما استفاده {helpEmojy}"]
    ]
    update.message.reply_text(
        """
        میم فایندر هستم چطور میتونم کمکت کنم؟
        """,
        reply_markup=ReplyKeyboardMarkup(keyboard,
                                         one_time_keyboard=True,
                                         resize_keyboard=True)
    )


def button(update: Update, context: CallbackContext):
    query = update.callback_query
    print(f"Selected option: {query.data}")

    if "memeNotFound" in query.data:
        user_id = get_user_id(query.from_user.id)
        addReport(user_id, 2, query.data[11:])
        query.answer(text="ببخشید :( گزارش رو ثبت کردم زودی درستش میکنیم :)", show_alert=True)
        query.delete_message()
    elif "irrelevantMeme" in query.data:
        user_id = get_user_id(query.from_user.id)
        addReport(user_id, 1, query.data[14:])
        query.answer(text="گزارش میم نامربوط ثبت شد. مرسی :)", show_alert=True)
        query.delete_message()
    elif "LikeFile" in query.data:
        likeFile(query.data[8:])
        query.answer(text="مرسی از کمکت :)", show_alert=True)
    elif "addMemeRequest" in query.data:
        user_id = get_user_id(query.from_user.id)
        addReport(user_id, 3, query.data[14:])
        query.answer(text="درخواست اضافه کردن میم ثبت شد. مرسی :)", show_alert=True)
        query.delete_message()
    # query.edit_message_text(text=f"Selected option: {query.data}")


start_handler = CommandHandler('start', start)
home_handler = MessageHandler(Filters.regex(r'صفحه اصلی'), home)
help_handler = MessageHandler(Filters.regex(r'راهنما'), help)
mostLiked_handler = MessageHandler(Filters.regex(r'پردانلود هفته'), mostLiked)
addHelp_handler = MessageHandler(Filters.regex(r'افزودن میم'), addMemeHelp)
inlineSearch_handler = InlineQueryHandler(inlineSearch)

# search_handler = CommandHandler('search', search)
search_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex(r'جستجو میم'), startSearch)],
    states={
        # START_SEARCH: [MessageHandler(Filters.regex(r'جستجو میم'), startSearch)],
        SEARCH: [MessageHandler(Filters.text & ~Filters.command, search)]
    },
    fallbacks=[CommandHandler('cancelSearch', cancellSearch)]
)

add_handler = MessageHandler(Filters.photo, addMeme)

dispathcer.add_handler(start_handler)
dispathcer.add_handler(home_handler)
dispathcer.add_handler(help_handler)
dispathcer.add_handler(mostLiked_handler)
dispathcer.add_handler(addHelp_handler)
dispathcer.add_handler(search_handler)
dispathcer.add_handler(add_handler)
dispathcer.add_handler(CallbackQueryHandler(button))
dispathcer.add_handler(inlineSearch_handler)

updater.start_polling()
