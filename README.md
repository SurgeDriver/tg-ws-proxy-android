# TG WS Proxy (Android / Termux Edition)

Локальный SOCKS5-прокси для Telegram на Android, запускаемый через Termux. Приложение перенаправляет трафик через WebSocket-соединения к указанным серверам, помогая частично ускорить работу Telegram и обойти блокировки.

**Ожидаемый результат аналогичен прокидыванию hosts для Web Telegram**: ускорение загрузки и скачивания файлов, загрузки сообщений и обход ограничений провайдера.

## Как это работает

```
Telegram Android → SOCKS5 (127.0.0.1:1080) → TG WS Proxy (Termux) → WSS (kws*.web.telegram.org) → Telegram DC
```

1. Скрипт поднимает локальный SOCKS5-прокси на `127.0.0.1:1080` в среде Termux.
2. Перехватывает подключения к IP-адресам Telegram.
3. Извлекает DC ID из MTProto obfuscation init-пакета.
4. Устанавливает WebSocket (TLS) соединение к соответствующему DC через домены `kws{N}.web.telegram.org`.
5. Если WS недоступен — автоматически переключается на прямое TCP-соединение.

## Быстрый старт

### Android (Termux)
Установите [Termux](https://f-droid.org/packages/com.termux/) (рекомендуется версия с F-Droid) и выполните одну команду:

```bash
bash <(curl -s https://raw.githubusercontent.com/SurgeDriver/tg-ws-proxy-android/main/install.sh)
```

Скрипт автоматически настроит окружение, установит зависимости и запустит прокси.

## Установка из исходников

Если автоматический скрипт не сработал, выполните шаги вручную.

### Android (Termux)

```bash
pkg update && pkg install python git rust clang python-cryptography python-psutil python-pillow -y
git clone https://github.com/SurgeDriver/tg-ws-proxy-android.git
cd tg-ws-proxy-android
pip install -r requirements.txt
```

### Запуск

```bash
termux-wake-lock
python android.py
```

**Аргументы:**

| Аргумент | По умолчанию | Описание |
|---|---|---|
| `--port` | `1080` | Порт SOCKS5-прокси |
| `--dc-ip` | `2:149.154.167.220` | Целевой IP для DC (настраивается в config.json) |
| `-v`, `--verbose` | выкл. | Подробное логирование (DEBUG) |

**Примеры:**

```bash
# Стандартный запуск
python android.py

# Другой порт
python android.py --port 9050

# С подробным логированием
python android.py -v
```

### Удобный алиас для повторного запуска

Чтобы не вводить полную команду каждый раз, добавьте алиас в `~/.bashrc`:

```bash
echo 'alias tgproxy="cd ~/tg-ws-proxy-android && termux-wake-lock && python android.py"' >> ~/.bashrc
source ~/.bashrc
```

Теперь для запуска достаточно команды `tgproxy`.

## Настройка Telegram Android

### Вручную

1. Telegram → **Настройки** → **Данные и память** → **Настройки прокси** (внизу)
2. Нажмите **Добавить прокси**:
   - **Тип:** SOCKS5
   - **Сервер:** `127.0.0.1`
   - **Порт:** `1080`
   - **Логин/Пароль:** оставить пустыми
3. Нажмите **Сохранить** и активируйте ползунок.

## Конфигурация

Приложение хранит данные в домашней директории Termux `~/TgWsProxy/config.json`:

```json
{
  "port": 1080,
  "host": "127.0.0.1",
  "dc_ip": [
    "2:149.154.167.220",
    "4:149.154.167.220"
  ],
  "verbose": false
}
```

**Список серверов (DC IP):**
Для лучшего пинга измените `dc_ip` на ближайший к вам сервер:

*   **DC 1 (Miami):** `149.154.175.53`
*   **DC 2 (Amsterdam):** `149.154.167.51`
*   **DC 5 (Singapore):** `91.108.56.190`

Для пользователей из России рекомендуется DC 2 (Amsterdam).

## Решение проблем

*   **`python: can't open file 'main.py'`:** Точка входа — `android.py`, а не `main.py`. Используйте `python android.py`.
*   **`[Errno 98] address already in use`:** Порт 1080 уже занят предыдущим экземпляром прокси. Дождитесь нескольких секунд — прокси запустится автоматически после освобождения порта. Либо завершите старый процесс явно: `pkill -f android.py && sleep 1 && python android.py`.
*   **Высокий пинг (>1000ms):** Проверьте параметр `dc_ip` в конфиге — возможно, выбран далёкий сервер.
*   **Прокси отваливается:** Android усыпляет фоновые процессы. Обязательно выполняйте `termux-wake-lock` перед запуском.
*   **Ошибки при установке:** Убедитесь, что используете Termux из F-Droid, а не Google Play.

## Лицензия

[MIT License](LICENSE)

*Based on [Flowseal/tg-ws-proxy](https://github.com/Flowseal/tg-ws-proxy)*
