from datetime import datetime
from app.extensions import db


class Incidente(db.Model):
    __tablename__ = "incidentes"

    __table_args__ = (
        db.CheckConstraint(
            "categoria IN ('bache', 'alumbrado', 'basura', 'alcantarillado', 'otro')",
            name="ck_incidente_categoria",
        ),
        db.CheckConstraint(
            "estado IN ('pendiente', 'en_proceso', 'resuelto', 'rechazado')",
            name="ck_incidente_estado",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    foto_path = db.Column(db.String(255), nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    usuario = db.relationship("Usuario", back_populates="incidentes_reportados", foreign_keys=[usuario_id])

    # distrito_id se guarda aquí también (no solo en usuario.distrito_id) a propósito:
    # 1) evita un JOIN extra al filtrar incidentes por distrito (caso de uso más frecuente del admin)
    # 2) preserva el distrito real del incidente si el usuario cambia de distrito después
    distrito_id = db.Column(db.Integer, db.ForeignKey("distritos.id"), nullable=False)
    distrito = db.relationship("Distrito", back_populates="incidentes", foreign_keys=[distrito_id])

    admin_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    admin = db.relationship("Usuario", back_populates="incidentes_atendidos", foreign_keys=[admin_id])

    comentario_admin = db.Column(db.Text, nullable=True)

    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_actualizacion = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "categoria": self.categoria,
            "estado": self.estado,
            "foto_path": self.foto_path,
            "usuario_id": self.usuario_id,
            "distrito_id": self.distrito_id,
            "admin_id": self.admin_id,
            "comentario_admin": self.comentario_admin,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

    def __repr__(self):
        return f"<Incidente {self.id} - {self.titulo} ({self.estado})>"
