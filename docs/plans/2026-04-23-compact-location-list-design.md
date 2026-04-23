# Compact Location List Design

## Problem

When a task is assigned to many locations (e.g., "Windows Server 2016 upgrade" with 40+ locations), finding and editing a specific location in the task detail page requires endless scrolling. There is no search or filter capability.

## Decision

Replace the current card-based location list with a compact accordion-style list, plus search and status filter controls. All filtering is done client-side (no new backend routes).

## UI Design

### Task Detail Page (`detail.html`)

**Before:** Large expandable cards (each ~150px tall) in a flat scrollable list.

**After:**

```
Location Assignments (42 locations)
─────────────────────────────────────────────────────
[Search by name...__________]  [All(42) | Blocked(3) | In Progress(12) | Pending(20) | Completed(7)]

┌─────────────────────────────────────────────────────────────────┐
│ ▶ Beijing Plant       Completed    Zhang Wei                    │
├─────────────────────────────────────────────────────────────────┤
│ ▶ Chennai Office      In Progress  Ravi Kumar                   │
├─────────────────────────────────────────────────────────────────┤
│ ▼ Osaka Data Center   Blocked      Tanaka        [Remove]       │  ← expanded
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Status: [Blocked v]  IT: [Tanaka________]               │   │
│   │ Log:                                                     │   │
│   │ [2026-04-20 10:30] Supplier delivery delayed...          │   │
│   │ [Add log entry_________________________] [Update]        │   │
│   └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ ▶ Seoul Plant         Pending      -                            │
└─────────────────────────────────────────────────────────────────┘

Showing 12 / 42 locations
```

**Compact row:** Single line per location (~40px height). Contains: expand icon, location name, status badge, IT person name. Remove button shows on hover.

**Accordion:** Click a row to expand its edit area below. Only one row expanded at a time. Previous row auto-collapses.

**Search:** Text input filters rows by location name (case-insensitive). Client-side JS with 300ms debounce.

**Status filter tabs:** Row of clickable badges showing count per status. Active tab is highlighted. Combinable with search.

**Count display:** Bottom text "Showing X / Y locations" updates as filters are applied.

**Right panel (Progress Summary) linkage:** Status count rows become clickable. Clicking "Blocked (3)" filters the left panel to show only blocked locations.

### Drawer (`drawer.html`)

Same compact accordion pattern but adapted for the narrower drawer width:

- Compact row: location name + status badge + IT name (one line)
- Search input + status dropdown (dropdown instead of tabs due to width constraint)
- Expand to show status selector, log, and update form inline

## Technical Details

### Frontend Filtering (pure JS)

Each location row has `data-name` and `data-status` HTML attributes. Search and filter events iterate rows and toggle visibility.

```javascript
function filterLocations() {
    const search = searchInput.value.toLowerCase();
    const status = activeStatusFilter; // empty string = all
    rows.forEach(row => {
        const matchName = row.dataset.name.toLowerCase().includes(search);
        const matchStatus = !status || row.dataset.status === status;
        row.style.display = (matchName && matchStatus) ? '' : 'none';
    });
    updateCount();
}
```

### Accordion

Each compact row wraps an expandable div. Click handler:
1. Collapse previously expanded row (if any)
2. Expand clicked row
3. Update arrow icons (▶ ↔ ▼)
4. If expanded row gets filtered out, auto-collapse it

### Form Submission

Existing backend routes (`update_assignment`, `remove_assignment`) are unchanged. After form POST, the page reloads. To preserve which row was expanded, use URL hash `#assignment-{id}` — JS reads hash on load and auto-expands that row.

### No New Backend Routes

All filtering is client-side. The `detail` route already loads all assignments. No API changes needed.

## Files to Modify

1. `app/templates/tasks/detail.html` — Replace location assignment section with compact accordion + search/filter
2. `app/templates/tasks/partials/drawer.html` — Same pattern adapted for drawer
3. `app/static/css/main.css` — Add compact row styles, accordion animation
4. `app/routes/tasks.py` — No changes needed (data already available)

## Edge Cases

- **0 locations:** Show "No assignments yet" as before
- **1-3 locations:** Compact layout still works, search/filter hidden or minimal
- **>100 locations:** Client-side filtering still performant; DOM heavy but acceptable for this use case
- **Form POST redirect:** Preserve expanded row via URL hash
