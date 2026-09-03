You are an adversarial Django/DRF reviewer. Assume the previous audit missed defects. Your job: attempt to BREAK the current implementation of the ERP's platform layer.

Audit these files ONLY:
- apps/core/transactions.py (atomic_with_events, advisory-lock helper)
- apps/core/events.py (event bus + subscribers incl. audit)
- apps/core/handlers.py (standardized exception handler + status mapping)
- apps/core/validation.py (PositiveDecimalField etc.)
- apps/core/viewsets.py (company-scope mixin, permission machinery, AuditedModelViewSet)
- apps/core/middleware.py (company context, correlation id)
- apps/inventory/services.py (post_movement with advisory xact lock, transfer_stock)
- apps/shipment/services.py (create_shipment allocation lock + nonce)
- apps/procurement/services.py (GRN receive + nonce idempotency)
- apps/production/services.py (output costing hook + RELEASED guard)

Attack angles:
1. Race conditions: two concurrent calls that both pass a pre-check (search for read-then-write without select_for_update/advisory lock). Ignore theoretical races Django already serializes; flag realistic ones.
2. Nonce/idempotency bypasses: can the same nonce be reused across companies? Can a retried request double-post? Is the nonce checked inside the same transaction as the write? Unique constraint vs race on first insert (IntegrityError handling)?
3. Lock scope errors: advisory lock keyed on wrong fields; select_for_update not followed by re-check of the guarded condition; lock taken but check outside it.
4. Decimal/quantity edge cases: 0/negative slipping through; huge magnitudes; rounding in costing layer (PRODUCTION_OUTPUT residual absorption).
5. Exception-handler leaks: does any path expose tracebacks/SQL/500 where a 4xx is expected? Does the handler map IntegrityError/DatabaseError correctly?
6. Company-scope bypass in viewsets: detail routes, actions, filters that escape the company filter; is the scope applied to update/destroy too?
7. Soft-delete + unique constraint interplay: deleted rows colliding with new rows?

CONSTRAINTS:
- Report ONLY concrete defects with file:line and an exact reproduction scenario.
- For each: Severity (P0/P1/P2/P3), Problem, Root cause, Fix (exact unified diff hunk), Regression test (exact test sketch).
- Do not report theoretical issues without a concrete exploit path. Mark confidence (high/med/low).
- Never suggest arbitrary sleeps to fix races; never suggest removing constraints or security checks.

Return a concise structured report, ordered by severity.