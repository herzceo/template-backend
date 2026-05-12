from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING
from uuid import uuid4

from backend.app.shared.events.v1.user_verification_requested import UserVerificationRequested
from backend.app.shared.ports.outreach.email import EmailSender, EmailType
from backend.app.shared.ports.security.verification import VerificationCodeStore
from tests.integration.mocks import MockEmailSender, MockVerificationCodeStore

if TYPE_CHECKING:
    from dishka import AsyncContainer

    from backend.infra.database.psql.dbus.executor import QueueExecutor


async def test_issues_code_and_sends_email(
    executor: QueueExecutor,
    publish: Callable[..., Awaitable[None]],
    queue_container: AsyncContainer,
) -> None:
    user_id = uuid4()
    event = UserVerificationRequested(
        user_id=user_id,
        email="alice@example.com",
        username="alice",
    )

    await publish(event)
    assert await executor.process_one()

    async with queue_container() as c:
        email_sender = await c.get(EmailSender)
        store = await c.get(VerificationCodeStore)

    assert isinstance(email_sender, MockEmailSender)
    assert isinstance(store, MockVerificationCodeStore)

    sent = email_sender.get_sent()
    assert len(sent) == 1
    assert sent[0].to == "alice@example.com"
    assert sent[0].type == EmailType.EMAIL_VERIFICATION
    assert sent[0].params["username"] == "alice"

    stored_code = store.get_code(user_id)
    assert stored_code is not None
    assert sent[0].params["code"] == stored_code


async def test_stores_code_for_user(
    executor: QueueExecutor,
    publish: Callable[..., Awaitable[None]],
    queue_container: AsyncContainer,
) -> None:
    user_id = uuid4()
    event = UserVerificationRequested(
        user_id=user_id,
        email="bob@example.com",
        username="bob",
    )

    await publish(event)
    assert await executor.process_one()

    async with queue_container() as c:
        store = await c.get(VerificationCodeStore)

    assert isinstance(store, MockVerificationCodeStore)
    code = store.get_code(user_id)
    assert code is not None
    assert len(code) > 0


async def test_each_invocation_issues_new_code(
    executor: QueueExecutor,
    publish: Callable[..., Awaitable[None]],
    queue_container: AsyncContainer,
) -> None:
    user_id = uuid4()
    event = UserVerificationRequested(
        user_id=user_id,
        email="carol@example.com",
        username="carol",
    )

    await publish(event)
    assert await executor.process_one()

    async with queue_container() as c:
        store = await c.get(VerificationCodeStore)
    assert isinstance(store, MockVerificationCodeStore)
    first_code = store.get_code(user_id)

    await publish(event)
    assert await executor.process_one()

    async with queue_container() as c:
        store = await c.get(VerificationCodeStore)
    assert isinstance(store, MockVerificationCodeStore)
    second_code = store.get_code(user_id)

    assert first_code is not None
    assert second_code is not None
    assert first_code != second_code
