# AI Bureau

AI Bureau — двуязычный сайт бюро и контентная система, которая связывает
Notion, ручной поиск подтверждающих материалов, Python-публикатор, GitHub и
Hugo.

> Машини повинні працювати. Люди повинні думати.

## Текущее состояние

- Публичный сайт: <https://ai-bureau.github.io/>
- Репозиторий: <https://github.com/ai-bureau/ai-bureau.github.io>
- Основная ветка: `main`
- GitHub Pages: GitHub Actions workflow
- Основной язык сайта: украинский
- Второй язык: английский
- Поиск статей: вручную с помощью Codex
- Одобрение публикации: статус `Публікувати` в Notion
- Запуск публикатора: вручную, один проход за запуск
- Полный цикл `Notion → GitHub → Hugo → сайт` проверен 13 июня 2026 года

## Назначение проекта

AI Bureau помогает находить интеллектуальную рутину в рабочих процессах и
передавать её проверяемым AI-системам. Контент сайта объясняет эту позицию и
подтверждает её материалами авторитетных авторов.

Проект состоит из трёх частей:

1. **Поиск статей.** Codex вручную ищет материалы, подтверждающие тезисы AI
   Bureau, проверяет релевантность и добавляет карточки в Notion.
2. **Публикатор.** Python-скрипт публикует только явно одобренные статьи.
3. **Сайт.** Hugo собирает двуязычный статический сайт, GitHub Actions
   публикует его на GitHub Pages.

## Общий поток

```text
Тезисы в Notion
    ↓
Codex вручную ищет и проверяет статьи
    ↓
Статьи в Notion: Знайдена → На review → Публікувати
    ↓
python -m publisher --env-file actual.env
    ↓
Markdown-коммит в GitHub через Contents API
    ↓
GitHub Actions собирает Hugo
    ↓
https://ai-bureau.github.io/
    ↓
Статус статьи в Notion: Опубліковано
```

## Быстрый старт

### Проверить сайт локально

Из Windows PowerShell:

```powershell
.\start-site.bat
```

Открыть <http://localhost:1313/>. Остановка: `Ctrl+C`.

### Проверить готовые публикации без изменений

```powershell
python -m publisher --env-file actual.env --dry-run
```

### Опубликовать одобренные статьи

```powershell
python -m publisher --env-file actual.env
```

Или:

```powershell
.\start-publisher.bat
```

### Запустить тесты

```powershell
python -m pytest
```

## Структура репозитория

```text
.
├── .github/workflows/hugo.yaml   # сборка и деплой GitHub Pages
├── assets/css/extended/          # фирменные стили поверх PaperMod
├── content/
│   ├── uk/                       # украинский контент
│   └── en/                       # английский контент
├── docs/                         # подробная документация
├── layouts/                      # собственные Hugo-шаблоны
├── publisher/                    # Python-публикатор
├── tests/                        # автоматические тесты публикатора
├── themes/PaperMod/              # Git submodule темы
├── hugo.toml                     # конфигурация сайта
├── actual.env                    # реальные секреты, не хранится в Git
├── start-site.bat                # локальный сайт из Windows
└── start-publisher.bat           # один запуск публикатора
```

## Ключевые гарантии публикатора

- Публикуются только записи со статусом `Публікувати`.
- Уже опубликованные записи не выбираются повторно.
- Notion обновляется только после успешного GitHub-коммита.
- Повторный запуск распознаёт уже созданный идентичный файл и не создаёт
  дубликат.
- Коллизии slug получают суффиксы `-2`, `-3` и далее.
- Будущая `Дата публікації` создаёт файл сразу, но Hugo скрывает статью до даты.
- Невалидная карточка пропускается и не блокирует остальные.
- Ошибки записываются в ежедневный лог.

## Документация

- [HOW_TO_USE.md](HOW_TO_USE.md) — ежедневная инструкция владельца
- [AGENTS.md](AGENTS.md) — обязательные правила для AI-агентов
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — техническая архитектура
- [docs/CONTENT_WORKFLOW.md](docs/CONTENT_WORKFLOW.md) — поиск и публикация контента
- [docs/NOTION_SCHEMA.md](docs/NOTION_SCHEMA.md) — точная схема Notion
- [docs/OPERATIONS.md](docs/OPERATIONS.md) — эксплуатация и восстановление
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — разработка и тестирование
- [docs/SECURITY.md](docs/SECURITY.md) — секреты и разрешения
- [docs/DECISIONS.md](docs/DECISIONS.md) — принятые решения и причины
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — диагностика проблем
- [CHANGELOG.md](CHANGELOG.md) — история значимых изменений

## Источники требований

Исходные технические задания сохранены для истории:

- [tz-ai-bureau-site.md](tz-ai-bureau-site.md)
- [tz-codex-article-finder.md](tz-codex-article-finder.md)

Фактическая работа системы и документы в `docs/` имеют приоритет над старыми
формулировками ТЗ, если они расходятся.
