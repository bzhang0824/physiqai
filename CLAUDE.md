# CLAUDE.md — PhysiqAI Coding Instructions

## What Is This Project?

PhysiqAI is an AI "Virtual Mirror" that shows users their realistic future physique based on their workout plan, genetics, and time horizon. Users upload a photo, enter their stats and workout plan, and get a hyper-realistic transformation image.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript (strict)
- **Styling:** Tailwind CSS + shadcn/ui
- **State:** Zustand with sessionStorage persistence
- **Validation:** Zod schemas
- **AI:** fal.ai Flux Kontext Pro (image gen), Gemini (analysis)

## Key Documentation

Before coding, READ these files in order:
1. `docs/PRD.md` — What we're building and why
2. `docs/APP_FLOW.md` — User journey and screens
3. `docs/TECH_STACK.md` — Technology decisions
4. `docs/FRONTEND_GUIDELINES.md` — Component patterns and styling
5. `docs/BACKEND_STRUCTURE.md` — API endpoints and logic
6. `docs/IMPLEMENTATION_PLAN.md` — Build order and checklist

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── api/               # API routes
│   └── transform/         # Multi-step form flow
├── components/
│   ├── ui/                # shadcn/ui components
│   └── transform/         # Feature-specific components
├── lib/                   # Utilities, store, API clients
└── styles/                # Global CSS
```

## Environment Variables

Required in `.env.local`:
```
FAL_KEY=           # fal.ai API for Flux Kontext Pro
GOOGLE_AI_KEY=     # Gemini API for photo analysis
```

## Coding Standards

### TypeScript
- Strict mode enabled
- No `any` types — define proper interfaces
- Use Zod for runtime validation

### Components
- Functional components only
- Use shadcn/ui patterns
- Keep components focused (single responsibility)
- Extract reusable logic to hooks

### State Management
- Zustand store in `lib/store.ts`
- Persist to sessionStorage (no auth = no server state)
- Validation via Zod before API calls

### Styling
- Tailwind utility classes
- Dark theme default (see FRONTEND_GUIDELINES.md for colors)
- Mobile-first responsive design

### API Routes
- Validate all inputs with Zod
- Return consistent response shape: `{ success, data?, error? }`
- Handle errors gracefully with useful messages

## Current Progress

Check `progress.txt` for completed/remaining tasks.

## Common Commands

```bash
# Development
pnpm dev

# Type check
pnpm tsc --noEmit

# Lint
pnpm lint

# Build
pnpm build
```

## Important Notes

1. **No auth for MVP** — Store data in browser only
2. **Single photo for MVP** — Front-facing only
3. **Generation can be slow** — Good loading states essential
4. **Identity preservation is critical** — Face must remain recognizable
5. **Physiological accuracy matters** — Use the physiology engine, don't guess

## When Stuck

1. Check the relevant doc file first
2. Look at existing similar components
3. Ask — don't guess on product decisions
