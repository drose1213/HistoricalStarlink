# Homepage Cinematic Star Map Design

## Goal

Optimize the home page into a cinematic star-map experience. The first screen should feel close to the selected reference: a dark star field, a few meaningful glowing event nodes, thin relationship lines, a subtle ring around the highlighted event, lightweight navigation, and a narrative title placed over the map.

## Scope

- Update `frontend/src/views/HomeView.vue` layout and scoped styles.
- Update `frontend/src/components/CosmicMap.vue` visual density and drawing style.
- Keep existing routes, stores, search behavior, filter behavior, and event navigation.
- Do not change backend APIs, database code, auth behavior, or event data.

## Visual Direction

The page should use a restrained observatory mood instead of the current heavy cyberpunk surface. The dominant background is near-black with faint teal and pink stars. Event nodes are larger colored points with soft glows. Only a small set of important nodes should visually dominate the first screen, while secondary nodes stay small and quiet.

The header becomes a thin overlay in the top safe area. The brand appears as a small glowing dot plus text. Main navigation uses compact bordered buttons: Home, Cards, Leaderboard, and Profile when authenticated. The active item uses a bright border and slightly stronger text.

The title block sits in the lower-left quadrant over the map. It contains the current Chinese title and subtitle with strong contrast, no card background, and a compact search bar below it. This keeps the map visible while giving new users a clear starting point.

## Components

### HomeView

- Keep `CosmicMap` full-screen and visually primary.
- Replace the centered hero overlay with a left-bottom narrative overlay.
- Keep search dropdown behavior and event routing unchanged.
- Keep the event drawer, but restyle it as a lighter side panel so it does not visually compete with the map.
- Keep filter buttons available in the header and drawer.
- Preserve login/logout behavior.

### CosmicMap

- Reduce perceived graph density on initial view by:
  - Drawing fewer bright edges.
  - Lowering opacity for concept nodes and secondary labels.
  - Making event-to-event links more legible than concept links.
- Shift the look toward:
  - Deep black background.
  - Sparse white star points.
  - Thin grey-white relationship lines.
  - Soft teal, pink, gold, and blue event colors.
  - One or more ringed event nodes, especially on hover or high-importance events.
- Keep click and hover behavior unchanged.

## Data Flow

The existing data flow remains unchanged:

1. `HomeView` reads all events and search helpers from `frontend/src/data/events.ts`.
2. `HomeView` uses `useAppStore` for filtering and toast state.
3. `CosmicMap` renders the graph from `allEvents`.
4. Clicking an event node or search result routes to `EventDetail`.

## Error Handling

- Search should continue to handle empty input by showing no dropdown results.
- Canvas rendering should continue to no-op safely when the canvas context is unavailable.
- Resize handling should preserve canvas dimensions and avoid layout shifts.

## Testing And Verification

- Run the frontend production build with `npm run build`.
- Start services with `.\start.ps1`.
- Verify `http://localhost:3000` responds.
- Verify `http://localhost:8000/health` responds.
- Inspect the home page at desktop width for:
  - Header buttons not overlapping.
  - Title and search fitting over the map.
  - Search dropdown staying above the canvas.
  - Drawer opening without covering the whole visual.
  - Event nodes still clickable.
- Inspect a narrow viewport for:
  - Header wrapping or compacting cleanly.
  - Title and search not overflowing.
  - Drawer trigger remaining usable.

## Risks

- Current source files contain mojibake text in several Vue templates. This design does not require solving the encoding issue, but visual work may expose it more clearly. If the browser output is garbled, a separate text encoding cleanup should follow.
- Reducing graph density may make some concept relationships less visible. The implementation should keep the underlying graph data intact and only adjust visual emphasis.
- The existing canvas layout uses random positioning. The final visual may vary slightly between reloads unless deterministic seeding is added. This pass should keep behavior minimal unless randomness causes poor composition.
