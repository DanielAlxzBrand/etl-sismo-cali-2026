"""Capturas, tiempos y contrastes del panel en tres anchos ANTES y DESPUÉS de los ajustes que salieron de la evaluación heurística (F-01 a F-14).

Uso:  python scripts/evidencias/evidencia_capturas_ajustes.py --momento antes|despues [--repeticiones 5]
Reutiliza `evidencia_capturas_anchos.py` (la misma medición, para que el antes y el después sean comparables) pero guarda en `docs/evidencias/ajustes_ux/` con identificadores nuevos y no
sobrescribe EV-066 a EV-069: antes = EV-073 (capturas), EV-074 (tiempos) y EV-075 (contraste); después = EV-077, EV-078 y EV-079.
Corrige una limitación de la medición original (F-12): el primer texto de un eje que encontraba el script podía ser una etiqueta que el propio gráfico oculta por solaparse (opacidad 0) y daba un
contraste de 1,0; aquí solo se mide texto visible. Son mediciones locales de una máquina y los tiempos varían entre corridas. No instala nada y cierra el navegador y el panel al terminar.
"""
import argparse
import importlib
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
anchos = importlib.import_module("evidencia_capturas_anchos")

DESTINO = REPO / "docs" / "evidencias" / "ajustes_ux"
IDENTIFICADORES = {
    "antes": {"EV-066": "EV-073", "EV-067": "EV-074", "EV-068": "EV-075"},
    "despues": {"EV-066": "EV-077", "EV-067": "EV-078", "EV-068": "EV-079"},
}
ROTULO = {"antes": "antes de los ajustes", "despues": "después de los ajustes"}
JS_PRIMER_TEXTO = "const e = document.querySelector('[data-testid=\"stVegaLiteChart\"] svg ' + sel) || document.querySelector('[data-testid=\"stArrowVegaLiteChart\"] svg ' + sel);"
JS_PRIMER_TEXTO_VISIBLE = ("const e = [...document.querySelectorAll('[data-testid=\"stVegaLiteChart\"] svg ' + sel + ', [data-testid=\"stArrowVegaLiteChart\"] svg ' + sel)]"
                           ".find(x => opac(x) > 0.5);")


def preparar(momento, carpeta_temporal):
    """Redirige `evidencia_capturas_anchos` a una carpeta temporal y a los identificadores nuevos, y le pide medir solo texto visible."""
    mapa = IDENTIFICADORES[momento]
    assert JS_PRIMER_TEXTO in anchos.CONTRASTE, "la medición original cambió: revise este script"
    anchos.CONTRASTE = anchos.CONTRASTE.replace(JS_PRIMER_TEXTO, JS_PRIMER_TEXTO_VISIBLE)
    anchos.DESTINO = carpeta_temporal
    original = anchos.evidencia.guardar

    def guardar(tema, nombre, titulo, comando, codigo, duracion, cuerpo):
        for viejo, nuevo in mapa.items():
            nombre, titulo, cuerpo = nombre.replace(viejo, nuevo), titulo.replace(viejo, nuevo), cuerpo.replace(viejo, nuevo)
        return original("ajustes_ux", nombre, f"{titulo} ({ROTULO[momento]})", f"python scripts/evidencias/evidencia_capturas_ajustes.py --momento {momento}", codigo, duracion, cuerpo)

    anchos.evidencia.guardar = guardar
    return mapa


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--momento", choices=("antes", "despues"), required=True)
    ap.add_argument("--repeticiones", type=int, default=5)
    a = ap.parse_args(argv)
    DESTINO.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        mapa = preparar(a.momento, Path(tmp))
        sys.argv = ["evidencia_capturas_anchos.py", "--repeticiones", str(a.repeticiones)]
        codigo = anchos.main()
        for f in sorted(Path(tmp).iterdir()):
            nombre = f.name
            for viejo, nuevo in mapa.items():
                nombre = nombre.replace(viejo, nuevo)
            if f.suffix == ".csv":
                f.write_text(f.read_text(encoding="utf-8").replace("EV-066", mapa["EV-066"]), encoding="utf-8", newline="\n")
            shutil.move(str(f), DESTINO / nombre)
    print(f"{a.momento}: evidencias en docs/evidencias/ajustes_ux/ con los identificadores {', '.join(mapa.values())}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
