from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    # CHECK constraint en vez de tabla Rol aparte: solo 2 valores fijos,
    # no se espera que crezcan dinámicamente en este proyecto.
    __table_args__ = (
        db.CheckConstraint("rol IN ('ciudadano', 'administrador')", name="ck_usuario_rol"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    rol = db.Column(db.String(20), nullable=False, default="ciudadano")

    distrito_id = db.Column(db.Integer, db.ForeignKey("distritos.id"), nullable=False)
    distrito = db.relationship("Distrito", back_populates="usuarios", foreign_keys=[distrito_id])

    email_verificado = db.Column(db.Boolean, nullable=False, default=False)
    token_verificacion = db.Column(db.String(255), nullable=True)

    intentos_fallidos = db.Column(db.Integer, nullable=False, default=0)
    bloqueado_hasta = db.Column(db.DateTime, nullable=True)

    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    activo = db.Column(db.Boolean, nullable=False, default=True)  # soft delete

    # Relaciones inversas hacia Incidente. Como Usuario se referencia dos
    # veces desde Incidente (usuario_id y admin_id), hay que indicar
    # foreign_keys explícitamente o SQLAlchemy no sabe cuál usar.
    incidentes_reportados = db.relationship(
        "Incidente",
        back_populates="usuario",
        foreign_keys="Incidente.usuario_id",
    )
    incidentes_atendidos = db.relationship(
        "Incidente",
        back_populates="admin",
        foreign_keys="Incidente.admin_id",
    )

    def set_password(self, password_plano):
        """Genera y guarda el hash. Nunca se guarda la contraseña en texto plano."""
        self.password_hash = generate_password_hash(password_plano)

    def check_password(self, password_plano):
        return check_password_hash(self.password_hash, password_plano)

    def esta_bloqueado(self):
        """True si el usuario tiene un bloqueo temporal vigente (throttling de login)."""
        return self.bloqueado_hasta is not None and self.bloqueado_hasta > datetime.utcnow()

    def to_dict(self):
        # OJO: nunca incluir password_hash aquí. Este dict es lo que
        # potencialmente se serializa y se envía al cliente vía API.
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "telefono": self.telefono,
            "rol": self.rol,
            "distrito_id": self.distrito_id,
            "email_verificado": self.email_verificado,
            "activo": self.activo,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
        }

    def __repr__(self):
        return f"<Usuario {self.email} ({self.rol})>"
