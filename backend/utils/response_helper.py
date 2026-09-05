from fastapi import HTTPException


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=404, detail={"error": message})
