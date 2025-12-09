export type AnswerType = 'yesno' | 'frequency' | 'stars';

export type Question = {
  id: string;
  label: string;
  helper?: string;
  section?: string; // top-level section (e.g., Diagramacion, Contenido)
  subsection?: string; // grouped subsection under the top-level section
  documentType?: 'Proyecto' | 'Tesis' | 'Both';
  answerType: AnswerType;
};

// Keep explicit per-document-type question lists: PROJECT_QUESTIONS and TESIS_QUESTIONS below.

export const FREQUENCY_OPTIONS = [
  { value: 1, label: 'Muy Poco/Nunca', color: 'bg-red-100 text-red-700 border-red-300' },
  { value: 2, label: 'A veces', color: 'bg-yellow-100 text-yellow-700 border-yellow-300' },
  { value: 3, label: 'Sí/Siempre', color: 'bg-green-100 text-green-700 border-green-300' },
  { value: 4, label: 'No aplica', color: 'bg-gray-100 text-gray-700 border-gray-300' },
];

export const YESNO_OPTIONS = [
  { value: 1, label: 'No', color: 'bg-red-100 text-red-700 border-red-300' },
  { value: 2, label: 'Sí', color: 'bg-green-100 text-green-700 border-green-300' },
];

// Derived per-document-type question sets for convenience
// Explicit per-document-type question lists (manually separated)
export const PROJECT_QUESTIONS: Question[] = [
  // Diagramacion → Portada (Both)
  { id: "q1", label: "Logo Universidad", helper: "Contiene a 3 cm del borde superior y de manera centrada el logo de la universidad en negro o azul (3,5 cm *1,3 cm)", section: "Diagramacion", subsection: "Portada", documentType: 'Both', answerType: 'yesno' },
  { id: "q2", label: "Nombre de la Universidad", helper: "Inmediatamente debajo del Logo de la universidad, y separados por 0,5 cm; se encuentra el nombre de la misma en letra Arial tamaño", section: "Diagramacion", subsection: "Portada", documentType: 'Both', answerType: 'yesno' },
  { id: "q3", label: "Nombre de la Facultad", helper: "Inmediatamente debajo del nombre de la universidad, y separados por 0,5 cm; se encuentra el nombre de la Facultad en letra Arial tamaño", section: "Diagramacion", subsection: "Portada", documentType: 'Both', answerType: 'yesno' },
  { id: "q4", label: "Título de la investigación", helper: "El título de la investigación está mayúscula y negrillas, centrado horizontal y verticalmente, con interlineado sencillo y en letra Verdana Tamaño 14", section: "Diagramacion", subsection: "Portada", documentType: 'Both', answerType: 'yesno' },
  { id: "q5", label: "Subtítulo de la investigación", helper: "En caso de existir subtítulo de la investigación, el mismo está mayúscula y negrillas, centrado horizontal y verticalmente, con interlineado sencillo, separado del título por espacio y medio; y en letra Verdana Tamaño 12", section: "Diagramacion", subsection: "Portada", documentType: 'Both', answerType: 'yesno' },
  { id: "q6", label: "Nombre del autor", helper: "El nombre del autor o autores y sus cédulas de identidad aparecen alineados a la derecha, en letra Verdana tamaño 12, e interlineado sencillo; precedido por la palabra Autor o Autores en negrillas, separada del primer autor por espacio y medio", section: "Diagramacion", subsection: "Portada", documentType: 'Both', answerType: 'yesno' },
  { id: "q7", label: "Ciudad y fecha", helper: "Aproximadamente a 3 cm del borde inferior de la hoja se encuentra la ciudad donde se realizó el trabajo, el mes y el año, centrados y en Verdana tamaño 12", section: "Diagramacion", subsection: "Portada", documentType: 'Both', answerType: 'yesno' },

  // Diagramacion → Página de Presentación (Both)
  { id: "q8", label: "Logo Universidad", helper: "Contiene a 3 cm del borde superior y de manera centrada el logo de la universidad en negro o azul (3,5 cm *1,3 cm)", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q9", label: "Nombre de la Universidad", helper: "Inmediatamente debajo del Logo de la universidad, y separados por 0,5 cm; se encuentra el nombre de la misma en letra Arial tamaño", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q10", label: "Nombre de la Facultad", helper: "Inmediatamente debajo del nombre de la universidad, y separados por 0,5 cm; se encuentra el nombre de la Facultad en letra Arial tamaño", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q11", label: "Título de la investigación", helper: "El título de la investigación está mayúscula y negrillas, centrado horizontal y verticalmente, con interlineado sencillo y en letra Verdana Tamaño 14", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q12", label: "Subtítulo de la investigación", helper: "En caso de existir subtítulo de la investigación, el mismo está mayúscula y negrillas, centrado horizontal y verticalmente, con interlineado sencillo, separado del título por espacio y medio (aproximadamente 0,8 cm); y en letra Verdana Tamaño 12", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q13", label: "Línea de Investigación", helper: "Inmediatamente debajo del Título (o subtítulo) y separada del mismo por espacio y medio (aproximadamente 0,8 cm) se indica la Línea de Investigación Rectora y Potencial, en Verdana tamaño 12, con sus primeras letras en mayúsculas, centrado, en Verdana tamaño 12", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q14", label: "Nombre del autor (derecha)", helper: "El nombre del autor o autores y sus cédulas de identidad aparecen alineados a la derecha, en letra Verdana tamaño 12, e interlineado sencillo; precedido por la palabra Autor o Autores en negrillas, separada del primer autor por espacio y medio", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q15", label: "Nombre del tutor (izquierda)", helper: "El nombre del tutor o tutores y sus cédulas de identidad aparecen alineados a la izquierda, en letra Verdana tamaño 12, e interlineado sencillo; precedido por la palabra Tutor o Tutores en negrillas, separada del primer tutor por espacio y medio", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q16", label: "Ciudad y fecha", helper: "Aproximadamente a 3 cm del borde inferior de la hoja se encuentra la ciudad donde se realizó el trabajo, el mes y el año, centrados y en Verdana tamaño 12", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },
  { id: "q17", label: "Carta de aprobación del tutor", helper: "El trabajo contiene la carta de aprobación del tutor", section: "Diagramacion", subsection: "Página de Presentación", documentType: 'Both', answerType: 'yesno' },

  // Diagramacion → Capítulo 1. Introducción (Both)
  { id: "q18", label: "Extensión máxima", helper: "Tiene una extensión máxima de 10 páginas", section: "Diagramacion", subsection: "Capítulo 1: Introducción", documentType: 'Both', answerType: 'yesno' },
  { id: "q19", label: "Título del capítulo", helper: "El título: CAPÍTULO 1. INTRODUCCIÓN se encuentra al borde del margen izquierdo de la hoja; en negrillas; mayúsculas y en Verdana 14", section: "Diagramacion", subsection: "Capítulo 1: Introducción", documentType: 'Both', answerType: 'yesno' },
  { id: "q20", label: "Subtítulos del capítulo", helper: "Los subtítulos: 1.1. Planteamiento del problema; 1.2 Justificación e impacto de la Investigación; 1.3 Interrogantes de la Investigación; 1.4 Objetivos de la Investigación; 1.4.1. Objetivo General; y 1.4.2. Objetivos específicos; se encuentran al borde del margen izquierdo de la hoja; en negrillas; en mayúscula la primera letra de la primera palabra y la primera letra de cada palabra principal; y en Verdana 12", section: "Diagramacion", subsection: "Capítulo 1: Introducción", documentType: 'Both', answerType: 'yesno' },

  // Diagramacion → Formato General (Both)
  { id: "q21", label: "Márgenes de página", helper: "En todas las páginas, el margen izquierdo es de cuatro (4) centímetros; mientras que el margen inferior, el margen superior y el margen derecho deben ser de tres (3) centímetros desde el borde de la hoja", section: "Diagramacion", subsection: "Formato General", documentType: 'Both', answerType: 'yesno' },
  { id: "q22", label: "Interlineado en párrafos", helper: "En todos los párrafos del cuerpo del documento el interlineado es de espacio y medio (1,5 líneas) agregando una separación de media línea (6 puntos) entre párrafo y párrafo; entre título y subtítulo; entre dos subtítulos y entre el párrafo las tablas o cuadros", section: "Diagramacion", subsection: "Formato General", documentType: 'Both', answerType: 'yesno' },
  { id: "q23", label: "Sangría en párrafos", helper: "En cada inicio de párrafo del cuerpo del documento hay una sangría de cinco (5) caracteres, lo que equivale a un (1) centímetro", section: "Diagramacion", subsection: "Formato General", documentType: 'Both', answerType: 'yesno' },
  { id: "q24", label: "Referencias en superíndice", helper: "En todos los párrafos del cuerpo del documento las referencias se indican mediante números arábigos en superíndice al final de cada oración o idea que requiere una cita bibliográfica", section: "Diagramacion", subsection: "Formato General", documentType: 'Both', answerType: 'yesno' },
  { id: "q25", label: "Reglas ortográficas", helper: "En todos los párrafos del cuerpo del documento se cumple con cada una de las reglas ortográficas", section: "Diagramacion", subsection: "Formato General", documentType: 'Both', answerType: 'yesno' },
  { id: "q26", label: "Redacción y coherencia", helper: "En todos los párrafos del cuerpo del documento la redacción presenta un lenguaje coherente, claro, técnicamente adecuado y organizado, y hay transiciones claras entre los párrafos y las secciones del texto", section: "Diagramacion", subsection: "Formato General", documentType: 'Both', answerType: 'yesno' },

  // Diagramacion → Referencias Bibliográficas (Both)
  { id: "q27", label: "Secuencia numérica", helper: "La lista de referencias siempre respeta la secuencia numérica en la que se presentan en el texto", section: "Diagramacion", subsection: "Referencias Bibliográficas", documentType: 'Both', answerType: 'yesno' },
  { id: "q28", label: "Formato APA", helper: "En la lista de referencias siempre se especifica la información en formato APA", section: "Diagramacion", subsection: "Referencias Bibliográficas", documentType: 'Both', answerType: 'yesno' },

  // Contenido → Título (Proyecto)
  { id: "q29", label: "Título - Claridad y concisión", helper: "Describe el contenido del trabajo de manera clara, concisa, y no excede de quince (15) palabras.", section: "Contenido", subsection: "Título", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q30", label: "Título - Precisión de variables/categorías", helper: "Contiene los términos precisos de las variables (para estudios cuantitativos) o categorías (para estudios cualitativos) esenciales.", section: "Contenido", subsection: "Título", documentType: 'Proyecto', answerType: 'frequency' },

  // Contenido → Subtítulo (Project)
  { id: "q31", label: "Subtítulo - Complemento del título", helper: "Complementa el título proporcionando información adicional para precisar el alcance o enfoque de la investigación.", section: "Contenido", subsection: "Subtítulo", documentType: 'Proyecto', answerType: 'frequency' },

  // Contenido → Capítulo 1. Introducción → 1.1 Planteamiento del Problema (Project)
  { id: "q32", label: "Planteamiento - General a particular", helper: "El planteamiento se realiza desde lo general a lo particular, basándose en referentes teóricos y empíricos.", section: "Contenido", subsection: "1.1 Planteamiento del problema", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q33", label: "Planteamiento - Delimitación y precisión", helper: "El planteamiento delimita, define y explica con claridad y precisión el problema.", section: "Contenido", subsection: "1.1 Planteamiento del problema", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q34", label: "Planteamiento - Causas y hechos", helper: "En el planteamiento se identifican y describen las causas y/o hechos que originan el problema.", section: "Contenido", subsection: "1.1 Planteamiento del problema", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q35", label: "Planteamiento - Elementos relacionados", helper: "En el planteamiento se relacionan, describen y explican los elementos que han generado el problema y que están interviniendo en el mismo.", section: "Contenido", subsection: "1.1 Planteamiento del problema", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q36", label: "Planteamiento - Efectos/impactos no deseados", helper: "En el planteamiento se mencionan los efectos y/o impactos no deseados del problema.", section: "Contenido", subsection: "1.1 Planteamiento del problema", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q37", label: "Planteamiento - Proyecciones/pronósticos", helper: "En el planteamiento se incluyen proyecciones o pronósticos de las variables involucradas en la situación problemática.", section: "Contenido", subsection: "1.1 Planteamiento del problema", documentType: 'Proyecto', answerType: 'frequency' },

  // Contenido → Capítulo 1. Introducción → 1.2 Justificación e impacto (Project)
  { id: "q38", label: "Justificación - Razones y utilidad", helper: "Se explican las razones por las cuales es importante y útil llevar a cabo la investigación, argumentando sobre el contexto actual, y el beneficio que aporta el estudio al campo de conocimiento y a la sociedad.", section: "Contenido", subsection: "1.2 Justificación e impacto", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q39", label: "Justificación - Consecuencias y aportes", helper: "Se analizan las consecuencias y los cambios que podrían derivarse de los resultados de la investigación. Se evalúa el alcance del estudio a nivel científico, social, económico o cultural, considerando los posibles aportes de la investigación en cada una de esas áreas.", section: "Contenido", subsection: "1.2 Justificación e impacto", documentType: 'Proyecto', answerType: 'frequency' },

  // Contenido → Capítulo 1. Introducción → 1.3 Interrogantes (Project)
  { id: "q40", label: "Interrogantes - Cinco o más", helper: "Son de tres a cinco.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q41", label: "Interrogantes - Factibles, interesantes, éticas, relevantes", helper: "Son factibles, interesantes, novedosas, éticas y relevantes.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q42", label: "Interrogantes - Lógica del problema", helper: "Son parte de la lógica del problema.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q43", label: "Interrogantes - Claridad y concisión", helper: "Son claras y concisas.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q44", label: "Interrogantes - Límites temporales y espaciales", helper: "Establecen los límites temporales y espaciales del estudio.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q45", label: "Interrogantes - Respuestas dicotómicas", helper: "Conducen a respuestas dicotómicas (sí/no).", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", documentType: 'Proyecto', answerType: 'frequency' },

  // Contenido → Objetivos (Project)
  { id: "q46", label: "Objetivo General - Único", helper: "Es único.", section: "Contenido", subsection: "1.4.1 Objetivo General", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q47", label: "Objetivo General - Logro general", helper: "Establece a modo general lo que se pretende lograr con la realización de la investigación.", section: "Contenido", subsection: "1.4.1 Objetivo General", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q48", label: "Objetivo General - Nivel de aplicación", helper: "Pertenece al menos al nivel de aplicación (cuarto nivel) de la taxonomía de Bloom.", section: "Contenido", subsection: "1.4.1 Objetivo General", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q49", label: "Objetivos Específicos - Consistencia", helper: "Son consistentes con el objetivo general.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q50", label: "Objetivos Específicos - Correspondencia", helper: "Por cada interrogante de la investigación, existe un objetivo específico.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q51", label: "Objetivos Específicos - Logros parciales", helper: "Establecen los logros parciales que facilitan el control sistemático de la investigación.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q52", label: "Objetivos Específicos - Orden", helper: "Están enumerados en orden de importancia, orden lógico y/o orden temporal.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q53", label: "Objetivos Específicos - Medibles y observables", helper: "Son medibles y observables.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q54", label: "Objetivos Específicos - Niveles inferiores", helper: "Tener niveles inferiores al nivel de la taxonomía de Bloom en que se ubica el objetivo general.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", documentType: 'Proyecto', answerType: 'frequency' },

  // Contenido → Referencias bibliográficas (Project)
  { id: "q55", label: "Referencias - Suficiencia y actualidad", helper: "La documentación utilizada como apoyo al estudio es suficiente, actualizada y acreditada.", section: "Contenido", subsection: "Referencias bibliográficas", documentType: 'Proyecto', answerType: 'frequency' },
  { id: "q56", label: "Referencias - Pertinencia", helper: "Se citaron las obras más pertinentes al campo de conocimiento.", section: "Contenido", subsection: "Referencias bibliográficas", documentType: 'Proyecto', answerType: 'frequency' },
];

export const TESIS_STAGE1_QUESTIONS: Question[] = [
  // 3. Diagramación
  { id: "q57", label: "Márgenes", helper: "¿El resumen respeta los márgenes (4cm izquierdo y 3cm superior, inferior y derecho)?", section: "Diagramación", subsection: "Formato", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q58", label: "Formato del Título", helper: "¿Está en mayúscula, negrillas, centrado, interlineado sencillo y letra Verdana 14?", section: "Diagramación", subsection: "Formato", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q59", label: "Formato del Subtítulo", helper: "¿Está en mayúscula, negrillas, centrado, interlineado sencillo, Verdana 12 y separado del título por espacio y medio?", section: "Diagramación", subsection: "Formato", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q60", label: "Leyenda del Título", helper: "¿Aparece debajo del título la leyenda \"Trabajo Especial de Grado presentado como requisito...\" con el formato correcto (centrada, Verdana 12, etc.)?", section: "Diagramación", subsection: "Formato", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q65", label: "Formato de Autores", helper: "¿Están los nombres alineados a la derecha, Verdana 12, precedidos por \"AUTORES:\" en mayúscula y negrita?", section: "Diagramación", subsection: "Formato", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q66", label: "Ciudad y Fecha", helper: "¿Se encuentra la ciudad, mes y año alineados a la derecha y en Verdana 12?", section: "Diagramación", subsection: "Formato", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q67", label: "Título \"RESUMEN\"", helper: "¿Aparece centrado, en mayúsculas, negritas y Verdana 12?", section: "Diagramación", subsection: "Resumen", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q68", label: "Cuerpo del Texto", helper: "¿El párrafo del resumen tiene interlineado sencillo, justificado y letra Verdana 12?", section: "Diagramación", subsection: "Resumen", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q69", label: "Palabras Clave", helper: "¿Hay un máximo de seis términos, ordenados alfabéticamente, justificados y en Verdana 12?", section: "Diagramación", subsection: "Resumen", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q70", label: "Pertinencia de Palabras Clave", helper: "¿Considera que los términos describen adecuadamente los aspectos relevantes de la investigación?", section: "Diagramación", subsection: "Resumen", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q71", label: "Extensión", helper: "¿El texto tiene una extensión igual o inferior a 300 palabras?", section: "Diagramación", subsection: "Resumen", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q72", label: "Redacción", helper: "¿Es fluida, clara, concisa y comprensible?", section: "Diagramación", subsection: "Resumen", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q73", label: "Gramática", helper: "¿Es adecuada (tiempos verbales en pasado, coherencia de género y número)?", section: "Diagramación", subsection: "Resumen", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q74", label: "Ortografía", helper: "¿Se cumplen todas las reglas ortográficas?", section: "Diagramación", subsection: "Resumen", documentType: 'Tesis', answerType: 'yesno' },

  // 4. Contenido, Congruencia y Coherencia
  // A. Título y Subtítulo
  { id: "q75", label: "Título - Claridad y precisión", helper: "¿El título describe el contenido de manera clara y concisa?", section: "Contenido, Congruencia y Coherencia", subsection: "Título y Subtítulo", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q76", label: "Subtítulo - Complemento", helper: "¿El subtítulo complementa al título proporcionando información adicional para precisar el alcance?", section: "Contenido, Congruencia y Coherencia", subsection: "Título y Subtítulo", documentType: 'Tesis', answerType: 'yesno' },

  // B. Planteamiento del Problema
  { id: "q77", label: "Planteamiento - Claridad", helper: "¿Está formulado de manera clara y estructurada?", section: "Contenido, Congruencia y Coherencia", subsection: "Planteamiento del Problema", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q78", label: "Planteamiento - Matriz de evaluación", helper: "¿Está formulado con precisión, claridad y delimita el problema? ¿Es coherente con el planteamiento?", section: "Contenido, Congruencia y Coherencia", subsection: "Planteamiento del Problema", documentType: 'Tesis', answerType: 'yesno' },

  // C. Justificación
  { id: "q79", label: "Justificación", helper: "¿Se expone de manera clara la justificación y/o importancia de la investigación?", section: "Contenido, Congruencia y Coherencia", subsection: "Justificación", documentType: 'Tesis', answerType: 'yesno' },

  // D. Objetivo General
  { id: "q80", label: "Objetivo General - Matriz", helper: "¿Está formulado con precisión, claridad y delimita el problema? ¿Es coherente con el planteamiento?", section: "Contenido, Congruencia y Coherencia", subsection: "Objetivo General", documentType: 'Tesis', answerType: 'yesno' },

  // E. Clasificación de la Investigación (Tipos de Investigación)
  { id: "q81", label: "Clasificación - Propósito", helper: "¿Se especifica el propósito (pura o aplicada) y es congruente con el objetivo?", section: "Contenido, Congruencia y Coherencia", subsection: "Clasificación de la Investigación", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q82", label: "Clasificación - Enfoque/Paradigma", helper: "¿Se indica el enfoque (cualitativa, cuantitativa, mixta, holística o transcompleja) y es adecuado al objetivo?", section: "Contenido, Congruencia y Coherencia", subsection: "Clasificación de la Investigación", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q83", label: "Clasificación - Diseño (Recolección)", helper: "¿Se especifica el diseño (documental, experimental, cuasi-experimental, no experimental) y es adecuado al objetivo?", section: "Contenido, Congruencia y Coherencia", subsection: "Clasificación de la Investigación", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q84", label: "Clasificación - Alcance Temporal", helper: "¿Se indica el alcance temporal (longitudinal o transaccional) y es congruente con el objetivo?", section: "Contenido, Congruencia y Coherencia", subsection: "Clasificación de la Investigación", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q85", label: "Clasificación - Nivel de Análisis", helper: "¿Se especifica el nivel (exploratoria, descriptiva, explicativa, comparativa, predictiva, proyectiva, interactiva, confirmatoria, evaluativa) y es congruente con el objetivo?", section: "Contenido, Congruencia y Coherencia", subsection: "Clasificación de la Investigación", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q86", label: "Clasificación - Proyecto Factible", helper: "Si aplica, ¿se indica proyecto factible según el enfoque?", section: "Contenido, Congruencia y Coherencia", subsection: "Clasificación de la Investigación", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q87", label: "Clasificación - Congruencia", helper: "¿La clasificación es adecuada y congruente con el objetivo?", section: "Contenido, Congruencia y Coherencia", subsection: "Clasificación de la Investigación", documentType: 'Tesis', answerType: 'yesno' },

  // F. Muestra
  { id: "q88", label: "Muestra", helper: "¿En el texto se especifica la muestra empleada?", section: "Contenido, Congruencia y Coherencia", subsection: "Muestra", documentType: 'Tesis', answerType: 'yesno' },

  // G. Técnicas, Métodos y Procedimientos
  { id: "q89", label: "Técnicas y Procedimientos", helper: "¿Su descripción es clara y precisa? ¿Son adecuadas y coherentes con el objetivo general?", section: "Contenido, Congruencia y Coherencia", subsection: "Técnicas, Métodos y Procedimientos", documentType: 'Tesis', answerType: 'yesno' },

  // H. Resultados Principales
  { id: "q90", label: "Resultados - Claridad", helper: "¿Están expresados de manera clara y acompañados de valores cuantitativos (cuando corresponda)?", section: "Contenido, Congruencia y Coherencia", subsection: "Resultados Principales", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q91", label: "Resultados - Significancia", helper: "¿Se expresa la significancia estadística de manera adecuada?", section: "Contenido, Congruencia y Coherencia", subsection: "Resultados Principales", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q92", label: "Resultados - Coherencia", helper: "¿Son coherentes y adecuados con las técnicas empleadas?", section: "Contenido, Congruencia y Coherencia", subsection: "Resultados Principales", documentType: 'Tesis', answerType: 'yesno' },

  // I. Análisis de Resultados y Conclusiones
  { id: "q93", label: "Análisis y Conclusiones - Presentación", helper: "¿Están claramente presentadas?", section: "Contenido, Congruencia y Coherencia", subsection: "Análisis y Conclusiones", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q94", label: "Análisis y Conclusiones - Coherencia con objetivos", helper: "¿Son coherentes y adecuadas con el objetivo general?", section: "Contenido, Congruencia y Coherencia", subsection: "Análisis y Conclusiones", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q95", label: "Análisis y Conclusiones - Coherencia con métodos", helper: "¿Son coherentes con las técnicas y métodos empleados?", section: "Contenido, Congruencia y Coherencia", subsection: "Análisis y Conclusiones", documentType: 'Tesis', answerType: 'yesno' },

  // J. Elementos Gráficos y Matemáticos
  { id: "q96", label: "Figuras/Cuadros", helper: "¿Se citan figuras, cuadros o se hace referencia a ellos dentro del texto?", section: "Contenido, Congruencia y Coherencia", subsection: "Elementos Gráficos y Matemáticos", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q97", label: "Ecuaciones", helper: "¿Las ecuaciones incluidas son imprescindibles, justificadas o innecesarias?", section: "Contenido, Congruencia y Coherencia", subsection: "Elementos Gráficos y Matemáticos", documentType: 'Tesis', answerType: 'yesno' },

  // 5. Consideraciones Finales
  { id: "q98", label: "Aporte", helper: "¿Considera que el tema constituye un aporte valioso al campo del conocimiento? (Use la calificación y complemente en comentarios)", section: "Consideraciones Finales", subsection: "Aporte", documentType: 'Tesis', answerType: 'stars' },
  { id: "q99", label: "Feedback", helper: "Espacio para observaciones, recomendaciones o comentarios para mejorar el documento (use la calificación y agregue detalles en el campo de comentarios).", section: "Consideraciones Finales", subsection: "Feedback", documentType: 'Tesis', answerType: 'stars' },
];

export const TESIS_STAGE2_QUESTIONS: Question[] = [
  // Placeholder for Stage 2 (Content)
  { id: "q61", label: "C.1 - Planteamiento del Problema", helper: "¿El planteamiento del problema es claro, preciso y está bien delimitado?", section: "Contenido", subsection: "Capítulo I", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q62", label: "C.2 - Objetivos", helper: "¿Los objetivos son medibles, alcanzables y coherentes con el problema planteado?", section: "Contenido", subsection: "Capítulo I", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q63", label: "C.3 - Marco Teórico", helper: "¿El marco teórico sustenta adecuadamente la investigación con fuentes actuales y relevantes?", section: "Contenido", subsection: "Capítulo II", documentType: 'Tesis', answerType: 'yesno' },
  { id: "q64", label: "C.4 - Metodología", helper: "¿La metodología descrita es adecuada para alcanzar los objetivos propuestos?", section: "Contenido", subsection: "Capítulo III", documentType: 'Tesis', answerType: 'yesno' },
];

// Alias for backward compatibility (points to Stage 1)
export const TESIS_QUESTIONS = TESIS_STAGE1_QUESTIONS;
