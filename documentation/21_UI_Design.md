# 21 - User Interface Design Modelling

**Project:** CyberGuard AI
**Lab experiment:** 10 - User Interface design modelling

---

## 1. Design goals

| Goal | How it is met |
|------|---------------|
| Read like a Security Operations Centre, not a student CRUD app | Dark navy surfaces, dense information layout, severity-driven colour, monospaced technical values, live activity feed |
| Communicate risk instantly | A single severity colour language used identically in badges, charts, borders and progress bars |
| Never leave the user guessing | Every data view has loading, empty and error states; every action produces a toast |
| Stay honest | Any derived figure states where it came from; simulated data is labelled as simulated |
| Remain accessible | Contrast above WCAG AA, visible focus rings, severity never signalled by colour alone |

---

## 2. Visual language

### 2.1 Colour system

```
SURFACES (dark navy, layered by elevation)
  navy-950  #060b18   page background
  navy-900  #0a1120   panels, sidebar, top bar
  navy-850  #0d1526   hover surface
  navy-800  #111c31   inset surfaces, inputs
  navy-700  #17253f   borders, progress tracks
  navy-600  #1f3050   scrollbar thumb

ACCENT (interactive, informational)
  accent       #22d3ee   cyan - primary actions, links, active nav, focus
  accent-soft  #67e8f9   hover
  info         #38bdf8   informational badges and secondary chart series

SEVERITY (the one semantic scale, used everywhere)
  LOW       #22c55e   green     safe, resolved, operational
  MEDIUM    #f59e0b   amber     warning, investigating, fallback
  HIGH      #fb7185   rose      elevated
  CRITICAL  #dc2626   red       immediate action

TEXT
  slate-100  primary headings and values
  slate-200  body
  slate-300  secondary body
  slate-400  labels and captions
  slate-500  hints
  slate-600  disclaimers
```

**The severity scale is defined exactly once**, in
`frontend/src/utils/format.js`, and consumed by badges, charts, risk bars and
panel borders. Restyling every severity indicator in the product is a change to
one object. This is the UI-layer counterpart of the single-source-of-truth rule
used for the state machine and the severity bands in the backend.

**Neon is used sparingly.** The accent cyan appears on interactive elements and
the active navigation item only. Surfaces are matte; glassmorphism is limited to
a subtle backdrop blur with a 10% white border on panels. The brief's warning
against overusing neon is respected deliberately.

### 2.2 Typography

| Role | Family | Usage |
|------|--------|-------|
| Interface | Inter | All prose, labels, headings |
| Technical | JetBrains Mono | IP addresses, ports, alert and incident codes, scores, timestamps, table identifiers |

Separating the technical font matters operationally: an analyst scanning a column
of IP addresses benefits from fixed-width alignment, and the font change itself
signals "this is a machine value, not prose".

| Size | Weight | Used for |
|------|--------|----------|
| 24px / 1.5rem | 600 | Page titles |
| 20px | 600 | KPI values |
| 14px | 600 | Panel titles |
| 14px | 400 | Body and table cells |
| 12px | 400 | Labels, captions |
| 11px | 500, uppercase, wide tracking | Field labels, KPI labels |

### 2.3 Spacing and layout grid

An 4px base unit throughout. Panels use 20px internal padding, grids a 16px gap.
The content column is capped at 1600px so the layout does not stretch
indefinitely on ultrawide displays.

---

## 3. Layout model

```
+==============================================================================+
| TOP BAR  (64px, sticky, backdrop blur)                                       |
| [menu]  [search................]              [API status] [bell] [avatar v] |
+==========+===================================================================+
|          |                                                                   |
| SIDEBAR  |  CONTENT AREA                                                     |
| 256px    |  max-width 1600px, 24px padding                                   |
| fixed    |                                                                   |
|          |  +-------------------------------------------------------------+  |
| [logo]   |  | PAGE HEADER                                                 |  |
| CyberGuard  | [icon] Title                            [action] [action]   |  |
|          |  | Description                                                 |  |
| Dashboard|  +-------------------------------------------------------------+  |
| Threat   |                                                                   |
|  Detection| +-------------------------------------------------------------+  |
| Alerts   |  | KPI ROW   4 columns >= 1280px, 2 >= 640px, 1 below          |  |
| Incidents|  +-------------------------------------------------------------+  |
| Threat   |                                                                   |
|  Intel   |  +----------------+ +----------------------------------------+    |
| Log      |  | PANEL          | | PANEL (spans 2)                        |    |
|  Analyzer|  | header         | | header                                 |    |
| Assets   |  | body           | | body                                   |    |
| Reports  |  +----------------+ +----------------------------------------+    |
| Settings |                                                                   |
|          |  +-------------------------------------------------------------+  |
|----------|  | TABLE PANEL                                                 |  |
| Engine:  |  | filters bar                                                 |  |
| hybrid-ml|  | table (horizontally scrollable below 720px)                 |  |
|          |  | pagination                                                  |  |
| Academic |  +-------------------------------------------------------------+  |
| prototype|                                                                   |
+==========+===================================================================+
| FOOTER   Academic prototype - all telemetry simulated                        |
+==============================================================================+
```

### 3.1 Responsive behaviour

| Breakpoint | Sidebar | KPI grid | Panels | Tables |
|------------|---------|----------|--------|--------|
| < 640px | Drawer over an overlay | 1 column | Stacked | Scroll within the panel |
| 640-1023px | Drawer | 2 columns | Stacked | Scroll within the panel |
| 1024-1279px | Permanent, 256px | 2 columns | 2 columns | Full width |
| >= 1280px | Permanent | 4 columns | Up to 3 columns | Full width |

Tables scroll **inside their panel**, never causing page-level horizontal
overflow - a common failure mode in dense dashboards on small screens.

---

## 4. Component inventory

All primitives live in `frontend/src/components/ui.jsx` and are composed by every
page. No page re-implements them.

### 4.1 Surfaces

| Component | Purpose |
|-----------|---------|
| `Panel` | The single card primitive: optional title, subtitle, action slot, body |
| `PageHeader` | Icon, title, description, action slot |
| `InfoNote` | Inline note in one of four tones |

### 4.2 Status indicators

| Component | Purpose |
|-----------|---------|
| `SeverityBadge` | Dot + uppercase label, coloured by the severity scale |
| `StatusBadge` | Lifecycle status in title case, colour-coded per state |
| `RiskBar` | 0-100 bar whose colour crosses the severity thresholds, with the numeric value |

### 4.3 Data states

| Component | Purpose |
|-----------|---------|
| `LoadingState` | Centred spinner with a label |
| `SkeletonCard`, `SkeletonTable`, `SkeletonBlock` | Shimmering placeholders matching the final layout |
| `EmptyState` | Icon, title, explanation, optional recovery action |
| `ErrorState` | Distinguishes "backend unreachable" (and shows the start command) from other failures; offers retry |

### 4.4 Inputs and controls

| Component | Purpose |
|-----------|---------|
| `SearchInput` | Search field with a leading icon |
| `Select` | Labelled dropdown |
| `Field` | Label + control + inline error or hint |
| `Pagination` | Range summary and page controls |

### 4.5 Overlays

| Component | Purpose |
|-----------|---------|
| `Modal` | Four sizes; closes on Escape and overlay click; locks body scroll |
| `ConfirmDialog` | Destructive-action confirmation with a busy state |
| Toast system | Four tones, auto-dismiss, stacked, `aria-live` region |

### 4.6 Charts

Seven wrappers in `components/charts/Charts.jsx`, all sharing one tooltip, one
axis style and one grid style: `ThreatsOverTimeChart`, `SeverityDonutChart`,
`CategoryBarChart`, `SourceBarChart`, `DetectionTrendChart`,
`DistributionDonut`, `HourlyBarChart`.

**Every chart is fed from an API response.** No chart contains hard-coded data.

---

## 5. Screen specifications

| # | Screen | Route | Primary components | Data source |
|---|--------|-------|--------------------|-------------|
| 1 | Login | `/login` | Split hero, form, demo account cards | `POST /api/auth/login` |
| 2 | Dashboard | `/dashboard` | 8 KPI cards, threat level, 6 charts, recent alerts, health, activity feed | `GET /api/dashboard/stats` |
| 3 | Threat Detection | `/detection` | Event form, score ring, reason list, sub-score bars, sample loader | `POST /api/events/analyze`, `GET /api/events/sample` |
| 4 | Alerts | `/alerts` | Filter bar, data table, detail modal, confirm dialogs | `GET`/`PUT /api/alerts` |
| 5 | Incidents | `/incidents` | Filter bar, data table, create modal | `GET`/`POST /api/incidents` |
| 6 | Incident Details | `/incidents/:id` | Lifecycle tracker, transition modal, history timeline, linked alerts, related events | `GET`/`PUT /api/incidents/:id` |
| 7 | Threat Intelligence | `/threat-intelligence` | Simulation banner, type cards, indicator table | `GET /api/threat-intelligence` |
| 8 | Log Analyzer | `/log-analyzer` | Drop zone, progress bar, 5 KPI tiles, 2 charts, results table | `POST /api/events/upload` |
| 9 | Assets | `/assets` | Summary tiles, filter bar, table, form modal, confirm dialog | `GET`/`POST`/`PUT`/`DELETE /api/assets` |
| 10 | Reports | `/reports` | Generation form, live preview, report list, content modal | `GET`/`POST /api/reports` |
| 11 | Settings | `/settings` | 5 tabs: profile, notifications, detection, system, audit | `GET /api/system/status`, `PUT /api/auth/*` |
| 12 | Not Found | `*` | Centred 404 with a route back | - |

---

## 6. Interaction design patterns

### 6.1 Feedback for every action

| Action | Immediate feedback | Completion feedback |
|--------|--------------------|---------------------|
| Submit a form | Button shows a spinner and disables | Success or error toast |
| Analyse an event | Button becomes "Analysing..." | Result panel animates in; toast states the verdict |
| Upload a file | Progress bar with a percentage | Summary renders; toast counts the records |
| Change a status | Row action disables | Toast; list refreshes quietly in place |
| Destructive action | Confirmation dialog | Toast; list refreshes |
| Download | Button shows a spinner | Browser download; toast names the file |

### 6.2 The four data states

Every page that loads data implements all four. This is checked in document 19,
test U2.

```
   LOADING              POPULATED            EMPTY                ERROR
   +-----------+        +-----------+        +-----------+        +-----------+
   | ~~~~~~~~  |        | real data |        |   [icon]  |        |  [alert]  |
   | ~~~~~~~~  |   ->   | rendered  |   or   | No alerts |   or   | Backend   |
   | ~~~~~~~~  |        | from the  |        | match     |        | unavail-  |
   | skeleton  |        | API       |        | [Clear    |        | able      |
   |           |        |           |        |  filters] |        | [Retry]   |
   +-----------+        +-----------+        +-----------+        +-----------+
```

The error state distinguishes a backend that is not running - and then shows the
literal commands to start it - from other failures. This turns the most common
demonstration-day problem into a self-correcting one.

### 6.3 Progressive disclosure

Dense information is layered rather than dumped:

- Alerts: table row -> detail modal -> linked incident page.
- Incidents: list -> details with history, alerts and related events.
- Reports: live preview -> generated report modal -> downloadable file.
- Threat Detection: verdict headline -> reasons -> sub-scores -> feature summary.

### 6.4 State-machine-driven controls

On the Incident Details page, the action buttons are generated from the
`allowed_transitions` array the API returns. The user is never offered a control
that would fail. This is the clearest example in the product of the UI being
driven by the domain model rather than duplicating its rules.

---

## 7. Accessibility

| Concern | Implementation |
|---------|----------------|
| Keyboard navigation | All interactive elements are focusable; a global `:focus-visible` ring in accent cyan with an offset |
| Modal behaviour | Escape closes; overlay click closes; body scroll locked while open; `role="dialog"` with `aria-modal` |
| Icon-only buttons | Every one carries an `aria-label` |
| Toggles | `role="switch"` with `aria-checked` |
| Toasts | `role="status"` with `aria-live="polite"` so they are announced without stealing focus |
| Form errors | Inline, adjacent to the field, with `aria-invalid` on the input |
| Colour independence | Every severity badge carries its text label, so meaning never depends on colour alone |
| Contrast | Body text `#e2e8f0` on `#0a1120` is roughly 14:1; all severity colours exceed 4.5:1 on the panel surface |
| Tables | Semantic `<thead>`/`<th>` markup; pagination controls carry labels and `aria-current` |
| Motion | Transitions are 150-300ms and limited to opacity and transform; nothing flashes or auto-plays |

**Not verified:** no automated audit (axe, Lighthouse) and no screen-reader
testing were performed. This is stated in document 19 rather than implied.

---

## 8. UI design principles applied

| Principle | Application |
|-----------|-------------|
| **Consistency** | One panel primitive, one badge system, one table style, one chart tooltip across all twelve screens |
| **Visibility of system status** | Engine mode in the sidebar, API status in the top bar, health panel on the dashboard, progress bar on upload |
| **Match to the real world** | SOC vocabulary throughout: triage, containment, false positive, indicator, MITRE tactic |
| **Error prevention** | Illegal lifecycle transitions are never offered; destructive actions confirm; client-side validation runs before the request |
| **Recognition over recall** | Filter dropdowns are populated from the API; sample scenarios are one click; the search box hints at what it accepts |
| **Aesthetic and minimalist design** | One accent colour; no decorative imagery; every pixel carries information |
| **Help users recover from errors** | Errors name the offending field and say what is acceptable; the backend-down state prints the fix |
| **Flexibility** | Keyboard and mouse paths; filters persist in the URL so views are shareable and survive a refresh |

---

## 9. From wireframe to implementation

| Design decision | Implementing file |
|-----------------|-------------------|
| Colour tokens, fonts, animations | `frontend/tailwind.config.js` |
| Component classes (`.panel`, `.btn-*`, `.data-table`, `.badge`) | `frontend/src/index.css` |
| Severity colours and badge classes | `frontend/src/utils/format.js` |
| Reusable primitives | `frontend/src/components/ui.jsx` |
| Chart wrappers | `frontend/src/components/charts/Charts.jsx` |
| Application shell | `frontend/src/layouts/DashboardLayout.jsx` |
| Toast system | `frontend/src/context/ToastContext.jsx` |
| Screens | `frontend/src/pages/*.jsx` |
