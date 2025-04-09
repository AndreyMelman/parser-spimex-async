# Парсер SPIMEX

Асинхронный парсер для скачивания и обработки данных с сайта SPIMEX (https://spimex.com/markets/oil_products/trades/results/).

## Описание

Проект состоит из двух основных компонентов:
1. Асинхронный парсер для скачивания файлов с сайта SPIMEX
2. Асинхронный процессор для обработки скачанных файлов и записи данных в PostgreSQL

## Требования

- Python 3.9+
- PostgreSQL
- Docker и Docker Compose (для запуска базы данных)

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd parser-spimex
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/Mac
# или
.venv\Scripts\activate  # для Windows
pip install -r requirements.txt
```

3. Настройте переменные окружения:
Создайте файл `.env` в корневой директории проекта со следующим содержимым:
```
APP_CONFIG__DB__URL=postgresql+asyncpg://postgres:postgres@localhost:5432/spimex-async
```

## Запуск базы данных

```bash
docker-compose up -d
```

## Запуск парсера

```bash
python main.py
```

## Структура проекта

- `main.py` - основной файл для запуска парсера
- `parser/spimex_parser.py` - модуль для скачивания файлов с сайта SPIMEX
- `parser/process.py` - модуль для обработки скачанных файлов и записи в БД
- `db/models/` - модели базы данных
- `db/config.py` - конфигурация базы данных
- `alembic/` - миграции базы данных

## Логирование

Логи сохраняются в файл `spimex_parser.log` и выводятся в консоль.

## Лицензия

MIT
