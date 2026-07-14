"""Testovi na privremenoj bazi — nikad ne diraju stvarnu (dev.db).
ERP koristi Alembic pa privremenoj bazi ručno kreiramo shemu (create_all
nad svim modelima koje registrira import app.main)."""
import os, sys, tempfile, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
_tmp = pathlib.Path(tempfile.mkdtemp(prefix="erp_test_")) / "test.db"
os.environ["DATABASE_URL"] = "sqlite:///" + str(_tmp).replace("\\", "/")

import app.main  # noqa: E402  — registrira sve module/modele
from app.core.database import Base, engine  # noqa: E402

Base.metadata.create_all(bind=engine)
