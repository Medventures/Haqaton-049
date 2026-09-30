#!/usr/bin/env bash
set -euo pipefail

# Docker создаёт named volume от root — чиним владельца до того, как в них полезут.
sudo chown -R node:node /home/node/.claude /home/node/.npm /home/node/.config/gh 2>/dev/null || true

if [ -f package.json ]; then
    npm install
fi

echo ""
echo "--- environment ---"
node   --version
claude --version || echo "  claude: NOT FOUND"
shadcn --version || echo "  shadcn: NOT FOUND"

if shadcn mcp --help >/dev/null 2>&1; then
    echo "  shadcn mcp: ok"
else
    echo "  shadcn mcp: FAILED — смотри .mcp.json"
fi

if [ -f /home/node/.claude/.credentials.json ] || [ -f /home/node/.claude.json ]; then
    echo "  claude auth: found"
else
    echo "  claude auth: нет — запусти 'claude' и залогинься один раз"
fi

if gh auth status >/dev/null 2>&1; then
    echo "  gh auth: found"
else
    echo "  gh auth: нет — 'gh auth login' (нужен только для push)"
fi
echo "-------------------"
echo ""
echo "start:  cc      (claude --dangerously-skip-permissions)"
echo "resume: ccr"
echo ""
