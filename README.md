## Тема проекта

«Умный ночник с дистанционным управлением на базе Raspberry Pi»

## Состав команды

Никулина Светлана Ивановна - GitHub: NikulinaSvetlana

## Тема проекта
«Умный ночник с дистанционным управлением на базе Raspberry Pi»

## Описание проекта
Устройство на базе Raspberry Pi для удаленного управления светодиодным освещением через веб-интерфейс и Telegram-бота. Проект реализует возможность включения/выключения, плавной регулировки яркости и создания сценариев освещения.

# Smart Nightlight MVP (Raspberry Pi + Web + Telegram)

## Возможности

- LED (GPIO PWM): включение/выключение, яркость 0–100%
- Web UI: `GET /` (простой интерфейс)
- REST API (FastAPI): управление устройствами, сценарии, статус, метрики
- Telegram-бот: команды `/on`, `/off`, `/brightness 0-100`, `/status`
- Аутентификация: Bearer token
- HTTPS: запуск с TLS-сертификатами (uvicorn `ssl_certfile/ssl_keyfile`)

## Переменные окружения

- `NIGHTLIGHT_API_TOKEN` (обязательно, длина ≥ 16)
- `NIGHTLIGHT_GPIO_BACKEND` (`mock` или `rpi`, по умолчанию `mock`)
- `NIGHTLIGHT_LED_GPIO_PIN` (BCM pin, по умолчанию `18`)
- `NIGHTLIGHT_PWM_FREQUENCY_HZ` (по умолчанию `800`)
- `NIGHTLIGHT_DEVICE_ID` (по умолчанию `nightlight`)
- `NIGHTLIGHT_SSLCERTFILE`, `NIGHTLIGHT_SSLKEYFILE` (пути к PEM)
- `NIGHTLIGHT_TELEGRAM_BOT_TOKEN` (для бота)
- `NIGHTLIGHT_TELEGRAM_ALLOWED_CHAT_IDS` (через запятую)
- `NIGHTLIGHT_TELEGRAM_API_URL` (например `https://nightlight:8443`)
- `NIGHTLIGHT_TELEGRAM_TLS_VERIFY` (`true/false`, по умолчанию `true`)

## Локальный запуск (без Docker)

1) Установить зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2) Создать самоподписанный сертификат (пример):

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes -keyout certs/key.pem -out certs/cert.pem -days 365 -subj "/CN=localhost"
```

3) Запустить API + Web:

```bash
export NIGHTLIGHT_API_TOKEN="change_me_change_me_1234"
export NIGHTLIGHT_SSLCERTFILE="certs/cert.pem"
export NIGHTLIGHT_SSLKEYFILE="certs/key.pem"
python -m app.main
```

Открыть: `https://localhost:8443/`

## Docker (виртуальный Raspberry Pi и реальное устройство)

1) Подготовить сертификаты в `./certs/cert.pem` и `./certs/key.pem`

2) Запуск:

```bash
export NIGHTLIGHT_API_TOKEN="change_me_change_me_1234"
docker compose up --build
```

Для реального Raspberry Pi и GPIO:

- собрать образ с `--build-arg INSTALL_RPI_GPIO=true`
- запустить контейнер с `NIGHTLIGHT_GPIO_BACKEND=rpi`
- обеспечить доступ к GPIO (обычно `--privileged` или проброс `/dev/gpiomem` и соответствующие группы)

## API

- `GET /health` — без авторизации
- `GET /status` — требует Bearer token
- `GET /metrics` — Prometheus-совместимый текст, требует Bearer token
- `GET /api/v1/devices` — список устройств
- `GET /api/v1/devices/{device_id}/state`
- `POST /api/v1/devices/{device_id}/power` `{ "is_on": true }`
- `POST /api/v1/devices/{device_id}/brightness` `{ "brightness": 0.5 }`
- `GET /api/v1/scenarios`
- `PUT /api/v1/scenarios/{scenario_id}`
- `POST /api/v1/scenarios/{scenario_id}/trigger`

## Тесты

```bash
pytest
```


