# SubastAgro Backend - Validación Arquitectónica y Clean Architecture (READMEv2)
**Dirigido a:** Prof. LUIS GUILLERMO MORELO  

## 1. Validación Arquitectónica (Clean Architecture & ISO/IEC 25010)
- **✔ Cumplimientos correctos**: Separación estricta por capas (`routes.py` -> `services.py` -> `models.py`), validación Pydantic v2 (`schemas.py`), hashing Bcrypt, cookies `HttpOnly` + `SameSite=Lax`, y control de Ownership.
- **⚠️ Riesgos mitigados**: Eliminación de `LocalStorage` para tokens sensibles mediante soporte nativo de cookies `HttpOnly`, prevención de Timing Attacks en login y bloqueo de fila (`with_for_update`) en pujas concurrentes.

## 2. Cuestionario Técnico de Validación (30 Preguntas Resueltas)
1. **Conexión BD `subastagro_db`**: `app/core/database.py`.
2. **Clase base ORM**: `DeclarativeBase` (`Base`) en `app/core/database.py`.
3. **Manejo centralizado de errores**: `app/core/exceptions.py` registrado en `app/main.py`.
4. **Excepción recurso inexistente**: `ResourceNotFoundException` (`HTTPException` 404).
5. **Hashing de contraseñas**: `app/core/security.py` con Passlib + Bcrypt.
6. **Tabla asociativa `usuario_roles`**: `app/users/models.py`.
7. **Campo `password_hash`**: Modelo `Usuario` (`app/users/models.py`).
8. **Contraseña en texto plano**: `UserCreate` (`app/users/schemas.py`).
9. **Esquema que omite `password_hash`**: `UserResponse` (`app/users/schemas.py`).
10. **Validación de email único**: `create_user()` en `app/users/services.py`.
11. **Endpoint `POST /auth/login`**: `app/auth/routes.py`.
12. **Sesión de BD en rutas**: `db: Session = Depends(get_db)`.
13. **Registro de routers**: `app/main.py` vía `app.include_router()`.
14. **Health check**: `GET /api/v1/health` en `app/main.py`.
15. **Entidad grupos de reses**: `LoteGanado` (`app/cattle_lots/models.py`).
16. **Unicidad de `codigo_lote`**: Restricción `unique=True` en `LoteGanado` y validación en `cattle_lots/services.py`.
17. **Entidad eventos de puja**: `EventoSubasta` (`app/auctions/models.py`).
18. **Validación `fecha_cierre > fecha_inicio`**: `@model_validator` en `AuctionCreate` (`app/auctions/schemas.py`).
19. **Entidad oferta de comprador**: `PujaOferta` (`app/bids/models.py`).
20. **Restricción puja mínima**: `place_bid()` en `app/bids/services.py`.
21. **Verificación subasta activa antes de pujar**: `place_bid()` en `app/bids/services.py`.
22. **Enum estado de subasta**: `EstadoSubasta` (`PROGRAMADA`, `ACTIVA`, `FINALIZADA`, `DESIERTA`).
23. **Entidad acta final**: `ActaAdjudicacion` (`app/adjudications/models.py`).
24. **Cálculo monto total final**: `close_auction_and_adjudicate()` en `app/adjudications/services.py`.
25. **CRUD de pujas**: `app/bids/routes.py` y `app/bids/services.py`.
26. **Capa de reglas de negocio**: Service Layer (`services.py`).
27. **Capa HTTP y dependencias**: API/Controller Layer (`routes.py`).
28. **Capa de mapeo PostgreSQL**: Persistence Layer (`models.py`).
29. **Dependencias del proyecto**: `requirements.txt`.
30. **Documentación técnica**: `READMEv1.md`, `READMEv2.md`, `READMEv3.md` y `README_TEST_5.md`.
