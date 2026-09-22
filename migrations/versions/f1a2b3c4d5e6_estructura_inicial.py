"""estructura inicial: distritos, usuarios, incidentes

Revision ID: f1a2b3c4d5e6
Revises: 
Create Date: 2026-09-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f1a2b3c4d5e6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'distritos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('provincia', sa.String(length=100), nullable=False),
        sa.Column('departamento', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('apellido', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('telefono', sa.String(length=20), nullable=True),
        sa.Column('rol', sa.String(length=20), nullable=False),
        sa.Column('distrito_id', sa.Integer(), nullable=False),
        sa.Column('email_verificado', sa.Boolean(), nullable=False),
        sa.Column('token_verificacion', sa.String(length=255), nullable=True),
        sa.Column('intentos_fallidos', sa.Integer(), nullable=False),
        sa.Column('bloqueado_hasta', sa.DateTime(), nullable=True),
        sa.Column('fecha_registro', sa.DateTime(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.CheckConstraint("rol IN ('ciudadano', 'administrador')", name='ck_usuario_rol'),
        sa.ForeignKeyConstraint(['distrito_id'], ['distritos.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    op.create_table(
        'incidentes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=150), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('categoria', sa.String(length=50), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('foto_path', sa.String(length=255), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('distrito_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('comentario_admin', sa.Text(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "categoria IN ('bache', 'alumbrado', 'basura', 'alcantarillado', 'otro')",
            name='ck_incidente_categoria',
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'en_proceso', 'resuelto', 'rechazado')",
            name='ck_incidente_estado',
        ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['distrito_id'], ['distritos.id']),
        sa.ForeignKeyConstraint(['admin_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('incidentes')
    op.drop_table('usuarios')
    op.drop_table('distritos')
