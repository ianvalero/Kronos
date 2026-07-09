class AppException(Exception):
    status_code = 500

    def __init__(self, detail: str):
        self.detail = detail


class InvalidApiKeyError(AppException):
    status_code = 401

class CollectionPermissionError(AppException):
    status_code = 403

class CollectionNotFoundError(AppException):
    status_code = 404

class DocumentNotFoundError(AppException):
    status_code = 404

class DocumentVersionNotFoundError(AppException):
    status_code = 404

class CeleryTaskEnqueueError(AppException):
    status_code = 503

class CeleryTaskNotFoundError(AppException):
    status_code = 404
