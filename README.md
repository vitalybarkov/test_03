## Инструкции по запуску
- Убедитесь, что у вас установлены Docker и Docker Compose
- Клонируйте репозиторий и перейдите в директорию проекта
- Запустите проект:
```bash
docker compose up -d
```
- Приложение будет доступно по адресу http://localhost:8000
- Документация API Swagger UI: http://localhost:8000/docs
- Документация API ReDoc: http://localhost:8000/edoc
- Токен авторизации X-API-KEY: x
- Показать логирование:
```bash
docker compose logs -f
```
- Остановить проект:
```bash
docker compose down -v
```