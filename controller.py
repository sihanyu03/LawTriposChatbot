import utils
from services import generate_answer, clear_thread_id_history
from models import LoginModel, TokenModel, QueryModel
import os
from typing import Annotated
import datetime
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials


load_dotenv()
router = APIRouter()
security = HTTPBearer()


@router.post('/login')
async def login(body: LoginModel):
    username = body.username
    password = body.password

    if not utils.check_login_details(username, password):
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail='Username or password incorrect')

    clear_thread_id_history(username)

    body_dict = {'username': body.username, 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)}
    jwt_token = jwt.encode(body_dict, os.getenv('JWT_SECRET'))
    return TokenModel(token=jwt_token)


@router.post('/get-answer')
async def get_answer(body: QueryModel, token: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]):
    query = body.query

    if not query.strip():
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Input query cannot be empty')

    try:
        decoded_token = jwt.decode(token.credentials, os.getenv('JWT_SECRET'), algorithms=os.getenv('TOKEN_ALGORITHM'))
    except DecodeError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid token')
    except ExpiredSignatureError:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='Token has expired, please refresh and log in again')

    return await generate_answer(query, decoded_token['username'])
