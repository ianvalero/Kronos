class AppException(Exception):
    status_code = 500

    def __init__(self, detail: str):
        self.detail = detail


class CollectionPermissionError(AppException):
    status_code = 403


class CollectionNotFoundError(AppException):
    status_code = 404


class InvalidApiKeyError(AppException):
    status_code = 401