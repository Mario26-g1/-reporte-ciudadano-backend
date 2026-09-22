import io
import uuid
import os
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image, UnidentifiedImageError


def extension_permitida(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def es_imagen_valida(file_storage):
    """
    Verifica que el CONTENIDO del archivo sea realmente una imagen abrible,
    no solo que el nombre termine en .jpg/.png. Sin esto, alguien podría
    renombrar cualquier archivo (incluyendo uno malicioso) a "foto.jpg" y
    la whitelist de extensión lo aceptaría igual.

    Usa Image.verify(), que detecta corrupción/formato inválido sin cargar
    la imagen completa en memoria innecesariamente. Deja el stream del
    archivo en la posición 0 al terminar, para que guardar_foto() pueda
    leerlo de nuevo desde el inicio.
    """
    try:
        posicion_original = file_storage.stream.tell()
        datos = file_storage.read()
        file_storage.stream.seek(posicion_original)

        Image.open(io.BytesIO(datos)).verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def guardar_foto(file_storage):
    filename_seguro = secure_filename(file_storage.filename)
    nombre_unico = f"{uuid.uuid4().hex}_{filename_seguro}"
    ruta_completa = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_unico)
    file_storage.save(ruta_completa)
    return nombre_unico
