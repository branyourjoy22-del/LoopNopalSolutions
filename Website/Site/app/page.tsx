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

const achievements = [
  "Primer modelo de optimizacion adaptativa de trafico.",
  "Analisis de flujo vehicular para intersecciones piloto.",
  "Arquitectura inicial preparada para integracion en la nube.",
  "Ruta escalable para futuras soluciones de movilidad inteligente.",
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

const team = [
  {
    name: "Oscar B. Lara Lopez",
    role: "Fundador y desarrollador de sistemas de movilidad inteligente",
    focus: "Analisis, direccion tecnica y sistemas de movilidad.",
  },
  {
    name: "Ricardo Andrade Prado",
    role: "Logistica, finanzas y soporte tecnico",
    focus: "Ingenieria industrial y coordinacion operativa.",
  },
  {
    name: "Edgar Renan Lopez Silva",
    role: "Desarrollo y despliegue de software",
    focus: "Soporte tecnico en campo y oficina.",
  },
];

const questions = [
  {
    question: "Donde se desarrolla el proyecto inicial?",
    answer:
      "El caso de estudio se concentra en el cruce de avenida Sombrerete, Calle 6 y Praxedis Guerrero, en Queretaro.",
  },
  {
    question: "Que compara la simulacion V4?",
    answer:
      "Compara el plan semaforico actual con una propuesta optimizada usando el mismo reloj y la misma llegada simulada de vehiculos.",
  },
  {
    question: "Los resultados sustituyen un aforo vial real?",
    answer:
      "No. El prototipo usa tasas demostrativas para evaluar escenarios. Una implementacion en campo requiere aforos, validacion tecnica y coordinacion con las autoridades correspondientes.",
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
          <a href="#empresa">Empresa</a>
          <a href="#simulaciones">Simulaciones</a>
          <a href="#equipo">Equipo</a>
          <a className="nav-cta" href="#contacto">
            Contacto
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
          <p className="eyebrow">Movilidad inteligente / Queretaro</p>
          <h1 id="hero-title">Loop Nopal Solutions</h1>
          <p className="hero-copy">
            Desarrollamos soluciones de movilidad urbana basadas en datos para
            convertir ciclos, demanda y congestion en decisiones que se pueden probar.
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
          <span>Av. Sombrerete / Calle 6</span>
        </div>
      </section>

      <section className="company-section" id="empresa" aria-labelledby="company-title">
        <div className="company-overview">
          <div>
            <p className="eyebrow dark">La empresa</p>
            <h2 id="company-title">Tecnologia practica para una movilidad urbana mas eficiente.</h2>
          </div>
          <div className="company-copy">
            <p>
              Loop Nopal Solutions es una empresa de tecnologia dedicada a crear
              software, analisis y herramientas para la gestion inteligente del trafico.
            </p>
            <p>
              Nuestra mision es ayudar a reducir congestion, mejorar la seguridad y
              hacer mas eficiente el transporte mediante soluciones medibles y basadas
              en datos.
            </p>
          </div>
        </div>

        <div className="history-band">
          <p className="eyebrow dark">Nuestra historia</p>
          <p>
            La empresa nace para atender uno de los retos mas comunes de las ciudades en
            crecimiento: la gestion ineficiente del trafico. La primera iniciativa
            desarrolla control semaforico adaptativo capaz de evolucionar desde una
            implementacion accesible hasta un sistema urbano inteligente.
          </p>
        </div>

        <div className="achievement-grid" aria-label="Logros del equipo">
          {achievements.map((achievement, index) => (
            <article className="achievement" key={achievement}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <p>{achievement}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="simulations-section" id="simulaciones" aria-labelledby="simulations-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow dark">Laboratorio abierto</p>
            <h2 id="simulations-title">Simulaciones ejecutables</h2>
          </div>
          <p>
            Cada experiencia se abre en una pestana nueva y funciona de manera
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
                aria-label={`Abrir ${simulation.title} en una pestana nueva`}
              >
                Ejecutar simulacion
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

      <section className="team-section" id="equipo" aria-labelledby="team-title">
        <div className="section-heading team-heading">
          <div>
            <p className="eyebrow dark">Equipo</p>
            <h2 id="team-title">Colaboracion tecnica con enfoque practico.</h2>
          </div>
          <p>
            Trabajamos con curiosidad, comunicacion transparente y una meta comun:
            construir tecnologia con impacto medible para las comunidades.
          </p>
        </div>
        <div className="team-grid">
          {team.map((member, index) => (
            <article className="team-member" key={member.name}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{member.name}</h3>
              <p className="member-role">{member.role}</p>
              <p>{member.focus}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="project-section" id="proyecto" aria-labelledby="project-title">
        <div>
          <p className="eyebrow dark">Proyecto en desarrollo</p>
          <h2 id="project-title">Cruce Sombrerete, Calle 6 y Praxedis Guerrero.</h2>
        </div>
        <p>
          El prototipo actual representa un ciclo de seis fases y escenarios de
          congestion simulada. Las tasas mostradas son demostrativas y no sustituyen
          aforos viales reales.
        </p>
      </section>

      <section className="faq-section" id="preguntas" aria-labelledby="faq-title">
        <div className="faq-intro">
          <p className="eyebrow dark">Preguntas frecuentes</p>
          <h2 id="faq-title">Informacion esencial del proyecto.</h2>
        </div>
        <div className="faq-list">
          {questions.map((item) => (
            <details key={item.question}>
              <summary>{item.question}</summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="contact-section" id="contacto" aria-labelledby="contact-title">
        <div>
          <p className="eyebrow">Contacto general</p>
          <h2 id="contact-title">Hablemos de movilidad urbana.</h2>
        </div>
        <p>
          Para informacion sobre el proyecto, colaboraciones o demostraciones, usa
          los canales oficiales de Loop Nopal Solutions.
        </p>
        <div className="contact-actions">
          <a className="button contact-primary" href="mailto:branurjoy1095@outlook.com">
            branurjoy1095@outlook.com
          </a>
          <a className="button contact-secondary" href="tel:+524462209873">
            446 220 9873
          </a>
        </div>
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
