from pydantic import BaseModel


class LoginModel(BaseModel):
    username: str
    password: str


class TokenModel(BaseModel):
    token: str

class QueryModel(BaseModel):
    query: str

class ResponseModel(BaseModel):
    files: list[str]
    pages: list[int]
    answer: str
