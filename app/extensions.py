"""
Extensiones de Flask instanciadas SIN vincularlas a una app todavía.
Se vinculan dentro de create_app() con extensión.init_app(app).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
cors = CORS()

# key_func=get_remote_address: limita por IP del cliente. En desarrollo,
# con storage en memoria (ver config.py), el contador se reinicia si el
# servidor se reinicia — limitación aceptable para este alcance; en
# producción real se recomienda un backend persistente (Redis).
limiter = Limiter(key_func=get_remote_address)
