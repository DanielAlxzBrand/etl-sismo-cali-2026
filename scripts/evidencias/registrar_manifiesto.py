"""Agrega al manifiesto de evidencias las filas de la capa de servicio (EV-013 a EV-024) con su sha256 calculado de cada archivo.

Idempotente: si un id ya está en el manifiesto, lo reemplaza. Solo escribe docs/evidencias/manifiesto.md.
Uso: .\\.venv\\Scripts\\python.exe scripts\\evidencias\\registrar_manifiesto.py
"""
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
MANIFIESTO = REPO / "docs" / "evidencias" / "manifiesto.md"
CARPETA = "docs/evidencias/api"
FECHA = "2026-11-12"
FILAS = {
    "EV-013": ("2.1", "fastapi, uvicorn y httpx instalados en el .venv, `pip check` sin conflictos y rueda de pydantic-core para Python 3.13", "archivo",
               "`<VENV>\\Scripts\\python.exe -c \"import fastapi, uvicorn, httpx\"`; `pip check`", "EV-013_instalacion_paquetes.txt"),
    "EV-014": ("2.1, 2.2, 2.3", "Todas las pruebas (incluidas test_api, test_catalogo, test_secretos y test_evidencias) pasan en un clon temporal", "archivo",
               "`<VENV>\\Scripts\\python.exe -m pytest -q -p no:cacheprovider --junitxml` en un clon temporal", "EV-014_pytest.txt"),
    "EV-025": ("2.1, 2.2, 2.3", "Informe JUnit de las pruebas de EV-014 (sin el atributo hostname)", "archivo", "mismo comando que EV-014", "junit_api.xml"),
    "EV-015": ("2.1", "Los sha256 de todo data/ y de la base son idénticos tras clonar, tras las pruebas y tras consultar el servidor real", "archivo",
               "sha256 de cada archivo de `data/` en el clon en tres momentos", "EV-015_sin_escritura_hashes.txt"),
    "EV-016": ("2.1, 2.2", "El servicio arranca en 127.0.0.1, cada ruta responde, se cierra de forma ordenada y se exporta /openapi.json", "archivo",
               "`uvicorn src.api.app:app --host 127.0.0.1 --port <libre>` y GET a cada ruta", "EV-016_respuestas_api.txt"),
    "EV-026": ("2.1, 2.2", "Esquema OpenAPI completo del servicio (11 rutas, solo GET)", "archivo", "`GET /openapi.json`", "openapi.json"),
    "EV-017": ("2.1", "Captura automatizada del navegador sin ventana de la documentación /docs (no es una captura manual)", "imagen",
               "`msedge.exe --headless=new --screenshot` sobre `/docs`", "EV-017_docs_navegador.png"),
    "EV-018": ("2.1", "Mediana y percentil 95 de la latencia por endpoint: 50 repeticiones tras 5 de calentamiento contra el servidor real (medición local de una máquina)", "archivo",
               "solicitudes GET con httpx contra el servicio en 127.0.0.1", "EV-018_latencia_api.csv"),
    "EV-019": ("2.3", "El escáner no halla secretos en el clon, su historial ni un zip de prueba armado con make_dist.py", "archivo",
               "`scripts/escanear_secretos.py --zip <zip temporal>`", "EV-019_escaner_secretos.txt"),
    "EV-020": ("2.1", "requirements.txt está completo: un entorno virtual nuevo instala y recolecta las pruebas", "archivo",
               "`python -m venv <TEMP>`; `pip install -r requirements.txt`; `pytest --collect-only`", "EV-020_requirements_entorno_nuevo.txt"),
    "EV-021": ("2.1", "Imagen renderizada con las latencias de EV-018", "imagen", "matplotlib sobre EV-018", "EV-021_latencias.png"),
    "EV-022": ("2.1", "Imagen renderizada con los sha256 de EV-015", "imagen", "matplotlib sobre EV-015", "EV-022_hashes_antes_despues.png"),
    "EV-023": ("2.1, 2.2, 2.3", "Imagen renderizada con el resultado de EV-014", "imagen", "matplotlib sobre EV-014", "EV-023_pytest.png"),
    "EV-024": ("2.3", "Imagen renderizada con el resultado de EV-019", "imagen", "matplotlib sobre EV-019", "EV-024_escaner.png"),
}


def main():
    lineas = [l for l in MANIFIESTO.read_text(encoding="utf-8").split("\n")]
    nuevas = []
    for ev, (item, que, tipo, cmd, archivo) in FILAS.items():
        p = REPO / CARPETA / archivo
        if not p.exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append((f"| {ev} |", f"| {ev} | {item} | {que} | {tipo} | {cmd} | {FECHA} | {CARPETA}/{archivo} | {hashlib.sha256(p.read_bytes()).hexdigest()} |"))
    ids = {pref for pref, _ in nuevas}
    lineas = [l for l in lineas if not any(l.startswith(i) for i in ids)]
    ultima = max(i for i, l in enumerate(lineas) if l.startswith("| EV-"))   # las filas nuevas van al final de la tabla, antes de la convención
    lineas[ultima + 1:ultima + 1] = [fila for _, fila in nuevas]
    MANIFIESTO.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    log.info("manifiesto: %s filas de la capa de servicio registradas", len(nuevas))


if __name__ == "__main__":
    main()
