# Аудит кода: качество, рабочие процессы, уведомления

## 1. apps/quality/services.py

**Дефект 1.1: Отсутствие `transaction.atomic` в `post_check_result`**
- **Серьёзность:** P1
- **Файл:строка:** `quality/services.py` ~ строка 117 (функция `post_check_result`)
- **Проблема:** Функция создаёт запись `QualityCheckResult` и при `disposition == "HOLD"` обновляет поле `notes` у `traceability_unit`. Обе операции не обёрнуты в атомарную транзакцию. При ошибке во втором `save` первая запись уже будет сохранена, что приведёт к несогласованным данным.
- **Коренная причина:** Отсутствие декоратора `@transaction.atomic` или явного контекстного менеджера.
- **Исправление (unified diff):**

```diff
+ from django.db import transaction
+
+ @transaction.atomic
  def post_check_result(...):
      ...
```

**Дефект 1.2: Отсутствие валидации `disposition`**
- **Серьёзность:** P2
- **Файл:строка:** `quality/services.py` ~ строка 117 (параметр `disposition`)
- **Проблема:** Функция принимает строку `disposition`, но не проверяет, что она входит в допустимые значения (`PASS`, `FAIL`, `HOLD`). Модель `QualityCheckResult` имеет поле с `choices`, но на уровне модели ограничения не проверяются — при сохранении недопустимое значение будет записано в БД (если поле `CharField` без внешнего ограничения). Сериализатор `QualityCheckResultSerializer` также не валидирует это поле. Это может привести к появлению некорректных значений.
- **Коренная причина:** Отсутствие явной проверки в сервисном слое; сериализатор должен иметь валидацию `disposition`.
- **Исправление:** Добавить проверку в начале функции:

```python
from apps.quality.models import QualityCheckResult
if disposition not in dict(QualityCheckResult.Disposition.choices):
    raise BusinessRuleError("Invalid disposition", code="qc.invalid_disposition")
```

Альтернативно, дополнить сериализатор валидатором поля.

---

## 2. apps/quality/views.py

**Дефект 2.1: Отсутствие проверки разрешения для custom action `activate`**
- **Серьёзность:** P1
- **Файл:строка:** `quality/views.py` — метод `activate` в `QualityPlanRevisionViewSet` (примерно строка 80)
- **Проблема:** Action `activate` не имеет явной проверки прав доступа. В `permission_map` перечислены только стандартные методы (`POST`, `PUT`, `PATCH`, `DELETE`). Для custom action не применяется общая логика `AuditedModelViewSet`, и в коде нет вызова `self.check_permissions()` или проверки на `quality.plan.manage`. Любой аутентифицированный пользователь (даже без права `quality.plan.view`) может вызвать этот эндпоинт, если у него есть доступ к объекту (через `get_object()`). Это нарушает изоляцию и позволяет активировать ревизию без необходимых прав.
- **Коренная причина:** Пропущена проверка разрешения для custom action.
- **Исправление:** Добавить проверку права в начале метода:

```python
@action(detail=True, methods=["post"], url_path="activate")
def activate(self, request, pk=None):
    self.check_permissions(request)  # или вручную проверить permission
    # ...
```

Либо указать `permission_classes` для действия через декоратор `@permission_classes([HasPermission('quality.plan.manage')])`.

---

## 3. apps/workflow/services.py

**Дефект 3.1: Race condition в `record_decision`**
- **Серьёзность:** P0
- **Файл:строка:** `workflow/services.py` ~ строка 55 (функция `record_decision`)
- **Проблема:** При принятии решения для шага нет блокировки строки (`select_for_update`). Два параллельных запроса могут одновременно получить один и тот же `step` в состоянии `PENDING`, и оба попытаются его обновить. Первый запрос изменит шаг, второй всё ещё будет считать его `PENDING` и тоже изменит, что приведёт к дублированию решения или нарушению последовательности (например, в последовательном режиме).
- **Коренная причина:** Отсутствие пессимистической блокировки при чтении шага перед обновлением.
- **Исправление:** Добавить блокировку при получении шага:

```diff
  step = (
      instance.steps
+     .select_for_update()
      .filter(approver=approver, decision=StepDecision.PENDING)
      .order_by("sequence")
      .first()
  )
```

Также можно добавить проверку, что после блокировки шаг всё ещё `PENDING` (хотя в данном случае `select_for_update` гарантирует, что другие транзакции не изменят его до завершения текущей).

---

## 4. apps/notifications/services.py

**Дефект 4.1: Необработанные исключения от провайдеров**
- **Серьёзность:** P3
- **Файл:строка:** `notifications/services.py` ~ строка 22 (цикл по `extra_channels`)
- **Проблема:** В цикле перехватывается только `NotImplementedError`. Если провайдер выбросит любое другое исключение (например, сетевую ошибку), оно не будет перехвачено, и функция `notify` завершится ошибкой, хотя запись в БД уже создана. Это может привести к тому, что уведомление в БД есть, но отправка не удалась, и клиент не получит его. Также это может помешать выполнению вызывающего кода.
- **Коренная причина:** Слишком узкий перехват исключений.
- **Исправление:** Обернуть вызов каждого провайдера в общий `try/except` и логировать ошибку:

```diff
  for provider in extra_channels or []:
      try:
          provider.send(...)
-     except NotImplementedError:
+     except Exception as e:
          # Channel not enabled yet or other error; in-app record still stands.
+         logger.warning("Notification provider %s failed: %s", provider.__class__.__name__, e)
```

---

## 5. Итог по модулям

- **apps/quality:** найдены дефекты P1 и P2.
- **apps/workflow:** найден дефект P0 (критическая гонка).
- **apps/notifications:** найден дефект P3.

Остальные проверенные аспекты (компанийная изоляция, N+1, невалидные статусные переходы, аудит) соответствуют ожидаемому поведению и не содержат явных уязвимостей.

**Рекомендация:** Приоритетно исправить дефекты P0 (гонка в `record_decision`) и P1 (отсутствие атомарности и проверки прав).