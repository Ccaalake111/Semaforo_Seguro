import pytest

from semaforo import (
    autenticar, cambiar_estado, inicializar, mis_incidentes, mis_solicitudes,
    registrar, registrar_incidente, registros_admin, resumen, solicitar_orientacion,
)


@pytest.fixture
def entorno(tmp_path):
    ruta = tmp_path / "pruebas.db"
    inicializar(ruta)
    return ruta


def crear_usuario(ruta, correo="demo@example.org"):
    return registrar(ruta, correo, "ClaveDePrueba123", True, True)


def test_registro_y_login(entorno):
    usuario = crear_usuario(entorno)
    assert autenticar(entorno, "DEMO@example.org", "ClaveDePrueba123") == usuario
    assert autenticar(entorno, "demo@example.org", "clave-incorrecta") is None


def test_login_inexistente(entorno):
    assert autenticar(entorno, "otro@example.org", "cualquiera") is None


def test_registro_correo_invalido(entorno):
    with pytest.raises(ValueError, match="correo"):
        registrar(entorno, "incorrecto", "ClaveDePrueba123", True, True)


def test_registro_sin_consentimiento(entorno):
    with pytest.raises(ValueError, match="consentimiento"):
        registrar(entorno, "demo@example.org", "ClaveDePrueba123", False, True)


def test_registro_sin_confirmar_edad(entorno):
    with pytest.raises(ValueError, match="mayoría"):
        registrar(entorno, "demo@example.org", "ClaveDePrueba123", True, False)


def test_registro_duplicado(entorno):
    crear_usuario(entorno)
    with pytest.raises(ValueError, match="registrado"):
        crear_usuario(entorno)


def test_incidente_validacion_y_seguimiento(entorno):
    usuario = crear_usuario(entorno)
    with pytest.raises(ValueError):
        registrar_incidente(entorno, usuario, "Zona norte", "Riesgo vial", "corto")
    codigo = registrar_incidente(entorno, usuario, "Zona norte", "Riesgo vial", "Ejemplo ficticio de tránsito peligroso")
    assert mis_incidentes(entorno, usuario)[0]["id"] == codigo
    assert mis_incidentes(entorno, usuario)[0]["estado"] == "Pendiente"


def test_no_acceder_reportes_ajenos(entorno):
    primero = crear_usuario(entorno)
    segundo = crear_usuario(entorno, "otra@example.org")
    registrar_incidente(entorno, primero, "Zona centro", "Otro", "Descripción totalmente ficticia")
    assert mis_incidentes(entorno, segundo) == []


def test_orientacion_validacion_y_consulta(entorno):
    usuario = crear_usuario(entorno)
    with pytest.raises(ValueError):
        solicitar_orientacion(entorno, usuario, "programa_inexistente", "Quiero información de un programa")
    codigo = solicitar_orientacion(entorno, usuario, "capacitacion", "Solicito información de prueba")
    assert mis_solicitudes(entorno, usuario)[0]["id"] == codigo


def test_admin_cambia_estado_y_resumen(entorno):
    usuario = crear_usuario(entorno)
    codigo = solicitar_orientacion(entorno, usuario, "orientacion", "Consulta académica de orientación")
    assert resumen(entorno) == {"usuarios": 1, "incidentes": 0, "solicitudes": 1, "pendientes": 1}
    assert cambiar_estado(entorno, "solicitudes", codigo, "Atendida")
    assert resumen(entorno)["pendientes"] == 0
    assert registros_admin(entorno, "solicitudes")[0]["estado"] == "Atendida"


def test_admin_rechaza_tabla_o_estado_invalido(entorno):
    with pytest.raises(ValueError):
        cambiar_estado(entorno, "usuarios", 1, "Atendida")
    with pytest.raises(ValueError):
        cambiar_estado(entorno, "solicitudes", 1, "Borrado")


def test_tablas_se_crean_idempotentemente(entorno):
    crear_usuario(entorno)
    inicializar(entorno)
    assert resumen(entorno)["usuarios"] == 1
