# Location Detail Page Design

## Goal

Add a reverse view from Location to Tasks: clicking a Location shows all Tasks assigned to it, with full edit capability (status, logs, IT person) and the ability to add new Task assignments.

## Current State

- Task detail page (`/tasks/<id>`) shows all assigned Locations with editable assignment fields
- Location only has list (`/locations/`) and edit (`/locations/<id>/edit`) pages — no detail page
- `task_assignment` join table links Tasks and Locations with per-assignment fields (local_status, it_name, task_log, etc.)

## Design

### Approach: Mirror Task Detail Page

Create a new Location detail page that is structurally symmetric to the existing Task detail page. No refactoring of existing code — purely additive changes.

### Route Changes (`app/routes/locations.py`)

New routes:

| Route | Method | Purpose |
|-------|--------|---------|
| `/locations/<id>` | GET | Location detail page with info + assigned Tasks |
| `/locations/<id>/assign` | POST | Assign a new Task to this Location |
| `/locations/<loc_id>/assignment/<a_id>` | POST | Update assignment (status, log, IT person) |
| `/locations/<loc_id>/assignment/<a_id>/delete` | POST | Remove an assignment |

### Frontend Template (`app/templates/locations/detail.html`)

Layout mirrors Task detail page:

- **Header**: Location name + Active/Inactive badge + Edit/Delete/Back buttons
- **Left column (2/3)**:
  - Location info card (country, city, type, region, IT manager, contacts, comments)
  - Task Assignments list — each assignment shows:
    - Task name (clickable link to `/tasks/<id>`)
    - Local status (editable dropdown)
    - IT person (editable input)
    - Task log (read-only display + add entry input)
    - Update / Remove buttons
  - Add Task section — dropdown of unassigned Tasks + Assign button
- **Right column (1/3)**:
  - Progress summary (Completed/In Progress/Pending/Blocked/N/A counts + progress bar)
  - Blocker alert if any assignments are Blocked

### Location List Page Change (`app/templates/locations/list.html`)

- Location name column becomes a clickable link to `/locations/<id>`

### No Changes to Existing Code

- Task routes, templates, and assignment logic remain untouched
- `task_assignment` table schema unchanged
- Both Task→Location and Location→Task views operate independently on the same data
