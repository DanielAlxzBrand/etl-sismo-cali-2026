"""Empaqueta el proyecto en dist/etl_sismo_<fecha>.zip con una lista de INCLUSIÓN: solo entra lo permitido.

Primer nivel permitido: archivos `RAIZ_ARCHIVOS` y carpetas `RAIZ_CARPETAS` (`dags/`, `orquestacion/` y `servicios/` solo si existen). Dentro de ellas se excluyen cachés,
`*.pyc`, `logs/`, el `.env` real, toda carpeta oculta (que empiece por punto) y toda carpeta que sea un entorno virtual (por nombre y, sobre todo, por su contenido:
`pyvenv.cfg`, `site-packages`, `conda-meta`, `python.exe`, `Scripts/python*` o `bin/python*`). En `docs/` solo entran los PDF de
`docs/proyecto/referencias/` y `docs/retroalimentacion/`. Tras armar el zip se verifica su contenido y falla con un mensaje claro si algo sobra.
"""
import os
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAIZ_ARCHIVOS = ("README.md", "main.py", "requirements.txt", "pytest.ini", ".env.example", ".gitignore", ".gitattributes", "DECLARACION_USO_IA.md")
RAIZ_CARPETAS = ("config", "src", "scripts", "tests", "notebooks", "docs", "data", "dags", "orquestacion", "servicios")
PDF_PERMITIDOS = ("docs/proyecto/referencias/", "docs/retroalimentacion/")
EXCLUIR_DIRS = {".git", "dist", "logs", "__pycache__", ".ipynb_checkpoints", ".pytest_cache", "venv", "env", ".env", "site-packages"}
EXCLUIR_PREFIJOS = (".venv",)
EXCLUIR_NOMBRES = {".env", "pyvenv.cfg"}
PROHIBIDOS_EN_ZIP = ("pyvenv.cfg", "site-packages", "conda-meta", "python.exe", "Scripts/python", "bin/python", ".venv", "__pycache__",
                     ".pytest_cache", ".ipynb_checkpoints", ".git/")
LIMITE_MB = 50


def parece_entorno_virtual(d):
    """True si la carpeta d tiene el contenido de un entorno virtual o de conda, aunque no tenga `pyvenv.cfg` ni un nombre conocido."""
    if (d / "pyvenv.cfg").is_file() or (d / "conda-meta").is_dir() or (d / "python.exe").is_file():
        return True
    if any(d.glob("Scripts/python*")) or any(d.glob("bin/python*")):
        return True
    return any(any(d.glob(g)) for g in ("site-packages", "*/site-packages", "*/*/site-packages"))


def dir_excluido(d):
    """True si la carpeta d no debe entrar al zip: por nombre, por ser una carpeta oculta (empieza por punto) o por ser un entorno virtual según su contenido."""
    return d.name in EXCLUIR_DIRS or d.name.startswith(".") or parece_entorno_virtual(d)


def archivo_excluido(p, root):
    """True si el archivo no debe entrar: `.env` real, notas locales, bytecode y los PDF de docs/ fuera de las carpetas permitidas."""
    rel = p.relative_to(root).as_posix()
    if p.name in EXCLUIR_NOMBRES or p.name.startswith(EXCLUIR_PREFIJOS) or p.suffix == ".pyc":
        return True
    return p.suffix.lower() == ".pdf" and rel.startswith("docs/") and not rel.startswith(PDF_PERMITIDOS)


def listar(root):
    """Archivos a empaquetar: los de primer nivel permitidos y los de las carpetas permitidas (sin entrar a las excluidas)."""
    root = Path(root)
    salida = [root / f for f in RAIZ_ARCHIVOS if (root / f).is_file()]
    for nombre in RAIZ_CARPETAS:
        base = root / nombre
        if not base.is_dir() or dir_excluido(base):
            continue
        for carpeta, subdirs, archivos in os.walk(base):
            c = Path(carpeta)
            subdirs[:] = sorted(d for d in subdirs if not dir_excluido(c / d))
            salida += [c / f for f in archivos if not archivo_excluido(c / f, root)]
    return sorted(salida)


def prohibidos(nombres):
    """Entradas del zip que nunca deben estar: entornos virtuales, cachés, `.env`, `dist/`, `.git/`, registros `.log`, notas locales."""
    malos = []
    for n in nombres:
        partes = n.split("/")
        if (n == ".env" or partes[-1] == ".env" or any(x in n for x in PROHIBIDOS_EN_ZIP) or n.startswith("dist/")
                or any(x in {"venv", "env", "Scripts"} or x.startswith(".") for x in partes[:-1]) or (partes[0] == "logs" and n.endswith(".log"))):
            malos.append(n)
    return malos


def fuera_de_la_lista(nombres):
    """Entradas cuyo primer nivel no está en la lista permitida."""
    permitidos = set(RAIZ_ARCHIVOS) | set(RAIZ_CARPETAS)
    return [n for n in nombres if n.split("/")[0] not in permitidos]


def pdf_no_permitidos(nombres):
    """PDF de docs/ fuera de las carpetas permitidas."""
    return [n for n in nombres if n.lower().endswith(".pdf") and n.startswith("docs/") and not n.startswith(PDF_PERMITIDOS)]


def verificar(nombres):
    """Falla con un mensaje claro si el zip no cumple la lista de inclusión; devuelve las advertencias (ninguna por ahora)."""
    malos = prohibidos(nombres)
    assert not malos, f"el zip contiene archivos prohibidos: {malos[:5]}"
    fuera = fuera_de_la_lista(nombres)
    assert not fuera, f"el zip tiene entradas fuera de la lista permitida de primer nivel: {fuera[:5]}"
    pdfs = pdf_no_permitidos(nombres)
    assert not pdfs, f"el zip contiene PDF de docs/ fuera de las carpetas permitidas: {pdfs[:5]}"
    assert "requirements.txt" in nombres, "falta requirements.txt en el zip"


def empaquetar(root=ROOT, destino=None):
    root = Path(root)
    destino = Path(destino) if destino else root / "dist"
    destino.mkdir(exist_ok=True)
    zpath = destino / f"etl_sismo_{date.today():%Y%m%d}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in listar(root):
            z.write(p, p.relative_to(root).as_posix())
    with zipfile.ZipFile(zpath) as z:
        nombres = z.namelist()
    verificar(nombres)
    return zpath, nombres


def main():
    zpath, nombres = empaquetar()
    mb = zpath.stat().st_size / 1024 / 1024
    primer_nivel = sorted({n.split("/")[0] for n in nombres})
    print(f"{zpath.name}: {len(nombres)} archivos, {mb:.2f} MB; primer nivel: {', '.join(primer_nivel)}; incluye data/bronze: {any(n.startswith('data/bronze/') for n in nombres)}")
    if mb > LIMITE_MB:
        print(f"ADVERTENCIA: el zip supera {LIMITE_MB} MB ({mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
