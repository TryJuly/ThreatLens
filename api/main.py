import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI

from api.route import router

DATABASE_URL = os.environ["DATABASE_URL"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        app.state.conn = conn
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
