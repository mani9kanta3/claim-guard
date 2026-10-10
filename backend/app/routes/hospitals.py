from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.auth.decorators import role_required
from app.extensions import db
from app.models import Hospital
from app.schemas.admin import HospitalCreateRequest

hospitals_bp = Blueprint("hospitals", __name__)


@hospitals_bp.get("")
@jwt_required()
def list_hospitals():
    hospitals = db.session.execute(db.select(Hospital).order_by(Hospital.name)).scalars().all()
    return jsonify([hospital.to_dict() for hospital in hospitals])


@hospitals_bp.post("")
@role_required("ADMIN")
def create_hospital():
    data = HospitalCreateRequest.model_validate(request.get_json(silent=True) or {})

    hospital = Hospital(name=data.name.strip(), city=data.city, is_network=data.is_network)
    db.session.add(hospital)
    db.session.commit()

    return jsonify(hospital.to_dict()), 201
