"""Script de sembrado (seeding) inicial para pruebas manuales de SubastAgro."""
from app.core.database import Base, SessionLocal, engine
from app.cattle_lots.schemas import BreedCreate
from app.cattle_lots.services import create_breed
from app.users.schemas import UserCreate
from app.users.services import create_user, get_user_by_email


def run_seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users = [
            UserCreate(
                email="admin@subastagro.co",
                password="AdminPassword2026*",
                nombre_completo="Administrador SubastAgro",
                documento_identidad="9001002001",
                telefono="+57 3001112233",
                rol="ADMINISTRADOR",
            ),
            UserCreate(
                email="ganadero@subastagro.co",
                password="GanaderoPassword2026*",
                nombre_completo="Carlos Mendoza (Hacienda El Roble)",
                documento_identidad="1098765432",
                telefono="+57 3104445566",
                rol="GANADERO",
            ),
            UserCreate(
                email="comprador@subastagro.co",
                password="CompradorPassword2026*",
                nombre_completo="Andrés Felipe Gómez (Frigorífico del Norte)",
                documento_identidad="1020304050",
                telefono="+57 3207778899",
                rol="COMPRADOR",
            ),
        ]

        for u in seed_users:
            if not get_user_by_email(db, u.email):
                create_user(db, u, allow_admin_creation=True)
                print(f"[OK] Usuario creado: {u.email} ({u.rol})")

        for raza, prop in [
            ("Brahman", "Carne"),
            ("Angus", "Carne"),
            ("Gyr", "Leche"),
            ("Holstein", "Leche"),
            ("Simmental", "Doble Propósito"),
        ]:
            try:
                create_breed(db, BreedCreate(nombre_raza=raza, proposito=prop))
                print(f"[OK] Raza creada: {raza}")
            except Exception:
                pass
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
