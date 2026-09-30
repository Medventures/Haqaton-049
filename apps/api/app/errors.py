"""Единый формат ошибок (раздел 13 SPEC.md): {"error": {"code", "message"}}."""
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"error": {"code": code, "message": message}})


def not_found(message: str = "Не найдено") -> AppError:
    return AppError(404, "not_found", message)


def forbidden(message: str = "Недостаточно прав") -> AppError:
    return AppError(403, "forbidden", message)


def conflict(message: str = "Недопустимый переход") -> AppError:
    return AppError(409, "conflict", message)


def bad_request(message: str = "Некорректный запрос") -> AppError:
    return AppError(422, "invalid_request", message)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        body = detail
    else:
        body = {"error": {"code": "http_error", "message": str(detail)}}
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_exception_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "invalid_request", "message": str(exc)}},
    )
