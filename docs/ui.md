# UI design system

SignalFlow AI’s dashboard is designed to feel like premium B2B software in the same class as Linear, Stripe, Vercel, and Mercury: quiet confidence, dense when needed, never noisy.

## Design philosophy

- Clean surfaces, slate neutrals, and restrained brand color
- Generous whitespace on an 8pt grid
- Clear hierarchy over decoration
- One job per region: navigation, action, insight, or detail
- Motion only to clarify hierarchy (150–250ms, no bounce)

## Color palette

| Token | Role | Light | Dark |
|-------|------|-------|------|
| Primary | Actions, links | Blue `#2563EB` | Blue `#3B82F6` |
| Accent | Success accents, positive status | Emerald `#10B981` | Emerald `#34D399` |
| Success / Warning / Danger | Semantic feedback | Green / Amber / Red | Same family |
| Neutral | Text, borders, muted chrome | Slate scale | Slate dark |
| Background | App canvas | Almost white `#F8FAFC` | Near black `#020617` |
| Card | Panels | Pure white | Slate `#0F172A` |

Tokens live as CSS variables in `frontend/src/index.css` and are consumed via Tailwind utilities (`bg-background`, `text-muted-foreground`, `border-border`, etc.).

## Typography

- **Font:** Inter (400–700)
- **Body:** 14px / relaxed leading for tables and forms
- **Titles:** semibold, tight tracking, 24–30px page headers
- Avoid decorative display fonts in product UI

## Component system

Reusable primitives under `frontend/src/components/ui` (shadcn-inspired Radix wrappers):

Button, Card, Badge, Input/Textarea, Label, Dialog, Dropdown, Tabs, Switch, Skeleton, Avatar, Toast

Product-level shared components under `frontend/src/components/shared`:

StatCard, SearchBar, EmptyState, ErrorState, ConfirmationDialog, Pagination, Breadcrumb, StatusIndicator, Charts

Layout under `frontend/src/components/layout`:

Sidebar, TopNav, PageHeader

Data hooks: `useDashboardData`, `useBusinessQuery` (TanStack Query keys), `useToast`, `useTheme`.

Product surface documented in [dashboard.md](dashboard.md). Authentication: [auth.md](auth.md).

**Rule:** do not paste one-off Tailwind blocks for controls that already exist in the library.

## Layout & responsive behavior

- Desktop-first shell: persistent sidebar + sticky top nav + scrollable main
- Sidebar collapses to an off-canvas drawer below `lg`
- Tables scroll horizontally instead of crushing columns
- Page content uses 8/16/24/32 spacing steps

## Dark mode

- Class strategy on `<html>` (`.dark`)
- Toggle in the top navigation
- Preference persisted in `localStorage` (`signalflow_theme`)
- All semantic tokens switch with the theme; avoid hard-coded hex in components

## Animation guidelines

- Framer Motion page fades/slides ≈ 180ms ease-out
- Hover/focus transitions ≈ 200ms
- No bounce, no parallax, no ornamental particle effects
- Skeletons for first load; toasts for mutation feedback

## States every view supports

- Loading (skeletons)
- Empty
- Error (with retry where data fetches fail)
- Success content

## Screenshots

Capture light and dark Overview, Calls detail, and Knowledge Base for `docs/images/` and link them from the root README when available.
