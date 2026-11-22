"""Interfaz web de Semáforo Seguro. Prototipo académico con datos ficticios."""
import hmac
import os
from pathlib import Path

import streamlit as st

from semaforo import (
    CATEGORIAS, ESTADOS, PROGRAMAS, ZONAS, autenticar, cambiar_estado,
    inicializar, mis_incidentes, mis_solicitudes, registrar,
    registrar_incidente, registros_admin, resumen, solicitar_orientacion,
)

st.set_page_config(page_title="Semáforo Seguro", page_icon="🚦", layout="wide")

BASE_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Semaforo_Seguro"
BASE_DIR.mkdir(parents=True, exist_ok=True)

DB = Path(os.environ.get("SEM_DB_PATH", str(BASE_DIR / "semaforo_seguro.db")))
DB.parent.mkdir(parents=True, exist_ok=True)

inicializar(DB)


st.title("🚦 Semáforo Seguro")
st.caption("Prototipo académico • Plataforma de orientación y reporte voluntario")
st.warning("DEMO: utiliza únicamente información ficticia. No es un canal de emergencias ni un servicio oficial. No está preparado para recopilar información real de personas vulnerables o menores.")

if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

menu = st.sidebar.radio(
    "Navegación",
    ("Inicio", "Cuenta", "Reportar incidente", "Mis reportes", "Programas de apoyo", "Solicitar orientación", "Administración"),
)
if st.session_state.usuario_id:
    st.sidebar.success("Sesión de usuario activa")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario_id = None
        st.session_state.admin_ok = False
        st.rerun()
else:
    st.sidebar.info("Inicia sesión para registrar solicitudes.")

if menu == "Inicio":
    st.subheader("¿Para qué sirve?")
    st.write("Esta propuesta académica permite reportar riesgos de forma voluntaria, conocer programas ilustrativos de apoyo y solicitar orientación.")
    c1, c2, c3 = st.columns(3)
    c1.info("🛣️ Reportes generales de riesgo")
    c2.info("🤝 Información de apoyo")
    c3.info("📋 Seguimiento de solicitudes")
    st.caption("Las instituciones y programas aquí mencionados son ejemplos; deben verificarse antes de su uso real.")

elif menu == "Cuenta":
    crear_tab, ingresar_tab = st.tabs(("Crear cuenta de demostración", "Iniciar sesión"))
    with crear_tab:
        with st.form("registro"):
            email = st.text_input("Correo ficticio")
            clave = st.text_input("Contraseña (mínimo 8 caracteres)", type="password")
            adulto = st.checkbox("Confirmo que soy mayor de edad")
            consentimiento = st.checkbox("Acepto usar datos exclusivamente de demostración")
            enviado = st.form_submit_button("Registrar")
            if enviado:
                try:
                    registrar(DB, email, clave, consentimiento, adulto)
                    st.success("Cuenta de demostración creada. Ya puedes iniciar sesión.")
                except ValueError as exc:
                    st.error(str(exc))
    with ingresar_tab:
        with st.form("login"):
            email_login = st.text_input("Correo", key="login_email")
            clave_login = st.text_input("Contraseña", type="password", key="login_pass")
            if st.form_submit_button("Ingresar"):
                usuario = autenticar(DB, email_login, clave_login)
                if usuario is None:
                    st.error("Credenciales inválidas.")
                else:
                    st.session_state.usuario_id = usuario
                    st.success("Sesión iniciada correctamente.")
                    st.rerun()

elif menu == "Reportar incidente":
    st.subheader("Registrar situación de riesgo")
    if not st.session_state.usuario_id:
        st.info("Accede a Cuenta e inicia sesión para enviar un reporte ficticio.")
    else:
        with st.form("incidente"):
            zona = st.selectbox("Zona general (sin ubicación exacta)", ZONAS)
            categoria = st.selectbox("Tipo de riesgo", CATEGORIAS)
            descripcion = st.text_area("Descripción ficticia (10 a 500 caracteres)", max_chars=500)
            if st.form_submit_button("Registrar reporte"):
                try:
                    identificador = registrar_incidente(DB, st.session_state.usuario_id, zona, categoria, descripcion)
                    st.success(f"Reporte de demostración registrado: INC-{identificador:04d}.")
                except ValueError as exc:
                    st.error(str(exc))

elif menu == "Mis reportes":
    st.subheader("Seguimiento de reportes y orientación")
    if not st.session_state.usuario_id:
        st.info("Inicia sesión para consultar tus registros.")
    else:
        incidentes = mis_incidentes(DB, st.session_state.usuario_id)
        solicitudes = mis_solicitudes(DB, st.session_state.usuario_id)
        st.markdown("**Incidentes registrados**")
        if incidentes:
            st.dataframe(incidentes, hide_index=True, use_container_width=True)
        else:
            st.info("No existen reportes disponibles.")
        st.markdown("**Solicitudes de orientación**")
        if solicitudes:
            st.dataframe(solicitudes, hide_index=True, use_container_width=True)
        else:
            st.info("No existen solicitudes disponibles.")

elif menu == "Programas de apoyo":
    st.subheader("Programas de apoyo (ejemplos ilustrativos)")
    for programa in PROGRAMAS:
        with st.expander(programa["nombre"], expanded=True):
            st.write(programa["detalle"])
            st.caption(f'Tipo: {programa["tipo"]} • Información: {programa["contacto"]}')

elif menu == "Solicitar orientación":
    st.subheader("Solicitar orientación")
    if not st.session_state.usuario_id:
        st.info("Inicia sesión para enviar una solicitud ficticia.")
    else:
        etiquetas = {p["nombre"]: p["id"] for p in PROGRAMAS}
        with st.form("solicitud"):
            nombre = st.selectbox("Programa de interés", list(etiquetas))
            consulta = st.text_area("Consulta de demostración (10 a 300 caracteres)", max_chars=300)
            if st.form_submit_button("Enviar solicitud"):
                try:
                    identificador = solicitar_orientacion(DB, st.session_state.usuario_id, etiquetas[nombre], consulta)
                    st.success(f"Solicitud de demostración registrada: SOL-{identificador:04d}.")
                except ValueError as exc:
                    st.error(str(exc))

elif menu == "Administración":
    st.subheader("Panel de administración")
    try:
        clave_admin = st.secrets.get("SEM_ADMIN_PASSWORD", "")
    except (FileNotFoundError, KeyError):
        clave_admin = ""
    clave_admin = clave_admin or os.getenv("SEM_ADMIN_PASSWORD", "")
    if not clave_admin:
        st.info("Panel protegido deshabilitado. Configura SEM_ADMIN_PASSWORD en los secretos del despliegue para habilitarlo.")
    elif not st.session_state.admin_ok:
        with st.form("acceso_admin"):
            intento = st.text_input("Clave de administración", type="password")
            if st.form_submit_button("Acceder"):
                if hmac.compare_digest(intento.encode(), clave_admin.encode()):
                    st.session_state.admin_ok = True
                    st.rerun()
                else:
                    st.error("Acceso denegado.")
    else:
        datos = resumen(DB)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Usuarios demo", datos["usuarios"])
        col2.metric("Incidentes demo", datos["incidentes"])
        col3.metric("Solicitudes demo", datos["solicitudes"])
        col4.metric("Solicitudes pendientes", datos["pendientes"])
        tabla = st.selectbox("Gestionar", ("incidentes", "solicitudes"))
        registros = registros_admin(DB, tabla)
        if not registros:
            st.info("No hay elementos registrados.")
        else:
            st.dataframe(registros, hide_index=True, use_container_width=True)
            identificador = st.selectbox("Identificador", [r["id"] for r in registros])
            estado_nuevo = st.selectbox("Nuevo estado", ESTADOS)
            if st.button("Actualizar estado"):
                if cambiar_estado(DB, tabla, identificador, estado_nuevo):
                    st.success("Estado actualizado.")
                    st.rerun()
        if st.button("Cerrar sesión administrativa"):
            st.session_state.admin_ok = False
            st.rerun()

st.divider()
st.caption("Semáforo Seguro • Caso académico: limpiaparabrisas en los semáforos • Datos ficticios")
