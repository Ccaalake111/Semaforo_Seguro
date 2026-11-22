# 🚦 Semáforo Seguro

**Prototipo académico** para el caso «Limpiaparabrisas en los semáforos». No es un servicio real de emergencia ni de asistencia social. Utiliza solo **datos ficticios**.

## Funcionalidades
- HU-01/02: registro e inicio de sesión de usuarios de demostración (contraseñas derivadas con PBKDF2 y sal aleatoria).
- HU-03/04: registro y consulta de incidentes generales, con identificador y estado.
- HU-05/06: catálogo **ilustrativo** de programas y solicitudes de orientación.
- HU-07/08: panel administrativo protegido por secreto configurado, cambio de estados y métricas.

## Ejecución local (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m streamlit run app.py
```
En otra terminal, ejecutar `python -m pytest tests/ -q`.

## Seguridad y limitaciones
- Consultas SQL parametrizadas; consultas administrativas solo sobre tablas permitidas.
- Sesiones locales en Streamlit, PBKDF2-HMAC para contraseñas.
- Confirmación de mayoría de edad y consentimiento para cuentas demo.
- Configurar `SEM_ADMIN_PASSWORD` como variable de entorno o secreto de Streamlit Cloud para habilitar administración. No incluirlo en el repositorio.
- Las ubicaciones se presentan como **zonas generales**, sin geolocalización ni identificación personal de personas en la calle.
- **Importante**: SQLite en Streamlit Community Cloud puede ser efímero y no está preparado para persistencia de producción ni uso multiusuario concurrente. Las cuentas y reportes son exclusivamente ficticios y podrían perderse tras un reinicio. Para uso real se requieren identidad validada, controles por roles a nivel backend, almacenamiento durable, protección de datos, protocolos de atención y evaluación ética/legal.

## Arquitectura
`Navegador -> Streamlit (UI + flujo de aplicación) -> semaforo.py (reglas de negocio y acceso a datos) -> SQLite`.

## GitHub y CI/CD
- Rama `main`: código integrable / producción de demostración.
- Rama `test`: cambios y validación antes de PR a `main`.
- Workflow `.github/workflows/ci.yml`: **build/sintaxis**, **pytest**, **Bandit (SAST)**, **pip-audit (dependencias)** y **verificación HTTP del despliegue** cuando `APP_URL` esté configurada.
- El **despliegue real** se configura en Streamlit Community Cloud conectando el repositorio a `main`, con archivo principal `app.py`.
- Configurar variable de Actions `APP_URL` con la URL pública después de publicar, para activar la comprobación HTTP en `main`.
- CI no equivale por sí solo a despliegue; añadir capturas de ejecuciones, el PR fusionado y el enlace público en el informe.

## Evidencias de evaluación
- Jira: cuatro épicas, ocho historias, story points, cuatro sprints simulados, Kanban y burndown.
- Informe: backlog, burndown ideal y simulado, velocidad, Gantt con dependencias e hitos, diagrama de arquitectura, matriz DevSecOps, enlaces a Jira/GitHub/nube y capturas.
- GitHub: commits en `test`, Pull Request a `main`, comprobaciones CI exitosas.

## Ejemplos de datos para demostración
Crear una cuenta ficticia `demo@example.org` con contraseña inventada no reutilizada, registrar un incidente sin datos personales y enviar una solicitud. Probar estado vacío y el panel de administrador con secreto de entorno.
