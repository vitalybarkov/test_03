# from pydantic import BaseSettings
from fastapi import HTTPException, Header

async def get_api_key(api_key: str = Header(..., alias = "X-API-KEY")):
    API_KEY: str = "x"
    if api_key != API_KEY:
        raise HTTPException(
            status_code = 403,
            detail = "Invalid API Key"
        )
    return api_key