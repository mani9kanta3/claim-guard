from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.utils.errors import AppError


def role_required(*allowed_roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            role = get_jwt().get("role")
            if role not in allowed_roles:
                raise AppError("FORBIDDEN", "You do not have permission to do this", 403)

            return view_function(*args, **kwargs)

        return wrapper

    return decorator
