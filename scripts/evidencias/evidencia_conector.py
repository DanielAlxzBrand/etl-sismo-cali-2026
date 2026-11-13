"""Evidencia de la instalación del conector MySQL: versiones, pip check y ruedas para Python 3.13 en Windows."""
import importlib.metadata as im
import subprocess
import sys

from evidencia import Cronometro, guardar


def main():
    with Cronometro() as c:
        cuerpo = ["paquetes instalados en el .venv (solo estos dos y sus dependencias):"]
        for paquete in ("PyMySQL", "cryptography", "cffi", "pycparser"):
            d = im.distribution(paquete)
            etiquetas = [l for l in (d.read_text("WHEEL") or "").splitlines() if l.startswith("Tag:")]
            cuerpo.append(f"- {paquete} {d.version}; {' '.join(etiquetas)}")
        pc = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, encoding="utf-8")
        cuerpo += ["", "pip check:", pc.stdout.strip() or pc.stderr.strip()]
        import cryptography
        import pymysql
        cuerpo += ["", f"importación: pymysql y cryptography {cryptography.__version__} importan sin errores",
                   "Las ruedas son `py3-none-any` (PyMySQL) y `cp311-abi3-win_amd64` (cryptography, compatible con Python 3.13).",
                   "Instalación: `<VENV>\\Scripts\\python.exe -m pip install pymysql cryptography` (nunca en el Python global)."]
    ruta = guardar("almacenamiento", "EV-027_conector_mysql.txt", "EV-027 · Conector MySQL instalado en el .venv", "<VENV>\\Scripts\\python.exe -m pip check; importación; lectura de las ruedas",
                   pc.returncode, c.duracion, "\n".join(cuerpo) + "\n")
    sys.stderr.write(f"escrito {ruta.name}\n")


if __name__ == "__main__":
    main()
