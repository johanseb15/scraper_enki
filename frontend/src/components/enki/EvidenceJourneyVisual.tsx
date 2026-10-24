/**
 * Representación conceptual del procesamiento de evidencia.
 * Nunca representa una cotización, precios o disponibilidad obtenidos en vivo.
 */
export function EvidenceJourneyVisual() {
  return (
    <figure
      className="enki-evidence-figure"
      aria-label="Cómo Enki conserva el contexto de una consulta"
    >
      <div className="enki-visual-aura" aria-hidden="true" />
      <svg
        className="enki-visual-orbit"
        viewBox="0 0 400 410"
        fill="none"
        aria-hidden="true"
        focusable="false"
      >
        <defs>
          <linearGradient id="enki-visual-line" x1="0" y1="0" x2="400" y2="410">
            <stop stopColor="#6FDAD1" stopOpacity=".7" />
            <stop offset="1" stopColor="#D6D4FF" stopOpacity=".15" />
          </linearGradient>
        </defs>
        <circle cx="260" cy="145" r="116" stroke="url(#enki-visual-line)" strokeWidth="1.5" />
        <circle cx="260" cy="145" r="159" stroke="url(#enki-visual-line)" strokeOpacity=".55" />
        <circle cx="260" cy="145" r="64" stroke="#B0E9E2" strokeOpacity=".45" />
        <circle cx="368" cy="101" r="7" fill="#88E4D7" />
        <circle cx="145" cy="174" r="4" fill="#C5BCF9" />
        <path d="M5 299 C110 238 212 368 401 295" stroke="url(#enki-visual-line)" strokeWidth="1.5" />
      </svg>
      <div className="enki-visual-content">
        <div className="enki-visual-topline">
          <span>ENKI / SIGNAL PATH</span>
          <span className="enki-visual-index">01—03</span>
        </div>
        <p className="enki-visual-caption">Ejemplo ilustrativo · no consulta datos en vivo</p>
        <div className="enki-flow-card enki-flow-first">
          <span className="enki-flow-label"><i aria-hidden="true" />01 / FUENTE</span>
          <p>“¿Cuánto cobrar por soporte remoto?”</p>
        </div>
        <div className="enki-flow-connector" aria-hidden="true">
          <span />
          <svg viewBox="0 0 14 15" width="14" height="15" fill="none">
            <path d="M7 0v12m-5-4 5 5 5-5" stroke="currentColor" strokeWidth="1.5" />
          </svg>
        </div>
        <div className="enki-flow-card enki-flow-second">
          <span className="enki-flow-label"><i aria-hidden="true" />02 / INTERPRETACIÓN</span>
          <p>Servicio · modalidad · alcance</p>
          <div className="enki-flow-pills" aria-hidden="true">
            <span>Servicio</span><span>Ubicación</span><span>Unidad</span>
          </div>
        </div>
        <div className="enki-flow-connector" aria-hidden="true">
          <span />
          <svg viewBox="0 0 14 15" width="14" height="15" fill="none">
            <path d="M7 0v12m-5-4 5 5 5-5" stroke="currentColor" strokeWidth="1.5" />
          </svg>
        </div>
        <div className="enki-flow-card enki-flow-final">
          <span className="enki-flow-label"><i aria-hidden="true" />03 / DECISIÓN RESPONSABLE</span>
          <p>Sin evidencia suficiente, no se asigna un precio.</p>
        </div>
      </div>
      <figcaption className="enki-visual-footnote">
        La fuente conserva su significado; la interpretación no inventa resultados.
      </figcaption>
    </figure>
  );
}
