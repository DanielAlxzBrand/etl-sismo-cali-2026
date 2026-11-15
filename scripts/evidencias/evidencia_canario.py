"""Comprobación canario con las credenciales reales de `.env`: árbol, registros, historial de git y un zip de prueba armado en una carpeta temporal.

Uso:  python scripts/evidencias/evidencia_canario.py
Los valores sensibles de `.env` se leen en memoria y se buscan; el informe solo tiene NOMBRES de variables y conteos, nunca valores. Guarda la evidencia saneada.
"""
import importlib.util
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidencia  # noqa: E402


def cargar(nombre):
    espec = importlib.util.spec_from_file_location(nombre, ROOT / "scripts" / f"{nombre}.py")
    m = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(m)
    return m


def main():
    t0 = time.perf_counter()
    esc, dist = cargar("escanear_secretos"), cargar("make_dist")
    can = esc.canarios(ROOT)
    lineas = [f"Variables sensibles de `.env` usadas como canarios (solo nombres): {', '.join(sorted(can)) or 'ninguna'}", f"Cantidad de canarios: {len(can)}", ""]
    ok = len(can) >= 1
    estado = esc.estado_de_env(ROOT)
    ok &= not estado
    lineas.append(f"1. `.env` ignorado por git y no versionado: {'sí' if not estado else 'NO ' + str(estado)}")
    arbol = esc.canario_arbol(ROOT, can)
    ok &= not arbol
    lineas.append(f"2. Árbol de trabajo (incluye `data/`, `docs/`, notebooks y evidencias; excluye `.env`, `.git`, entornos y cachés): {len(arbol)} hallazgos")
    logs = []
    for p in sorted((ROOT / "logs").glob("*.log")):
        logs += esc._buscar_en(p.name, p.read_bytes(), can)
    ok &= not logs
    lineas.append(f"3. Registros de ejecución (`logs/*.log`): {len(logs)} hallazgos en {len(list((ROOT / 'logs').glob('*.log')))} archivos")
    hist = esc.canario_historial(ROOT, can)
    ok &= not hist
    n_commits = int(subprocess.run(["git", "rev-list", "--all", "--count"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip() or 0)
    lineas.append(f"4. Historial de git completo (todas las ramas y etiquetas, {n_commits} commits, mensajes y cambios): {len(hist)} hallazgos")
    with tempfile.TemporaryDirectory() as tmp:
        clon = Path(tmp) / "clon"
        subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clon)], check=True, capture_output=True)
        salida = Path(tmp) / "zip"
        salida.mkdir()
        subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, r'{clon}'); import importlib.util as u; "
                        f"e=u.spec_from_file_location('md', r'{clon / 'scripts' / 'make_dist.py'}'); m=u.module_from_spec(e); e.loader.exec_module(m); "
                        f"from pathlib import Path; m.empaquetar(Path(r'{clon}'), Path(r'{salida}'))"], cwd=clon, check=True, capture_output=True)
        z = sorted(salida.glob("*.zip"))[-1]
        zhall = esc.canario_zip(z, can)
        import zipfile
        with zipfile.ZipFile(z) as zf:
            n_entradas, trae_env = len(zf.namelist()), any(n == ".env" or n.endswith("/.env") for n in zf.namelist())
    ok &= not zhall and not trae_env
    lineas.append(f"5. Zip de prueba armado con `scripts/make_dist.py` en una carpeta temporal ({n_entradas} entradas; trae `.env`: {'sí' if trae_env else 'no'}): {len(zhall)} hallazgos")
    gen = esc.escanear_arbol(ROOT) + esc.escanear_historial(ROOT)
    ok &= not gen
    lineas.append(f"6. Escáner de patrones de secretos (árbol e historial): {len(gen)} hallazgos")
    lineas += ["", f"Resultado: {'0 hallazgos: la contraseña de MySQL no aparece fuera de `.env`' if ok else 'HAY HALLAZGOS (se informan archivo y variable, nunca el valor)'}."]
    if not ok:
        lineas += [f"- {h[0]}:{h[1]}: {h[2]}" for h in (arbol + logs + hist + zhall + gen)[:20]]
    cuerpo = "\n".join(lineas) + "\n"
    print(cuerpo)
    ruta = evidencia.guardar("almacenamiento", "EV-033_canario_credenciales.txt", "Comprobación canario de las credenciales de MySQL", "python scripts/evidencias/evidencia_canario.py",
                             0 if ok else 1, time.perf_counter() - t0, cuerpo)
    print("evidencia:", ruta.relative_to(ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
