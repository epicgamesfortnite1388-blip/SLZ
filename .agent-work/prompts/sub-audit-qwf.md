You are a senior Django/DRF engineer auditing part of an ERP (modular monolith, Django 4.2 + DRF, company-scoped multi-tenant, soft-delete, audited writes, status state machines).

Audit ONLY these modules for concrete defects:
- apps/quality (services.py: revision activation + post_check_result; views.py actions; cross-company checks)
- apps/workflow (services.py: start_workflow/record_decision/cancel/finalize; views.py decision endpoints; permission gating)
- apps/notifications (services.py notify(); views.py mark_read/mark_all_read/unread_count; providers.py)

Look specifically for:
1. Company-isolation gaps (an object from company A readable/writable via company B context)
2. Missing transaction.atomic around multi-write operations; race conditions (check-then-act without locking)
3. Permission bypasses (viewset permission_map vs required_permission vs actions; unauth access to actions)
4. Business-rule violations: status transitions not validated against declared choices; append-only semantics broken (updates/deletes on immutable rows)
5. N+1 or unbounded querysets in list endpoints
6. Incorrect error semantics (500-prone paths: .get() on empty, missing field handling, None derefs)
7. Cross-company FK validation gaps in serializers (site/customer/product/company mismatches accepted)
8. Inconsistent audit/event usage

CONSTRAINTS:
- Report ONLY concrete code-level defects you can point to with file:line. Do NOT invent issues; if a pattern looks intentional (documented in module docstrings as OPEN/gated), say so and skip it.
- For each confirmed defect output: Severity (P0/P1/P2/P3), File:line, Problem, Root cause, Fix (as an exact unified diff hunk against the current file content), Regression test suggestion.
- If you find nothing reportable in a module, say "module X: no concrete defects found" — do not pad.
- Never propose removing security checks, loosening permissions, or disabling tests.

Return a concise structured report. Be precise; prefer fewer, real issues over speculative ones.