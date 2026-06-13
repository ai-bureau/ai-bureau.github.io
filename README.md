# AI Bureau

Двуязычный сайт AI Bureau и публикатор одобренных статей из Notion.

## Архитектура

```text
Тезисы Notion
    ↓
Codex вручную ищет подтверждающие статьи
    ↓
Таблица «Статьи» в Notion
    ↓ статус «Публікувати»
Python publisher
    ↓ GitHub Contents API
Hugo + GitHub Actions
    ↓
ai-bureau.github.io
```

### Сайт

- Hugo Extended `0.163.1`
- PaperMod, закреплённый на конкретном commit
- украинский раздел: `content/uk/`
- английский раздел: `content/en/`
- GitHub Pages workflow: `.github/workflows/hugo.yaml`

### Публикатор

Публикатор выполняет один проход и завершается:

1. Запрашивает в Notion статьи со статусом `Публікувати` и пустым полем `Опубліковано`.
2. Проверяет обязательные поля и пропускает невалидные карточки.
3. Получает названия связанных тезисов.
4. Генерирует Hugo Markdown.
5. Подбирает свободный slug в GitHub.
6. Создаёт файл через GitHub Contents API.
7. Только после успешного GitHub-коммита меняет статус Notion на `Опубліковано`.

Если GitHub-коммит прошёл, но Notion временно не обновился, следующий запуск узнает
идентичный файл и завершит обновление Notion без создания дубликата.

## Модули публикатора

- `publisher/config.py` — загрузка и валидация `.env`
- `publisher/notion_gateway.py` — актуальный Notion Data Source API
- `publisher/github_gateway.py` — GitHub Contents API
- `publisher/renderer.py` — Hugo Markdown и front matter
- `publisher/slug.py` — транслитерация и slug
- `publisher/service.py` — порядок публикации и идемпотентность
- `publisher/http.py` — повтор внешних запросов

## Команды

```bash
# Локальный сайт
./start-site.sh

# Один проход публикатора
python -m publisher

# Проверка без записей в GitHub и Notion
python -m publisher --dry-run

# Использовать другой env-файл
python -m publisher --env-file actual.env --dry-run

# Тесты
python -m pytest

# Production-сборка сайта
.tools/hugo/hugo --gc --minify --cleanDestinationDir
```

Подробная настройка описана в [HOW_TO_USE.md](HOW_TO_USE.md).
