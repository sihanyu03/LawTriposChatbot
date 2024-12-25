import controller
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI()
load_dotenv()
allowed_origins = [os.getenv('ORIGIN')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(controller.router)
handler = Mangum(app)
