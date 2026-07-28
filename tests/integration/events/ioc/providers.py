from __future__ import annotations

from dishka import AsyncContainer, Provider, Scope, make_async_container

from backend.app.shared.ports.outreach.email import EmailSender
from backend.app.shared.ports.security.login_code import LoginCodeStore
from backend.app.shared.ports.security.verification import VerificationCodeStore
from backend.entry.queue.ioc import create_event_handlers_provider
from tests.integration.mocks import (
    MockEmailSender,
    MockLoginCodeStore,
    MockVerificationCodeStore,
)


def create_test_queue_container() -> AsyncContainer:
    mock_email = MockEmailSender()
    mock_verification = MockVerificationCodeStore()
    mock_login_code = MockLoginCodeStore()

    mocks = Provider(scope=Scope.APP)
    mocks.provide(lambda: mock_email, provides=EmailSender)
    mocks.provide(lambda: mock_verification, provides=VerificationCodeStore)
    mocks.provide(lambda: mock_login_code, provides=LoginCodeStore)

    return make_async_container(mocks, create_event_handlers_provider())
