"""CI smoke — boot i ključne stranice svih modula."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app


def test_root_redirect():
    c = TestClient(app)
    r = c.get("/", follow_redirects=True)
    assert r.status_code == 200


def test_moduli():
    c = TestClient(app)
    for u in ["/materijali", "/strojevi", "/kupci", "/pantoni",
              "/reklamacije", "/normativi/kalkulator", "/normativi/montaza"]:
        assert c.get(u, follow_redirects=True).status_code == 200, u


def test_skladiste_zakljucano():
    c = TestClient(app)
    r = c.get("/skladiste", follow_redirects=False)
    assert r.status_code == 423  # prebačeno na vanjski WMS modul
