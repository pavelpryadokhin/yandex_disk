from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router as apirouter
from config import get_settings
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from loguru import logger
from api.schemas.error import ErrorResult
settings = get_settings()


def get_application() -> FastAPI:
    application = FastAPI(title=settings.PROJECT_NAME,
                          debug=settings.DEBUG,
                          version=settings.VERSION)
    application.add_middleware(CORSMiddleware,
                               allow_origins=settings.ALLOWED_HOSTS or ['*'],
                               allow_credentials=True,
                               allow_methods=['*'],
                               allow_headers=['*'])
    application.include_router(router=apirouter, prefix=settings.API_PREFIX)

    @application.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(exc)
        return JSONResponse(status_code=exc.status_code,
                            content=ErrorResult(code=exc.status_code,
                                                message=exc.detail).dict())

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        logger.error(exc)
        return JSONResponse(status_code=400,
                            content=ErrorResult(code=400,
                                                message='Validation Failed').dict())

    return application


app = get_application()
