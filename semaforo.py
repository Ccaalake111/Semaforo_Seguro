"""Reglas de negocio y persistencia para el prototipo académico Semáforo Seguro.

Solo se deben utilizar datos ficticios. No es un sistema de emergencias.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROGRAMAS = (
    {"id": "capacitacion", "nombre": "Capacitación para el empleo", "tipo": "Formación", "detalle": "Orientación y talleres de habilidades laborales.", "contacto": "Consultar con el centro municipal correspondiente (referencia ilustrativa)."},
    {"id": "orientacion", "nombre": "Orientación social", "tipo": "Acompañamiento", "detalle": "Información general sobre servicios sociales disponibles.", "contacto": "Contactar con servicios oficiales de atención social (referencia ilustrativa)."},
    {"id": "emprendimiento", "nombre": "Taller de emprendimiento", "tipo": "Emprendimiento", "detalle": "Información para evaluar alternativas voluntarias de autoempleo.", "contacto": "Consultar programas locales de capacitación (referencia ilustrativa)."},
)
ESTADOS = ("Pendiente", "En proceso", "Atendida")
CATEGORIAS = ("Riesgo vial", "Exposición ambiental", "Trato hostil", "Otro")
ZONAS = ("Zona norte", "Zona centro", "Zona sur", "Otra zona general")


def conectar(ruta: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(str(ruta), timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def inicializar(ruta: str | Path) -> None:
    with conectar(ruta) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                clave_hash TEXT NOT NULL,
                creado TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS incidentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                zona TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Pendiente',
                creado TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS solicitudes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                programa_id TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Pendiente',
                creado TEXT NOT NULL
            );
        """)


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def registrar(ruta: str | Path, email: str, clave: str, consentimiento: bool, mayor_edad: bool) -> int:
    email = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Introduce un correo válido.")
    if len(clave) < 8 or len(clave) > 128:
        raise ValueError("La contraseña debe tener entre 8 y 128 caracteres.")
    if not consentimiento or not mayor_edad:
        raise ValueError("Esta demostración requiere consentimiento y confirmación de mayoría de edad.")
    sal = secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, 260_000)
    codificado = f"{sal.hex()}${derivada.hex()}"
    try:
        with conectar(ruta) as db:
            cursor = db.execute(
                "INSERT INTO usuarios(email, clave_hash, creado) VALUES (?, ?, ?)",
                (email, codificado, ahora()),
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ValueError("El correo ya está registrado.") from exc


def autenticar(ruta: str | Path, email: str, clave: str) -> int | None:
    with conectar(ruta) as db:
        fila = db.execute("SELECT id, clave_hash FROM usuarios WHERE email=?", (email.strip().lower(),)).fetchone()
    if fila is None:
        return None
    try:
        sal_hex, esperado_hex = fila["clave_hash"].split("$")
        derivada = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal_hex), 260_000)
        return int(fila["id"]) if hmac.compare_digest(derivada, bytes.fromhex(esperado_hex)) else None
    except (ValueError, TypeError):
        return None


def registrar_incidente(ruta: str | Path, usuario_id: int, zona: str, categoria: str, descripcion: str) -> int:
    descripcion = descripcion.strip()
    if zona not in ZONAS or categoria not in CATEGORIAS or not (10 <= len(descripcion) <= 500):
        raise ValueError("Selecciona zona y categoría válidas e introduce entre 10 y 500 caracteres.")
    with conectar(ruta) as db:
        cursor = db.execute(
            "INSERT INTO incidentes(usuario_id,zona,categoria,descripcion,creado) VALUES(?,?,?,?,?)",
            (usuario_id, zona, categoria, descripcion, ahora()),
        )
        return int(cursor.lastrowid)


def mis_incidentes(ruta: str | Path, usuario_id: int) -> list[dict]:
    with conectar(ruta) as db:
        rows = db.execute(
            "SELECT id,zona,categoria,descripcion,estado,creado FROM incidentes WHERE usuario_id=? ORDER BY id DESC",
            (usuario_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def solicitar_orientacion(ruta: str | Path, usuario_id: int, programa_id: str, mensaje: str) -> int:
    mensaje = mensaje.strip()
    if programa_id not in {p["id"] for p in PROGRAMAS} or not (10 <= len(mensaje) <= 300):
        raise ValueError("Selecciona un programa válido y describe tu consulta (10–300 caracteres).")
    with conectar(ruta) as db:
        cursor = db.execute(
            "INSERT INTO solicitudes(usuario_id,programa_id,mensaje,creado) VALUES(?,?,?,?)",
            (usuario_id, programa_id, mensaje, ahora()),
        )
        return int(cursor.lastrowid)


def mis_solicitudes(ruta: str | Path, usuario_id: int) -> list[dict]:
    with conectar(ruta) as db:
        rows = db.execute(
            "SELECT id,programa_id,mensaje,estado,creado FROM solicitudes WHERE usuario_id=? ORDER BY id DESC",
            (usuario_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def resumen(ruta: str | Path) -> dict[str, int]:
    with conectar(ruta) as db:
        usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        incidentes = db.execute("SELECT COUNT(*) FROM incidentes").fetchone()[0]
        solicitudes = db.execute("SELECT COUNT(*) FROM solicitudes").fetchone()[0]
        pendientes = db.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Pendiente'").fetchone()[0]
    return {"usuarios": usuarios, "incidentes": incidentes, "solicitudes": solicitudes, "pendientes": pendientes}


def registros_admin(ruta: str | Path, tabla: str) -> list[dict]:
    if tabla not in ("incidentes", "solicitudes"):
        raise ValueError("Tipo de registro inválido.")
    # Lista restringida: no incluye emails, contraseñas ni descripciones personales.
    with conectar(ruta) as db:
        if tabla == "incidentes":
            rows = db.execute("SELECT id,estado,creado,categoria,zona FROM incidentes ORDER BY id DESC LIMIT 100").fetchall()
        else:
            rows = db.execute("SELECT id,estado,creado,programa_id FROM solicitudes ORDER BY id DESC LIMIT 100").fetchall()
    return [dict(r) for r in rows]


def cambiar_estado(ruta: str | Path, tabla: str, registro_id: int, estado: str) -> bool:
    if tabla not in ("incidentes", "solicitudes") or estado not in ESTADOS or registro_id <= 0:
        raise ValueError("Datos inválidos para actualización de estado.")
    with conectar(ruta) as db:
        if tabla == "incidentes":
            cur = db.execute("UPDATE incidentes SET estado=? WHERE id=?", (estado, registro_id))
        else:
            cur = db.execute("UPDATE solicitudes SET estado=? WHERE id=?", (estado, registro_id))
        return cur.rowcount == 1
