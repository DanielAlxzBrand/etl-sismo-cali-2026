"""Script de análisis de las sesiones con personas usuarias (6.2): fórmula SUS, cero sesiones, origen de las filas, n pequeño y datos sintéticos.

Todos los datos de estas pruebas son SINTÉTICOS (inventados para probar el código); no representan a ninguna persona.
"""
import csv
import importlib.util
import math
import re

import pytest

from src.common import ROOT

CARPETA = ROOT / "scripts" / "usuarios"


def _cargar(nombre):
    espec = importlib.util.spec_from_file_location(nombre, CARPETA / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(espec)
    import sys
    sys.path.insert(0, str(CARPETA))
    try:
        espec.loader.exec_module(modulo)
    finally:
        sys.path.remove(str(CARPETA))
    return modulo


an = _cargar("analizar_sesiones")
gen = _cargar("generar_datos_sinteticos")


def _escribir(carpeta, registro, cuestionarios):
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, campos, filas in (("registro.csv", an.CAMPOS_REGISTRO, registro), ("cuestionarios.csv", an.CAMPOS_CUESTIONARIOS, cuestionarios)):
        with open(carpeta / nombre, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
            w.writeheader()
            w.writerows(filas)


def _fila_registro(p, t, resultado, tiempo, origen):
    return {"participante": p, "perfil": "otro", "fecha": "2000-01-01", "tarea": t, "resultado": resultado, "tiempo_s": tiempo, "ayudas": 0, "errores": 0, "comentario_breve": "", "origen": origen}


def _fila_cuestionario(p, sus, csat, origen):
    f = {"participante": p, "perfil": "otro", "fecha": "2000-01-01", "csat": csat, "origen": origen}
    f.update({f"sus_{i}": v for i, v in enumerate(sus, 1)})
    return f


# ---------------------------------------------------------------- fórmula SUS
def test_sus_con_todo_en_3_da_50():
    assert an.puntuar_sus([3] * 10) == 50


def test_sus_del_mejor_caso_da_100_y_del_peor_da_0():
    assert an.puntuar_sus([5, 1, 5, 1, 5, 1, 5, 1, 5, 1]) == 100
    assert an.puntuar_sus([1, 5, 1, 5, 1, 5, 1, 5, 1, 5]) == 0


def test_sus_de_un_caso_mixto_calculado_a_mano():
    respuestas = [4, 2, 5, 1, 3, 3, 4, 2, 5, 2]
    impares = (4 - 1) + (5 - 1) + (3 - 1) + (4 - 1) + (5 - 1)        # ítems 1, 3, 5, 7 y 9: respuesta menos 1
    pares = (5 - 2) + (5 - 1) + (5 - 3) + (5 - 2) + (5 - 2)          # ítems 2, 4, 6, 8 y 10: 5 menos la respuesta
    assert (impares, pares) == (16, 15) and an.puntuar_sus(respuestas) == 2.5 * 31 == 77.5


@pytest.mark.parametrize("malas", [[3] * 9, [3] * 11, [0] + [3] * 9, [3] * 9 + [6], ["a"] * 10])
def test_sus_rechaza_respuestas_que_no_son_diez_enteros_de_1_a_5(malas):
    with pytest.raises((an.FilaNoValida, ValueError)):
        an.puntuar_sus(malas)


# ---------------------------------------------------------------- cero sesiones reales
def test_con_cero_sesiones_reales_no_calcula_nada_y_lo_dice(tmp_path):
    (tmp_path / "sesiones_reales").mkdir()
    for plantilla in ("plantilla_registro.csv", "plantilla_cuestionarios.csv"):       # las plantillas no se leen
        (tmp_path / "sesiones_reales" / plantilla).write_text((ROOT / "docs" / "usuarios" / "sesiones_reales" / plantilla).read_text(encoding="utf-8"), encoding="utf-8")
    assert an.main(["--base", str(tmp_path)]) == 0
    texto = (tmp_path / "resultados.md").read_text(encoding="utf-8")
    assert "No hay sesiones reales" in texto
    assert "| Tarea |" not in texto and "Media del SUS" not in texto and "%" not in texto


# ---------------------------------------------------------------- origen de las filas
def test_una_fila_simulada_en_sesiones_reales_se_rechaza_y_no_se_escribe_nada(tmp_path):
    _escribir(tmp_path / "sesiones_reales", [_fila_registro("P01", "T1", "exito", 60, "real"), _fila_registro("P01", "T2", "exito", 60, "sintetico")], [])
    assert an.main(["--base", str(tmp_path)]) == 2
    assert not (tmp_path / "resultados.md").exists()


@pytest.mark.parametrize("origen", ["simulado", "sintetico", "", "Real", "real "])
def test_solo_origen_real_se_acepta_en_sesiones_reales(tmp_path, origen):
    _escribir(tmp_path / "sesiones_reales", [_fila_registro("P01", "T1", "exito", 60, origen)], [])
    assert an.main(["--base", str(tmp_path)]) == 2


def test_una_fila_real_en_la_simulacion_se_rechaza(tmp_path):
    _escribir(tmp_path / "simulacion", [_fila_registro("S01", "T1", "exito", 60, "real")], [])
    assert an.main(["--simulado", "--base", str(tmp_path)]) == 2
    assert not (tmp_path / "resultados_simulacion.md").exists()


def test_las_columnas_equivocadas_se_rechazan(tmp_path):
    (tmp_path / "sesiones_reales").mkdir()
    (tmp_path / "sesiones_reales" / "registro.csv").write_text("participante,origen\nP01,real\n", encoding="utf-8")
    assert an.main(["--base", str(tmp_path)]) == 2


# ---------------------------------------------------------------- n pequeño y n suficiente
def _sesion_real(tmp_path, n):
    registro, cuestionarios = [], []
    for i in range(1, n + 1):
        p = f"P{i:02d}"
        for t in an.TAREAS:
            registro.append(_fila_registro(p, t, "exito" if (i + int(t[1])) % 2 else "fracaso", 40 + 10 * i, "real"))
        cuestionarios.append(_fila_cuestionario(p, [3] * 10, 4, "real"))
    _escribir(tmp_path / "sesiones_reales", registro, cuestionarios)


def test_con_menos_de_cinco_personas_muestra_k_de_n_y_no_porcentajes(tmp_path):
    _sesion_real(tmp_path, 3)
    assert an.main(["--base", str(tmp_path)]) == 0
    texto = (tmp_path / "resultados.md").read_text(encoding="utf-8")
    assert " de 3 |" in texto and "no se informa (n < 5)" in texto
    assert re.search(r"\d+,\d %", texto) is None            # ningún porcentaje con decimal (el encabezado solo nombra el 95 %)


def test_con_cinco_personas_agrega_el_intervalo_de_wilson(tmp_path):
    _sesion_real(tmp_path, 5)
    assert an.main(["--base", str(tmp_path)]) == 0
    texto = (tmp_path / "resultados.md").read_text(encoding="utf-8")
    assert "no se informa" not in texto and " % (" in texto


def test_wilson_coincide_con_un_valor_de_referencia_calculado_en_la_prueba():
    """Referencia: límites de Wilson por la ecuación cuadrática en p (otro camino que la fórmula cerrada del proyecto)."""
    k, n, z = 3, 5, 1.96
    p = k / n
    a, b, c = 1 + z * z / n, -(2 * p + z * z / n), p * p
    r = math.sqrt(b * b - 4 * a * c)
    esperado = ((-b - r) / (2 * a), (-b + r) / (2 * a))
    calculado = an.wilson(k, n)
    assert calculado == pytest.approx(esperado, abs=1e-12)
    assert calculado == pytest.approx((0.2307, 0.8824), abs=1e-3)


def test_el_intervalo_del_informe_es_el_de_wilson_del_proyecto():
    registro = [_fila_registro(f"P{i:02d}", "T1", "exito" if i <= 3 else "fracaso", 30, "real") for i in range(1, 6)]
    r = an.calcular(registro, [])
    assert r["por_tarea"]["T1"]["exito"] == 3 and r["por_tarea"]["T1"]["intervalo"] == an.wilson(3, 5)


# ---------------------------------------------------------------- datos sintéticos
def test_los_datos_sinteticos_son_deterministas_y_no_tienen_texto_libre():
    a1, b1 = gen.generar()
    a2, b2 = gen.generar()
    assert (a1, b1) == (a2, b2)
    assert gen.generar(semilla=gen.SEMILLA + 1) != (a1, b1)
    assert {f["participante"] for f in a1} == {"S01", "S02", "S03"} and len(a1) == 18 and len(b1) == 3
    assert all(f["comentario_breve"] == "" and f["origen"] == "sintetico" for f in a1) and all(f["origen"] == "sintetico" for f in b1)


def test_los_archivos_sinteticos_se_generan_byte_a_byte_iguales(tmp_path):
    gen.escribir(tmp_path / "uno")
    gen.escribir(tmp_path / "dos")
    for nombre in ("registro.csv", "cuestionarios.csv"):
        assert (tmp_path / "uno" / nombre).read_bytes() == (tmp_path / "dos" / nombre).read_bytes()


def test_los_archivos_sinteticos_del_repositorio_son_los_que_genera_la_semilla(tmp_path):
    gen.escribir(tmp_path / "x")
    for nombre in ("registro.csv", "cuestionarios.csv"):
        assert (tmp_path / "x" / nombre).read_bytes() == (ROOT / "docs" / "usuarios" / "simulacion" / nombre).read_bytes()


def test_la_simulacion_escribe_solo_su_archivo_con_el_aviso_y_no_mezcla_fuentes(tmp_path):
    gen.escribir(tmp_path / "simulacion")
    _sesion_real(tmp_path, 3)
    assert an.main(["--simulado", "--base", str(tmp_path)]) == 0
    assert not (tmp_path / "resultados.md").exists()
    sim = (tmp_path / "resultados_simulacion.md").read_text(encoding="utf-8")
    assert "DATOS SINTÉTICOS: no son personas" in sim and "S01" in sim and "P01" not in sim
    assert an.main(["--base", str(tmp_path)]) == 0
    real = (tmp_path / "resultados.md").read_text(encoding="utf-8")
    assert "P01" in real and "S01" not in real and "SINTÉTICOS" not in real


# ---------------------------------------------------------------- sesiones simuladas (D109): ni reales ni sintéticas
NM = "simulado, no medido"


def _fila_simulada(p="Participante simulado 1", t="T1", **cambios):
    f = {"participante": p, "perfil": "otro", "fecha": "2000-01-01", "tarea": t, "resultado": NM, "tiempo_s": NM, "ayudas": NM, "errores": NM, "comentario_breve": "", "origen": "simulada"}
    f.update(cambios)
    return f


def test_las_sesiones_simuladas_se_cuentan_aparte_y_no_calculan_ninguna_cifra(tmp_path):
    _escribir(tmp_path / "sesiones_simuladas", [_fila_simulada(), _fila_simulada(t="T2"), _fila_simulada("Participante simulado 2")], [])
    assert an.main(["--base", str(tmp_path), "--simuladas"]) == 0
    texto = (tmp_path / "resultados_sesiones_simuladas.md").read_text(encoding="utf-8")
    assert "Sesión simulada, no realizada con una persona real" in texto and "**Participantes simulados:** 2" in texto and "**Filas de tareas:** 3" in texto
    assert "| Tarea |" not in texto and "Wilson" not in texto and "mediana" not in texto.lower() and "SUS (0 a 100)" not in texto and "%" not in texto
    assert not (tmp_path / "resultados.md").exists() and not (tmp_path / "resultados_simulacion.md").exists(), "solo escribe su archivo"


def test_sin_sesiones_simuladas_lo_dice_y_no_cuenta_a_nadie(tmp_path):
    (tmp_path / "sesiones_simuladas").mkdir()
    assert an.main(["--base", str(tmp_path), "--simuladas"]) == 0
    assert "No hay sesiones simuladas registradas" in (tmp_path / "resultados_sesiones_simuladas.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("cambios", [{"tiempo_s": "60"}, {"ayudas": "0"}, {"errores": "1"}, {"resultado": "exito"}, {"participante": "P01"}, {"participante": "Participante simulado"},
                                     {"origen": "real"}, {"origen": "sintetico"}, {"origen": "simulado"}, {"tarea": "T9"}])
def test_una_cifra_de_verdad_un_participante_real_o_un_origen_equivocado_se_rechazan_en_sesiones_simuladas(tmp_path, cambios):
    _escribir(tmp_path / "sesiones_simuladas", [_fila_simulada(**cambios)], [])
    assert an.main(["--base", str(tmp_path), "--simuladas"]) == 2
    assert not (tmp_path / "resultados_sesiones_simuladas.md").exists()


def test_una_fila_simulada_se_rechaza_en_sesiones_reales_y_en_los_datos_sinteticos(tmp_path):
    _escribir(tmp_path / "sesiones_reales", [_fila_registro("P01", "T1", "exito", 60, "simulada")], [])
    assert an.main(["--base", str(tmp_path)]) == 2
    _escribir(tmp_path / "simulacion", [_fila_registro("S01", "T1", "exito", 60, "simulada")], [])
    assert an.main(["--base", str(tmp_path), "--simulado"]) == 2
