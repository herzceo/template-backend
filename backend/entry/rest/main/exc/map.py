from litestar import status_codes as status
from litestar.types import ExceptionHandlersMap

from backend.app import errors

from .handler import generic_exc_handler_factory


def create_exception_handlers() -> ExceptionHandlersMap:
    return {
        errors.InvalidInputError: generic_exc_handler_factory(status.HTTP_400_BAD_REQUEST),
        errors.AuthenticationRequiredError: generic_exc_handler_factory(
            status.HTTP_401_UNAUTHORIZED
        ),
        errors.PermissionDeniedError: generic_exc_handler_factory(status.HTTP_403_FORBIDDEN),
        errors.NotFoundError: generic_exc_handler_factory(status.HTTP_404_NOT_FOUND),
        errors.ConflictError: generic_exc_handler_factory(status.HTTP_409_CONFLICT),
        errors.AlreadyExistsError: generic_exc_handler_factory(status.HTTP_409_CONFLICT),
        errors.ValidationFailedError: generic_exc_handler_factory(
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ),
    }
