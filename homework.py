import logging
import os
import time
from exceptions import ResponseIsNot200
from http import HTTPStatus
from json import JSONDecodeError
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from telegram.error import TelegramError
from urllib3.util.retry import Retry

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('logs.log', maxBytes=50_000_000, backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME_S = 600
MONTH_AGO = 60 * 60 * 24 * 30
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
    except TelegramError as error:
        logger.error(f'Ошибка при отправке сообщения {error}')


def get_api_answer(current_timestamp):
    """Получает список домашек."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        # тесты не пропускают
        # s = requests.Session()
        # retries = Retry(total=5,
        #                 backoff_factor=0.1,
        #                 status_forcelist=[500, 502, 503, 504])
        # s.mount('https://', HTTPAdapter(max_retries=retries))
        # response = s.get(ENDPOINT, headers=HEADERS, params=params)
        # response.raise_for_status()
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except RequestException as error:
        logger.error(f'Ошибка запроса к API {error}')
        raise RequestException(f'Ошибка запроса к API {error}')

    if response.status_code != HTTPStatus.OK:
        logger.error('Ошибка ответа от сервера '
                     f'{response.status_code} != 200')
        raise ResponseIsNot200('Ошибка ответа от сервера '
                               f'{response.status_code} != 200')

    try:
        response = response.json()
    except JSONDecodeError as error:
        logger.error(f'Ошибка форматирования json {error}')

    return response


def check_response(response):
    """Проверяется ответ на запрос к API Яндекс.Домашка."""
    if not isinstance(response, dict):
        error_msg = 'Ответ от сервера не является словарем'
        logger.error(error_msg)
        raise TypeError(error_msg)

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
    """Извлекает из информации о домашней работе статус этой работы."""
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
    """Проверяет переменное окружение."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.error('Ошика переменных окружения')
        exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - MONTH_AGO
    old_message = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            answer = check_response(response)
            if answer != []:
                message = parse_status(answer[0])
                send_message(bot, message)
            else:
                logger.debug('Статус не обновился')
            current_timestamp = response['current_date']

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != old_message:
                send_message(bot, message)
                old_message = message
        time.sleep(RETRY_TIME_S)


if __name__ == '__main__':
    main()
