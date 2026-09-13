# DECISIONS.md — Engineering & Architecture Decisions

This document records the major architectural decisions, alternative approaches considered, and engineering rationale for the Cross-System Reconciliation & Tenant Isolation application.

---

### Decision 1 — SQLite Database for Zero-Dependency Storage

- **Decision**: Use Django with an embedded SQLite database (`db.sqlite3`).
- **Alternative**: PostgreSQL or MySQL hosted in Docker.
- **Reasoning**: The dataset size (120 rows per system) and single-node requirement make SQLite ideal. It eliminates setup friction for reviewers, allows instant clean-clone execution without spinning up external containers, and satisfies the assignment preference for a lightweight, production-minded stack.

---

### Decision 2 — Decimal Normalization for Currency & Numeric Comparisons

- **Decision**: Normalize numeric and currency values into Python `Decimal` objects quantized to 2 decimal places, while preserving the raw string in `raw_value`.
- **Alternative**: Native Python `float` or direct string comparison.
- **Reasoning**: Floating-point numbers suffer from IEEE 754 precision issues (e.g. `0.1 + 0.2 != 0.3`). Currency strings formatted as `"$120.50"`, `"1,200.00"`, or `" 50.00 "` represent equivalent monetary values and must not trigger false `VALUE_MISMATCH` alerts. Non-parseable strings like `"N/A"` or `"NULL"` fall back to safe raw string comparison without crashing ingestion.

---

### Decision 3 — Pure Python Reconciliation Engine

- **Decision**: Implement reconciliation matching logic as a pure Python module (`backend/reconciliation/services/comparator.py`) independent of HTTP and database layers.
- **Alternative**: Complex SQL joins with regular expressions or heavy Django ORM aggregations.
- **Reasoning**: Keeping the comparator decoupled from ORM/HTTP plumbing ensures fast unit testing (under 0.1s), high readability, and line-by-line defensibility in technical interviews. SQL regex joins are fragile across database engines (especially SQLite).

---

### Decision 4 — Query-Layer Tenant Isolation (No Authentication)

- **Decision**: Enforce tenant boundaries directly at the Django database query layer in `DiscrepancyListView` (`Location.objects.filter(org_id=org_id)`). Requests missing `org_id` return HTTP 400 Bad Request.
- **Alternative**: Fetching all records globally and filtering client-side in React.
- **Reasoning**: Authentication is explicitly excluded from the assignment requirements. However, tenant data isolation is mandatory. Filtering strictly at the API database layer guarantees that a tenant can never receive another organization's records under any circumstances.

---

### Decision 5 — Preserving Raw Values & Storing Orphan B Entries Without Foreign Keys

- **Decision**: Omit foreign key constraints between `SystemBEntry` and `SystemARecord`, storing raw strings and full row JSON payloads (`raw_json`).
- **Alternative**: Enforce a database Foreign Key from System B to System A.
- **Reasoning**: System B orphan entries (pointing to non-existent System A records) are expected dirty data. A strict Foreign Key constraint would cause database insertion failures or drop rows silently. Omitting FKs and preserving raw strings ensures 100% auditability and zero silent data loss.

---

### Decision 6 — Idempotent Reset-and-Reimport Command

- **Decision**: Implement `python manage.py import_data` within an atomic transaction that clears existing data before importing.
- **Alternative**: Non-destructive upserts or append-only imports.
- **Reasoning**: CSV source files represent authoritative periodic snapshots. An idempotent reset ensures deterministic local development and test execution without accumulating duplicate rows across multiple command runs.

---

### Decision 7 — Server-Side Filtering and Decimal Value Sorting

- **Decision**: Handle reason filtering and value sorting on the backend API layer.
- **Alternative**: Sorting and filtering in React state.
- **Reasoning**: Server-side sorting leverages Decimal normalization, ensuring that formatted currency strings (e.g. `"$120.50"`, `"1,200.00"`) sort by true numerical value rather than lexicographical string order or JS `NaN` errors.

---

### Decision 8 — Minimal React + Vite SPA (No Heavy UI Libraries)

- **Decision**: Build the frontend using React 18, Vite 5, standard HTML table elements, and scoped inline styling.
- **Alternative**: Material UI, Tailwind CSS, Next.js, or Redux.
- **Reasoning**: Avoids bloated node_modules, complex build pipelines, and unnecessary state management frameworks. Focuses strictly on functional correctness, clean user experience, and fast build times (~1.0s).
