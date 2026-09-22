from app.extensions import db


class Distrito(db.Model):
    __tablename__ = "distritos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    provincia = db.Column(db.String(100), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)

    # Relaciones inversas (no crean columnas, solo permiten navegar
    # distrito.usuarios / distrito.incidentes desde Python).
    usuarios = db.relationship(
        "Usuario",
        back_populates="distrito",
        foreign_keys="Usuario.distrito_id",
    )
    incidentes = db.relationship(
        "Incidente",
        back_populates="distrito",
        foreign_keys="Incidente.distrito_id",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "provincia": self.provincia,
            "departamento": self.departamento,
        }

    def __repr__(self):
        return f"<Distrito {self.nombre}>"
