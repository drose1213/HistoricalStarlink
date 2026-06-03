# Star Map Focus Rotation Design

## Scope

Update the historical star map interaction so hovering or clicking a node no longer pushes outer star links farther apart. The selected node should become the foreground focus, while the rest of the map rotates and compresses toward the screen interior. Clicking a node must still navigate to the single event detail page for that event.

## Current Behavior

- `frontend/src/components/HistoryStarMap.vue` renders D3 force-layout nodes and links inside one SVG group.
- Hover pauses the simulation and rotates the whole SVG group around the canvas center.
- Mouse leave clears hover, restarts the simulation, and returns the group rotation to `0`.
- Click currently mirrors hover behavior but does not navigate to `EventDetail`.

## Target Behavior

- Hover freezes the current layout and applies a focus projection:
  - The hovered node is visually brought forward.
  - Non-focused nodes rotate around the canvas center and move slightly inward.
  - Links follow their projected node endpoints.
  - The force simulation stays stopped while focus is active so unrelated nodes do not drift apart.
- Mouse leave clears transient hover focus and restores the original node positions smoothly.
- Click applies the same focus feedback and then routes to `EventDetail` with the clicked node id.
- The detail page remains single-event oriented; no broader multi-event detail panel is added.

## Approach

Keep the existing SVG/D3 structure and add a projected-position layer in `HistoryStarMap.vue`.

- Store immutable layout positions from D3 ticks in `basePositions`.
- Compute displayed `positions` from `basePositions` plus the active focus node.
- Replace whole-group rotation on hover with per-node projection math:
  - focused node: eased toward the canvas center and rendered last;
  - other nodes: rotated by a small angle and scaled inward from the center;
  - links: use the same projected endpoints.
- Use Vue Router inside the component for click navigation.

## Validation

- Build should pass with `npm run build` in `frontend`.
- Manual check should confirm:
  - hover does not make distant clusters drift outward;
  - focused node appears in front;
  - non-focused nodes rotate inward;
  - click opens `#/event/<id>`;
  - mouse leave restores the star map without restarting outward spread.

## Risks

- Projection math must preserve readable labels and avoid placing the focused node directly under fixed UI.
- Navigation on click must not conflict with drag gestures; a drag threshold may be needed if click and drag share the same pointer path.
