import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
from dotenv import load_dotenv
import telebot
from telebot.types import Message
import json

with open("users.json", "r") as f_o:
    admin_ip = next(iter(json.load(f_o)))
today = datetime.date.today()
load_dotenv()
# Файл, полученный в Google Developer Console
CREDENTIALS_FILE = 'creds.json'
# ID Google Sheets документа (взят из файла ".env")
spreadsheet_id = str(os.getenv('GOOGLE_SHEETS_ID'))
# Bot's token (взят из файла ".env")
bot_client = telebot.TeleBot(token=str(os.getenv('TOKEN')))


# Настройка команды "start" и получение id пользователя
@bot_client.message_handler(commands=["start"])
def start(message: Message):
    try:
        with open("users.json", "r") as f_o:
            data_from_json = json.load(f_o)

        user_id = message.from_user.id
        username = message.from_user.username

        if str(user_id) not in data_from_json:
            data_from_json[user_id] = {"username": username}
    except Exception:
        bot_client.send_message(admin_ip, str('Произошла ошибка при обработке команды "start"'))
    try:
        with open("users.json", "w") as f_o:
            json.dump(data_from_json, f_o, indent=4, ensure_ascii=False)
        bot_client.reply_to(message=message, text=str("Вы зарегистрированы."))
    except Exception:
        bot_client.send_message(admin_ip, str('Произошла ошибка во время внесения id в json файл'))


# Авторизуемся и получаем service — экземпляр доступа к API
def authoriz():
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE,
            ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)
        return httpAuth, service
    except Exception:
        bot_client.send_message(admin_ip, str('Произошла ошибка во время авторизации в Google sheets'))


# Чтения файла
def read(service):
    try:
        values = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='A2:E300',
            majorDimension='COLUMNS'
        ).execute()
        return values
    except Exception:
        bot_client.send_message(admin_ip, str('Произошла ошибка во время прочтения Google sheets'))


with open("users.json", "r") as f_o:
    data_from_json = json.load(f_o)


def send(values):
    try:
        for i in range(len(values['values'][3])):
            birthday_str = values['values'][3][i]
            birthday_obj = datetime.datetime.strptime(birthday_str, '%d.%m.%Y')
            if today.day == birthday_obj.day and today.month == birthday_obj.month:
                for ids in data_from_json:
                    bot_client.send_message(ids, 'У ' + values['values'][1][
                        i] + ' сегодня День Рождения. Не забудьте поздравить!\n' + "Вот его(её) номер: ")
                    if (values['values'][4][i]).strip():
                        bot_client.send_message(ids, str((values['values'][4][i]).replace('-', '')))
    except Exception:
        bot_client.send_message(admin_ip, str('Произошла ошибка при отправке сообщения'))


if __name__ == '__main__':
    httpAuth, service = authoriz()
    values = read(service)
    send(values)
    bot_client.polling()

