# Udatracker Starter Code

This directory contains the starter code for the Udatracker project. The initial structure of directories and files is described below.

```
.
├── backend
│   ├── __init__.py
│   ├── app.py
│   ├── in_memory_storage.py
│   ├── order_tracker.py
│   ├── requirements.txt
│   └── tests
│       ├── __init__.py
│       ├── test_api.py
│       └── test_order_tracker.py
├── frontend
│   ├── css
│   │   └── style.css
│   ├── index.html
│   └── js
│       └── script.js
├── pytest.ini
└── README.md
```

## Reflection

For local container startup instructions, see the [Docker quick start](../README.md#docker-quick-start) in the root README.

- I centralized business rules (required fields, positive quantity, valid status values) inside OrderTracker so API routes stay thin and consistent.
- A key trade-off was strict status validation. It prevents accidental states early, but it requires updating one shared allowed-status list whenever new workflow states are introduced.
- The first red-to-green moment was `test_update_order_status_empty_order_id_raises`: missing order IDs were flowing into storage lookups instead of failing fast, which pushed me to add the shared non-empty-string validator before expanding the API routes.
- I added the `RLock` because even this simple in-memory version has read/write sequences that should stay consistent if multiple requests arrive close together.
- The in-memory store is intentionally bounded for local demo use; in production I would replace it with a database-backed repository and add bounded-retention plus profiling/load checks to confirm memory behavior over time.
- Next improvement: add persistent storage with a repository interface (SQLite/PostgreSQL), then keep the same OrderTracker tests by swapping only the storage fixture.
