from fastapi import FastAPI
from . import websocket_handler

app = FastAPI()

app.include_router(websocket_handler.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Motospect API"}
