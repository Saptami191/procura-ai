from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException
from app.repositories.exceptions import EntityNotFoundError, DuplicateEntityError

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    status_code = exc.status_code
    
    # Map repository exceptions to standard HTTP status codes
    if isinstance(exc, EntityNotFoundError):
        status_code = 404
    elif isinstance(exc, DuplicateEntityError):
        status_code = 409
        
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
