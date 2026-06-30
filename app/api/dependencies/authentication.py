"""API dependencies for authentication."""

from typing import Annotated

from app.application.services.authentication_service import (
    get_authenticated_page_user,
    get_current_user,
    get_optional_user,
)
from app.database.models.user import User
from fastapi import Depends
from fastapi.responses import RedirectResponse

CurrentUserDependency = Annotated[User, Depends(get_current_user)]
OptionalUserDependency = Annotated[User | None, Depends(get_optional_user)]
AuthenticatedPageUserDependency = Annotated[
    User | RedirectResponse,
    Depends(get_authenticated_page_user),
]
