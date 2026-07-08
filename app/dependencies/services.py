from fastapi import Request

import app.services as services


def get_collection_service(request: Request) -> services.CollectionService:
    return request.app.state.collection_service

def get_user_service(request: Request) -> services.UserService:
    return request.app.state.user_service