# Guía de simulación: sesiones de uso del panel

**Ítems del checklist:** 6.1, 6.2, 6.3, 6.5 y 7.4 (material de apoyo; el estado de estos ítems lo fija D111, no esta guía) · **Decisiones:** [D82 a D90](../../DECISIONES.md), [D99 y D100](../../DECISIONES.md) · **Estado:** material preparado; las sesiones todavía no se han hecho.

Esta carpeta es la **única fuente** de la guía en PDF para las sesiones de uso del panel entre las tres personas del equipo: un archivo `.md` por parte, en el orden de sus nombres. La guía no repite lo que ya está escrito en otros documentos: lo trae por inclusión (`{{incluir: ruta#sección}}`) al generar el PDF, porque dos copias de un mismo hecho se desactualizan.

| Archivo | Parte | Para quién |
|---|---|---|
| [01_como_usar.md](01_como_usar.md) | Cómo usar la guía: roles, reparto de sesiones y qué lee cada quien | todos |
| [02_parte_a_antes_de_empezar.md](02_parte_a_antes_de_empezar.md) | Parte A · instalar el modo mínimo desde el zip | todos |
| [03_parte_b_primera_vez_con_el_panel.md](03_parte_b_primera_vez_con_el_panel.md) | Parte B · arrancar el panel, moverse y cerrarlo | todos |
| [04_parte_c_la_sesion.md](04_parte_c_la_sesion.md) | Parte C · la sesión, con las tareas | quien facilita |
| [05_parte_d_que_anotar.md](05_parte_d_que_anotar.md) | Parte D · qué anotar y en qué formato | quien facilita |
| [06_parte_e_devolver_los_resultados.md](06_parte_e_devolver_los_resultados.md) | Parte E · devolver y juntar los resultados | quien facilita |
| [07_anexo_lista_del_participante.md](07_anexo_lista_del_participante.md) | Anexo 1 · lista del participante | todos |
| [08_anexos_del_facilitador.md](08_anexos_del_facilitador.md) | Anexo 2 · lista y hoja de sesión del facilitador | quien facilita |
| [09_que_no_demuestra.md](09_que_no_demuestra.md) | Qué no demuestra este procedimiento | todos |

## Cómo se genera
```powershell
.\.venv\Scripts\python.exe scripts\usuarios\generar_guia_simulacion.py
```
Escribe en `dist/` (que Git ignora) dos PDF: `guia_simulacion_completa.pdf`, para quien facilita, y `guia_simulacion_participante.pdf`, que solo trae las partes marcadas «todos» y por eso **no incluye las tareas ni sus criterios**. Lo hicimos así porque quien lee las tareas antes de su sesión ya no puede responderlas de primera vez. El PDF sale de Edge en modo sin ventana, que ya trae Windows 11, y el conversor de Markdown es propio: no hay dependencias nuevas. Con `--solo-html` se escribe solo el HTML, para abrirlo en otro navegador.

## Qué no demuestra
Esta carpeta dice cómo hacer las sesiones, no que se hayan hecho ni qué resultaron. Los límites de las sesiones están en [09_que_no_demuestra.md](09_que_no_demuestra.md). Las pruebas de `tests/test_guia_simulacion.py` comprueban que las fuentes existan, que cada comando y bandera citados existan, que las inclusiones se resuelvan y que el texto no traiga rutas locales ni afirme lo que las sesiones no demuestran.
