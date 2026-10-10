from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.errors import AppError

auth_bp = Blueprint("auth", __name__)


def find_user_by_email(email):
    return db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()


@auth_bp.post("/register")
def register():
    data = RegisterRequest.model_validate(request.get_json(silent=True) or {})

    if find_user_by_email(data.email):
        raise AppError("EMAIL_TAKEN", "An account with this email already exists", 409)

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=generate_password_hash(data.password),
        role="CUSTOMER",
    )
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@auth_bp.post("/login")
def login():
    data = LoginRequest.model_validate(request.get_json(silent=True) or {})

    user = find_user_by_email(data.email)

    if user is None or not check_password_hash(user.password_hash, data.password):
        raise AppError("INVALID_LOGIN", "Wrong email or password", 401)

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    return jsonify({"access_token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))

    if user is None:
        raise AppError("NOT_FOUND", "User not found", 404)

    return jsonify(user.to_dict())
