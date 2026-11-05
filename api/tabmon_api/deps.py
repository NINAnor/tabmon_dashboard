from fastapi import Request

from .data import DataStore


def get_store(request: Request) -> DataStore:
    return request.app.state.store
