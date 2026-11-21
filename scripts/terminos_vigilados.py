"""Términos vigilados, guardados como sha256 de la palabra normalizada para que ningún archivo del repositorio los escriba.

Una palabra normalizada va en minúsculas y sin tildes. `encuentra(texto, conjunto)` parte el texto en palabras (con o sin guiones), también por mayúsculas internas
(«UnaPalabra» se mira entera y en sus partes) y revisa además cada pareja de palabras seguidas. Devuelve las posiciones (índice de carácter) donde hay un término del conjunto.
`HERRAMIENTAS` reúne nombres de herramientas, las palabras que describen cómo se les habla y las marcas de procedencia de las imágenes.
`DE_IA` reúne la sigla y el nombre del campo, que solo se vigilan donde la redacción debe prescindir de ellos (el README).
`canario()` devuelve un término de `HERRAMIENTAS` guardado en base64 (no coincide con ninguna búsqueda por texto) para probar que el escáner detecta.
Qué NO hace: no entiende contexto; una palabra coincidente se marca aunque la use otra cosa, y la persona decide.
"""
import base64
import hashlib
import re
import unicodedata

HERRAMIENTAS = frozenset({
    "c857d09db23e6822e3600bc06ad8d58f92ed62bc8efd81c753f77048662cb97d",
    "c70eca6b0f88f44d81a41311647e50fda1ac454ec04ffd442b0eb4743a993131",
    "60965168ce762e949600281ba6d01fee136e5b6e8257b1f216f9025ed324474c",
    "7d3194f79e645c42e4396dda38be04766810ec6a00d00aced3ffc2a0a1f1a9ef",
    "053ea4804ef1bb33d4a3d6fb024a614b6d257cebc2bc7cd915da9c9522f37ffc",
    "5d72436256ada53828b51895a94bb8489e9f1ac4fe937a8024ef1594e7045ff6",
    "57de4cf40144bdf7d00010f2f5557a7d642c2b9705309bfade167dd313e2ca93",
    "3ea125d0bff386e6754b3782b300016fc79a9cf8f8669c0a5c3db64467ddb681",
    "ac0a3dfd6dddb20962cecff6ee5fe65e19d3923be20e52c5ab52ff877f7e4c32",
    "9058f79c893a1d7e20b13009b95b9cf3211478a91a47e2ad65bdfedad6fc98f4",
    "d931372ba7f836a0bf8405601b0a293927ba20bf368f12b2cf3affc384c8a9da",
    "6f7ac1823da81d2e52d1a1549ee69c85bbf8bb56d06682849e7c09da2785ce3b",
    "45d780f82c9247fc1142f8b60c12b6c6cd3d9f23dd836cfa6e84c498d2f83292",
    "add92b9cde2bdbf3daaf65a0db79e9b1a7fa428b71b4d6ce38c742eb6dca0c1c",
    "5d0c0ab127fdea24d94e7e3326b6ceb965ab82ad897f9de1bd6b1a9a23f87578",
    "cf07194ee232eb531e15f690000d19846dea69cf05504782658afcfacb9228a2",
    "eb7526362ee7678cb5650f67d90cfdb84485363ca148ff3993ded032560941fb",
    "6d92475719b10e266cceead6b4dca3b637c0d5adae37d2b91a5f094e40b57e9e",
    "5996d0d1afbe8dbfdb03b1c8512187de8229553ad3fadaa7bdfca8088de1a230",
    "0002dabb0f9d5511113d9e95ddc1cac604f88624339fc5358e579a7420a6585b",
    "7a7aa6b26413666ae42f4127197f26554ac45dc26d7f7c0ea18c4aca118d45ca",
    "4bd0b7cf893e8ac77eab9777aeeeb03e948f3a57719c4b2d39dca47fcfdc37dc",
    "7e3132332f1f8b95d6860e5b8943fd5de540a895b8b0f5a51091de139c520912",
})
DE_IA = frozenset({
    "26138d8a757dd1dc09df6301bc4a47f0a1f7f785a725ae72574c6862127a2201",
    "fb79a0a30e791cdaebf4fde3dd5a9822bc2aed9a251ba58e179d5380c141e0b3",
    "2b302f3e9adcbb7159bf54d4035260e5df49effedb1d56f670837efb25a46e5a",
    "25b53b8d9b901bedce8f4be7571d18b7813dd58d9b505b3abcb8748af62dd105",
})
# Identificadores técnicos de otra herramienta (opciones de configuración del panel) que contienen una palabra vigilada y no se pueden renombrar: se comparan enteros, sin guiones bajos.
PERMITIDOS = frozenset({
    "ee6fa4e4a2a88bca906a788445ff6cdb613eb8d4b28e53c77e491b6a8a93fc86",
    "d89c489e339d2f3807b2828dbddb79b27a89911b9e3b0da3ba974575694f964d",
})
FRASES_DE_ELABORACION = frozenset({
    "7433d76eda96f21e2c51c273e79423fb82b5cbf914ef7378528dcb2022436087",
    "50381cfb6f94629ae0247256988e6ce847cbe1193281df2888bf269755b6db73",
    "796c92995b5012083559b026b3896a6533c592e2dc7859a616d4eb1f36c9e209",
    "d08b93077d3ea612272ff49e60b6791e9ed31cc2708ddb4c98a33c37f8f758d7",
    "8511d00157c2e54408833d5d53e338b66a0ec793da88f42d6e12430160f578a5",
    "5befd7eb0e8cce2558409cef4ccf677d4dc2bf8f657941d2d06612a1cc1495f3",
    "79ab5f2cb1fa4e0269f61768e5796f4b612a34d09d2152bcefc83fbd2cca985d",
})
# Las dos formas de la palabra con que se llamaba a los mensajes enviados a una herramienta; `sustituir` las escribe como «mensaje» y «mensajes».
MENSAJES = {
    "cf07194ee232eb531e15f690000d19846dea69cf05504782658afcfacb9228a2": "mensaje",
    "eb7526362ee7678cb5650f67d90cfdb84485363ca148ff3993ded032560941fb": "mensajes",
}
_CANARIO_B64 = "Y2xhdWRl"
_PALABRA = re.compile(r"[A-Za-z0-9À-ɏ]+(?:-[A-Za-z0-9À-ɏ]+)*")
_IDENTIFICADOR = re.compile(r"[A-Za-z0-9_]+")
_PARTES = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-zß-ɏ]+|[0-9]+")


def canario():
    """Un término vigilado de `HERRAMIENTAS`, armado en el momento (el archivo solo guarda su base64)."""
    return base64.b64decode(_CANARIO_B64).decode("ascii")


def _normal(palabra):
    texto = unicodedata.normalize("NFD", palabra.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def _hash(palabra):
    return hashlib.sha256(_normal(palabra).encode("utf-8")).hexdigest()


def _permitido(texto, pos):
    """True si la palabra que empieza en `pos` es parte de un identificador técnico permitido."""
    ini = pos
    while ini > 0 and (texto[ini - 1].isalnum() or texto[ini - 1] == "_"):
        ini -= 1
    m = _IDENTIFICADOR.match(texto, ini)
    return m is not None and _hash(m.group(0).replace("_", "")) in PERMITIDOS


def encuentra(texto, conjunto=HERRAMIENTAS, partes=True):
    """Posiciones de carácter donde empieza una palabra, una parte de ella (con `partes`, también las de mayúsculas internas) o una frase de hasta cuatro palabras seguidas vigilada."""
    hallazgos = []
    tokens = [(m.group(0), m.start(), m.end()) for m in _PALABRA.finditer(texto)]
    for i, (palabra, ini, _fin) in enumerate(tokens):
        candidatas = {palabra, palabra.replace("-", "")} | set(palabra.split("-"))
        if partes:
            candidatas |= set(_PARTES.findall(palabra.replace("-", " ")))
        if any(_hash(c) in conjunto for c in candidatas if c):
            if not _permitido(texto, ini):
                hallazgos.append(ini)
            continue
        frase = [_normal(palabra)]
        for k in range(1, 4):
            if i + k >= len(tokens) or texto[tokens[i + k - 1][2]:tokens[i + k][1]].strip(" 	") != "":
                break
            frase.append(_normal(tokens[i + k][0]))
            if hashlib.sha256(" ".join(frase).encode("utf-8")).hexdigest() in conjunto:
                hallazgos.append(ini)
                break
    return hallazgos


def contiene(texto, conjunto=HERRAMIENTAS):
    return bool(encuentra(texto, conjunto))


class Vigilados:
    """Interfaz parecida a la de una expresión regular (`search`, `findall`) sobre un conjunto de sha256."""

    def __init__(self, conjunto=HERRAMIENTAS, partes=True):
        self.conjunto = conjunto
        self.partes = partes

    def search(self, texto):
        """Una tupla con la posición del primer hallazgo (siempre verdadera, aunque sea la posición 0) o None."""
        pos = encuentra(texto, self.conjunto, self.partes)
        return (pos[0],) if pos else None

    def findall(self, texto):
        return encuentra(texto, self.conjunto, self.partes)


def sustituir(texto, por="herramienta"):
    """Texto con cada palabra (o parte de una palabra con mayúsculas internas) vigilada reemplazada: «mensaje(s)» para las de `MENSAJES` y `por` para las demás."""
    def cambio(parte):
        h = _hash(parte)
        if h in MENSAJES:
            return MENSAJES[h]
        return por if h in HERRAMIENTAS else None

    def palabra(m):
        entera = m.group(0)
        c = cambio(entera)
        if c is not None:
            return c
        return _PARTES.sub(lambda q: cambio(q.group(0)) or q.group(0), entera) if any(cambio(q) for q in _PARTES.findall(entera)) else entera

    return _PALABRA.sub(palabra, texto)
