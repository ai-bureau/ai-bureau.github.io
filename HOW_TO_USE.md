# Как использовать AI Bureau

## 1. Подготовка Python на Windows

Требуется Python 3.10 или новее.

Открой PowerShell в папке проекта:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Для запуска тестов:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## 2. Настройка Notion

Создай внутреннюю интеграцию Notion и предоставь ей доступ к исходной базе
`Статьи`, а не к связанной копии.

База уже содержит необходимые поля:

- `Заголовок`
- `URL`
- `Мова`: `UA` или `EN`
- `Саммари`
- `Тезиси`
- `Дата додавання`
- `Дата публікації`
- `Опубліковано`
- `Статус`, включая `Публікувати` и `Опубліковано`

Если `Дата публікації` пуста, публикатор использует `Дата додавання`.

## 3. Настройка GitHub

После создания репозитория `ai-bureau/ai-bureau.github.io`:

1. Создай fine-grained personal access token.
2. Предоставь токену доступ к репозиторию и разрешение `Contents: Read and write`.
3. В настройках репозитория открой **Settings → Pages**.
4. Выбери **Source: GitHub Actions**.

## 4. Файл `.env`

Создай `.env` рядом с `.env.example`:

```env
NOTION_TOKEN=secret_...
NOTION_ARTICLES_DATA_SOURCE_ID=882c92e1-9948-42d6-9e7e-a67371630f9f
GITHUB_TOKEN=github_pat_...
GITHUB_REPO=ai-bureau/ai-bureau.github.io
GITHUB_BRANCH=main
RETRY_PAUSE_SEC=60
MAX_RETRIES=3
LOG_DIR=logs
```

`.env` исключён из Git и не должен публиковаться.

## 5. Проверка перед первой публикацией

Запусти:

```powershell
python -m publisher --dry-run
```

Режим проверяет Notion, обязательные поля и выбранные GitHub-пути, но ничего не
коммитит и не меняет в Notion.

## 6. Публикация

В Notion установи статье статус `Публікувати`, затем запусти:

```powershell
python -m publisher
```

Либо:

```powershell
.\start-publisher.bat
```

Публикатор выполнит один проход и завершится. Пока запуск ручной; запускать его
можно раз в сутки или сразу после одобрения статьи.

## 7. Отложенная публикация

Укажи будущее значение в `Дата публікації`. Markdown будет сразу добавлен в
GitHub, но Hugo не покажет статью до указанной даты.

## 8. Диагностика

Логи находятся в:

```text
logs/publisher_YYYY-MM-DD.log
```

Типовые случаи:

- `[SKIP]` — карточка неполная или имеет неподдерживаемый язык.
- `Slug already exists` — выбран путь с суффиксом `-2`, `-3` и далее.
- GitHub ошибка — Notion не изменяется, публикацию можно повторить.
- Notion ошибка после GitHub-коммита — следующий запуск распознает существующий
  идентичный файл и завершит обновление статуса.

## 9. Локальный сайт

Из PowerShell:

```powershell
.\start-site.bat
```

Открой `http://localhost:1313/`. Для остановки нажми `Ctrl+C`.
