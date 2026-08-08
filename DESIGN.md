---
name: "Solara Hire"
description: "An editorial evidence workspace for clear, review-first career decisions."
colors:
  paper: "#f2efe7"
  paper-soft: "#faf8f2"
  ink: "#10231f"
  ink-soft: "#4d5e59"
  line: "rgba(16, 35, 31, 0.14)"
  acid: "#cdf86f"
  acid-deep: "#acd94d"
  coral: "#ff8068"
  mint: "#b9ead5"
  night: "#0e2823"
  white: "#fffdf8"
  supported-text: "#365218"
  develop-text: "#7c291c"
typography:
  display:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "clamp(3.2rem, 7vw, 7rem)"
    fontWeight: 500
    lineHeight: 0.94
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "clamp(1.8rem, 3vw, 3rem)"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.035em"
  body:
    fontFamily: "Aptos, Segoe UI Variable, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Aptos, Segoe UI Variable, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 700
    lineHeight: 1.5
  mono:
    fontFamily: "Cascadia Code, SFMono-Regular, Consolas, Liberation Mono, monospace"
    fontSize: "0.62rem"
    fontWeight: 400
rounded:
  soft: "0.75rem"
  surface: "1rem"
  pill: "999px"
spacing:
  filter-gap: "0.4rem"
  control-y: "0.55rem"
  compact: "0.8rem"
  cell: "1rem"
  section: "2.4rem"
components:
  action-primary:
    backgroundColor: "{colors.night}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0.8rem 1.1rem"
    height: "2.8rem"
  filter-default:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0.55rem 0.8rem"
    height: "2.35rem"
  filter-selected:
    backgroundColor: "{colors.night}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0.55rem 0.8rem"
    height: "2.35rem"
  comparison-surface:
    backgroundColor: "{colors.paper-soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.surface}"
    padding: "2.4rem"
  status-supported:
    backgroundColor: "rgba(172, 217, 77, 0.28)"
    textColor: "{colors.supported-text}"
    rounded: "{rounded.pill}"
    padding: "0.35rem 0.55rem"
  status-develop:
    backgroundColor: "rgba(255, 128, 104, 0.16)"
    textColor: "{colors.develop-text}"
    rounded: "{rounded.pill}"
    padding: "0.35rem 0.55rem"
---

# Design System: Solara Hire

## Overview

**Creative North Star: "The Editorial Evidence Ledger"**

Solara Hire presents career intelligence like a carefully edited working paper: warm paper fields, dark green ink, precise rules, and generous editorial typography. The atmosphere is calm and exacting rather than clinical. Familiar controls remain visibly interactive while the page composition gives evidence, scope, and limitations the visual authority usually reserved for promotional claims.

The system is deliberately not a generic dashboard. It avoids interchangeable KPI tiles and market-wide data theater; the shipped skill-intelligence surface instead moves from an evidence boundary to a source ledger and then into the working comparison. Mint and acid tints create a living paper atmosphere, while coral is held for focus and caution.

**Key Characteristics:**

- Warm paper surfaces with deep green ink and hairline rules.
- Source Serif 4 editorial hierarchy paired with an Aptos/Segoe UI workhorse body.
- Evidence scope and source coverage appear before interpretation.
- Familiar pill controls and tabular structures keep dense comparisons usable.
- Responsive tables become labeled records instead of shrinking into illegibility.

## Colors

The palette reads as botanical ink on warm paper, with restrained high-chroma signals used for interaction and evidence state.

### Primary

- **Night Ink:** The deepest green anchors selected controls, action surfaces, and the brand mark.
- **Acid Highlight:** A rare chartreuse signal used for emphasis and positive alignment; its deeper companion supports stronger positive states.

### Secondary

- **Mint Wash:** A quiet atmospheric wash used in page backgrounds, row-settle feedback, and focus support.

### Tertiary

- **Coral Signal:** The focus-ring and development/caution family; it must remain legible through shape, copy, or state labels rather than color alone.
- **Supported Text:** Dark olive text provides readable contrast over translucent acid state fills.
- **Develop Text:** Deep rust text provides readable contrast over translucent coral state fills.

### Neutral

- **Warm Paper:** The application canvas and dominant field.
- **Soft Paper:** The slightly lighter comparison and card surface.
- **Editorial Ink:** The default text and structural rule color.
- **Soft Ink:** Supporting copy, metadata, inactive navigation, and table detail.
- **Hairline Ink:** Translucent dividers that organize without turning the page into a boxed grid.
- **Warm White:** Text on night controls and high-contrast dark surfaces.

### Named Rules

**The Evidence Color Rule.** Color may distinguish a state, but the state must also be written in plain language.

**The Rare Acid Rule.** Acid is an emphasis signal, not a canvas color; its scarcity preserves its meaning.

## Typography

**Display Font:** Source Serif 4 (with Georgia and generic serif fallbacks)

**Body Font:** Aptos (with Segoe UI Variable, Segoe UI, Helvetica, Arial, and generic sans-serif fallbacks)
**Label/Mono Font:** Aptos/Segoe UI for controls; Cascadia Code with system monospace fallbacks for compact system metadata

**Character:** The serif is editorial, humane, and authoritative without becoming ceremonial. The sans-serif is neutral and highly readable, carrying controls, evidence detail, and dense table content without competing with the headline.

### Hierarchy

- **Display** (500, fluid from 3.2rem to 7rem, 0.94 line-height): First-view headlines and major empty states; use compact negative tracking and a controlled line length.
- **Headline** (500, fluid from 1.8rem to 3rem, approximately 1 line-height): Matrix and section titles that introduce a working region.
- **Body** (400, 1rem baseline, 1.65 line-height): Explanations and evidence limits; prose is generally constrained to 62-68ch.
- **Label** (700 where structural, 0.72-0.9rem): Filters, column headings, evidence labels, and compact status text.
- **Mono** (400, 0.62rem): Footer and small system-brand annotations, not general body copy.

### Named Rules

**The Serif Authority Rule.** Use the editorial serif for meaning-setting headlines; keep controls, measurements, evidence detail, and navigation in the workhorse sans-serif.

**The Readable Ledger Rule.** Dense evidence text stays small but never decorative: preserve strong contrast, explicit labels, and generous line-height.

## Layout

The outer site shell is centered and capped at 1800px. The skill-intelligence workspace uses a 1450px content measure with fluid page padding: `clamp(3.5rem, 7vw, 7rem)` vertically and `clamp(1.25rem, 6vw, 6rem)` horizontally.

Its opening is an asymmetric two-column editorial spread: the headline and explanation occupy a 1.45fr field, while the evidence boundary occupies a minimum 280px, 0.55fr field aligned to the baseline. The source ledger spans the full content measure beneath it, followed by a bordered comparison surface. This order is specific to evidence-comparison views and should be preserved when that same task is extended.

At 900px, the opening becomes one column and the matrix header stacks above its filters. At 680px, page padding tightens to 1rem, filters become a two-column control grid, and the fixed-width desktop table becomes a sequence of block records. Each cell exposes its column name through a visible `data-label`, while the visual table header is clipped for assistive access. The global header simplifies at 1180px and hides its primary navigation at 620px.

**The Evidence Before Inventory Rule.** On comparison surfaces, state the data boundary and source coverage before presenting interpreted rows.

## Elevation & Depth

The evidence workspace is flat by default. It creates depth through warm tonal layering, one-pixel rules, and a subtle mint-to-paper background wash rather than card shadows. The wider system permits a restrained shadow on high-priority primary actions and elevated overlays, but the matrix itself remains flush and ledger-like.

### Shadow Vocabulary

- **Action Lift** (`0 12px 34px rgba(14, 40, 35, 0.17)`): Reserved for the global high-priority primary button treatment.
- **Ambient Surface** (`0 28px 70px rgba(14, 40, 35, 0.07)`): Used on selected raised cards elsewhere in the system, never on every container.
- **Focus Halo** (`0 0 0 3px rgba(185, 234, 213, 0.42)`): A secondary interactive focus treatment in contexts where the global coral outline is not used.

### Named Rules

**The Flat Ledger Rule.** Tables and evidence containers use tonal contrast and rules at rest; shadow is reserved for actions, overlays, or genuinely raised surfaces.

## Shapes

The system combines soft rectangular work surfaces with fully rounded action controls. Comparison containers use a gently curved 1rem corner, tightening to 0.75rem on small screens; filter and status controls use a 999px pill. Thin borders are structural, not ornamental. Circular geometry is limited to the brand mark and other compact state seals.

**The Two-Silhouette Rule.** Use soft rectangles for information regions and pills for compact actions or states; do not introduce arbitrary intermediate corner styles.

## Components

### Buttons

- **Shape:** Fully rounded pill controls, with a minimum 2.8rem action height and 2.35rem compact-filter height.
- **Primary:** Night Ink on Warm White, set in the workhorse sans-serif with bold label weight and compact `0.8rem 1.1rem` padding.
- **Hover / Focus:** Global action links rise 2px over 180ms; keyboard focus uses a 3px Coral Signal outline with a 4px offset.
- **Filter:** Transparent with a Hairline Ink border at rest; the pressed state fills with Night Ink and reverses to Warm White. `aria-pressed` is the source of truth.

### Chips

- **Style:** Evidence status chips use translucent semantic fills, dark semantic text, and a pill silhouette.
- **State:** Supported and develop states always include explicit interpretation copy. Resume-only rows keep the neutral ink wash rather than inventing a warning state.

### Cards / Containers

- **Corner Style:** Soft rectangular comparison surface (1rem; 0.75rem on small screens).
- **Background:** Soft Paper over the Warm Paper page canvas.
- **Shadow Strategy:** Flat on the evidence workspace; see the Flat Ledger Rule.
- **Border:** One-pixel Hairline Ink around the container and between tabular regions.
- **Internal Padding:** Fluid header padding up to 2.4rem; table cells use 1rem vertical rhythm with fluid horizontal padding.

### Navigation

The centered desktop navigation uses compact Soft Ink labels with 160ms color and 1px lift feedback. The active page switches to Editorial Ink and receives a 2px Coral Signal underline offset by 0.45rem. Navigation is reduced as width tightens and hidden below 620px, leaving the brand and account tools.

### Evidence Boundary

A top ink rule and compact supporting copy distinguish scope disclosure from both the headline and the data surface. It is an aside, not a promotional card: no shadow, no decorative icon, and no invented confidence score.

### Source Ledger

The ledger is a full-width strip between two Hairline Ink rules. It begins with the distinct-role total, follows with source counts, and ends with a smaller deduplication note. On small screens, its inline sequence becomes a readable vertical list.

### Comparison Matrix

The desktop matrix uses a fixed five-column structure with a 980px minimum width and a deliberately wide “Where it appeared” column. Table headers use a faint ink wash, rows are divided by rules, and filter changes receive a 180ms mint row-settle animation. At 680px, rows become stacked labeled records; reduced-motion preferences disable the animation.

## Do's and Don'ts

### Do:

- **Do** put evidence limits and source coverage before interpreted comparison data.
- **Do** use Source Serif 4 for editorial hierarchy and Aptos/Segoe UI for working information.
- **Do** preserve explicit state text, semantic table structure, visible keyboard focus, and reduced-motion behavior.
- **Do** convert wide evidence tables into labeled records below 680px.
- **Do** keep paper fields, green ink, mint atmosphere, acid emphasis, and coral focus within their observed roles.

### Don't:

- **Don't** turn evidence views into generic KPI-card dashboards.
- **Don't** imply market-wide demand from a user-selected role set or hide missing provider data.
- **Don't** rely on acid, coral, or any color alone to communicate evidence status.
- **Don't** add shadows to every surface or replace precise hairline rules with heavy boxes.
- **Don't** shrink the desktop matrix until its labels and evidence become illegible.
