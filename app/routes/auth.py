import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    decode_token,
)
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.models import Usuario, Distrito, TokenRevocado

auth_bp = Blueprint("auth", __name__)

# Espejo exacto de la regla que ya existe en Flutter (register_screen.dart):
# mínimo 6 caracteres, al menos una letra y un número. Se repite aquí porque
# la validación del cliente nunca debe ser la única línea de defensa — un
# request directo a la API (como los que hicimos en Postman toda esta
# conversación) se salta cualquier regla que solo viva en la app.
PATRON_LETRA = re.compile(r"[A-Za-z]")
PATRON_NUMERO = re.compile(r"[0-9]")


def _password_valida(password):
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    if not PATRON_LETRA.search(password) or not PATRON_NUMERO.search(password):
        return False, "La contraseña debe incluir al menos una letra y un número."
    return True, None


def _claims_para(usuario):
    return {"rol": usuario.rol, "distrito_id": usuario.distrito_id}


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    data = request.get_json(silent=True) or {}

    campos_requeridos = ["nombre", "apellido", "email", "password", "distrito_id"]
    faltantes = [c for c in campos_requeridos if not data.get(c)]
    if faltantes:
        return jsonify({"error": f"Faltan campos requeridos: {', '.join(faltantes)}"}), 400

    password_ok, mensaje_password = _password_valida(data["password"])
    if not password_ok:
        return jsonify({"error": mensaje_password}), 400

    email = data["email"].strip().lower()

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con ese email."}), 409

    distrito = Distrito.query.get(data["distrito_id"])
    if not distrito:
        return jsonify({"error": "El distrito indicado no existe."}), 400

    usuario = Usuario(
        nombre=data["nombre"].strip(),
        apellido=data["apellido"].strip(),
        email=email,
        telefono=data.get("telefono"),
        rol="ciudadano",
        distrito_id=distrito.id,
        # TODO: revertir a False cuando SMTP esté resuelto.
        email_verificado=True,
    )
    usuario.set_password(data["password"])

    db.session.add(usuario)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe una cuenta con ese email."}), 409

    return jsonify({
        "mensaje": "Cuenta creada correctamente.",
        "usuario": usuario.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20 per minute")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email y contraseña son requeridos."}), 400

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or not usuario.activo:
        return jsonify({"error": "Credenciales inválidas."}), 401

    if usuario.esta_bloqueado():
        minutos_restantes = int((usuario.bloqueado_hasta - datetime.utcnow()).total_seconds() // 60) + 1
        return jsonify({
            "error": f"Cuenta bloqueada temporalmente. Intenta en {minutos_restantes} minuto(s)."
        }), 423

    if not usuario.check_password(password):
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= current_app.config["MAX_INTENTOS_FALLIDOS"]:
            usuario.bloqueado_hasta = datetime.utcnow() + timedelta(
                minutes=current_app.config["MINUTOS_BLOQUEO"]
            )
        db.session.commit()
        return jsonify({"error": "Credenciales inválidas."}), 401

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.session.commit()

    claims = _claims_para(usuario)
    access_token = create_access_token(identity=str(usuario.id), additional_claims=claims)
    refresh_token = create_refresh_token(identity=str(usuario.id), additional_claims=claims)

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "usuario": usuario.to_dict(),
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)

    if not usuario or not usuario.activo:
        return jsonify({"error": "Usuario no encontrado o inactivo."}), 401

    claims = _claims_para(usuario)
    nuevo_access_token = create_access_token(identity=str(usuario.id), additional_claims=claims)

    return jsonify({"access_token": nuevo_access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        return jsonify({"error": "Usuario no encontrado."}), 404

    return jsonify({"usuario": usuario.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Revoca el access_token actual (el que viaja en el header Authorization)
    y, si se envía en el body, también el refresh_token — así un logout
    invalida de verdad la sesión del lado del servidor, no solo borra el
    token guardado en el celular.
    """
    jti_access = get_jwt()["jti"]
    db.session.add(TokenRevocado(jti=jti_access))

    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token")
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            db.session.add(TokenRevocado(jti=payload["jti"]))
        except Exception:
            # Si el refresh_token ya es inválido o está mal formado, no es
            # un error del logout en sí — el access_token ya se revocó.
            pass

    db.session.commit()
    return jsonify({"mensaje": "Sesión cerrada correctamente."}), 200
