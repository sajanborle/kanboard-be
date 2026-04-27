from typing import Any

from starlette.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str | None = None,
    status_code: int = 200,
) -> JSONResponse:
    content = {
        "success": True,
        "data": data,
    }

    if message:
        content["message"] = message

    return JSONResponse(content=content, status_code=status_code)


def error_response(
    message: str,
    errors: dict | None = None,
    status_code: int = 400,
) -> JSONResponse:
    content = {
        "success": False,
        "message": message,
    }

    if errors:
        content["errors"] = errors

    return JSONResponse(content=content, status_code=status_code)


def paginated_response(
    items: list,
    pagination: dict,
    message: str | None = None,
    status_code: int = 200,
) -> JSONResponse:
    content = {
        "success": True,
        "data": items,
        "pagination": pagination,
    }

    if message:
        content["message"] = message

    return JSONResponse(content=content, status_code=status_code)
