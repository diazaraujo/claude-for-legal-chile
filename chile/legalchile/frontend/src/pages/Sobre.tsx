import '../styles/decide.css'

export default function Sobre() {
  return (
    <div className="decide-root">
      {/* HEADER */}
      <header className="nav">
        <div className="wrap">
          <a href="/" className="brand"><b>Claude Legal Chile</b><span className="sub">· Derecho chileno real</span></a>
          <div className="spacer" />
          <nav className="navlinks">
            <a href="/jueces">Jueces</a>
            <a href="/empresas">Empresas</a>
            <a href="/fiscales">Fiscales</a>
            <a href="/tribunales">Tribunales</a>
            <details className="more">
              <summary>Más <span className="caret">▾</span></summary>
              <div className="more-menu">
                <a href="/">Inicio</a>
                <a href="/buscar">Buscar</a>
                <a href="/analisis">Análisis ↗</a>
                <a href="#que-es">¿Qué es?</a>
                <a href="#comparativa">Antes / después</a>
                <a href="#corpus">El corpus</a>
                <a href="#pipeline">El recorrido</a>
                <a href="#capacidades">Capacidades</a>
                <a href="#participar">Participar</a>
              </div>
            </details>
            <a className="btn btn-primary" href="mailto:antonio@unholster.com?subject=Claude%20Legal%20Chile">Contacto</a>
          </nav>
        </div>
      </header>

      {/* INTRO */}
      <section className="hero">
        <div className="wrap">
          <div className="toprow">
            <span className="section-tag">Sobre el proyecto</span>
            <span className="status"><span className="dot"></span> Corpus verificable · cero citas inventadas</span>
          </div>
          <h1>El asistente legal que <em>cita el derecho chileno</em>, no lo inventa.</h1>
          <p className="lead">Responde preguntas jurídicas apoyándose en un corpus real y verificable —legislación vigente, jurisprudencia de los tribunales y jurisprudencia administrativa— y no en lo que un modelo de lenguaje “recuerda”. Cada respuesta cita su fuente. Si la información no está en el corpus, lo dice.</p>
        </div>
      </section>

      {/* ¿QUÉ ES? */}
      <section className="blk gray" id="que-es">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">¿Qué es?</span>
            <h2>Qué es Claude Legal Chile</h2>
            <p>Un asistente legal construido sobre un corpus real y verificable del derecho chileno. No responde desde la memoria de un modelo de lenguaje: recupera primero las fuentes pertinentes y cita cada afirmación. Si algo no está en el corpus, lo dice.</p>
          </div>
          <div className="qedl">
            <div className="qrow"><div className="qk">Sobre qué responde</div><div className="qv"><b>48 fuentes oficiales chilenas.</b> Legislación vigente (BCN / LeyChile, Diario Oficial, Historia de la Ley), 3,3M sentencias judiciales de todas las competencias, 290k+ dictámenes y jurisprudencia administrativa (Contraloría, Dirección del Trabajo, SII, CPLT, SUSESO), normativa de reguladores y superintendencias, y registros públicos como el Boletín Concursal. 4,6M documentos en total.</div></div>
            <div className="qrow"><div className="qk">Cómo responde</div><div className="qv"><b>Recuperación aumentada (RAG).</b> Ante cada pregunta busca —híbrido exacto + semántico— las fuentes pertinentes del corpus y construye la respuesta a partir de ellas, citando ley, artículo, rol de causa o número de dictamen. No improvisa desde patrones aprendidos.</div></div>
            <div className="qrow"><div className="qk">Qué garantiza</div><div className="qv"><b>Cita verificable o “no sé”.</b> Toda afirmación es contrastable contra el texto oficial. Solo cita derecho vigente y advierte si una norma fue modificada o derogada. Si la respuesta no está en las fuentes, lo dice en lugar de rellenar con una explicación plausible.</div></div>
            <div className="qrow"><div className="qk">Más allá de citar</div><div className="qv"><b>Analítica del comportamiento real de los tribunales.</b> Sobre el corpus de fallos se extraen montos, materias, resultados y jueces de cada causa — duración por juzgado, proporción del monto que se acoge, materias que prosperan, tendencia de fallo de cada juez y estrategia litigiosa de cada empresa. Datos que una IA general no puede saber porque no los tiene.</div></div>
            <div className="qrow"><div className="qk">Cómo se mantiene</div><div className="qv"><b>Pipelines de ingesta propios.</b> Las fuentes se actualizan de forma incremental y verificada (sin re-descargar el histórico), con cobertura histórica completa donde la fuente lo permite.</div></div>
            <div className="qrow"><div className="qk">Quién lo construye</div><div className="qv"><b>Unholster</b> — tecnología con propósito. Claude como modelo, con un RAG construido a medida sobre el corpus jurídico chileno; no un copiloto genérico de proveedor.</div></div>
          </div>
        </div>
      </section>

      {/* WHY DIFFERENT */}
      <section className="blk" id="confianza">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">Por qué es distinto</span>
            <h2>Un chatbot genérico improvisa. Este recupera y cita.</h2>
            <p>La diferencia con cualquier IA legal general no está en el modelo: está en el corpus y en el método. Construimos y mantenemos actualizada la base documental del derecho chileno, y cada respuesta se arma recuperando primero las fuentes pertinentes.</p>
          </div>
          <div className="cols3">
            <div className="card hov feature">
              <div className="ico-box"><svg className="ic"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div>
              <h3>Corpus real, no memoria</h3>
              <p>Responde recuperando de una base de leyes, fallos y dictámenes chilenos verificables — no de patrones aprendidos que pueden alucinar normas o roles inexistentes.</p>
            </div>
            <div className="card hov feature">
              <div className="ico-box"><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg></div>
              <h3>Citas que existen</h3>
              <p>Toda afirmación viene con su fuente —ley, artículo, rol de causa o número de dictamen— recuperada del corpus. Tú verificas; no tienes que confiar a ciegas.</p>
            </div>
            <div className="card hov feature">
              <div className="ico-box"><svg className="ic"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg></div>
              <h3>Sabe decir “no sé”</h3>
              <p>Si la respuesta no está en las fuentes, lo dice — en lugar de rellenar con una explicación plausible. La honestidad sobre lo que no cubre es parte del diseño.</p>
            </div>
          </div>
        </div>
      </section>

      {/* COMPARATIVA */}
      <section className="blk gray" id="comparativa">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">El antes y el después</span>
            <h2>La misma pregunta, dos respuestas muy distintas.</h2>
            <p>Una IA general responde desde lo que “recuerda”: suena convincente, pero puede inventar una norma, un rol o un dictamen que no existe. Claude Legal Chile recupera del corpus y cita. Mismo ejemplo, lado a lado:</p>
          </div>
          <div className="compare">
            <div className="cc bad">
              <div className="hd"><span className="dot"></span> IA genérica · sin el corpus</div>
              <div className="bd">
                <div className="qa">Plazo para reclamar un despido injustificado en Chile</div>
                <div className="ans">“El plazo es de aproximadamente <span className="hl">30 días</span>. La jurisprudencia reciente, como el fallo de la Corte Suprema <span className="hl">Rol N° 12.345-2022</span>, ha confirmado este criterio…”</div>
                <ul className="feat">
                  <li><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> Responde desde la memoria del modelo</li>
                  <li><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> Cita un rol que <strong>puede no existir</strong></li>
                  <li><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> No distingue derecho chileno vigente</li>
                  <li><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> Si no sabe, igual improvisa</li>
                </ul>
              </div>
            </div>
            <div className="cc good">
              <div className="hd"><span className="dot"></span> Claude Legal Chile · con el corpus</div>
              <div className="bd">
                <div className="qa">Plazo para reclamar un despido injustificado en Chile</div>
                <div className="ans">“El plazo es de <span className="ok">60 días hábiles</span> desde la separación, conforme al <span className="ok">art. 168 del Código del Trabajo</span> (texto vigente recuperado del corpus). Si quieres, te muestro fallos de la Corte Suprema que aplican este plazo y sus matices.”</div>
                <ul className="feat">
                  <li><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> Recupera la norma real del corpus</li>
                  <li><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> Cita verificable contra el texto oficial</li>
                  <li><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> Acota al derecho chileno vigente</li>
                  <li><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> Si no está en el corpus, lo dice</li>
                </ul>
              </div>
            </div>
          </div>
          <div className="ctbl">
            <div className="row head">
              <div className="cell">Consulta</div>
              <div className="cell">IA genérica · sin corpus</div>
              <div className="cell">Claude Legal Chile · con corpus</div>
            </div>
            <div className="row">
              <div className="cell q"><span className="mat">Socio · Libre competencia</span>En una operación de concentración aprobada con condiciones, ¿qué precedentes del TDLC y de la FNE hay sobre cláusulas de no competencia entre las partes?</div>
              <div className="cell bad">Cita una <strong>sentencia del TDLC</strong> y una resolución de la FNE con número y año de apariencia verosímil, sin que puedas comprobar si existen.</div>
              <div className="cell good">Recupera <strong>sentencias del TDLC y resoluciones de la FNE reales</strong>, con su número y carátula, sobre cláusulas de no competencia y remedios conductuales.</div>
            </div>
            <div className="row">
              <div className="cell q"><span className="mat">Asociada · Mercado de capitales</span>¿Qué exige la normativa de la CMF sobre el momento de divulgar un hecho esencial durante la negociación de una OPA?</div>
              <div className="cell bad">Atribuye el deber a una <strong>Norma de Carácter General de la CMF</strong> de número plausible y mezcla disposiciones legales sin precisar la versión vigente.</div>
              <div className="cell good">Trae la <strong>Norma de Carácter General de la CMF</strong> aplicable y la disposición de la Ley 18.045, con texto vigente y verificable.</div>
            </div>
            <div className="row">
              <div className="cell q"><span className="mat">Socio · Tributario corporativo</span>¿Ha fijado el SII criterio sobre la facultad de tasación del art. 64 del Código Tributario en reorganizaciones acogidas a la neutralidad del art. 14?</div>
              <div className="cell bad">Atribuye el criterio a un <strong>oficio del SII</strong> con número de apariencia real que puede no corresponder a ninguno existente.</div>
              <div className="cell good">Recupera los <strong>oficios y circulares del SII</strong> efectivamente aplicables, con número y año verificables, del corpus tributario.</div>
            </div>
            <div className="row">
              <div className="cell q"><span className="mat">Abogado senior · Insolvencia</span>Para una persona deudora con un único acreedor relevante, ¿qué vía de la Ley 20.720 conviene y cómo se tramita?</div>
              <div className="cell bad">Responde con generalidades sobre la Ley 20.720 y no distingue las modificaciones vigentes ni los plazos exactos.</div>
              <div className="cell good">Cita la <strong>norma vigente de la Ley 20.720</strong> y cruza con datos reales del <strong>Boletín Concursal</strong> sobre tramitación de casos análogos.</div>
            </div>
            <div className="row">
              <div className="cell q"><span className="mat">Abogada · Protección del consumidor</span>¿Qué criterio han fijado el SERNAC y los tribunales sobre intereses y gastos de cobranza extrajudicial abusivos bajo la Ley 19.496?</div>
              <div className="cell bad">Describe un criterio plausible y le atribuye dictámenes o fallos con <strong>números y roles inventados</strong>.</div>
              <div className="cell good">Recupera <strong>pronunciamientos reales del SERNAC y fallos</strong> sobre la Ley 19.496, con su identificación verificable.</div>
            </div>
            <div className="row">
              <div className="cell q"><span className="mat">Abogado · Cobranza · Due diligence</span>¿El RUT de la contraparte registra procedimientos concursales o avisos de remate vigentes?</div>
              <div className="cell bad">No tiene acceso al dato: supone que no hay procedimiento o pide “revisar el Boletín manualmente”.</div>
              <div className="cell good">Consulta el <strong>Boletín Concursal por RUT</strong> y devuelve rol, tribunal, tipo de procedimiento y la línea de tiempo de publicaciones.</div>
            </div>
            <div className="row">
              <div className="cell q"><span className="mat">Socio · Litigios · jurisprudencia</span>¿Cómo ha resuelto la Corte Suprema el daño moral en responsabilidad contractual en la última década?</div>
              <div className="cell bad">Generaliza “la jurisprudencia mayoritaria…” sin roles, o cita fallos con <strong>roles y fechas inventados</strong>.</div>
              <div className="cell good">Entrega <strong>fallos reales de la Corte Suprema</strong> con su rol y traza la evolución del criterio en el tiempo.</div>
            </div>
            <div className="row">
              <div className="cell q"><span className="mat">Cualquier área · Verificación</span>El artículo que voy a citar en el escrito, ¿dice realmente lo que creo y está vigente?</div>
              <div className="cell bad">Parafrasea de memoria; puede <strong>cambiar el número de artículo</strong> o citar una versión derogada como vigente.</div>
              <div className="cell good">Verifica el artículo contra el <strong>texto oficial vigente</strong> de la BCN y advierte si fue modificado o derogado.</div>
            </div>
          </div>
          <p style={{ textAlign: 'center', color: 'var(--muted)', fontSize: '12.5px', marginTop: '20px', fontWeight: '300' }}>Los números y citas atribuidos a la columna “sin corpus” son ejemplos ficticios que ilustran el riesgo de alucinación.</p>
        </div>
      </section>

      {/* ANALYTICS */}
      <section className="blk" id="analitica">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">Más allá de citar</span>
            <h2>Lee el comportamiento real de los tribunales.</h2>
            <p>El corpus no sirve solo para citar. Sobre los 3,3M de fallos se pueden extraer —con modelos de lenguaje sobre el texto de cada sentencia— los montos, materias, jueces y resultados de cada causa, y construir analítica del comportamiento real de la justicia.</p>
          </div>
          <div className="agrid">
            <div className="card acard">
              <div className="qq">“¿Cuánto demora realmente una causa laboral según el juzgado donde caiga?”</div>
              <div className="line with"><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> <span><b>Con el corpus:</b> cada fallo trae fecha y tribunal — se mide la duración real por juzgado y se comparan, en vez de suponerla.</span></div>
              <div className="line without"><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> <span><b>Sin corpus:</b> imposible — no tiene los tiempos reales de cada tribunal.</span></div>
            </div>
            <div className="card acard">
              <div className="qq">“¿Qué proporción del monto demandado se suele acoger, y cómo conviene resolver?”</div>
              <div className="line with"><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> <span><b>Con el corpus:</b> extrayendo el monto solicitado y el acogido de cada fallo se obtiene la tasa de aceptación real por vía (sentencia / avenimiento / conciliación) y por materia.</span></div>
              <div className="line without"><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> <span><b>Sin corpus:</b> inventa un porcentaje o responde “depende del caso”.</span></div>
            </div>
            <div className="card acard">
              <div className="qq">“¿Qué materias tienen mayor probabilidad de prosperar?”</div>
              <div className="line with"><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> <span><b>Con el corpus:</b> cruzando la materia y el resultado de cada causa se ordena, con datos, qué materias se acogen más y cuáles menos.</span></div>
              <div className="line without"><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> <span><b>Sin corpus:</b> teoriza sin saber qué materias efectivamente ganan.</span></div>
            </div>
            <div className="card acard">
              <div className="qq">“¿Cómo litiga esta empresa: pelea en tribunal o transa?”</div>
              <div className="line with"><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> <span><b>Con el corpus:</b> identificando a la demandada en cada causa se reconstruye su historial — qué proporción resuelve por sentencia y cuánta por acuerdo.</span></div>
              <div className="line without"><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> <span><b>Sin corpus:</b> no tiene el historial litigioso de esa contraparte.</span></div>
            </div>
            <div className="card acard">
              <div className="qq">“¿Cómo tiende a fallar el juez al que le tocó mi causa?”</div>
              <div className="line with"><svg className="ic"><path d="M20 6 9 17l-5-5"/></svg> <span><b>Con el corpus:</b> sobre las sentencias públicas de cada juez se construye su ficha —materias, duración, tipo de resolución y montos— es decir, su tendencia histórica.</span></div>
              <div className="line without"><svg className="ic"><path d="M18 6 6 18M6 6l12 12"/></svg> <span><b>Sin corpus:</b> no conoce el historial de ese juez ni de su juzgado.</span></div>
            </div>
          </div>
          <p className="afoot">Es leer el comportamiento real de la justicia chilena a partir de los fallos — no buscar una cita. La capa de extracción profunda se está corriendo sobre el corpus; las cifras se publican cuando están medidas y validadas.</p>
          <div style={{ textAlign: 'center', marginTop: '8px' }}><a className="btn btn-primary" href="/analisis">Ver el análisis del corpus completo <svg className="ic"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></div>
        </div>
      </section>

      {/* CORPUS */}
      <section className="blk gray" id="corpus">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">El corpus</span>
            <h2>El derecho chileno, reunido en un solo lugar.</h2>
            <p>48 fuentes oficiales: legislación, jurisprudencia judicial y administrativa, normativa regulatoria y registros públicos. Desde la Corte Suprema hasta la última circular del SII.</p>
          </div>
          <div className="cols3">
            <div className="card hov csrc">
              <div className="top"><div className="ico-box"><svg className="ic"><path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7M3 7l9-4 9 4M3 7l9 4 9-4"/></svg></div><h3>Legislación</h3></div>
              <div className="num">175k+ normas</div>
              <ul>
                <li>· Leyes, decretos y resoluciones (BCN / LeyChile)</li>
                <li>· Diario Oficial</li>
                <li>· Historia de la Ley — la tramitación y la intención detrás de cada norma</li>
              </ul>
            </div>
            <div className="card hov csrc">
              <div className="top"><div className="ico-box"><svg className="ic"><path d="M3 21h18M5 21V7l8-4 8 4v14M9 9h.01M9 13h.01M9 17h.01M15 9h.01M15 13h.01M15 17h.01"/></svg></div><h3>Jurisprudencia judicial</h3></div>
              <div className="num">3,3M sentencias</div>
              <ul>
                <li>· Corte Suprema y Cortes de Apelaciones</li>
                <li>· Civiles, Penales, Laborales, Familia, Cobranza</li>
                <li>· Tribunal Constitucional, libre competencia (TDLC), ambientales, tributario-aduanero, propiedad industrial, arbitral</li>
              </ul>
            </div>
            <div className="card hov csrc">
              <div className="top"><div className="ico-box"><svg className="ic"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M9 13h6M9 17h6"/></svg></div><h3>Dictámenes y jurisprud. administrativa</h3></div>
              <div className="num">290k+ dictámenes</div>
              <ul>
                <li>· Contraloría General de la República</li>
                <li>· Dirección del Trabajo · SII (oficios y circulares)</li>
                <li>· Consejo para la Transparencia · SUSESO</li>
              </ul>
            </div>
            <div className="card hov csrc">
              <div className="top"><div className="ico-box"><svg className="ic"><path d="M3 3v18h18"/><path d="M18 17V9M13 17V5M8 17v-3"/></svg></div><h3>Reguladores y superintendencias</h3></div>
              <div className="num">20+ organismos</div>
              <ul>
                <li>· CMF, SEC, SAG, DGA, SISS, Pensiones, Salud</li>
                <li>· UAF, SERNAC, SERVEL, Aduanas, FNE</li>
                <li>· Defensoría Penal Pública, INDH</li>
              </ul>
            </div>
            <div className="card hov csrc">
              <div className="top"><div className="ico-box"><svg className="ic"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M8 4v16"/></svg></div><h3>Registros públicos</h3></div>
              <div className="num">747k publicaciones</div>
              <ul>
                <li>· Boletín Concursal (Ley 20.720): liquidaciones y reorganizaciones por RUT, rol o deudor</li>
              </ul>
            </div>
            <div className="card hov csrc">
              <div className="top"><div className="ico-box"><svg className="ic"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg></div><h3>Actualización viva</h3></div>
              <div className="num">continua</div>
              <ul>
                <li>· Las fuentes se mantienen al día con pipelines de ingesta propios</li>
                <li>· Cobertura histórica completa donde la fuente lo permite</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* PIPELINE */}
      <section className="blk" id="pipeline">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">El recorrido de la data</span>
            <h2>De la fuente oficial a la respuesta con cita.</h2>
            <p>Detrás de cada respuesta hay un pipeline completo: reunir las fuentes, normalizarlas, indexarlas, vectorizarlas y recuperarlas. Esto es lo que construimos con la data.</p>
          </div>
          <div className="flow">
            <div className="step">
              <div className="si"><svg className="ic"><path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7M3 7l9-4 9 4M3 7l9 4 9-4"/></svg></div>
              <div className="bod"><div className="sn">01</div><h3>Fuentes oficiales</h3><p>Tribunales, BCN, Contraloría, superintendencias, registros.<span className="big">48 fuentes</span></p></div>
            </div>
            <div className="step">
              <div className="si"><svg className="ic"><path d="M21 12a9 9 0 1 1-6.2-8.5"/><path d="M21 3v6h-6"/></svg></div>
              <div className="bod"><div className="sn">02</div><h3>Ingesta</h3><p>Scrapers y pipelines propios — APIs, buscadores, boletines — con verificación dato a dato.<span className="big">histórico completo</span></p></div>
            </div>
            <div className="step">
              <div className="si"><svg className="ic"><path d="M4 7V4h16v3M9 20h6M12 4v16"/></svg></div>
              <div className="bod"><div className="sn">03</div><h3>Corpus normalizado</h3><p>Texto limpio y estructurado, con metadatos (rol, fecha, organismo, materia).<span className="big">4,6M documentos</span></p></div>
            </div>
            <div className="step">
              <div className="si"><svg className="ic"><path d="M21 21l-4.3-4.3M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z"/></svg></div>
              <div className="bod"><div className="sn">04</div><h3>Índice full-text</h3><p>Búsqueda exacta por número, RUT, rol, artículo o palabra clave.<span className="big">consulta instantánea</span></p></div>
            </div>
            <div className="step">
              <div className="si"><svg className="ic"><path d="M12 2v20M2 12h20M5 5l14 14M19 5 5 19"/></svg></div>
              <div className="bod"><div className="sn">05</div><h3>Embeddings</h3><p>Vectorización semántica para encontrar por significado, no solo por palabra.<span className="big">3,8M vectores</span></p></div>
            </div>
            <div className="step">
              <div className="si"><svg className="ic"><path d="M14 9V5a3 3 0 0 0-6 0v4M5 9h14l1 12H4z"/></svg></div>
              <div className="bod"><div className="sn">06</div><h3>Recuperación (RAG)</h3><p>Ante cada pregunta, recupera las fuentes pertinentes — híbrido exacto + semántico.<span className="big">cita verificable</span></p></div>
            </div>
            <div className="step">
              <div className="si"><svg className="ic"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M9 10h.01M13 10h.01"/></svg></div>
              <div className="bod"><div className="sn">07</div><h3>Respuesta citada</h3><p>El asistente responde solo con lo recuperado, citando la fuente — o dice que no está.<span className="big">cero invención</span></p></div>
            </div>
          </div>
        </div>
      </section>

      {/* CAPACIDADES / SKILLS */}
      <section className="blk gray" id="capacidades">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">Capacidades</span>
            <h2>Qué puedes pedirle.</h2>
            <p>Habilidades especializadas sobre el corpus. Todas citan la fuente; ninguna inventa.</p>
          </div>
          <div>
            <div className="skill">
              <div className="name">verificar-cita<span className="badge badge-primary">Validación</span></div>
              <div className="desc"><p>Confirma si una ley, artículo o sentencia que vas a citar existe y dice lo que crees — contra el texto oficial, no la memoria del modelo.</p>
                <div className="ex">“¿El art. 1545 del Código Civil consagra la ley del contrato?”</div></div>
            </div>
            <div className="skill">
              <div className="name">buscar-jurisprudencia<span className="badge badge-primary">Fallos</span></div>
              <div className="desc"><p>Encuentra sentencias de los tribunales chilenos por materia, partes o criterio, sobre 3,3 millones de fallos reales.</p>
                <div className="ex">“Fallos de la Corte Suprema sobre término de contrato por necesidades de la empresa.”</div></div>
            </div>
            <div className="skill">
              <div className="name">buscar-dictamen<span className="badge badge-primary">Jurisprud. adm.</span></div>
              <div className="desc"><p>Recupera dictámenes de la Contraloría y jurisprudencia administrativa (SII, Dirección del Trabajo, CPLT) sobre un tema.</p>
                <div className="ex">“Dictámenes de Contraloría sobre feriado legal de funcionarios a contrata.”</div></div>
            </div>
            <div className="skill">
              <div className="name">linea-jurisprudencial<span className="badge badge-primary">Análisis</span></div>
              <div className="desc"><p>Traza cómo evolucionó el criterio de los tribunales sobre un asunto a lo largo del tiempo, con los fallos clave.</p>
                <div className="ex">“Línea jurisprudencial sobre daño moral en responsabilidad contractual.”</div></div>
            </div>
            <div className="skill">
              <div className="name">consulta-concursal<span className="badge badge-primary">Due diligence</span></div>
              <div className="desc"><p>¿Una persona o empresa tiene un procedimiento concursal? Lookup por RUT, razón social o rol sobre el Registro del Boletín Concursal, con la línea de tiempo de publicaciones.</p>
                <div className="ex">“¿El RUT de esta empresa tiene procedimientos de liquidación vigentes?”</div></div>
            </div>
            <div className="skill">
              <div className="name">red-flags-contrato<span className="badge badge-primary">Revisión</span></div>
              <div className="desc"><p>Revisa un contrato y marca cláusulas riesgosas, vacíos y puntos a negociar, con fundamento en la normativa vigente recuperada.</p>
                <div className="ex">“Revisa este contrato de arriendo comercial y dime qué cláusulas son riesgosas.”</div></div>
            </div>
          </div>
        </div>
      </section>

      {/* AUDIENCE */}
      <section className="blk">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">Para quién</span>
            <h2>Pensado para el ejercicio profesional.</h2>
          </div>
          <div className="cols3">
            <div className="card hov feature">
              <div className="ico-box"><svg className="ic"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>
              <h3>Abogados y abogadas</h3>
              <p>Investiga una consulta, prepara un escrito o revisa un contrato con respaldo en fuentes reales. Como un asociado que siempre cita.</p>
            </div>
            <div className="card hov feature">
              <div className="ico-box"><svg className="ic"><path d="M3 21h18M5 21V7l7-4 7 4v14M10 9h4M10 13h4M10 17h4"/></svg></div>
              <h3>Estudios jurídicos</h3>
              <p>Acelera la investigación del equipo y estandariza la verificación de citas. Implementación a medida sobre el corpus o sobre los documentos del estudio.</p>
            </div>
            <div className="card hov feature">
              <div className="ico-box"><svg className="ic"><path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/></svg></div>
              <h3>Áreas legales y compliance</h3>
              <p>Due diligence de contraparte (concursal, regulatorio), monitoreo normativo y consultas internas con trazabilidad a la fuente.</p>
            </div>
          </div>
        </div>
      </section>

      {/* PARTICIPAR / CTA */}
      <section className="blk gray" id="participar">
        <div className="wrap">
          <div className="ctaband">
            <h2>Buscamos abogados que lo pongan a prueba.</h2>
            <p>Estamos abriendo un grupo inicial de validadores. Úsalo en consultas reales durante unas semanas y dinos, sin filtros, qué funciona y qué no. Tu mirada como profesional en ejercicio es lo que necesitamos para que sea confiable.</p>
            <div className="cta" style={{ justifyContent: 'center' }}>
              <a className="btn btn-primary" href="mailto:antonio@unholster.com?subject=Quiero%20probar%20Claude%20Legal%20Chile"><svg className="ic"><path d="M22 6 12 13 2 6M2 6h20v12H2z"/></svg> Sumarme a probar</a>
              <a className="btn btn-ghost" href="mailto:antonio@unholster.com?subject=Demo%20Claude%20Legal%20Chile">Agendar una demo</a>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

export function Footer() {
  return (
    <footer>
      <div className="wrap cols">
        <div className="f-brand">
          <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
            <b>Claude Legal Chile</b>
          </div>
          <div className="sub">· Derecho chileno real</div>
          <p>Un proyecto de <strong style={{ color: 'var(--ink)', fontWeight: 600 }}>Unholster</strong> · Tecnología con propósito.</p>
        </div>
        <div>
          <div className="f-h">Explorar</div>
          <ul>
            <li><a href="/jueces">Jueces</a></li>
            <li><a href="/tribunales">Tribunales</a></li>
            <li><a href="/buscar">Buscar en el corpus</a></li>
            <li><a href="/analisis">Análisis ↗</a></li>
            <li><a href="/sobre">Sobre el proyecto</a></li>
            <li><a href="/sobre#corpus">El corpus</a></li>
          </ul>
        </div>
        <div>
          <div className="f-h">Contacto</div>
          <ul>
            <li><a href="mailto:antonio@unholster.com">antonio@unholster.com</a></li>
            <li><a href="https://www.unholster.com">www.unholster.com</a></li>
            <li>Monseñor Eyzaguirre 620, Ñuñoa, Santiago</li>
          </ul>
        </div>
      </div>
      <div className="bar">
        <div className="wrap">
          <span>Corpus mantenido al día con pipelines propios</span>
          <span>Claude Legal Chile · Unholster</span>
        </div>
      </div>
      <p className="disc">Claude Legal Chile es una herramienta de apoyo a la investigación jurídica. Sus respuestas son un insumo para el análisis de un abogado habilitado y no constituyen asesoría legal. El usuario es responsable de verificar las fuentes citadas antes de su uso en cualquier actuación.</p>
    </footer>
  )
}
