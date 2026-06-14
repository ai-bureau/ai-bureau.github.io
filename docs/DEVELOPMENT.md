# Разработка

## Требования

- Python 3.10+
- Git
- WSL/Bash для локального Hugo-скрипта
- доступ к интернету для API и зависимостей

Hugo и GitHub CLI установлены локально в `.tools/` и не коммитятся.

## Клонирование

Из-за PaperMod submodule:

```bash
git clone --recurse-submodules https://github.com/ai-bureau/ai-bureau.github.io.git
```

Если репозиторий уже клонирован:

```bash
git submodule update --init --recursive
```

## Python-окружение

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Тесты

```bash
python -m pytest
```

Покрыты:

- повторы transient API errors;
- парсинг актуального Notion Data Source API;
- Hugo Markdown renderer;
- нормальная публикация;
- коллизия slug;
- восстановление после частичного сбоя;
- отказ GitHub без изменения Notion;
- dry-run;
- транслитерация slug.

## Fresh Hugo build

Проверяй в пустом каталоге, чтобы старые файлы `public/` не скрыли проблему:

```bash
destination=$(mktemp -d /tmp/ai-bureau-build-XXXXXX)
.tools/hugo/hugo --gc --minify --destination "$destination"
```

## Локальный сервер

```bash
./start-site.sh
```

Из Windows:

```powershell
.\start-site.bat
```

## Изменение статических страниц

- Украинские страницы: `content/uk/`
- Английские страницы: `content/en/`
- Главное меню: `hugo.toml`
- Главная: `layouts/home.html`
- Статья: `layouts/single.html`
- Стили: `assets/css/extended/bureau.css`

После изменений проверь обе языковые версии и мобильный viewport.

## Изменение публикатора

Сохраняй порядок:

```text
получить → валидировать → отрендерить UA+EN → проверить пути → один commit GitHub → update Notion
```

Не меняй порядок GitHub/Notion без отдельного анализа согласованности.

Новое поведение должно иметь тест. Внешние API в unit-тестах заменяются fake
sessions/gateways; тесты не должны писать в реальный Notion или GitHub.

## Проверки перед commit

```bash
python -m pytest
python -m compileall -q publisher tests
git diff --check
```

Затем свежая Hugo-сборка и, при необходимости, dry-run.

## PaperMod

Тема подключена submodule и закреплена на конкретном commit. Не редактируй
файлы внутри `themes/PaperMod`. Переопределения размещай в корневых `layouts/`
и `assets/`.
