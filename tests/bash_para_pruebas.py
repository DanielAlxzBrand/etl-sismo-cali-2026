"""Un `bash` que lea rutas de Windows, para las pruebas que ejecutan un trozo de script del compose de Airflow.

Por qué existe: dos pruebas llamaban al primer `bash` del PATH. En un PowerShell normal ese `bash` puede ser el de WSL (`bash.exe` de System32), que no entiende rutas con letra de unidad y hacía fallar las pruebas con
«No such file or directory» (visto al correr la suite completa en un clon y en el zip con el entorno nuevo). Aquí se prueba cada candidato con un guion de verdad y se devuelve el primero que lo ejecuta; si ninguno puede,
la prueba se omite con un motivo visible en lugar de pasar sin comprobar nada.
Además, `entorno_con_el_bash_delante` pone la carpeta de ese `bash` al principio del PATH: lanzado desde PowerShell, el `bash` de Git encuentra primero el `find.exe` de Windows (que no es el de GNU y sale con 2)
y no su propio `find`; con su carpeta delante usa sus herramientas (visto en la suite del clon y del zip).
Qué NO hace: instalar nada ni elegir un `bash` por su nombre.
"""
import os
import shutil
import subprocess
from pathlib import Path


def _candidatos():
    git = Path(os.environ.get("ProgramFiles", "")) / "Git"
    return [shutil.which("bash"), str(git / "usr" / "bin" / "bash.exe"), str(git / "bin" / "bash.exe")]


def bash_que_lee_rutas(tmp_path):
    """Ruta de un `bash` que ejecuta un guion dado por su ruta absoluta, o None si el equipo no tiene ninguno."""
    guion = tmp_path / "sonda.sh"
    guion.write_text("exit 0\n", encoding="utf-8", newline="\n")
    probados = set()
    for candidato in _candidatos():
        if not candidato or candidato in probados or not Path(candidato).exists():
            continue
        probados.add(candidato)
        try:
            if subprocess.run([candidato, guion.as_posix()], capture_output=True, timeout=30).returncode == 0:
                return candidato
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def entorno_con_el_bash_delante(bash):
    """Copia del entorno con la carpeta del `bash` elegido al principio del PATH, para que `find`, `grep`, `head` y `cut` sean los suyos y no los de Windows."""
    entorno = dict(os.environ)
    entorno["PATH"] = str(Path(bash).parent) + os.pathsep + entorno.get("PATH", "")
    return entorno
