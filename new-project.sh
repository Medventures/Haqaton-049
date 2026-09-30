#!/usr/bin/env bash
#
# new-project — создаёт новый ПРИВАТНЫЙ проект из ПРИВАТНОГО шаблона.
#
# Установка (один раз на машине):
#   mkdir -p ~/bin
#   cp new-project.sh ~/bin/new-project && chmod +x ~/bin/new-project
#   echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
#
# Использование:
#   new-project frost-hack
#
set -euo pipefail

# ↓↓↓ ПОМЕНЯЙ НА СВОЙ ↓↓↓
TEMPLATE_REPO="${TEMPLATE_REPO:-Arturptr/hackathon-template}"

NAME="${1:-}"

if [ -z "$NAME" ]
then
    echo "usage: new-project <имя-проекта>"
    exit 1
fi

if [ -e "$NAME" ]
then
    echo "папка '$NAME' уже существует"
    exit 1
fi

# gh — единственное место, где нужна авторизация. Приватный шаблон без неё не скачается.
if ! command -v gh >/dev/null 2>&1
then
    echo "gh не установлен: https://cli.github.com"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1
then
    echo "не авторизован в GitHub, запускаю логин..."
    gh auth login
fi

echo "создаю приватный репозиторий '$NAME' из $TEMPLATE_REPO ..."
gh repo create "$NAME" --template "$TEMPLATE_REPO" --private --clone

cd "$NAME"

# подставляем имя проекта в package.json
node -e "
  const fs = require('fs');
  const p = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  p.name = process.argv[1].toLowerCase().replace(/[^a-z0-9-]/g, '-');
  fs.writeFileSync('package.json', JSON.stringify(p, null, 2) + '\n');
" "$NAME"

git add package.json
git commit -q -m "init: $NAME"
git push -q

echo ""
echo "готово: $(pwd)"
echo "дальше: code . → F1 → Reopen in Container → cc"

if command -v code >/dev/null 2>&1
then
    code .
fi
