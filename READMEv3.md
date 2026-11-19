# SubastAgro Backend - Hardening y Producción OWASP Top 10 (READMEv3)
**Dirigido a:** Prof. LUIS GUILLERMO MORELO  

## 1. Perfiles de Entorno (`development` vs `production`)
Configurados en `app/core/config.py`:
- **Development**: `APP_ENV=development`, `APP_COOKIE_SECURE=false`, CORS local (`http://localhost:5173`, `http://localhost:3000`).
- **Production**: `APP_ENV=production`, `APP_COOKIE_SECURE=true` forzado automáticamente, CORS estricto a dominios autorizados, `APP_DEBUG=false`.

## 2. Matriz de Seguridad RBAC & Ownership
| Recurso | ADMINISTRADOR | GANADERO | COMPRADOR |
| :--- | :---: | :---: | :---: |
| Gestión Usuarios / Razas | Total | Lectura | Lectura |
| Lotes de Ganado | Total | CRUD **solo propios** (`ganadero_id == user.id`) | Lectura |
| Eventos de Subasta | Total | Crear/Editar **solo de sus lotes** | Lectura activas |
| Pujas y Ofertas | Lectura | Lectura | Crear y ver **solo propias** (`comprador_id == user.id`) |
| Actas de Adjudicación | Cerrar y ver todas | Ver de sus lotes | Ver **solo ganadas** (`comprador_ganador_id == user.id`) |

## 3. Checklist OWASP Top 10 Verificado
- **A01 Broken Access Control**: Dependencias `get_current_active_admin`, `get_current_active_ganadero`, `get_current_active_comprador` + validación de Ownership en servicios.
- **A02 Cryptographic Failures**: Passlib + Bcrypt, JWT HS256, Cookies `HttpOnly` + `SameSite=Lax`.
- **A03 Injection**: Consultas 100% parametrizadas con SQLAlchemy 2.0 ORM y validación Pydantic v2.
- **A05 Security Misconfiguration**: Encabezados HTTP (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `CSP`) y manejador global de excepciones sin fuga de stack traces.

## 4. Despliegue en Producción
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
