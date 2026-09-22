from flask import Blueprint, jsonify
from app.models import Distrito
from app.routes.incidentes import CATEGORIAS_VALIDAS, ESTADOS_VALIDOS, REACCIONES_INFO

catalogos_bp = Blueprint("catalogos", __name__)


@catalogos_bp.route("/distritos", methods=["GET"])
def listar_distritos():
    # Público a propósito: el formulario de registro lo necesita
    # ANTES de que exista una sesión con JWT.
    distritos = Distrito.query.order_by(Distrito.nombre).all()
    return jsonify({"distritos": [d.to_dict() for d in distritos]}), 200


@catalogos_bp.route("/categorias", methods=["GET"])
def listar_categorias():
    # Se reutilizan las mismas constantes que validan en el backend
    # (app/routes/incidentes.py), para que Flutter y el backend nunca
    # se desincronicen sobre qué valores son válidos.
    return jsonify({"categorias": sorted(CATEGORIAS_VALIDAS)}), 200


@catalogos_bp.route("/estados", methods=["GET"])
def listar_estados():
    return jsonify({"estados": sorted(ESTADOS_VALIDOS)}), 200


@catalogos_bp.route("/reacciones", methods=["GET"])
def listar_reacciones():
    return jsonify({
        "reacciones": [
            {"tipo": tipo, "emoji": info["emoji"], "etiqueta": info["etiqueta"]}
            for tipo, info in REACCIONES_INFO.items()
        ]
    }), 200
