## Инструкция по запуску
- убедитесь, что у вас установлены docker и docker compose
- склонируйте репозиторий и перейдите в директорию проекта
- запустите проект:
```bash
docker compose up -d
```
- приложение будет доступно по адресу http://localhost:8000
- документация API Swagger UI: http://localhost:8000/docs
- документация API ReDoc: http://localhost:8000/edoc
- токен авторизации X-API-KEY: x
- показать логирование:
```bash
docker compose logs -f
```
- остановить проект:
```bash
docker compose down -v
```
