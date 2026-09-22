import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración base, compartida por todos los entornos."""

    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-key-no-usar-en-produccion")

    # PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # Uploads
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    # SMTP (pendiente, ver TODO en auth.py)
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    # Throttling de login
    MAX_INTENTOS_FALLIDOS = 5
    MINUTOS_BLOQUEO = 15

    # CORS: lista de orígenes permitidos, separados por coma en el .env.
    # "*" (todos) queda como valor por defecto SOLO para desarrollo — en
    # producción debe reemplazarse por el dominio real del frontend.
    _origenes_raw = os.getenv("ALLOWED_ORIGINS", "*")
    ALLOWED_ORIGINS = [o.strip() for o in _origenes_raw.split(",")] if _origenes_raw != "*" else "*"

    # Rate limiting global (Flask-Limiter). Límite generoso por defecto:
    # protege contra abuso/DoS accidental sin restringir uso normal.
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"  # ver nota de limitación en el código


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
