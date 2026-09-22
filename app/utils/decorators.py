from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def rol_requerido(*roles_permitidos):
    """
    Decorador para proteger rutas por rol.
    Uso: @rol_requerido("administrador")
         @rol_requerido("ciudadano", "administrador")

    Se apoya en el claim 'rol' que se agrega al token en /auth/login,
    no vuelve a consultar la BD en cada request — así la autorización
    es rápida y no depende de una query extra por petición.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("rol") not in roles_permitidos:
                return jsonify({"error": "No tienes permiso para acceder a este recurso."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
