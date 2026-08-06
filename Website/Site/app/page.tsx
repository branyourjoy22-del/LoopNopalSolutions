const simulations = [
  {
    id: "01",
    title: "Comparativa actual vs optimizada",
    description:
      "Compara el plan actual con una propuesta optimizada mediante ciclos, metricas y congestion a lo largo del dia.",
    href: "/simulaciones/v4.html",
    meta: "Version 4",
    accent: "blue",
  },
  {
    id: "02",
    title: "Ciclo semaforico",
    description:
      "Vista de consola del ciclo de 100 segundos y sus seis fases coordinadas.",
    href: "/simulaciones/v1.html",
    meta: "Version 1",
    accent: "amber",
  },
  {
    id: "03",
    title: "Congestion en 24 horas",
    description:
      "Simulacion acelerada con periodos pico, colas vehiculares y reloj de operacion diario.",
    href: "/simulaciones/v2.html",
    meta: "Version 2",
    accent: "red",
  },
];

const capabilities = [
  {
    number: "01",
    title: "Simulacion semaforica",
    copy: "Modelamos fases, tiempos y movimientos para observar el comportamiento operativo antes de intervenir el cruce.",
  },
  {
    number: "02",
    title: "Lectura de congestion",
    copy: "Traducimos la demanda vehicular en indicadores claros para comparar horas valle, periodos pico y puntos de saturacion.",
  },
  {
    number: "03",
    title: "Integracion de datos",
    copy: "La arquitectura esta preparada para conectar API, sensores, mapas y una base de datos en siguientes etapas.",
  },
];

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#inicio" aria-label="Loop Nopal Solutions, inicio">
          <span className="brand-mark" aria-hidden="true">
            LN
          </span>
          <span>Loop Nopal Solutions</span>
        </a>
        <nav aria-label="Navegacion principal">
          <a href="#simulaciones">Simulaciones</a>
          <a href="#soluciones">Soluciones</a>
          <a className="nav-cta" href="#contacto">
            Proyecto
          </a>
        </nav>
      </header>

      <section className="hero" id="inicio" aria-labelledby="hero-title">
        <img
          className="hero-image"
          src="/og.png"
          alt="Cruce urbano inteligente con semaforos y rutas de datos en Queretaro"
        />
        <div className="hero-shade" aria-hidden="true" />
        <div className="hero-content">
          <p className="eyebrow">Movilidad inteligente · Queretaro</p>
          <h1 id="hero-title">Loop Nopal Solutions</h1>
          <p className="hero-copy">
            Simulamos la operacion de cruces urbanos para convertir ciclos,
            demanda y congestion en decisiones que se pueden probar.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#simulaciones">
              Explorar simulaciones
            </a>
          </div>
        </div>
        <div className="hero-status" aria-label="Estado del prototipo">
          <span className="status-light" aria-hidden="true" />
          Prototipo operativo
          <span>Av. Sombrerete · Calle 6</span>
        </div>
      </section>

      <section className="simulations-section" id="simulaciones" aria-labelledby="simulations-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow dark">Laboratorio abierto</p>
            <h2 id="simulations-title">Simulaciones ejecutables</h2>
          </div>
          <p>
            Cada experiencia se abre en una pestaña nueva y funciona de manera
            independiente, directamente desde este sitio.
          </p>
        </div>

        <div className="simulation-grid">
          {simulations.map((simulation) => (
            <article className={`simulation-card accent-${simulation.accent}`} key={simulation.href}>
              <div className="card-topline">
                <span className="card-number">{simulation.id}</span>
                <span className="card-meta">{simulation.meta}</span>
              </div>
              <div className="phase-strip" aria-hidden="true">
                <span />
                <span />
                <span />
                <span />
                <span />
                <span />
              </div>
              <h3>{simulation.title}</h3>
              <p>{simulation.description}</p>
              <a
                className="card-link"
                href={simulation.href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`Abrir ${simulation.title} en una pestaña nueva`}
              >
                Ejecutar simulacion <span aria-hidden="true">↗</span>
              </a>
            </article>
          ))}
        </div>
      </section>

      <section className="capabilities-section" id="soluciones" aria-labelledby="capabilities-title">
        <div className="capabilities-intro">
          <p className="eyebrow">De la fase al sistema</p>
          <h2 id="capabilities-title">Una base clara para evolucionar la movilidad urbana.</h2>
        </div>
        <div className="capabilities-list">
          {capabilities.map((capability) => (
            <article className="capability" key={capability.number}>
              <span>{capability.number}</span>
              <h3>{capability.title}</h3>
              <p>{capability.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="project-section" id="contacto" aria-labelledby="project-title">
        <div>
          <p className="eyebrow dark">Proyecto en desarrollo</p>
          <h2 id="project-title">Cruce Sombrerete, Calle 6 y Praxedis Guerrero.</h2>
        </div>
        <p>
          El prototipo actual representa un ciclo de seis fases y escenarios de
          congestion simulada. Las tasas mostradas son demostrativas y no
          sustituyen aforos viales reales.
        </p>
        <a
          className="button button-dark"
          href="https://sites.google.com/view/loopnopalsolutions"
          target="_blank"
          rel="noopener noreferrer"
        >
          Ver sitio de referencia <span aria-hidden="true">↗</span>
        </a>
      </section>

      <footer>
        <a className="brand footer-brand" href="#inicio">
          <span className="brand-mark" aria-hidden="true">
            LN
          </span>
          <span>Loop Nopal Solutions</span>
        </a>
        <p>Movilidad urbana, medida y simulada.</p>
        <p>Queretaro, Qro, Mexico</p>
      </footer>
    </main>
  );
}
