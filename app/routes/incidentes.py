from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.extensions import db
from app.models import Incidente, Distrito, Reaccion
from app.utils.decorators import rol_requerido
from app.utils.archivos import extension_permitida, es_imagen_valida, guardar_foto

incidentes_bp = Blueprint("incidentes", __name__)

CATEGORIAS_VALIDAS = {"bache", "alumbrado", "basura", "alcantarillado", "otro"}
ESTADOS_VALIDOS = {"pendiente", "en_proceso", "resuelto", "rechazado"}

REACCIONES_INFO = {
    "me_afecta": {"emoji": "👍", "etiqueta": "Me afecta también"},
    "es_urgente": {"emoji": "😠", "etiqueta": "Es urgente"},
    "ya_mejoro": {"emoji": "✅", "etiqueta": "Ya mejoró"},
    "sigue_igual": {"emoji": "⚠️", "etiqueta": "Sigue igual"},
}
TIPOS_REACCION_VALIDOS = set(REACCIONES_INFO.keys())


def _conteo_reacciones(incidente_id):
    filas = (
        db.session.query(Reaccion.tipo, db.func.count(Reaccion.id))
        .filter_by(incidente_id=incidente_id)
        .group_by(Reaccion.tipo)
        .all()
    )
    conteo = {tipo: 0 for tipo in TIPOS_REACCION_VALIDOS}
    for tipo, cantidad in filas:
        conteo[tipo] = cantidad
    return conteo


def _mi_reaccion(incidente_id, usuario_id):
    reaccion = Reaccion.query.filter_by(incidente_id=incidente_id, usuario_id=usuario_id).first()
    return reaccion.tipo if reaccion else None


def _incidente_con_reacciones(incidente, usuario_id):
    data = incidente.to_dict()
    data["reacciones"] = _conteo_reacciones(incidente.id)
    data["mi_reaccion"] = _mi_reaccion(incidente.id, usuario_id)
    return data


@incidentes_bp.route("", methods=["POST"])
@rol_requerido("ciudadano")
def crear_incidente():
    usuario_id = int(get_jwt_identity())

    titulo = (request.form.get("titulo") or "").strip()
    descripcion = (request.form.get("descripcion") or "").strip()
    categoria = (request.form.get("categoria") or "").strip()
    distrito_id = request.form.get("distrito_id")

    if not titulo or not descripcion or not categoria or not distrito_id:
        return jsonify({"error": "titulo, descripcion, categoria y distrito_id son requeridos."}), 400

    if len(titulo) > 150:
        return jsonify({"error": "El título no puede superar los 150 caracteres."}), 400

    if categoria not in CATEGORIAS_VALIDAS:
        return jsonify({"error": f"categoria inválida. Valores permitidos: {', '.join(CATEGORIAS_VALIDAS)}"}), 400

    distrito = Distrito.query.get(distrito_id)
    if not distrito:
        return jsonify({"error": "El distrito indicado no existe."}), 400

    foto_filename = None
    if "foto" in request.files:
        foto = request.files["foto"]
        if foto.filename:
            if not extension_permitida(foto.filename):
                return jsonify({
                    "error": f"Extensión no permitida. Solo se aceptan: {', '.join(current_app.config['ALLOWED_EXTENSIONS'])}"
                }), 400
            # Validación de CONTENIDO, no solo de extensión: rechaza un
            # archivo renombrado a .jpg que en realidad no es una imagen.
            if not es_imagen_valida(foto):
                return jsonify({"error": "El archivo no es una imagen válida."}), 400
            foto_filename = guardar_foto(foto)

    incidente = Incidente(
        titulo=titulo,
        descripcion=descripcion,
        categoria=categoria,
        foto_path=foto_filename,
        usuario_id=usuario_id,
        distrito_id=distrito.id,
    )
    db.session.add(incidente)
    db.session.commit()

    return jsonify({"mensaje": "Incidente creado correctamente.", "incidente": incidente.to_dict()}), 201


@incidentes_bp.route("", methods=["GET"])
@jwt_required()
def listar_incidentes():
    claims = get_jwt()
    usuario_id = int(get_jwt_identity())
    rol = claims.get("rol")

    query = Incidente.query

    if rol == "administrador":
        query = query.filter_by(distrito_id=claims.get("distrito_id"))
    else:
        query = query.filter_by(usuario_id=usuario_id)

    estado = request.args.get("estado")
    if estado:
        if estado not in ESTADOS_VALIDOS:
            return jsonify({"error": f"estado inválido. Valores permitidos: {', '.join(ESTADOS_VALIDOS)}"}), 400
        query = query.filter_by(estado=estado)

    categoria = request.args.get("categoria")
    if categoria:
        if categoria not in CATEGORIAS_VALIDAS:
            return jsonify({"error": f"categoria inválida. Valores permitidos: {', '.join(CATEGORIAS_VALIDAS)}"}), 400
        query = query.filter_by(categoria=categoria)

    incidentes = query.order_by(Incidente.fecha_creacion.desc()).all()
    return jsonify({"incidentes": [i.to_dict() for i in incidentes]}), 200


@incidentes_bp.route("/comunidad", methods=["GET"])
@rol_requerido("ciudadano")
def listar_comunidad():
    claims = get_jwt()
    usuario_id = int(get_jwt_identity())
    distrito_id = claims.get("distrito_id")

    query = Incidente.query.filter_by(distrito_id=distrito_id)

    estado = request.args.get("estado")
    if estado:
        if estado not in ESTADOS_VALIDOS:
            return jsonify({"error": f"estado inválido. Valores permitidos: {', '.join(ESTADOS_VALIDOS)}"}), 400
        query = query.filter_by(estado=estado)

    categoria = request.args.get("categoria")
    if categoria:
        if categoria not in CATEGORIAS_VALIDAS:
            return jsonify({"error": f"categoria inválida. Valores permitidos: {', '.join(CATEGORIAS_VALIDAS)}"}), 400
        query = query.filter_by(categoria=categoria)

    incidentes = query.order_by(Incidente.fecha_creacion.desc()).all()
    resultado = [_incidente_con_reacciones(inc, usuario_id) for inc in incidentes]
    return jsonify({"incidentes": resultado}), 200


@incidentes_bp.route("/<int:incidente_id>", methods=["GET"])
@jwt_required()
def detalle_incidente(incidente_id):
    claims = get_jwt()
    usuario_id = int(get_jwt_identity())
    rol = claims.get("rol")

    incidente = Incidente.query.get(incidente_id)
    if not incidente:
        return jsonify({"error": "Incidente no encontrado."}), 404

    if rol == "administrador" and incidente.distrito_id != claims.get("distrito_id"):
        return jsonify({"error": "No tienes permiso para ver este incidente."}), 403
    if rol == "ciudadano" and incidente.usuario_id != usuario_id:
        return jsonify({"error": "No tienes permiso para ver este incidente."}), 403

    return jsonify({"incidente": incidente.to_dict()}), 200


@incidentes_bp.route("/<int:incidente_id>/estado", methods=["PATCH"])
@rol_requerido("administrador")
def cambiar_estado(incidente_id):
    claims = get_jwt()
    admin_id = int(get_jwt_identity())

    incidente = Incidente.query.get(incidente_id)
    if not incidente:
        return jsonify({"error": "Incidente no encontrado."}), 404

    if incidente.distrito_id != claims.get("distrito_id"):
        return jsonify({"error": "No tienes permiso para modificar incidentes de otro distrito."}), 403

    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado")
    comentario = data.get("comentario_admin")

    if not nuevo_estado or nuevo_estado not in ESTADOS_VALIDOS:
        return jsonify({"error": f"estado inválido. Valores permitidos: {', '.join(ESTADOS_VALIDOS)}"}), 400

    incidente.estado = nuevo_estado
    if comentario is not None:
        incidente.comentario_admin = comentario
    incidente.admin_id = admin_id

    db.session.commit()

    return jsonify({"mensaje": "Estado actualizado.", "incidente": incidente.to_dict()}), 200


@incidentes_bp.route("/<int:incidente_id>/reaccion", methods=["POST"])
@rol_requerido("ciudadano")
def reaccionar(incidente_id):
    usuario_id = int(get_jwt_identity())

    incidente = Incidente.query.get(incidente_id)
    if not incidente:
        return jsonify({"error": "Incidente no encontrado."}), 404

    data = request.get_json(silent=True) or {}
    tipo = data.get("tipo")
    if tipo not in TIPOS_REACCION_VALIDOS:
        return jsonify({
            "error": f"tipo de reacción inválido. Valores permitidos: {', '.join(TIPOS_REACCION_VALIDOS)}"
        }), 400

    existente = Reaccion.query.filter_by(incidente_id=incidente_id, usuario_id=usuario_id).first()
    if existente:
        existente.tipo = tipo
    else:
        db.session.add(Reaccion(incidente_id=incidente_id, usuario_id=usuario_id, tipo=tipo))

    db.session.commit()

    return jsonify({
        "mensaje": "Reacción registrada.",
        "reacciones": _conteo_reacciones(incidente_id),
        "mi_reaccion": tipo,
    }), 200


@incidentes_bp.route("/<int:incidente_id>/reaccion", methods=["DELETE"])
@rol_requerido("ciudadano")
def quitar_reaccion(incidente_id):
    usuario_id = int(get_jwt_identity())

    existente = Reaccion.query.filter_by(incidente_id=incidente_id, usuario_id=usuario_id).first()
    if existente:
        db.session.delete(existente)
        db.session.commit()

    return jsonify({
        "mensaje": "Reacción eliminada.",
        "reacciones": _conteo_reacciones(incidente_id),
    }), 200


@incidentes_bp.route("/uploads/<path:filename>", methods=["GET"])
def servir_foto(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
