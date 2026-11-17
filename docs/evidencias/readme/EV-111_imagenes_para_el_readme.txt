EV-111 · Imágenes del README: copias en escala de grises de capturas reales, diagramas e insignias

Comando: python scripts/make_imagenes_readme.py. Los originales no se modifican; la copia solo se convierte a gris y, donde se indica, se recorta.

| Copia (docs/img/readme/) | Original | Recorte | Tamaño | Qué muestra | sha256 del original | sha256 de la copia |
|---|---|---|---|---|---|---|
| airflow_dag.png | docs/evidencias/modo_completo/EV-102_captura_airflow_cuatro_tareas.png | sin recorte | 1846x676 | cuadrícula del DAG con las cuatro tareas en verde (captura manual, 2026-11-16) | 3616ce986b8624f61830239b000cff9c31459c3b0fab7f11e03731b8e60bd204 | fd079c5c753c41c8807d08139c5a32cd30dc0da05bba52215527c6d8420813ad |
| phpmyadmin_tablas.png | docs/evidencias/modo_completo/EV-102_captura_phpmyadmin_siete_tablas.png | sin recorte | 1233x427 | las siete tablas de la base con sus filas, con la cuenta de solo lectura (captura manual, 2026-11-16) | 43f3e55759a19eb121c90ed34ff4bee644260454857fc2ea4a8fd4f2f734206e | 73c168f9601b3f71c8029a3e12214a4f8fdde6a52b37f2df620731e8b76a028b |
| phpmyadmin_insert_rechazado.png | docs/evidencias/modo_completo/EV-102_captura_phpmyadmin_insert_rechazado.png | sin recorte | 1669x828 | un INSERT rechazado para la cuenta de solo lectura (captura manual, 2026-11-16) | f39c3b30c2f62c0c20c81df99d5b793750d95c3a42b77c56844d3b543f0ebf72 | 37216b5ea4037d2097d5c687110ea85fd468dda65edd1e347cd422ac393e821d |
| panel_respuesta.png | docs/evidencias/readme/EV-110_captura_panel_respuesta.png | sin recorte | 1400x1355 | página Respuesta del panel (captura automatizada del navegador) | 7f4f244f60b39f0998f7e6538e0d4bf2c4ce68470d55b4e88bb472e24e214401 | 5afaa9ba29b5842479908b724be3475dfaacb24d5261e57122dd7877622a3258 |
| api_docs.png | docs/evidencias/readme/EV-110_captura_api_docs.png | izq, arriba, der, abajo = (0, 0, 1400, 1040) | 1400x1040 | documentación automática de la API, solo la lista de rutas (captura automatizada, recortada) | 0df4bf9ba377c7dcc1019858f39f2fced5efe775142989b94ecceb4e03237355 | 296b35cfbe6b106e115407b126b970c606705cf119e2b403cd757e4e966ac33d |
| arquitectura_gris.png | docs/diagramas/arquitectura_nueva.png | sin recorte | 1774x757 | diagrama de la arquitectura aportado por Daniel (EV-112), solo convertido a gris | e6e079d3ebbdcfe837ddc67f205712302acc54e80f5c2158c639d69ab2680435 | 4052fbdb6e0f5b78732c4d9555d8ae39bb536801f9e16dd53b5476a0ffed3b45 |
| flujo_dag_gris.png | docs/diagramas/flujo_dag_nueva.png | sin recorte | 1752x897 | diagrama del flujo del DAG aportado por Daniel (EV-112), solo convertido a gris | 6bf7af0c82e65b4c470f9fd114f59476a7be1e8d9c2cee946d800cbcdd6b6b00 | 9cf94b9e48b946160a8617486f1a4e34df0e395c8096fa8955e3f16ff61f7fc1 |

Imágenes generadas desde su fuente en texto (no son capturas; las aportadas a mano, sin fuente, se registran en EV-112):

| Archivo | Fuente | Comando | sha256 |
|---|---|---|---|
| docs/diagramas/arquitectura.png | docs/diagramas/arquitectura.yaml | python scripts/make_diagramas.py | d8cdc53e84f5074744aa6209a7c6304e5ddbec93fbf4245689cb1bb65c67bac0 |
| docs/diagramas/flujo_dag.png | docs/diagramas/flujo_dag.yaml | python scripts/make_diagramas.py | 21f5dd4874b2c0f8b326ba9e8f56696161281df03438e088bd9984e3bc953268 |
| docs/diagramas/arquitectura.svg | docs/diagramas/arquitectura.yaml | python scripts/make_diagramas.py | b916dee78e4e8f80bd7ae06075db8af9cddd8a51f7dcee3915d1109593eb718a |
| docs/diagramas/flujo_dag.svg | docs/diagramas/flujo_dag.yaml | python scripts/make_diagramas.py | 9191df2b384b37f667e3055f335bfde19942d4f6a06f5d501048b6e2e178a858 |
| docs/img/insignias/airflow.svg | valores medidos del repositorio | python scripts/make_insignias.py | 21b584e0b7cc212b9d4d2e8c9e7f6799d398246a0817e8af0e2d6f6c7cd47e61 |
| docs/img/insignias/cobertura.svg | valores medidos del repositorio | python scripts/make_insignias.py | 6deb9ea0570b2116fd26b303c3570da64aa5ad1e789713d921a314e16442e9d3 |
| docs/img/insignias/licencia.svg | valores medidos del repositorio | python scripts/make_insignias.py | 3ec6eae897e34b003950129e6e448ada65edda3eb6093b80a15ebb38a5df2aae |
| docs/img/insignias/madurez.svg | valores medidos del repositorio | python scripts/make_insignias.py | 1bcc283d9cd4442b2fe692c973217e648db92e51017d02eb54dc4b11d56ddce0 |
| docs/img/insignias/mysql.svg | valores medidos del repositorio | python scripts/make_insignias.py | d76990921e6387bc823da42dcb52b9b73711b61e6dcea6964f4e7a10628e7e56 |
| docs/img/insignias/pruebas.svg | valores medidos del repositorio | python scripts/make_insignias.py | dce8d93bf6e7f5ff9d1405de21358b39aee093ebe03423b3a0b1da955222b92e |
| docs/img/insignias/python.svg | valores medidos del repositorio | python scripts/make_insignias.py | 6e153fae4d12dd489ac5bb53d23d79c51a68c4a8d40cd11af511d98e13310da0 |
| docs/img/insignias/verificacion.svg | valores medidos del repositorio | python scripts/make_insignias.py | 92c1d52cd188753226f5064eb67e1daf8a989694ac66cfe2ba902c03cbe52eb9 |
