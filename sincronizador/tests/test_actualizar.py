import io
import zipfile

from actualizar import actualizar


def test_actualiza_sin_tocar_config_ni_reportes(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("repo-rama/sincronizador/sincronizar.py", "nuevo")
        z.writestr("repo-rama/sincronizador/config.json", "PISADO")
        z.writestr("repo-rama/sincronizador/reportes/x.csv", "PISADO")
        z.writestr("repo-rama/README.md", "otro")
    (tmp_path / "sincronizar.py").write_text("viejo")
    (tmp_path / "config.json").write_text("mio")
    cambiados = actualizar(zipfile.ZipFile(buf), tmp_path)
    assert cambiados == ["sincronizar.py"]
    assert (tmp_path / "sincronizar.py").read_text() == "nuevo"
    assert (tmp_path / "config.json").read_text() == "mio"
    assert not (tmp_path / "reportes").exists() and not (tmp_path / "README.md").exists()
