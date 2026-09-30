"""Переходы статуса шага (раздел 11.4 SPEC.md). Любой другой переход
API отклоняет с кодом 409."""
from app.errors import bad_request, conflict, forbidden


def validate_transition(
    old_status: str,
    new_status: str,
    actor_role: str,
    responsible: str | None = None,
    reason: str | None = None,
    comment: str | None = None,
):
    if old_status == new_status:
        raise conflict(f"Шаг уже в статусе {new_status}")

    # любой, кроме done -> done: куратор, ручное закрытие с комментарием
    if new_status == "done" and old_status != "done":
        if actor_role != "curator":
            raise forbidden("Закрыть шаг может только куратор")
        if not comment:
            raise bad_request("Ручное закрытие шага требует комментарий")
        return

    if (old_status, new_status) == ("blocked", "not_started"):
        if actor_role != "system":
            raise conflict("Этот переход выполняет только система")
        return

    if (old_status, new_status) == ("not_started", "in_progress"):
        if actor_role not in ("parent", "curator"):
            raise forbidden("Недостаточно прав")
        return

    if old_status in ("not_started", "in_progress", "overdue") and new_status == "done_by_parent":
        if actor_role != "parent":
            raise forbidden("Кнопка «Я сделал» доступна только родителю")
        if responsible != "parent":
            raise conflict("Кнопка «Я сделал» доступна только для шагов с ответственным parent")
        return

    if (old_status, new_status) == ("done_by_parent", "in_progress"):
        if actor_role != "curator":
            raise forbidden("Отклонить может только куратор")
        if not comment:
            raise bad_request("Отклонение требует комментарий")
        return

    if old_status in ("not_started", "in_progress", "blocked") and new_status == "overdue":
        if actor_role != "system":
            raise conflict("Этот переход выполняет только система")
        return

    if (old_status, new_status) == ("overdue", "in_progress"):
        if actor_role != "curator":
            raise forbidden("Перенести срок может только куратор")
        if not reason:
            raise bad_request("Перенос срока требует причину")
        return

    raise conflict(f"Переход {old_status} -> {new_status} недопустим")
