import os
from flask import Flask, jsonify
from app.config import config_by_name
from app.extensions import db, jwt, migrate, cors, limiter


def create_app(config_name=None):
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, origins=app.config["ALLOWED_ORIGINS"])
    limiter.init_app(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    with app.app_context():
        from app import models  # noqa: F401

        # Callback de Flask-JWT-Extended: se ejecuta en CADA petición
        # protegida con @jwt_required. Si el jti del token está en la
        # lista negra, la petición se rechaza aunque la firma sea válida.
        from app.models import TokenRevocado

        @jwt.token_in_blocklist_loader
        def token_esta_revocado(jwt_header, jwt_payload):
            jti = jwt_payload["jti"]
            return TokenRevocado.query.filter_by(jti=jti).first() is not None

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.routes.incidentes import incidentes_bp
    app.register_blueprint(incidentes_bp, url_prefix="/api/incidentes")

    from app.routes.catalogos import catalogos_bp
    app.register_blueprint(catalogos_bp, url_prefix="/api")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso no encontrado."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Método no permitido para esta ruta."}), 405

    @app.errorhandler(413)
    def payload_too_large(e):
        max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return jsonify({"error": f"El archivo supera el límite permitido de {max_mb}MB."}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        # Manejador propio para que el límite de tasa responda igual de
        # consistente (JSON) que el resto de errores, no la página default.
        return jsonify({"error": "Demasiadas peticiones. Intenta de nuevo en unos minutos."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Error interno del servidor."}), 500

    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "ok", "servicio": "reporte-ciudadano-api"}), 200

    return app
