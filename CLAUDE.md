# Project

React 19 + Vite 8 + Tailwind CSS 4 + TypeScript. Package manager: npm.

```
npm run dev      # vite, port 5173
npm run build
npm run lint     # oxlint
```

Path alias `@/` -> `src/`.

---

## UI components — MANDATORY WORKFLOW

The `shadcn` MCP server is configured in `.mcp.json` and the `@react-bits`
registry is declared in `components.json`. It is available in every session.
Use it.

Before writing **any** visual component, animation, background, text effect,
card, loader, cursor effect or transition from scratch:

1. **Search `@react-bits` first** via the shadcn MCP
   (`search_items_in_registries`, then `view_items_in_registries`).
   This is not optional and not conditional on how simple the task looks.
2. If a matching or near-matching component exists — install it with the MCP
   `get_add_command_for_items` output, then **adapt** it (props, colors,
   sizing, copy). Do not reimplement it by hand.
3. Only if nothing relevant exists — write custom code, and say explicitly in
   your reply: `registry: no match for <query>`.

**Never skip step 1.** If you catch yourself writing a `motion.div` with a
hand-rolled animation, stop and search the registry instead.

### Registry usage notes

- Registry name is `@react-bits`. Query it with plain words: `blur text`,
  `particles background`, `magnet button`, `dock`, `aurora`.
- Search with 2-3 different phrasings before concluding there is no match.
  Single-query misses are the usual failure mode.
- ReactBits components land in `src/components/` — check the file after
  install, they often ship their own local deps (`ogl`, `gsap`).
- `ogl` and `gsap` are already in `package.json`. Do not swap a component's
  animation library for another one.

### Stack rules

- Tailwind v4: config lives in `src/index.css` via `@theme`. There is no
  `tailwind.config.js` — do not create one.
- Animation: `framer-motion` (v12) or `gsap` — both installed. No new libs
  without asking.
- Icons: `lucide-react` only.
- Class merging: `cn()` from `@/lib/utils`.
- Base UI (`@base-ui/react`) for primitives (dialog, popover, select).

### Aesthetic default

Dark, minimal, high-contrast. No generic icon-grid layouts, no default
system font stack — Geist Variable is loaded. Prefer custom SVG / geometric
shapes over stock icon decoration.

---

## Code style

- Opening and closing braces on their own lines.
- Blank line between logical blocks.
- No abstraction into helper functions unless it is used 3+ times.
