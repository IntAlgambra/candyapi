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