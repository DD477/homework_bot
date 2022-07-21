# Бот-ассистент

## Описание:
Telegram бот для оповещения о проверки домашнего задания на Яндекс.Практикуме. Данным проектом могут пользоваться только студентами Яндекс.Практикума. Тем не менее, проект может быть интересен как пример по написанию Telegram ботов.

## Оглавление

* [Использованные технологии](#использованные-технологии)
* [Необходимый софт](#необходимый-софт)
* [Как запустить проект](#как-запустить-проект)

## Использованные технологии:

-   [python-telegram-bot](https://pypi.org/project/python-telegram-bot/) 13.7
-   [requests](https://pypi.org/project/requests/) 2.26.0


## Необходимый софт:
-   [Python](https://www.python.org/) 3.8.10 или выше


## Как запустить проект:
- Клонировать репозиторий 
   ```sh
   git clone https://github.com/DD477/homework_bot.git
   ```
- Перейти в папку с проектом
   ```sh
   cd homework_bot
   ```
- Cоздать и активировать виртуальное окружение
   ```sh
   python3 -m venv venv
   ```
   ```sh
   source venv/bin/activate
   ```
- Обновить менеджер пакетов (pip)
   ```sh
   pip install --upgrade pip
   ```
- Установить зависимости из файла requirements.txt
   ```sh
   pip install -r ./backend/requirements.txt
   ```
- Создать файл `.env` в корне, с необходимым содержимым
  ```sh
  PRACTICUM_TOKEN=YOUR_PRACTICUM_TOKEN
  TELEGRAM_TOKEN=YOUR_TELEGRAM_TOKEN
  TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID
  ```
- Запустить файл `homework.py`

[К оглавлению](#оглавление) ↑

## Автор:
[Dmitry Dobrodeev](https://github.com/DD477)

## Лицензия:
- MIT
