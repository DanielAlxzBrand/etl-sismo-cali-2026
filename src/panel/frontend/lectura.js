// Herramientas de lectura del panel (guía, curiosidades, avisos, modo presentación y selección coordinada).
// Todo texto que llega de Python se escribe con textContent: este archivo no construye HTML a partir de datos.
// La figura y el detalle los dibuja Streamlit (st.html, ya escapado desde Python); aquí solo se leen y se marcan.
export default function ({parentElement, data}) {
  const lienzo = parentElement.closest(".st-key-lienzo");
  if (!lienzo) return undefined;
  const anfitrion = parentElement;
  const buscar = selector => lienzo.querySelector(selector);
  const accion = nombre => anfitrion.querySelector('[data-accion="' + nombre + '"]');
  const parte = nombre => anfitrion.querySelector('[data-parte="' + nombre + '"]');
  const cuaderno = anfitrion.querySelector("#cuaderno");
  const aviso = anfitrion.querySelector(".aviso-v3");
  const auto = anfitrion.querySelector("[data-auto]");
  const clave = "sismo-cali.v4." + data.slug;
  let estado = {};
  try { estado = JSON.parse(sessionStorage.getItem(clave)) || {}; } catch (error) { estado = {}; }
  const guardar = () => {
    try { sessionStorage.setItem(clave, JSON.stringify(estado)); } catch (error) { /* sin almacenamiento: no pasa nada */ }
  };
  const pasos = data.guia;
  const fichas = data.fichas;
  auto.checked = !estado.silencio;
  let seccion = "";
  let indice = 0;
  let fichaAvisada = 0;
  let inicio = null;
  let reloj;
  let vigente = true;
  let exponiendo = false;
  const grupos = () => Array.from(lienzo.querySelectorAll("[name=categoria]"));
  const vistas = () => Array.from(lienzo.querySelectorAll("[name=vista]"));

  function ubicar(elemento) {
    if (!elemento) return;
    elemento.focus({preventScroll: true});
    elemento.scrollIntoView({block: "nearest"});
  }
  function pausar() {
    clearTimeout(reloj);
    if (inicio !== null) {
      estado.activo = (estado.activo || 0) + performance.now() - inicio;
      inicio = null;
      guardar();
    }
  }
  function programar() {
    pausar();
    if (!vigente || document.hidden || !document.hasFocus() || estado.avisada || estado.silencio || seccion || exponiendo) return;
    inicio = performance.now();
    reloj = setTimeout(() => {
      pausar();
      if (!vigente || !anfitrion.isConnected || document.hidden || !document.hasFocus()) return;
      fichaAvisada = estado.proxima || 0;
      aviso.hidden = false;
      aviso.querySelector("p").textContent = fichas[fichaAvisada].titulo;
      estado.avisada = true;
      estado.proxima = (fichaAvisada + 1) % fichas.length;
      guardar();
    }, Math.max(0, 40000 - (estado.activo || 0)));
  }
  function ocultarAviso() {
    aviso.hidden = true;
    if (aviso.contains(document.activeElement)) accion("fichas").focus({preventScroll: true});
  }
  function mostrar(tipo, posicion, enfocar = true) {
    ocultarAviso();
    seccion = tipo;
    indice = posicion;
    const esGuia = tipo === "guia";
    const total = esGuia ? pasos.length : fichas.length;
    parte("serie").textContent = (esGuia ? "Guía de lectura" : "Curiosidades") + " · " + (indice + 1) + " de " + total;
    parte("titulo").textContent = esGuia ? pasos[indice].titulo : fichas[indice].titulo;
    parte("texto").textContent = esGuia ? pasos[indice].texto : fichas[indice].explicacion;
    parte("fuente").hidden = false;
    if (esGuia) {
      parte("fuente").textContent = "En la página · " + pasos[indice].region;
    } else {
      const ficha = fichas[indice];
      parte("fuente").textContent = [ficha.categoria, ficha.fundamento].filter(Boolean).join(" · ");
      estado.proxima = (indice + 1) % total;
      guardar();
    }
    auto.parentElement.hidden = esGuia;
    accion("anterior").disabled = esGuia && indice === 0;
    accion("siguiente").disabled = esGuia && indice === total - 1;
    accion("guia").setAttribute("aria-expanded", String(esGuia));
    accion("fichas").setAttribute("aria-expanded", String(!esGuia));
    cuaderno.hidden = false;
    estado.seccion = tipo;
    estado.indice = indice;
    guardar();
    if (enfocar) ubicar(parte("titulo"));
    programar();
  }
  function cerrarCuaderno() {
    if (!seccion) return;
    const origen = accion(seccion);
    origen.setAttribute("aria-expanded", "false");
    seccion = "";
    estado.seccion = "";
    guardar();
    cuaderno.hidden = true;
    ubicar(origen);
    programar();
  }
  function presentar(activar) {
    const boton = accion("presentar");
    ocultarAviso();
    exponiendo = activar;
    estado.exposicion = activar;
    guardar();
    lienzo.classList.toggle("exposicion-local", activar);
    if (activar) {
      lienzo.setAttribute("role", "dialog");
      lienzo.setAttribute("aria-modal", "true");
      lienzo.setAttribute("aria-label", "Presentación de " + data.titulo);
    } else {
      for (const atributo of ["role", "aria-modal", "aria-label"]) lienzo.removeAttribute(atributo);
    }
    boton.textContent = activar ? "Salir de presentación" : "Presentar";
    boton.setAttribute("aria-pressed", String(activar));
    ubicar(boton);
    programar();
  }
  function clic(evento) {
    const nombre = evento.target.closest("[data-accion]")?.dataset.accion;
    switch (nombre) {
      case "guia": case "fichas":
        if (seccion === nombre) cerrarCuaderno();
        else mostrar(nombre, nombre === "fichas" ? (estado.proxima || 0) : 0);
        break;
      case "leer": mostrar("fichas", fichaAvisada); break;
      case "anterior": mostrar(seccion, seccion === "fichas" ? (indice + fichas.length - 1) % fichas.length : indice - 1); break;
      case "siguiente": mostrar(seccion, seccion === "fichas" ? (indice + 1) % fichas.length : indice + 1); break;
      case "cerrar": cerrarCuaderno(); break;
      case "ocultar": ocultarAviso(); break;
      case "silenciar":
        auto.checked = false;
        estado.silencio = true;
        guardar();
        ocultarAviso();
        programar();
        break;
      case "presentar": presentar(!exponiendo); break;
      case "arriba": {
        const titulo = buscar("h1");
        if (titulo) {
          titulo.tabIndex = -1;
          titulo.focus({preventScroll: true});
        }
        buscar(".barra")?.scrollIntoView({block: "start"});
        break;
      }
      default: break;
    }
  }
  function cambio({target}) {
    if (target.name === "vista") estado.vista = target.value;
    if (target.name === "categoria") estado.grupo = grupos().indexOf(target);
    if (target === auto) {
      estado.silencio = !auto.checked;
      programar();
    }
    guardar();
  }
  function teclado(evento) {
    if (evento.key === "Escape") {
      if (exponiendo && !seccion && aviso.hidden && !evento.defaultPrevented) {
        evento.preventDefault();
        presentar(false);
      } else if (seccion) {
        evento.preventDefault();
        cerrarCuaderno();
      } else if (!aviso.hidden) {
        evento.preventDefault();
        ocultarAviso();
      }
      return;
    }
    if (evento.key === "Tab" && exponiendo) {
      const controles = Array.from(lienzo.querySelectorAll("button,a[href],summary,input,[tabindex]"))
        .filter(elemento => elemento.tabIndex >= 0 && !elemento.disabled && elemento.getClientRects().length);
      if (!controles.length) return;
      const destino = evento.shiftKey ? controles.at(-1) : controles[0];
      if (document.activeElement === (evento.shiftKey ? controles[0] : controles.at(-1))) {
        evento.preventDefault();
        destino.focus();
      }
    }
  }
  function ajustarAyuda(evento) {
    const fila = evento.target.closest?.(".dato");
    if (!fila || fila.contains(evento.relatedTarget)) return;
    fila.classList.remove("sin-ayuda");
    const ayuda = fila.querySelector(".ayuda");
    if (!ayuda) return;
    const caja = fila.getBoundingClientRect();
    ayuda.style.left = Math.max(4, Math.min(caja.width * 0.26, innerWidth - caja.left - ayuda.offsetWidth - 12)) + "px";
    ayuda.style.top = caja.bottom + ayuda.offsetHeight + 8 > innerHeight && caja.top > ayuda.offsetHeight ? (-ayuda.offsetHeight + 3) + "px" : "75%";
  }
  function apagarAyuda(evento) {
    if (evento.key !== "Escape" || exponiendo || seccion) return;
    const fila = buscar(".dato:hover") || buscar(".dato:focus-within");
    if (fila) fila.classList.add("sin-ayuda");
  }
  function abrirFila(evento) {
    const fila = evento.target;
    if (!(fila instanceof Element) || !fila.classList.contains("lectura-fila") || !fila.open) return;
    grupos()[Number(fila.dataset.fila)]?.click();
    for (const otra of lienzo.querySelectorAll(".lectura-fila[open]")) if (otra !== fila) otra.open = false;
  }
  // La figura puede llegar después que este componente: se restaura la selección guardada cuando aparece.
  function restaurar() {
    const modos = vistas();
    const opciones = grupos();
    if (!modos.length || !opciones.length) return false;
    const modo = modos.find(entrada => entrada.value === estado.vista);
    if (modo) modo.checked = true;
    if (opciones[estado.grupo]) opciones[estado.grupo].checked = true;
    return true;
  }

  const oyentes = new AbortController();
  const opciones = {signal: oyentes.signal};
  lienzo.addEventListener("click", clic, opciones);
  lienzo.addEventListener("change", cambio, opciones);
  lienzo.addEventListener("keydown", teclado, opciones);
  lienzo.addEventListener("pointerover", ajustarAyuda, opciones);
  lienzo.addEventListener("focusin", ajustarAyuda, opciones);
  lienzo.addEventListener("toggle", abrirFila, {signal: oyentes.signal, capture: true});
  document.addEventListener("keydown", apagarAyuda, opciones);
  for (const tipo of ["focus", "pageshow"]) window.addEventListener(tipo, programar, opciones);
  window.addEventListener("pagehide", pausar, opciones);
  window.addEventListener("blur", pausar, opciones);
  document.addEventListener("visibilitychange", programar, opciones);

  const observador = new MutationObserver(() => { if (restaurar()) observador.disconnect(); });
  if (!restaurar()) observador.observe(lienzo, {childList: true, subtree: true});
  if (estado.exposicion) presentar(true);
  if (estado.seccion === "guia" || estado.seccion === "fichas") mostrar(estado.seccion, estado.indice || 0, false);
  programar();
  return () => {
    vigente = false;
    pausar();
    observador.disconnect();
    oyentes.abort();
    lienzo.classList.remove("exposicion-local");
    for (const atributo of ["role", "aria-modal", "aria-label"]) lienzo.removeAttribute(atributo);
  };
}
