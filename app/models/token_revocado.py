from datetime import datetime
from app.extensions import db


class TokenRevocado(db.Model):
    """
    Lista negra de tokens JWT invalidados manualmente (logout).

    Por qué existe: un JWT es válido por sí mismo hasta que expira — el
    servidor normalmente no necesita "recordar" nada. Pero eso significa
    que sin esta tabla, un token robado o copiado antes del logout seguiría
    funcionando el resto de su vigencia (hasta 7 días en el caso del
    refresh_token). Guardar el jti (JWT ID, único por token) revocado
    permite que el servidor rechace ese token específico de inmediato,
    aunque su firma siga siendo válida.
    """
    __tablename__ = "tokens_revocados"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    fecha_revocacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<TokenRevocado {self.jti}>"
