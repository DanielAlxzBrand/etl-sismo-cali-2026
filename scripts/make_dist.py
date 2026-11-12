"""Empaqueta la entrega en dist/avance2_etl_<fecha>.zip: solo código, dependencias y archivos necesarios.

Se excluyen los entornos virtuales (con cualquier nombre), las cachés, `.env` y `dist/`. Un entorno virtual se reconoce por el nombre
(`.venv*`, `venv`, `env`, `site-packages`) y, sobre todo, por su contenido: toda carpeta que tenga un `pyvenv.cfg` o cualquiera de las
huellas de un entorno (`site-packages`, `conda-meta`, `python.exe`, `Scripts/python*`, `bin/python*`) se descarta entera.
"""
import os
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUIR_DIRS = {".git", "dist", "__pycache__", ".ipynb_checkpoints", ".pytest_cache", "venv", "env", "site-packages"}
EXCLUIR_PREFIJOS = (".venv",)
EXCLUIR_NOMBRES = {".env"}
PROHIBIDOS_EN_ZIP = ("pyvenv.cfg", "site-packages", "conda-meta", "python.exe", "Scripts/python", "bin/python", ".venv", "__pycache__",
                     ".pytest_cache", ".ipynb_checkpoints", ".git/")


def parece_entorno_virtual(d):
    """True si la carpeta d tiene el contenido de un entorno virtual o de conda, aunque no tenga `pyvenv.cfg` ni un nombre conocido."""
    if (d / "pyvenv.cfg").is_file() or (d / "conda-meta").is_dir() or (d / "python.exe").is_file():
        return True
    if any(d.glob("Scripts/python*")) or any(d.glob("bin/python*")):
        return True
    return any(any(d.glob(g)) for g in ("site-packages", "*/site-packages", "*/*/site-packages"))


def dir_excluido(d):
    """True si la carpeta d no debe entrar al zip (por nombre o porque es un entorno virtual por su contenido)."""
    return d.name in EXCLUIR_DIRS or d.name.startswith(EXCLUIR_PREFIJOS) or parece_entorno_virtual(d)


def archivo_excluido(p, root):
    rel = p.relative_to(root).parts
    return p.name in EXCLUIR_NOMBRES or p.name.startswith(EXCLUIR_PREFIJOS) or p.name == "pyvenv.cfg" or (rel[0] == "logs" and p.suffix == ".log")


def listar(root):
    """Archivos a empaquetar, sin entrar a las carpetas excluidas (no se recorre el entorno virtual)."""
    root = Path(root)
    salida = []
    for carpeta, subdirs, archivos in os.walk(root):
        c = Path(carpeta)
        subdirs[:] = sorted(d for d in subdirs if not dir_excluido(c / d))
        salida += [c / f for f in archivos if not archivo_excluido(c / f, root)]
    return sorted(salida)


def prohibidos(nombres):
    """Entradas del zip que nunca deben estar: entornos virtuales, cachés, `.env`, `dist/`, `.git/`, registros `.log`."""
    malos = []
    for n in nombres:
        partes = n.split("/")
        if (n == ".env" or partes[-1] == ".env" or any(x in n for x in PROHIBIDOS_EN_ZIP) or n.startswith("dist/")
                or any(x in {"venv", "env", "Scripts"} for x in partes[:-1]) or (partes[0] == "logs" and n.endswith(".log"))):
            malos.append(n)
    return malos


def empaquetar(root=ROOT, destino=None):
    root = Path(root)
    destino = Path(destino) if destino else root / "dist"
    destino.mkdir(exist_ok=True)
    zpath = destino / f"avance2_etl_{date.today():%Y%m%d}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in listar(root):
            if p.resolve() == zpath.resolve():
                continue
            z.write(p, p.relative_to(root).as_posix())
    with zipfile.ZipFile(zpath) as z:
        nombres = z.namelist()
    malos = prohibidos(nombres)
    assert not malos, f"el zip contiene archivos prohibidos: {malos[:5]}"
    return zpath, nombres


def main():
    zpath, nombres = empaquetar()
    mb = zpath.stat().st_size / 1024 / 1024
    print(f"{zpath.name}: {len(nombres)} archivos, {mb:.2f} MB; incluye data/bronze: {any(n.startswith('data/bronze/') for n in nombres)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
