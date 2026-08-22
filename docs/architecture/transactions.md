# Transactions

The platform uses one consistent write strategy so that data integrity, the
audit trail, and domain events stay in lockstep.

## The strategy: validate → begin → apply → audit → commit → publish

```
1. VALIDATE   Check input and domain invariants BEFORE opening a transaction.
              Reject early with the right standardized error
              (validation_error / business_rule_error / conflict).

2. BEGIN      Open a single atomic block for the whole use-case.

3. APPLY      Perform all writes. Either everything lands or nothing does.

4. AUDIT      Record the audit entry / queue domain events inside the same
              transaction, so the trail can never diverge from the data.

5. COMMIT     One commit for the use-case.

6. PUBLISH    Domain events fire on transaction.on_commit — i.e. only after a
              durable commit. Subscribers (audit fan-out, notifications) never
              observe rolled-back state.
```

## `atomic_with_events`

`apps/core/transactions.py` provides a context manager that wraps
`transaction.atomic()` and defers event publication to `transaction.on_commit`:

```python
from apps.core.transactions import atomic_with_events
from apps.core.events import EntityCreated

def create_company(data, actor):
    validate(data)                       # (1) before the transaction
    with atomic_with_events() as publish:  # (2) begin
        company = Company.objects.create(**data, created_by=actor)  # (3) apply
        publish(EntityCreated(            # (4) queued, not sent yet
            entity_type="organization.company",
            entity_id=str(company.id),
            actor_id=str(actor.id),
        ))
        return company
    # (5) commit happens on block exit
    # (6) queued events publish via on_commit → audit + notifications react
```

Key guarantees:

- **Atomicity** — partial writes are impossible; a raised exception rolls back
  everything, and queued events are discarded (never published).
- **Ordering** — events publish *after* commit, so a subscriber that reads the
  DB sees the committed rows.
- **Isolation of side effects** — event handler failures are logged and
  swallowed (see the event bus), so a flaky notification cannot corrupt or roll
  back a committed business write.

## Where to put transactional logic

- In **services**, not views or serializers. Views validate shape and delegate;
  services own the transaction and events.
- Keep transactions **short**: do slow/remote work (email, SMS, external calls)
  in event subscribers or Celery tasks triggered by post-commit events, never
  inside the atomic block.

## Concurrency

- Rely on DB constraints for correctness; a violated unique/state constraint
  becomes a `ConflictError` (409).
- For check-then-write races, use `select_for_update()` within the atomic block
  or an optimistic version/status guard, depending on the module's needs.
