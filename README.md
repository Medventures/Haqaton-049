# hackathon-template (приватный)

Devcontainer + Claude Code + shadcn MCP + ReactBits. Шаблон и все проекты из него —
приватные, снаружи не видно ничего.

---

## Настройка (один раз в жизни)

**1. Создай приватный репозиторий-шаблон**

```bash
cd hackathon-template
git init && git add -A && git commit -m "init template"
gh repo create hackathon-template --private --source=. --push
```

**2. Включи флаг шаблона**

`Settings` -> галочка **Template repository** -> Save.
Флаг не делает репо публичным, шаблоном он остаётся только для тебя.

**3. Поставь скрипт-обёртку**

```bash
mkdir -p ~/bin
cp new-project.sh ~/bin/new-project && chmod +x ~/bin/new-project
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

Внутри `new-project` поменяй `TEMPLATE_REPO` на свой `юзер/hackathon-template`.

**4. Авторизуйся в GitHub**

```bash
gh auth login
```

Токен ложится в `~/.config/gh`. На этой машине больше не понадобится.

---

## Каждый хакатон

```bash
new-project frost-hack
```

Скрипт делает: создаёт приватный репо на GitHub из шаблона -> клонирует ->
подставляет имя в `package.json` -> коммитит -> открывает VS Code.

Дальше в VS Code: `F1` -> **Reopen in Container** -> ждёшь сборку -> в терминале `cc`.

Первый раз собирается ~2-3 минуты (тянется образ + npm i -g). Дальше секунды:
образ и named volumes кешируются.

---

## Что видно снаружи

Ничего. Приватный репозиторий отдаёт 404 всем, кроме тебя и приглашённых:
ни кода, ни имени, ни коммитов, ни списка контрибуторов.

Единственный канал утечки — график контрибуций на профиле. По умолчанию он
выключен для приватных репо. Проверь: `Settings` -> `Public profile` ->
`Contributions` -> **Include private contributions on my profile** должно быть
снято. Даже если включено — наружу идут только числа, без имён репозиториев
и коммитов.

Если проект станет публичным потом — откроется вся история git целиком.
Поэтому `.env` в `.gitignore` с самого начала, а не «потом уберу».

---

## Без gh CLI (запасной вариант)

Если `gh` нет и ставить некогда, но SSH-ключ на машине есть:

```bash
git clone --depth=1 git@github.com:ТВОЙ_ЮЗЕР/hackathon-template.git my-project
cd my-project && rm -rf .git && git init
```

`npx degit` с приватным репо **не работает** — он ходит без авторизации.

---

## Что здесь исправлено

**1. `@latest` больше не резолвится в рантайме.**
`shadcn` ставится глобально в образ с пином версии (`Dockerfile`, ARG
`SHADCN_VERSION`), а `.mcp.json` вызывает голый бинарник `shadcn mcp` — без
`npx`. Ни сети, ни кеша, ни гонки с `npm install`.

**2. Логины переживают пересборку и новые проекты.**
Named volumes `claude-code-home`, `gh-config`, `npm-cache` общие для всех
проектов из шаблона. Логинишься один раз, а не на каждом хакатоне.

**3. MCP подключается сам.**
`.mcp.json` в корне (project scope) + `enableAllProjectMcpServers: true` в
`.claude/settings.json`.

**4. `components.json` содержит реестр `@react-bits`.**
Без него MCP видит только базовый shadcn-реестр.

**5. `CLAUDE.md` заставляет искать в реестре до написания кода.**

---

## Проверка после первого запуска

```
/mcp          # внутри claude — shadcn должен быть connected
```

Пусто -> `shadcn mcp --help` в терминале контейнера и `cat .mcp.json`.

## Обновить версию shadcn

`.devcontainer/Dockerfile` -> `ARG SHADCN_VERSION=` -> Rebuild Container.
Потом закоммить в шаблон — новые проекты подхватят.
