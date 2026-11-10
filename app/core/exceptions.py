# app/core/exceptions.py
from fastapi import HTTPException, status

class KolixException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundException(KolixException):
    def __init__(self, resource: str, identifier: str | None = None):
        msg = f"{resource} '{identifier}' introuvable." if identifier else f"{resource} introuvable."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=msg)

class UnauthorizedException(KolixException):
    def __init__(self, detail: str = "Authentification requise ou identifiants incorrects."):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class ForbiddenException(KolixException):
    def __init__(self, detail: str = "Vous n'avez pas les permissions requises pour ce module."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class BadRequestException(KolixException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ConflictException(KolixException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

