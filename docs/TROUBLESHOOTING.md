# Диагностика

## `Нових статей для публікації немає`

Это не ошибка. Проверь:

- есть ли карточка со статусом `Публікувати`;
- пусто ли поле `Опубліковано`;
- работаешь ли ты с правильной базой `Статьи`.

## `Could not find database ... Make sure ... shared with integration`

Notion Public API integration не имеет доступа к базе.

Открой базы `Статьи` и `Тезисы` в Notion и добавь connection
`AI Bureau Publisher`.

## GitHub `401 Bad credentials`

`GITHUB_TOKEN` неверен, истёк или отозван.

Создай/получи корректный токен, замени значение в `actual.env`, затем запусти
dry-run.

## GitHub `403`

Токен существует, но не имеет нужного разрешения. Проверь доступ к репозиторию
и `Contents: Read and write`.

## `[SKIP] ... missing`

Карточка `Публікувати` не заполнена. Исправь перечисленные поля и повтори
запуск.

## `[SKIP] ... unsupported language: RU`

Публикатор намеренно принимает только `UA` и `EN`. Измени язык только если
материал действительно соответствует выбранной версии.

## `Slug already exists`

Это предупреждение. Если существующий файл отличается, будет выбран slug с
суффиксом `-2`, `-3` и далее.

Если это неожиданно, проверь дубликаты URL и заголовков в Notion.

## GitHub-файл появился, статус Notion остался `Публікувати`

Повтори обычный запуск. При идентичном содержимом публикатор не создаст новый
файл и завершит обновление Notion.

## Статус `Опубліковано`, но статья не видна

Проверь:

1. `Дата публікації` — возможно, она в будущем.
2. GitHub Actions — возможно, deployment упал.
3. Язык и соответствующий URL блога.
4. Кэш браузера/CDN.

## Actions failed

Открой <https://github.com/ai-bureau/ai-bureau.github.io/actions>.

Локально выполни:

```bash
python -m pytest
destination=$(mktemp -d /tmp/ai-bureau-build-XXXXXX)
.tools/hugo/hugo --gc --minify --destination "$destination"
```

Исправь причину и повторно запусти workflow.

## Локальный `start-site.bat` сразу завершился

Убедись, что WSL установлен и `.tools/hugo/hugo` существует. Из PowerShell
можно проверить:

```powershell
wsl bash ./start-site.sh
```

## В `public/` осталась удалённая статья

`public/` — локальный игнорируемый результат сборки и может содержать старые
файлы. Для достоверной проверки собирай в новый пустой каталог. GitHub Actions
использует свежую среду.

## Где искать подробности

- логи: `logs/publisher_YYYY-MM-DD.log`;
- эксплуатация: [OPERATIONS.md](OPERATIONS.md);
- схема Notion: [NOTION_SCHEMA.md](NOTION_SCHEMA.md);
- безопасность: [SECURITY.md](SECURITY.md).

