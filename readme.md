# Universal Test Unit

## Description
- Покрывает весь функционал Pepeunit.
- Поддерживает Компилируемые и Интерпритируемые обновления.
- Используется для Интеграционных тестов.

## Software platform
- `Python >3.9`

## Firmware format
Интерпритируемый
Компилируемый

## Hardware platform
- `any Desktop`

## Required physical components
- Desktop

## env_example.json

```json
{
    "DELAY_PUB_MSG": 1,   
    "PEPEUNIT_URL": "unit.example.com",
    "HTTP_TYPE": "https",
    "MQTT_URL": "emqx.example.com",
    "MQTT_PORT": 1883,
    "PEPEUNIT_TOKEN": "jwt_token",
    "SYNC_ENCRYPT_KEY": "",
    "SECRET_KEY": "32_bit_secret_key",
    "PING_INTERVAL": 30,
    "STATE_SEND_INTERVAL": 300
}
```

### Env variable assignment
1. `DELAY_PUB_MSG` - частота отправки данных в `output_topic` в секундах

## schema_example.json

```json
{
    "input_base_topic": [
        "update/pepeunit",
        "schema_update/pepeunit"
    ],
    "output_base_topic": [
        "state/pepeunit"
    ],
    "input_topic": [
        "input/pepeunit"
    ],
    "output_topic": [
        "output/pepeunit"
    ]
}
```

### Assignment of Device Topics
- `input` `input/pepeunit` - принимает в качестве значения натуральные числа, записывает их в `log.json`. После записи, отправляет полученное число в `output_topic`.
- `output` `output/pepeunit` - отправляет сообщение в формате: `message: N`, где `N` - остаток от деления на `10`, числа циклов отправки сообщений в `output/pepeunit`

## Work algorithm
Алгоритм работы с момента запуска через `entrypoint.sh`:
1. Подключение к `MQTT Брокеру`
1. Подписка на `input` топики
1. Каждые `DELAY_PUB_MSG` секунд публикуются сообщения в `output/pepeunit`

Алгоритм работы в момент получения сообщения из `input/pepeunit`
1. Полученный текст преобразуется в число
1. Число записывается в `log.json` в формате `{"value": 1, "input_topic": "example.com/dc2d6f5e-90b3-4cdb-91a4-5ae12db1887f/pepeunit"}`
1. Число преобразуется в строку и отправляется в `output/pepeunit`