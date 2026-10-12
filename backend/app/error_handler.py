from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

async def global_exception_handler(
    request: Request,
    exc: Exception
):
    print("ERROR:")
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
            "detail": str(exc)
        }
    )