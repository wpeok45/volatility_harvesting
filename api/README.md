# API Module Structure

Модульная структура API с использованием FastAPI Router для каждой биржи.

## Структура

```
api/
├── __init__.py           # Экспорт всех роутеров
├── dependencies.py       # Общие зависимости (traders, main_loop, data dirs)
├── config.py            # Управление конфигурацией (save/load)
├── bybit.py             # Роуты для ByBit биржи
├── binance.py           # Роуты для Binance (placeholder)
└── cryptocom.py         # Роуты для Crypto.com (placeholder)
```

## Файлы

### `dependencies.py`
- Глобальные переменные: `traders`, `main_loop`
- Директории данных: `EXCHANGE_DATA_DIRS`
- Создание папок для каждой биржи

### `config.py`
- `save_api_config()` - сохранение настроек
- `load_api_config()` - загрузка настроек

### `bybit.py`
- `POST /bybit/start` - запуск бота
- `POST /bybit/stop` - остановка бота
- `GET /bybit/status` - статус бота
- `GET /bybit/balance` - баланс аккаунта
- `GET /bybit/stats` - статистика торговли
- `start_bybit_internal()` - внутренняя функция для автостарта

### `binance.py` & `cryptocom.py`
- Placeholder endpoints (501 Not Implemented)
- Готовы к добавлению модулей

## Использование

```python
from api import bybit_router, binance_router, cryptocom_router

app = FastAPI()
app.include_router(bybit_router)
app.include_router(binance_router)
app.include_router(cryptocom_router)
```

## Добавление новой биржи

1. Создать файл `api/exchange_name.py`
2. Импортировать зависимости:
   ```python
   from fastapi import APIRouter
   from .dependencies import traders, main_loop, EXCHANGE_DATA_DIRS
   from .config import save_api_config
   ```
3. Создать router:
   ```python
   router = APIRouter(prefix="/exchange", tags=["Exchange"])
   ```
4. Добавить endpoints (start, stop, status, etc.)
5. Импортировать в `api/__init__.py`
6. Подключить в `api_main.py`

## Преимущества модульной структуры

✅ Чистый и организованный код  
✅ Легко добавлять новые биржи  
✅ Изоляция логики каждой биржи  
✅ Простое тестирование отдельных модулей  
✅ Переиспользование кода через dependencies  
✅ Автоматическая документация по тегам
