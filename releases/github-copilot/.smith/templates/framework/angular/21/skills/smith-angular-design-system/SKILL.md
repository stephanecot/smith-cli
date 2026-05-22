---
name: smith-angular-design-system
description: Unified design system — Tailwind v4, reusable UI primitives, no duplicate CSS, no custom CSS in feature components, centralised theme tokens.
---


# Skill — Design system (single source of UI truth)

Mission: **zero CSS duplication, zero custom CSS or class inside feature components**. Every visual element is either a Tailwind utility composition or a design-system component.

## Smith Editorial Idiom

The Smith DS follows a deliberate editorial / kiosque aesthetic — NOT generic SaaS.

### Typography
- **Display (Fraunces)** — editorial headings: `<h1 class="display">`, big numerals `<ds-number>`. 300/400/500/600 + italic.
- **UI (Instrument Sans)** — body text, labels. 400/500/600.
- **Mono (JetBrains Mono)** — all labels, codes, tracked uppercase metadata. 400/500.

Typography utility classes (global, in `styles.scss`):
- `.label` — mono 0.6875 rem, 0.18 em tracked, uppercase, `text-dim`. **Always** use `<ds-label>` in templates.
- `.num` — Fraunces tabular, -0.04 em tracked. **Always** use `<ds-number>` in templates.
- `.display` — Fraunces 600 italic, -0.02 em tracked, line-height 0.96. Apply on `h1`/`h2` with `class="display"`.
- `.frame` — max-width: 88rem, centered, 2 rem horizontal padding.

### Decorative motifs
- **◇ Brandmark** — only via `<ds-brand>`. Never inline in feature templates.
- **Grain overlay** — SVG fractal noise, global via `body::before`. No per-component grain.
- **Radial gradients** — atmospheric, global via `body` background.
- **Accent glow** — `filter: drop-shadow(0 0 12px var(--color-accent-glow))` for brand mark only.
- **Dashed borders** for vitals / section separators — `<ds-divider variant="dashed">`.
- **Accent left-border** on active nav items — `border-l-2 border-accent`.
- **Animated pulse** on live indicators only. Honour `prefers-reduced-motion`.

### Palette

Dark (default):
```
bg-page:     #0a0d18   bg-elevated: #11162a   bg-deep: #06080f
text:        #ece6d5   text-dim: rgba(236,230,213,0.62)
text-faint:  rgba(236,230,213,0.32)   text-ghost: rgba(236,230,213,0.12)
rule:        rgba(236,230,213,0.18)
accent:      #e85d2c   accent-deep: #b8400e   accent-glow: rgba(232,93,44,0.35)
spark:       #f4c23a   moss: #8aa67b   rust: #c4493a   steel: #5b7a99
on-accent:   #0a0d18
```
Light (`[data-theme="light"]`):
```
bg-page:     #f4ede0   bg-elevated: #ebe2d0   bg-deep: #e3d9c5
text:        #1a1612   accent: #d44b1e
```

## Layout

```
frontend/src/app/design-system/
├── components/
│   ├── brand/          ds-brand           ◇ + SMITH wordmark + edition
│   ├── button/         ds-button          primary/outline/ghost/danger; square/circle/pill
│   ├── card/           ds-card            plain/ruled/dashed-top/outlined
│   ├── divider/        ds-divider         solid/dashed, optional inline label
│   ├── form-field/     ds-form-field      label (via ds-label) + hint + error
│   ├── icon/           ds-icon            curated SVG set
│   ├── input/          ds-input           ControlValueAccessor, flat 2 px radius
│   ├── label/          ds-label           .label class + optional withRule filler
│   ├── link/           ds-link            router/external, styled
│   ├── number/         ds-number          Fraunces tabular stat; md/lg/xl
│   ├── pill/           ds-pill            pill border chip, interactive or display
│   ├── stat-tile/      ds-stat-tile       vital dashed-top + label + number + optional aside
│   ├── tag/            ds-tag             flat 2 px chip; accent/moss/rust/spark/steel/neutral
│   └── theme-toggle/   ds-theme-toggle    the only place that flips data-theme
└── index.ts            public barrel — import ONLY from here
```

## Theme tokens — one place, two themes

Tokens are **semantic** (purpose-named, not colour-named), in `frontend/src/styles.scss`. Both themes use the same token names; the palette swaps via `[data-theme]` on `<html>`. Tailwind `@theme` block registers them as utilities (`bg-bg-page`, `text-accent`, etc.).

```scss
@use "tailwindcss";

@theme {
  --color-bg-page:      #0a0d18;
  --color-text:         #ece6d5;
  --color-text-dim:     rgba(236, 230, 213, 0.62);
  --color-text-faint:   rgba(236, 230, 213, 0.32);
  --color-text-ghost:   rgba(236, 230, 213, 0.12);
  --color-rule:         rgba(236, 230, 213, 0.18);
  --color-accent:       #e85d2c;
  --color-spark:        #f4c23a;
  --color-moss:         #8aa67b;
  --color-rust:         #c4493a;
  --color-steel:        #5b7a99;
  /* … full token set in styles.scss … */
  --font-display:       "Fraunces", serif;
  --font-sans:          "Instrument Sans", system-ui, sans-serif;
  --font-mono:          "JetBrains Mono", "SF Mono", Menlo, monospace;
  --radius-tag:         2px;
  --radius-pill:        999px;
  --grid:               88rem;
  --gutter:             2rem;
}
```

Rules:
- **Semantic only**. Never `--color-blue-500`. Names describe roles.
- **Both themes are first-class**. Every token needs a light-theme override.
- **Feature consumption via Tailwind classes only** — `bg-bg-page`, `text-text-dim`, `text-accent`. Features never reference `var(--color-*)` directly.
- A `<ds-theme-toggle>` primitive is the **only** place that flips `data-theme`.

## Primitive catalog (14 total)

### Restyled primitives

| Primitive | Selector | Key signal inputs | Notes |
|---|---|---|---|
| `DsButtonComponent` | `ds-button` | `variant: 'primary'\|'outline'\|'ghost'\|'danger'\|'secondary'`, `size: 'sm'\|'md'\|'lg'`, `shape: 'square'\|'circle'\|'pill'`, `disabled`, `ariaLabel`, `type` | `secondary` aliases `outline` (back-compat). Editorial: flat 2 px radius on `square`. |
| `DsCardComponent` | `ds-card` | `variant: 'plain'\|'ruled'\|'dashed-top'\|'outlined'`, `padding: 'none'\|'sm'\|'md'\|'lg'`, `outlined` (deprecated) | Default `plain` — no opaque fill. |
| `DsInputComponent` | `ds-input` | `type`, `placeholder`, `autocomplete`, `inputId`, `ariaDescribedBy`, `ariaInvalid` | ControlValueAccessor. Flat 2 px radius, transparent bg. |
| `DsFormFieldComponent` | `ds-form-field` | `label` (req), `fieldId` (req), `hint`, `error`, `required` | Label rendered via `<ds-label>`. |
| `DsIconComponent` | `ds-icon` | `name` (req), `size`, `ariaLabel` | Curated SVG set: sun/moon/menu/close/check/alert/logout/user/home/folder/shield/arrow-right/diamond. |
| `DsLinkComponent` | `ds-link` | `to`, `href`, `external`, `variant: 'default'\|'subtle'\|'accent'` | Router/external, accent bottom-border on hover. |
| `DsThemeToggleComponent` | `ds-theme-toggle` | none | Only theme-flipping primitive. Round 2.5 rem. |

### New editorial primitives

| Primitive | Selector | Key signal inputs | Slots | Notes |
|---|---|---|---|---|
| `DsLabelComponent` | `ds-label` | `withRule: boolean` | default | Renders `.label` span. `withRule=true` adds 1 px accent filler. |
| `DsNumberComponent` | `ds-number` | `size: 'md'\|'lg'\|'xl'` | default | Fraunces tabular stat; md=1.5rem, lg=3rem, xl=5rem. |
| `DsDividerComponent` | `ds-divider` | `variant: 'solid'\|'dashed'` | default (optional inline label) | Horizontal rule with optional centered label slot. |
| `DsTagComponent` | `ds-tag` | `tone: 'accent'\|'moss'\|'rust'\|'spark'\|'steel'\|'neutral'` | default | Flat 2 px chip, mono uppercase. Roles, statuses, action types. |
| `DsPillComponent` | `ds-pill` | `ariaLabel`, `interactive: boolean` | default, `[slot=avatar]` | Pill border chip. `interactive=true` → `<button>`, emits `pillClick`. |
| `DsBrandComponent` | `ds-brand` | `compact: boolean` | none | ◇ glyph + SMITH wordmark + edition. `compact` hides edition. |
| `DsStatTileComponent` | `ds-stat-tile` | `label` (req), `vital: boolean`, `callout?` | `[slot=value]` (ds-number), `[slot=aside]` | Vital stat tile. `vital=true` → dashed top border. |

Every primitive: standalone, OnPush, signal-based inputs/outputs, `templateUrl` only, variant API via input signals (never via class strings from outside).

## Iron rules

1. **Feature components import only design-system components for UI primitives**. Tailwind utilities are fine for *layout glue* (`flex`, `gap-4`, `grid-cols-3`, `mt-6`) — never to restyle a primitive.
2. **No custom CSS classes** in feature components. `.scss` files in features are forbidden.
3. **No re-implementation**. If a primitive doesn't exist, build it in `design-system/` and reuse it.

### Forbidden patterns (editorial idiom guardrails)

- **`rounded-md` / `rounded-lg` on buttons or cards** — editorial buttons are flat (`rounded-[2px]`). Use `<ds-button>` / `<ds-card>` instead.
- **Opaque `bg-bg-elevated` as default card fill** — cards are `plain` (transparent) by default.
- **Ad-hoc label re-implementation** — never `class="text-xs uppercase tracking-widest text-text-dim font-mono"` in a feature template. Use `<ds-label>`.
- **Ad-hoc stat re-implementation** — never `class="text-5xl font-semibold tabular-nums"` for a big number. Use `<ds-number size="lg">` + `<ds-label>`.
- **Ad-hoc role badge** — never `<span class="inline-flex items-center px-2 rounded ...">`. Use `<ds-tag tone="accent">ADMIN</ds-tag>`.
- **Raw `<button>` for mock-user pills** — use `<ds-pill [interactive]="true" (pillClick)="...">`.
- **Hardcoded `text-xs uppercase tracking-[0.24em]`** in feature headers — wrap with `<ds-label>`.

## Reuse-check workflow

Before any UI work: open `frontend/src/app/design-system/index.ts` (all 14 primitives listed). Find the closest, use it. If a variant is missing, **extend the primitive** (add a value to its `variant` input). Don't fork. If no primitive matches, design one in `design-system/`.

## Accessibility & responsive

WCAG 2.2 AA + responsive baselines apply (focus-visible, ≥ 44 px hit targets, semantic HTML, `prefers-reduced-motion`, `prefers-color-scheme`, fluid layout from 360 px) — see `.claude/rules/angular/code-quality.md`. The DS primitives ship those defaults; features compose, never override.

## Icon mapping for textual buttons

When adding an icon to a `<ds-button>` with a textual label, use the following canonical mapping. **Always verify the slug exists in `DsIconName`** (`ds-icon.component.ts`). If the primary slug is missing, use the listed fallback. If neither exists, leave the button without an icon (do not add missing slugs unless they are in this list and genuinely needed).

| Verb / action | `icon` value | Fallback |
|---|---|---|
| Add (member, item) | `plus` | — |
| Save / Apply / Validate | `check` | — |
| Cancel / Close | `close` | — |
| Refresh / Reload | `refresh` | — |
| Detach / Unlink | `close` | — |
| Configure / Settings | `wrench` | — |
| Verify / Probe | `search` | `sparkles` |
| Attach / Link | `check` | — |
| Agentify | `sparkles` | — |
| Copy | `copy` | — |
| Edit / Modify | `wrench` | — |
| Delete / Remove | `close` | — |
| Sign in | `arrow-right` | — |
| Sign out (logout) | `logout` | `arrow-right` |
| Submit / Send | `check` | — |
| Promote (admin) | `chevron-up` | — |
| Demote | `chevron-down` | — |
| Search (standalone) | `search` | — |
| Navigate → Next | `chevron-right` | `arrow-right` |
| Navigate ← Previous | `chevron-left` | — |

**Implementation notes:**
- `plus`, `refresh`, `search`, `chevron-up` were added in feature 004 US4 (T091).
- `chevron-left`, `chevron-right` were added in feature 002 (breadcrumb).
- `logout` (not `log-out`) is the canonical slug in `DsIconName`.
- Icon-only buttons (`shape="circle"`) should use `ariaLabel` only — do not set the `icon` input on them.

## Done criteria

A UI change is complete when:

1. No `.scss` added to a feature folder.
2. No Tailwind class string duplicated across two feature templates for a primitive concern.
3. Every interactive element uses a `<ds-*>` primitive.
4. `ng build` clean, `ng test --watch=false` green, `npm run i18n:check` zero drift.
5. Works at 360 / 768 / 1024 / 1440 px without document-level horizontal scroll.
6. `prefers-reduced-motion` and `prefers-color-scheme` respected.
