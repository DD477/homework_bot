import datetime as dt
import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в чат Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправлено')
    except Exception as error:
        logger.error('Ошибка при отправке сообщения')


def get_api_answer(current_timestamp):
    """Получает список домашек"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(f'Ошибка запроса к API {error}')
        raise Exception(f'Ошибка запроса к API {error}')

    if response.status_code != HTTPStatus.OK:
        logger.error('Ошибка ответа от сервера '
                     f'{response.status_code} != 200')
        raise Exception('Ошибка ответа от сервера '
                        f'{response.status_code} != 200')

    try:
        response = response.json()
    except Exception as error:
        logger.error('Ошибка форматирования json')

    return response


def check_response(response):
    """Проверяется ответ на запрос к API Яндекс.Домашка"""
    if not isinstance(response, dict):
        logger.error('Ответ от сервера не является словарем')
        raise TypeError('Ответ от сервера не является словарем')

    key = 'homeworks'
    if key not in response:
        logger.error(f'Ответ от сервера не содержит ключ {key}')
        raise KeyError(f'Ответ от сервера не содержит ключ {key}')

    if not isinstance(response[key], list):
        logger.error(f'Ответ под ключом {key} приходят не в виде списка')
        raise TypeError(f'Ответ под ключом {key} приходят не в виде списка')

    try:
        response = response[key]
    except Exception as error:
        logger.error(f'Ошибка {error}')

    return response


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы"""
    if 'homework_name' not in homework:
        logger.error('В словаре нету ключа "homework_name"')
        raise KeyError('В словаре нету ключа "homework_name"')
    homework_name = homework.get('homework_name')

    if 'status' not in homework:
        logger.error('В словаре нету ключа "status"')
        raise KeyError('В словаре нету ключа "status"')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        logger.error(f'В словаре нету ключа {homework_status}')
        raise KeyError(f'В словаре нету ключа {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет переменное окружение"""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def get_unix_time(time_str):
    """Получает время последней проверки домашней работы.
    Отдает результат в форамате timestamp.
    """
    timestamp = dt.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    timestamp = int(time.mktime(timestamp.timetuple()))
    return timestamp


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.error('Ошика переменных окружения')
        exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 60 * 60 * 24 * 30
    old_msg = ''
    old_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            answer = check_response(response)
            message = parse_status(answer[0])
            if message != old_msg:
                send_message(bot, message)
                old_msg = message
            else:
                logger.debug('Статус не обновился')
            current_timestamp = get_unix_time(answer[0]['date_updated'])
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != old_message:
                send_message(bot, message)
                old_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
