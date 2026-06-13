# Эксплуатация

## Сервисы и адреса

- Сайт: <https://ai-bureau.github.io/>
- Репозиторий: <https://github.com/ai-bureau/ai-bureau.github.io>
- Actions: <https://github.com/ai-bureau/ai-bureau.github.io/actions>
- Основная ветка: `main`
- Pages source: GitHub Actions
- HTTPS: включён

## Обычный запуск публикатора

```powershell
python -m publisher --env-file actual.env --dry-run
python -m publisher --env-file actual.env
```

Публикатор выполняет один проход и завершается. Рекомендуемая текущая модель —
ручной запуск раз в сутки или сразу после одобрения статьи.

## Exit codes

- `0` — запуск завершён без ошибок, включая случай отсутствия статей;
- `1` — ошибка инициализации или хотя бы одной статьи.

## Deployment сайта

Каждый push в `main` запускает workflow `Build and deploy`.

Workflow можно запустить вручную:

```bash
.tools/gh/bin/gh workflow run hugo.yaml --repo ai-bureau/ai-bureau.github.io
```

Проверка:

```bash
.tools/gh/bin/gh run list --repo ai-bureau/ai-bureau.github.io --workflow hugo.yaml
```

## Проверка после deployment

```bash
curl -L -s -o /dev/null -w '%{http_code}\n' https://ai-bureau.github.io/
curl -L -s -o /dev/null -w '%{http_code}\n' https://ai-bureau.github.io/en/
curl -L -s -o /dev/null -w '%{http_code}\n' https://ai-bureau.github.io/blog/
```

Ожидаемый ответ: `200`.

## Логи

Публикатор пишет:

```text
logs/publisher_YYYY-MM-DD.log
```

Логи не коммитятся. Для расследования сохрани нужный файл отдельно до очистки
рабочей папки.

## Восстановление после частичного сбоя

### GitHub-файл не создан

Notion остаётся `Публікувати`. Исправь причину и повтори запуск.

### GitHub-файл создан, Notion не обновился

Повтори запуск. Публикатор сравнит существующий файл с детерминированно
сгенерированным содержимым, не создаст `-2` и обновит Notion.

### Actions упал

Файл и статус Notion уже могут быть опубликованы. Исправь workflow или Hugo,
затем перезапусти Actions. Не создавай статью повторно.

### Нужно убрать статью

Автоматического unpublish нет. Требуется отдельное подтверждённое действие:

1. удалить или изменить Markdown в GitHub;
2. дождаться deployment;
3. согласованно исправить статус Notion.

## Резервирование

GitHub хранит историю сайта и опубликованных файлов. Notion хранит контентный
pipeline. Рекомендуется периодически экспортировать страницу проекта и базы
Notion, особенно перед изменением схемы.

## Обновления зависимостей

Перед обновлением Hugo, PaperMod, GitHub Actions или Python-зависимостей:

1. изучить официальные release notes;
2. обновить закреплённую версию;
3. запустить тесты и свежую Hugo-сборку;
4. проверить локальный сайт;
5. выполнить push и проверить публичные маршруты;
6. обновить `CHANGELOG.md`.

