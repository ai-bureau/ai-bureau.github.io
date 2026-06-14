# Диагностика

## `Нових публікацій немає`

Это не ошибка. Проверь:

- есть ли карточка со статусом `Публікувати`;
- пусто ли поле `Опубліковано`;
- работаешь ли ты с правильной базой `Публикации`.

## `Could not find database ... Make sure ... shared with integration`

Notion Public API integration не имеет доступа к базе.

Открой базы `Публикации` и `Тезисы` в Notion и добавь connection
`AI Bureau Publisher`.

Новая база не наследует доступ старой базы `Источники` автоматически. Это
подключение выполняется один раз через меню базы Notion.

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

## `[SKIP] ... must contain exact # UA and # EN sections`

Внутри страницы отсутствуют точные служебные заголовки первого уровня или один
из разделов пуст.

## `[SKIP] ... unsupported Notion block`

В готовом тексте есть блок, который публикатор не умеет безопасно преобразовать.
Замени его поддерживаемыми абзацами, H2/H3, списками, цитатами, ссылками,
divider или code.

## `publication path already contains different content`

Стабильный slug уже занят другим содержимым. Публикатор намеренно не создаёт
`-2`: проверь slug и опубликованные файлы.

## GitHub-файлы появились, статус Notion остался `Публікувати`

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

## `start-publisher.bat` сообщает ошибку

Окно остаётся открытым и показывает exit code. Сначала проверь WSL и dry-run:

```powershell
wsl.exe --cd . python3 -m publisher --env-file actual.env --dry-run
```

Затем проверь свежие записи в `logs/publisher_YYYY-MM-DD.log`. Если лог не
создан, ошибка произошла до запуска Python: обычно недоступен WSL или команда
запущена не из папки проекта.

## В `public/` осталась удалённая статья

`public/` — локальный игнорируемый результат сборки и может содержать старые
файлы. Для достоверной проверки собирай в новый пустой каталог. GitHub Actions
использует свежую среду.

## Где искать подробности

- логи: `logs/publisher_YYYY-MM-DD.log`;
- эксплуатация: [OPERATIONS.md](OPERATIONS.md);
- схема Notion: [NOTION_SCHEMA.md](NOTION_SCHEMA.md);
- безопасность: [SECURITY.md](SECURITY.md).
