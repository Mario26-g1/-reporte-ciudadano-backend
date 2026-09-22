from datetime import datetime
from app.extensions import db


class Reaccion(db.Model):
    __tablename__ = "reacciones"

    __table_args__ = (
        db.CheckConstraint(
            "tipo IN ('me_afecta', 'es_urgente', 'ya_mejoro', 'sigue_igual')",
            name="ck_reaccion_tipo",
        ),
        # Un usuario no puede tener 2 reacciones simultáneas sobre el mismo
        # incidente. Si cambia de opinión, se actualiza la fila existente
        # (ver lógica en la ruta), no se inserta una nueva.
        db.UniqueConstraint("incidente_id", "usuario_id", name="uq_reaccion_usuario_incidente"),
    )

    id = db.Column(db.Integer, primary_key=True)
    incidente_id = db.Column(db.Integer, db.ForeignKey("incidentes.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    incidente = db.relationship("Incidente", backref="reacciones")
    usuario = db.relationship("Usuario")

    def __repr__(self):
        return f"<Reaccion {self.tipo} - incidente {self.incidente_id} - usuario {self.usuario_id}>"
