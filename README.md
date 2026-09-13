# Cross-System Reconciliation & Tenant Isolation Application

A complete, production-minded full-stack application built to import, normalize, reconcile, and audit data disagreements between System A and System B across strictly isolated tenant organizations.

---

## 1. Project Overview

System A and System B record the same transaction events. Neither system is authoritative; most records agree, but some disagree. This application identifies four categories of data disagreements:
1. **Missing in System B** (`MISSING_IN_SYSTEM_B`): Record exists in System A but has no corresponding System B entry.
2. **Orphan in System B** (`ORPHAN_IN_SYSTEM_B`): System B entry points to a non-existent System A record.
3. **Duplicate in System B** (`DUPLICATE_IN_SYSTEM_B`): Multiple System B entries point to the same normalized System A record reference.
4. **Value Mismatch** (`VALUE_MISMATCH`): Exactly one System A record matches one System B entry, but their values differ.

---

## 2. Architecture & Directory Structure

```text
project-root/
├── backend/
│   ├── manage.py
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── reconciliation/
│       ├── migrations/
│       ├── management/
│       │   └── commands/
│       │       └── import_data.py
│       ├── models.py
│       ├── serializers.py
│       ├── urls.py
│       ├── views.py
│       ├── services/
│       │   ├── normalizer.py
│       │   └── comparator.py
│       └── tests/
│           ├── test_api.py
│           └── test_comparator.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       └── components/
│           ├── FilterBar.jsx
│           └── DiscrepancyTable.jsx
│
├── data/
│   ├── system_a.csv
│   ├── system_b.csv
│   └── locations.csv
│
├── README.md
├── DECISIONS.md
└── .gitignore
```

---

## 3. Tech Stack

- **Backend**: Python 3.13, Django 6.1, Django REST Framework 3.18, `django-cors-headers`
- **Database**: SQLite (`db.sqlite3`)
- **Frontend**: React 18, Vite 5 (Vanilla JSX, standard CSS/HTML)
- **Testing**: `pytest` 9.1, `pytest-django` 4.14

---

## 4. Data Model

- **`Organization`**: `org_id` (PK), `name`
- **`Location`**: `location_id` (PK), `org` (FK to `Organization`)
- **`SystemARecord`**: `record_id`, `location_id`, `raw_value`, `normalized_value` (DecimalField), `raw_json`
- **`SystemBEntry`**: `record_ref`, `normalized_record_ref`, `location_id`, `raw_value`, `normalized_value` (DecimalField), `raw_json` *(Note: No Foreign Key to System A, preserving orphan rows)*
- **`ImportIssue`**: `source`, `row_number`, `field`, `raw_value`, `error_message`, `created_at`

---

## 5. Import Process & Normalization

The ingestion command `python manage.py import_data`:
1. Reads `locations.csv` to build tenant mappings (`location_id -> org_id`).
2. Reads `system_a.csv` and `system_b.csv`.
3. Normalizes dirty record references using `normalize_record_ref`:
   - `"REC-001"`, `" rec_001 "`, `"REC001"`, `"001"` -> `"REC-001"`
4. Safely parses numeric/currency values using `normalize_decimal`:
   - `"$120.50"` -> `Decimal('120.50')`
   - `"1,200.00"` -> `Decimal('1200.00')`
   - `"N/A"`, `"NULL"`, `""` -> Logs `ImportIssue`, preserves `raw_value`, sets `normalized_value = None`.
5. **Zero Silent Drops**: Every row is preserved in the database.

---

## 6. Reconciliation Logic (4-Pass Engine)

`backend/reconciliation/services/comparator.py`:
- **Pass 1 (Duplicates)**: If >1 System B entries share a normalized reference, flag each entry as `DUPLICATE_IN_SYSTEM_B`.
- **Pass 2 (Missing)**: If a System A record has 0 matching System B entries, flag as `MISSING_IN_SYSTEM_B`.
- **Pass 3 (Orphans)**: If a System B entry has 0 matching System A records, flag as `ORPHAN_IN_SYSTEM_B`.
- **Pass 4 (Value Mismatches)**: For 1-to-1 matches, compare `normalized_value` (Decimal). If both are Decimal and `A != B`, flag as `VALUE_MISMATCH`. (Note: `100.00` and `"$100.00"` resolve to equal Decimals and are NOT mismatches).

---

## 7. Tenant Isolation

Tenant isolation is strictly enforced at the API database query layer:
- The `/api/discrepancies/` endpoint **requires** `org_id`.
- Missing `org_id` immediately returns `400 Bad Request`.
- Database queries scope `SystemARecord` and `SystemBEntry` strictly to `location_id`s belonging to the requested `org_id`.
- Cross-tenant record comparisons are impossible.

---

## 8. API Endpoints

- `GET /api/orgs/`: Returns list of available tenant organizations.
- `GET /api/discrepancies/?org_id=<org_id>&reason=<reason>&sort=<asc|desc>`: Returns tenant-isolated discrepancies.
  - Required: `org_id`
  - Optional: `reason` (`ALL`, `MISSING_IN_SYSTEM_B`, `ORPHAN_IN_SYSTEM_B`, `DUPLICATE_IN_SYSTEM_B`, `VALUE_MISMATCH`)
  - Optional: `sort` (`asc`, `desc`)

---

## 9. Frontend Behavior

React SPA built with Vite:
- **Tenant Selector**: Dropdown populated from `/api/orgs/`.
- **Reason Filter**: Dropdown filtering discrepancies server-side.
- **Sort by Value**: Toggle button for ascending/descending numeric sort.
- **States**: Clear Loading, Error, and Empty state messages.

---

## 10. Testing

Run backend test suite using `pytest`:
```bash
cd backend
python -m pytest
```
Tests cover:
- Detection of all 4 discrepancy types
- Decimal equivalence (`$100.00` vs `100.00`)
- Dirty reference normalization (`"001"` vs `"REC-001"`)
- Tenant boundary isolation (API 400 response on missing `org_id` and strict query scoping)

---

## 11. Setup from Clean Clone & Execution Commands

### Prerequisites
- Python 3.10+
- Node.js 18+

### Step 1 — Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py import_data
python manage.py runserver 8000
```

### Step 2 — Frontend Setup (New Terminal)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 in your browser.

---

## 12. What Was Built vs Deliberately NOT Built

### What Was Built
- Production-grade ingestion pipeline preserving dirty data
- Pure Python 4-pass reconciliation engine
- Strict query-layer tenant isolation
- Full test suite covering edge cases
- React dashboard with filtering and value sorting

### What Was Deliberately NOT Built
- Authentication / User login (explicitly non-required)
- Docker / Kubernetes overhead (SQLite provides instant local execution)
- Heavy UI frameworks like Material-UI / Tailwind
- Celery / Redis background queues (dataset fits memory cleanly)

---

## 13. Answers to Technical Follow-Up Questions

### a. Name one thing the AI agent got wrong. How did you notice?
During initial test suite setup, `pytest` failed with `django.core.exceptions.ImproperlyConfigured: Requested setting REST_FRAMEWORK, but settings are not configured` when importing `APIClient` in `test_api.py`. I noticed this error immediately in the terminal test run logs. The root cause was a missing `pytest.ini` setting `DJANGO_SETTINGS_MODULE` and a conflicting auto-generated `reconciliation/tests.py` file from Django `startapp`. I fixed this by adding `backend/pytest.ini` pointing to `config.settings` and removing the redundant `tests.py` file.

### b. Which part of your submission are you least confident about, and why?
I am least confident about reference normalization heuristics for completely unknown/unstandardized vendor prefixes beyond the `REC-`, `REC_`, `REC<digits>`, and `001` patterns specified. In a production system with unconstrained dirty vendor inputs, fuzzy matching algorithms or configurable regex lookup rules would be necessary to avoid misclassifying dirty references as orphan records.

### c. If you had a second day, what would you fix first?
If I had a second day, I would build an UI view for `ImportIssue` records. Currently, invalid values like `"N/A"` or `"NULL"` create `ImportIssue` database entries and fall back safely to string comparison, but giving operations teams an inline dashboard tab to review raw CSV parse errors would provide complete operational transparency.

---

## 14. AI Agent Usage Transparency

An AI coding assistant (Antigravity) was used throughout development for scaffolding boilerplate (Django app setup, Vite configuration), generating test data fixtures, and refining pure Python functions. All generated code, database models, API views, tenant isolation boundaries, and reconciliation logic were reviewed, executed, and verified empirically through test suites and manual server checks.
