# Validación semántica de la llave (H18)

Para cada código derivado `int(COMUNA)*100 + int(BARRIO)` se compara el nombre del barrio en el CSV de estrato (2015) con el nombre del polígono 2026 que domina entre sus construcciones (difflib.SequenceMatcher sobre `normalize_key`, umbral de similitud ≥ 0.85).

- Códigos validados: **44 de 51**.
- Construcciones en códigos con nombre validado: **93.52 %** (4807 de 5140).
- Entre las construcciones cuyo código coincide con el polígono: 93.37 %; entre las que no coinciden: 95.19 %.
- **llave_confianza = alta** (alta ≥ 0,90; media 0,80-0,90; baja < 0,80).

**Qué NO demuestra:** que el nombre coincida no prueba que la llave sea perfecta (dos barrios distintos pueden llamarse parecido y un barrio puede haberse renombrado entre 2015 y 2026). Tampoco prueba lo contrario cuando no coincide. No se cambió la llave ni se crearon alias para mejorar estas cifras.

**Casos a revisar a mano:** el código 2098 ("Venezuela Urb. Cañaveralejo" en el CSV frente a "Venezuela" en el polígono, similitud 0,51) es el más dudoso: puede ser un barrio distinto o solo un nombre más largo. Los demás códigos sin validar (1011, 1802, 1898, 1905, 1922, 1999) difieren sobre todo por prefijos o abreviaturas ("Barrio", "Sector", "Urb.", "Unidad Res.") y son probables falsos negativos de la métrica de texto; no se tocó la métrica ni se crearon alias.

## Códigos de H13 destacados: 0 % de coincidencia con el polígono (13)

12 están en la tabla; los otros 1 (1920 con 4 construcciones) no existen en el CSV 2015 y por eso son huérfanos, no aparecen en la tabla.

| código | n construcciones | nombre CSV 2015 | nombre polígono 2026 (dominante) | similitud | % coincide polígono | veredicto |
|---|---|---|---|---|---|---|
| 1778 | 48 | Santa Anita La Selva | Santa Anita - La Selva | 1.00 | 0.0 % | coincide |
| 1783 | 2 | Ciudad Capri | Ciudad Capri | 1.00 | 0.0 % | coincide |
| 1785 | 42 | Los Portales Nuevo Rey | Los Portales - Nuevo Rey | 1.00 | 0.0 % | coincide |
| 1788 | 7 | Bosques del Limonar | Bosques del Limonar | 1.00 | 0.0 % | coincide |
| 1890 | 60 | Sector Alto de los Chorros | Sector Alto de los Chorros | 1.00 | 0.0 % | coincide |
| 1898 | 3 | Alto Nápoles | Sector Alto Nápoles | 0.77 | 0.0 % | NO coincide |
| 1983 | 11 | Tejares Cristales | Tejares - Cristales | 1.00 | 0.0 % | coincide |
| 1984 | 30 | Unidad Res. Santiago de Cali | Unidad Residencial Santiago de Cali | 0.87 | 0.0 % | coincide |
| 1988 | 18 | Cañaveralejo Seguros Patria | Cañaveralejo - Seguros Patria | 1.00 | 0.0 % | coincide |
| 1994 | 198 | Pampa Linda | Pampa Linda | 1.00 | 0.0 % | coincide |
| 1999 | 2 | U. Dep. A. Galindo Plaza Toros | Sector Unidad Deportiva Alberto Galindo Plaza de Toros | 0.67 | 0.0 % | NO coincide |
| 2098 | 16 | Venezuela Urb. Cañaveralejo | Venezuela | 0.51 | 0.0 % | NO coincide |

## Todos los códigos (51)

| código | n construcciones | nombre CSV 2015 | nombre polígono 2026 (dominante) | similitud | % coincide polígono | veredicto |
|---|---|---|---|---|---|---|
| 304 | 62 | San Cayetano | San Cayetano | 1.00 | 100.0 % | coincide |
| 305 | 264 | Los Libertadores | Los Libertadores | 1.00 | 100.0 % | coincide |
| 306 | 285 | San Juan Bosco | San Juan Bosco | 1.00 | 100.0 % | coincide |
| 901 | 122 | Alameda | Alameda | 1.00 | 100.0 % | coincide |
| 902 | 80 | Bretaña | Bretaña | 1.00 | 100.0 % | coincide |
| 1002 | 251 | El Guabal | El Guabal | 1.00 | 100.0 % | coincide |
| 1007 | 33 | Jorge Zawadsky | Jorge Zawadsky | 1.00 | 100.0 % | coincide |
| 1008 | 52 | Olímpico | Olímpico | 1.00 | 100.0 % | coincide |
| 1009 | 46 | Cristóbal Colón | Cristóbal Colón | 1.00 | 100.0 % | coincide |
| 1010 | 61 | La Selva | La Selva | 1.00 | 100.0 % | coincide |
| 1011 | 55 | Barrio Departamental | Departamental | 0.79 | 100.0 % | NO coincide |
| 1014 | 51 | Colseguros Andes | Colseguros Andes | 1.00 | 100.0 % | coincide |
| 1016 | 28 | Las Granjas | Las Granjas | 1.00 | 100.0 % | coincide |
| 1778 | 48 | Santa Anita La Selva | Santa Anita - La Selva | 1.00 | 0.0 % | coincide |
| 1783 | 2 | Ciudad Capri | Ciudad Capri | 1.00 | 0.0 % | coincide |
| 1785 | 42 | Los Portales Nuevo Rey | Los Portales - Nuevo Rey | 1.00 | 0.0 % | coincide |
| 1788 | 7 | Bosques del Limonar | Bosques del Limonar | 1.00 | 0.0 % | coincide |
| 1802 | 9 | Barrio Caldas | Caldas | 0.63 | 100.0 % | NO coincide |
| 1805 | 39 | Los Farallones | Los Farallones | 1.00 | 100.0 % | coincide |
| 1813 | 2 | Alferez Real | Alférez Real | 1.00 | 100.0 % | coincide |
| 1890 | 60 | Sector Alto de los Chorros | Sector Alto de los Chorros | 1.00 | 0.0 % | coincide |
| 1898 | 3 | Alto Nápoles | Sector Alto Nápoles | 0.77 | 0.0 % | NO coincide |
| 1901 | 202 | El Refugio | El Refugio | 1.00 | 100.0 % | coincide |
| 1903 | 235 | El Lido | El Lido | 1.00 | 100.0 % | coincide |
| 1904 | 219 | Urbanización Tequendama | Urbanización Tequendama | 1.00 | 100.0 % | coincide |
| 1905 | 177 | Barrio Eucarístico | Eucarístico | 0.76 | 100.0 % | NO coincide |
| 1906 | 208 | San Fernando Nuevo | San Fernando Nuevo | 1.00 | 100.0 % | coincide |
| 1907 | 148 | Urbanización Nueva Granada | Urbanización Nueva Granada | 1.00 | 100.0 % | coincide |
| 1908 | 174 | Santa Isabel | Santa Isabel | 1.00 | 100.0 % | coincide |
| 1910 | 88 | San Fernando Viejo | San Fernando Viejo | 1.00 | 100.0 % | coincide |
| 1911 | 24 | Miraflores | Miraflores | 1.00 | 100.0 % | coincide |
| 1912 | 154 | 3 de Julio | 3 de Julio | 1.00 | 100.0 % | coincide |
| 1913 | 316 | El Cedro | El Cedro | 1.00 | 100.0 % | coincide |
| 1914 | 385 | Champagnat | Champagnat | 1.00 | 100.0 % | coincide |
| 1915 | 95 | Urbanización Colseguros | Urbanización Colseguros | 1.00 | 100.0 % | coincide |
| 1916 | 67 | Los Cambulos | Los Cámbulos | 1.00 | 100.0 % | coincide |
| 1918 | 34 | Urbanización Militar | Urbanización Militar | 1.00 | 100.0 % | coincide |
| 1919 | 150 | Cuarto de Legua Guadalupe | Cuarto de Legua - Guadalupe | 1.00 | 100.0 % | coincide |
| 1921 | 69 | Nueva Tequendama | Nueva Tequendama | 1.00 | 100.0 % | coincide |
| 1922 | 71 | Camino Real J. Borrero S. | Camino Real - Joaquín Borrero Sinisterra | 0.75 | 100.0 % | NO coincide |
| 1923 | 62 | Camino Real Los Fundadores | Camino Real - Los Fundadores | 1.00 | 100.0 % | coincide |
| 1983 | 11 | Tejares Cristales | Tejares - Cristales | 1.00 | 0.0 % | coincide |
| 1984 | 30 | Unidad Res. Santiago de Cali | Unidad Residencial Santiago de Cali | 0.87 | 0.0 % | coincide |
| 1988 | 18 | Cañaveralejo Seguros Patria | Cañaveralejo - Seguros Patria | 1.00 | 0.0 % | coincide |
| 1994 | 198 | Pampa Linda | Pampa Linda | 1.00 | 0.0 % | coincide |
| 1999 | 2 | U. Dep. A. Galindo Plaza Toros | Sector Unidad Deportiva Alberto Galindo Plaza de Toros | 0.67 | 0.0 % | NO coincide |
| 2001 | 126 | El Cortijo | El Cortijo | 1.00 | 100.0 % | coincide |
| 2003 | 34 | Siloé | Siloé | 1.00 | 100.0 % | coincide |
| 2004 | 129 | Lleras Camargo | Lleras Camargo | 1.00 | 100.0 % | coincide |
| 2006 | 96 | Brisas de Mayo | Brisas de Mayo | 1.00 | 100.0 % | coincide |
| 2098 | 16 | Venezuela Urb. Cañaveralejo | Venezuela | 0.51 | 0.0 % | NO coincide |
