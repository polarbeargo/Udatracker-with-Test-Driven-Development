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

- I centralized business rules (required fields, positive quantity, valid status values) inside OrderTracker so API routes stay thin and consistent.
- A key trade-off was strict status validation. It prevents accidental states early, but it requires updating one shared allowed-status list whenever new workflow states are introduced.
- Unit tests around invalid updates caught an early bug where missing order IDs were flowing into storage lookups instead of failing fast with a validation error.
- Next improvement: add persistent storage with a repository interface (SQLite/PostgreSQL), then keep the same OrderTracker tests by swapping only the storage fixture.
