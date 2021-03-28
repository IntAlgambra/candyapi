# Candyapi

Реализация тестового задания от школы бэкенд-разработки Яндекса, реализующее REST API 
для управления курьерами и заказами службы доставки

## Требования

1. Docker

2. docker-compose

## Инструкции по деплою

1. Клонируем репозиторий

```
git clone https://github.com/IntAlgambra/candyapi.git
```

2. Переходим в папку проекта и создаем файл с переменными окружения .candyapi.env

```
cd candyapi
touch .candyapi.env
```

3. Прописываем в .candyapi.env необходимые переменные окружения

```
DJANGO_SECRET_KEY=секретный ключ приложения Джанго
DJANGO_HOST=хост или ip на котором развернуто приложение
DJANGO_PRODUCTION=флаг, устанавливающий режим работы. Строго True для продакшн-режима.
POSTGRES_USER=имя пользователя в БД Postgres
POSTGRES_PASSWORD=пароль пользователя в БД Postgres

```

4. Запускаем приложение  и производим миграции БД

```
docker-compose up -d --build
docker-compose run --rm backend python manage.py migrate
```

## Обновление приложения

1. Подтягиваем новую версию приложения из удаленного репозитория

```
git pull
```

2. Пересобираем контейнеры и запускаем миграции БД

```
docker-compose up -d --build
docker-compose run --rm backend python manage.py migrate
```

## Тестирование

Запускаем тесты в отдельном контейнере, имеющем доступ к контейнеру с БД

```
docker-compose run --rm backend python manage.py test
```

## Развертывание в режиме для разработки

В данном режиме сервис запускается с помощью встроенного веб-сервера django,
обновляется при изменении исходного кода и выводит информацию о запросах и
ошибках непосредственно в консоль.

```
docker-compose -f docker-compose.dev.yml up --build
```

## Схема базы данных приложения

В схеме таблицы обозначены именами моделей Django (реальные имена таблиц в Postgres сгенерированы фремворком и отличаются)

Представление интервалов доставки и работы в качестве записей в БД позволяет подбирать для курьера подходящие заказы только sql запросами (геренируются django).

![Image description](candyapi_db_schema.png)

## Используемые библиотеки

1.  ### Django

    Основной фреймворк проекта, выбран из-за наличия опыта работы с Django и удобства работы с БД 
    через Django ORM

2.  ### django-extensions

    Набор инстрементов, облегчающих управление django-проектами. Используется для удобного запуска скриптов в контексте django

3.  ### pydantic

    Используется для валидации и структурирования входных данных

4.  ### python-dateutil

    Используется для парсинга времени

5. ### gunicorn

    wsgi сервер для деплоя приложения

## Примечания

1.  ### Неоднозначное поведение при назначении развозов.

    На данный момент в функционале программы возможен следующий случай - курьеру назначаются заказы и сразу же закрываются с указанием в complete_time будущего времени. В результате, после выполнения развоза и нового назначения, время в assign_time нового развоза может быть меньшим, чем время завершения заказов из предыдущего. Данный баг предусмотрен и оставлен сознательно, чтобы системы тестирования имели возможность использовать любое время в complete_time. В боевой системе было бы запрещено передавать в complete_time время большее, чем текущее по серверу (django.utils.timezone.now()).

2.  ### Проверка уникальности id курьеров и заказов в пределах запроса

    Так как в условии явно указано, что в пределах запроса гарантируется уникальность courier_id и order_id. Проверка на уникальность не проводится, но при попытке поослать запрос с повторяющимися id будет возвращена ошика базы данных "попытка добавить существующий заказ/курьера"


3.  ### Обработка ситуации, при которых из развоза исчезают заказы

    Возможна ситуация, при которой курьеру будут назначены заказы, но до того, как курьер выполнит хотя бы один, он будет изменен PATCH запросом на /couriers/{courier_id} таким образом, что все заказы из назначенного развоза не смогут быть выполнены. В таком случае развоз будет просто удален и не пойдет в зачем при расчете заработка.

4.  ### Возобновление работы приложения после перезагрузки серврера

    После перезагрузки сервера приложение возобновляет свою работу в случае, если docker демону прописан автозапуск (по умолчанию на большинстве ОС).