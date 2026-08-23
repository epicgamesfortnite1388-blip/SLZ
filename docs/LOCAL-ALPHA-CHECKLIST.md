# SLZ ERP — Local Alpha Manual Checklist (non-developer walkthrough)

Open **http://localhost:5173** in a browser.

Seeded accounts (local alpha):

| Account | Password | Purpose |
|---|---|---|
| `admin@slz.local` | `demo123` | Platform superuser / IT admin |
| `operator@slz.local` | `demo123` | Operational demo user |

Log in with **admin@slz.local / demo123** first.

For every step: ✅ = works as expected · ❌ = note exactly what you did and
what happened instead.

| # | Step | Expected result |
|---|---|---|
| 1 | Login | Dashboard loads; company name visible in the header |
| 2 | Select company | Header dropdown lists your companies; switching refreshes all tiles/rows |
| 3 | Dashboard | Count tiles + order-book rows reflect the selected company |
| 4 | Create user | Identity → Users → New → save → user appears in list |
| 5 | Assign role to user | User edit → pick role → save → role shows on detail |
| 6 | Assign permissions to role | Roles → role detail → toggle permission → saved |
| 7 | Permission changes behavior | Log in as that user → nav/actions match permissions |
| 8 | Create master data | Materials/Products/UoMs → New → save → appears in list |
| 9 | Create customer + product | Partners → customer; engineering → customer product created |
| 10 | Sales order create | Sales Orders → New → header + line → save → CONFIRMED via action |
| 11 | Purchase order create/approve | Procurement → PO → approve |
| 12 | Receive material (GRN) | Goods Receipts → post against the approved PO line → traceability unit + stock IN created |
| 13 | Inventory check | Balances page shows the received quantity; Kardex shows the movement history |
| 14 | Production order create/release | Production Orders → new → release |
| 15 | Issue material (printing stage = explicit) | Execution Center → issue against a roll → OUT movement posted |
| 16 | Extrusion backflush | Extrusion-stage consumption posts automatically per confirmed rule |
| 17 | Record output | Output row creates a serialized roll into WIP/FG warehouse |
| 18 | Allocate | Allocations → reserve a produced roll for the SO line |
| 19 | Ship | Deliveries → ship allocated unit → OUT movement + customer recorded |
| 20 | Over-allocation / over-shipment rejected | Requesting more than available/allocated → clear business-rule error, nothing changes |
| 21 | Quarantine cannot issue/ship | Movements out of a quarantine store → rejected |
| 22 | Audit history | Any record's History panel shows who did what and when |
| 23 | Switch company | All lists/tiles refetch; no stale rows from the previous company |
| 24 | Isolation spot-check | A user without membership sees no other company's records (404s) |
| 25 | Persian toggle | Language switcher → fa: RTL layout, Vazirmatn font, Jalali-style dates, translated labels |
| 26 | English toggle | Back to en: clean LTR layout preserved |
| 27 | Mobile width (~390px) | Sidebar becomes a drawer; tables scroll horizontally; nothing clipped |
| 28 | Refresh on a detail page | Deep link reloads correctly (no blank screen) |

## Known alpha limitations

* Costing valuation engine not yet implemented.
* Celery has no live tasks locally (eager mode).
* Virus scanning of uploads deferred.
* Persian date *entry* is Gregorian inputs (display converts).
