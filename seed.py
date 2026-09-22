"""
Seed script: puebla la BD con datos mínimos para poder probar el sistema
de punta a punta sin depender de que el registro de ciudadanos (bloqueado
por SMTP) ya funcione.

Uso:
    python seed.py

Es idempotente: si ya hay distritos cargados, no hace nada, para evitar
errores de UNIQUE al correrlo dos veces sobre la misma BD.
"""

from app import create_app
from app.extensions import db
from app.models import Distrito, Usuario, Incidente


def run():
    app = create_app()
    with app.app_context():
        if Distrito.query.first():
            print("La base de datos ya tiene distritos cargados. Seed cancelado (evita duplicados).")
            print("Si quieres re-sembrar desde cero, borra las tablas y corre 'flask --app run db upgrade' de nuevo.")
            return

        # --- Distritos ---
        distritos_data = [
            {"nombre": "San Isidro", "provincia": "Lima", "departamento": "Lima"},
            {"nombre": "Miraflores", "provincia": "Lima", "departamento": "Lima"},
            {"nombre": "Surco", "provincia": "Lima", "departamento": "Lima"},
            {"nombre": "San Borja", "provincia": "Lima", "departamento": "Lima"},
            {"nombre": "La Molina", "provincia": "Lima", "departamento": "Lima"},
        ]
        distritos = {}
        for data in distritos_data:
            d = Distrito(**data)
            db.session.add(d)
            distritos[data["nombre"]] = d
        db.session.flush()  # asigna IDs sin hacer commit todavía, para poder usarlos abajo

        # --- Admins, uno por distrito (3 de los 5, para probar aislamiento) ---
        # Password de prueba única para los 3, SOLO para desarrollo/pruebas: Admin123!
        admins_data = [
            {"nombre": "Admin", "apellido": "San Isidro", "email": "admin.sanisidro@reportociudadano.pe", "distrito": "San Isidro"},
            {"nombre": "Admin", "apellido": "Miraflores", "email": "admin.miraflores@reportociudadano.pe", "distrito": "Miraflores"},
            {"nombre": "Admin", "apellido": "Surco", "email": "admin.surco@reportociudadano.pe", "distrito": "Surco"},
        ]
        admins = {}
        for data in admins_data:
            admin = Usuario(
                nombre=data["nombre"],
                apellido=data["apellido"],
                email=data["email"],
                rol="administrador",
                distrito_id=distritos[data["distrito"]].id,
                email_verificado=True,  # los admins no pasan por verificación de email
            )
            admin.set_password("Admin123!")
            db.session.add(admin)
            admins[data["distrito"]] = admin
        db.session.flush()

        # --- Ciudadano de prueba (email_verificado=True a propósito, ver nota arriba) ---
        ciudadano = Usuario(
            nombre="Ciudadano",
            apellido="Prueba",
            email="ciudadano.prueba@reportociudadano.pe",
            rol="ciudadano",
            distrito_id=distritos["San Isidro"].id,
            email_verificado=True,
        )
        ciudadano.set_password("Ciudadano123!")
        db.session.add(ciudadano)
        db.session.flush()

        # --- Incidentes de ejemplo en distritos distintos, para probar el filtro por distrito ---
        incidentes_data = [
            {
                "titulo": "Bache grande en la cuadra 5",
                "descripcion": "Bache profundo que afecta el tránsito vehicular.",
                "categoria": "bache",
                "distrito": "San Isidro",
            },
            {
                "titulo": "Poste de luz apagado hace una semana",
                "descripcion": "El poste frente al parque no enciende desde hace 7 días.",
                "categoria": "alumbrado",
                "distrito": "Miraflores",
            },
        ]
        for data in incidentes_data:
            inc = Incidente(
                titulo=data["titulo"],
                descripcion=data["descripcion"],
                categoria=data["categoria"],
                usuario_id=ciudadano.id,
                distrito_id=distritos[data["distrito"]].id,
            )
            db.session.add(inc)

        db.session.commit()

        print("Seed completado:")
        print(f"  - {len(distritos_data)} distritos creados.")
        print(f"  - {len(admins_data)} admins creados (password de prueba: Admin123!):")
        for data in admins_data:
            print(f"      {data['email']}  -> distrito: {data['distrito']}")
        print(f"  - 1 ciudadano de prueba creado (password: Ciudadano123!): {ciudadano.email}")
        print(f"  - {len(incidentes_data)} incidentes de ejemplo creados, en distritos distintos.")


if __name__ == "__main__":
    run()
