from model import generate_response

from starlette.status import HTTP_400_BAD_REQUEST
from fastapi import HTTPException, APIRouter

router = APIRouter()


@router.get('/get-response')
async def get_response(query: str):
    if not query.strip():
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Input query cannot be empty')

    return generate_response(query)
