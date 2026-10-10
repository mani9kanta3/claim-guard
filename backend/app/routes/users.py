from flask import Blueprint, jsonify, request

from app.auth.decorators import role_required
from app.extensions import db
from app.models import User

users_bp = Blueprint("users", __name__)


@users_bp.get("")
@role_required("ADMIN")
def list_users():
    query = db.select(User).order_by(User.full_name)

    role = request.args.get("role")
    if role:
        query = query.filter_by(role=role)

    users = db.session.execute(query).scalars().all()
    return jsonify([user.to_dict() for user in users])
