Мы разделили api  на состанвные и сделал модульно

Разделили проверки и api

- В папке api только api, 2 класса, отправить на проверку, получить результат
- В папке checks python проверки. По папкам разбиты проверки со своим rest
- В папке checks go проверки, наработки по rtp

```
Разбор  протокола и заголовков rtp позволяет диагностировать
- потери пакетов (frame loss);
- повторную посылку пакета (duplicate);
- изменение порядка прихода (reordering);
- перезагрузку камеры
- задержку прохождения пакета

Нетребовательное решение к железу, которое позволяет мониторить видео потоки без вмешательства в работу камер, не дает никакого сайд эффекта, и использует существующие соединения.

В стадии разработки

```

Установка python api:

- python 3.7
- pip install -r requriments.txt
- redis server

Запуск:

#Менеджер очередей
rq worker

#api
python 3 run.ru


Примеры:

```
curl -u admin:admin  \
  --request POST \
  --url http://127.0.0.1/cameras/check \
  --header 'content-type: application/json' \
  --data '{
    "id": "DVN_SAO_0318_5",
    "check": "flow",
    "ip": "127.0.0.1",
    "ip_flow": "192.168.31.10",
    "url": "http://34.91.190.119:8300/",
    "longitude": "55.763338",
    "latitude": "37.565466",
    "port": "554"
}' | jq .

curl -u admin:admin \
     --data id=DVN_SAO_0318_5 \
     --data check=flow \
     -X GET "http://127.0.0.1/cameras/result" | jq

```

