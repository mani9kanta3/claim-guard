from flask import jsonify
from pydantic import ValidationError

from app.extensions import jwt


class AppError(Exception):
    def __init__(self, error, message, status_code=400):
        super().__init__(message)
        self.error = error
        self.message = message
        self.status_code = status_code


def error_response(error, message, status_code):
    return jsonify({"error": error, "message": message}), status_code


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        return error_response(e.error, e.message, e.status_code)

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        first = e.errors()[0]
        message = first["msg"].removeprefix("Value error, ")
        field = ".".join(str(part) for part in first["loc"])
        if field:
            message = f"{field}: {message}"
        return error_response("VALIDATION_ERROR", message, 400)

    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response("NOT_FOUND", "This URL does not exist", 404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error_response("METHOD_NOT_ALLOWED", "This method is not allowed here", 405)

    @app.errorhandler(413)
    def handle_file_too_large(e):
        return error_response("FILE_TOO_LARGE", "File is too large. Maximum size is 2 MB", 413)

    @app.errorhandler(500)
    def handle_server_error(e):
        return error_response("SERVER_ERROR", "Something went wrong on the server", 500)

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_response("UNAUTHORIZED", "Please log in first", 401)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_response("UNAUTHORIZED", "Invalid token, please log in again", 401)

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return error_response("UNAUTHORIZED", "Session expired, please log in again", 401)
