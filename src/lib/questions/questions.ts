export type AnswerType = 'yesno' | 'frequency' | 'stars';

export type Question = {
  id: string;
  label: string;
  helper?: string;
  section?: string; // top-level section (e.g., Diagramacion, Contenido)
  subsection?: string; // grouped subsection under the top-level section
  answerType: AnswerType;
};

export const QUESTIONS: Question[] = [
  // Diagramacion → Portada (7 questions)
  { id: "q1", label: "Logo Universidad", helper: "Contiene a 3 cm del borde superior y de manera centrada el logo de la universidad en negro o azul (3,5 cm *1,3 cm)", section: "Diagramacion", subsection: "Portada", answerType: 'yesno' },
  { id: "q2", label: "Nombre de la Universidad", helper: "Inmediatamente debajo del Logo de la universidad, y separados por 0,5 cm; se encuentra el nombre de la misma en letra Arial tamaño", section: "Diagramacion", subsection: "Portada", answerType: 'yesno' },
  { id: "q3", label: "Nombre de la Facultad", helper: "Inmediatamente debajo del nombre de la universidad, y separados por 0,5 cm; se encuentra el nombre de la Facultad en letra Arial tamaño", section: "Diagramacion", subsection: "Portada", answerType: 'yesno' },
  { id: "q4", label: "Título de la investigación", helper: "El título de la investigación está mayúscula y negrillas, centrado horizontal y verticalmente, con interlineado sencillo y en letra Verdana Tamaño 14", section: "Diagramacion", subsection: "Portada", answerType: 'yesno' },
  { id: "q5", label: "Subtítulo de la investigación", helper: "En caso de existir subtítulo de la investigación, el mismo está mayúscula y negrillas, centrado horizontal y verticalmente, con interlineado sencillo, separado del título por espacio y medio; y en letra Verdana Tamaño 12", section: "Diagramacion", subsection: "Portada", answerType: 'yesno' },
  { id: "q6", label: "Nombre del autor", helper: "El nombre del autor o autores y sus cédulas de identidad aparecen alineados a la derecha, en letra Verdana tamaño 12, e interlineado sencillo; precedido por la palabra Autor o Autores en negrillas, separada del primer autor por espacio y medio", section: "Diagramacion", subsection: "Portada", answerType: 'yesno' },
  { id: "q7", label: "Ciudad y fecha", helper: "Aproximadamente a 3 cm del borde inferior de la hoja se encuentra la ciudad donde se realizó el trabajo, el mes y el año, centrados y en Verdana tamaño 12", section: "Diagramacion", subsection: "Portada", answerType: 'yesno' },

  // Diagramacion → Página de Presentación (10 questions)
  { id: "q8", label: "Logo Universidad", helper: "Contiene a 3 cm del borde superior y de manera centrada el logo de la universidad en negro o azul (3,5 cm *1,3 cm)", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q9", label: "Nombre de la Universidad", helper: "Inmediatamente debajo del Logo de la universidad, y separados por 0,5 cm; se encuentra el nombre de la misma en letra Arial tamaño", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q10", label: "Nombre de la Facultad", helper: "Inmediatamente debajo del nombre de la universidad, y separados por 0,5 cm; se encuentra el nombre de la Facultad en letra Arial tamaño", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q11", label: "Título de la investigación", helper: "El título de la investigación está mayúscula y negrillas, centrado horizontal y verticalmente, con interlineado sencillo y en letra Verdana Tamaño 14", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q12", label: "Subtítulo de la investigación", helper: "En caso de existir subtítulo de la investigación, el mismo está mayúscula y negrillas, centrado horizontal y verticalmente, con interlineado sencillo, separado del título por espacio y medio (aproximadamente 0,8 cm); y en letra Verdana Tamaño 12", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q13", label: "Línea de Investigación", helper: "Inmediatamente debajo del Título (o subtítulo) y separada del mismo por espacio y medio (aproximadamente 0,8 cm) se indica la Línea de Investigación Rectora y Potencial, en Verdana tamaño 12, con sus primeras letras en mayúsculas, centrado, en Verdana tamaño 12", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q14", label: "Nombre del autor (derecha)", helper: "El nombre del autor o autores y sus cédulas de identidad aparecen alineados a la derecha, en letra Verdana tamaño 12, e interlineado sencillo; precedido por la palabra Autor o Autores en negrillas, separada del primer autor por espacio y medio", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q15", label: "Nombre del tutor (izquierda)", helper: "El nombre del tutor o tutores y sus cédulas de identidad aparecen alineados a la izquierda, en letra Verdana tamaño 12, e interlineado sencillo; precedido por la palabra Tutor o Tutores en negrillas, separada del primer tutor por espacio y medio", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q16", label: "Ciudad y fecha", helper: "Aproximadamente a 3 cm del borde inferior de la hoja se encuentra la ciudad donde se realizó el trabajo, el mes y el año, centrados y en Verdana tamaño 12", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },
  { id: "q17", label: "Carta de aprobación del tutor", helper: "El trabajo contiene la carta de aprobación del tutor", section: "Diagramacion", subsection: "Página de Presentación", answerType: 'yesno' },

  // Diagramacion → Capítulo 1. Introducción (3 questions)
  { id: "q18", label: "Extensión máxima", helper: "Tiene una extensión máxima de 10 páginas", section: "Diagramacion", subsection: "Capítulo 1: Introducción", answerType: 'yesno' },
  { id: "q19", label: "Título del capítulo", helper: "El título: CAPÍTULO 1. INTRODUCCIÓN se encuentra al borde del margen izquierdo de la hoja; en negrillas; mayúsculas y en Verdana 14", section: "Diagramacion", subsection: "Capítulo 1: Introducción", answerType: 'yesno' },
  { id: "q20", label: "Subtítulos del capítulo", helper: "Los subtítulos: 1.1. Planteamiento del problema; 1.2 Justificación e impacto de la Investigación; 1.3 Interrogantes de la Investigación; 1.4 Objetivos de la Investigación; 1.4.1. Objetivo General; y 1.4.2. Objetivos específicos; se encuentran al borde del margen izquierdo de la hoja; en negrillas; en mayúscula la primera letra de la primera palabra y la primera letra de cada palabra principal; y en Verdana 12", section: "Diagramacion", subsection: "Capítulo 1: Introducción", answerType: 'yesno' },

  // Diagramacion → Formato General (6 questions)
  { id: "q21", label: "Márgenes de página", helper: "En todas las páginas, el margen izquierdo es de cuatro (4) centímetros; mientras que el margen inferior, el margen superior y el margen derecho deben ser de tres (3) centímetros desde el borde de la hoja", section: "Diagramacion", subsection: "Formato General", answerType: 'yesno' },
  { id: "q22", label: "Interlineado en párrafos", helper: "En todos los párrafos del cuerpo del documento el interlineado es de espacio y medio (1,5 líneas) agregando una separación de media línea (6 puntos) entre párrafo y párrafo; entre título y subtítulo; entre dos subtítulos y entre el párrafo las tablas o cuadros", section: "Diagramacion", subsection: "Formato General", answerType: 'yesno' },
  { id: "q23", label: "Sangría en párrafos", helper: "En cada inicio de párrafo del cuerpo del documento hay una sangría de cinco (5) caracteres, lo que equivale a un (1) centímetro", section: "Diagramacion", subsection: "Formato General", answerType: 'yesno' },
  { id: "q24", label: "Referencias en superíndice", helper: "En todos los párrafos del cuerpo del documento las referencias se indican mediante números arábigos en superíndice al final de cada oración o idea que requiere una cita bibliográfica", section: "Diagramacion", subsection: "Formato General", answerType: 'yesno' },
  { id: "q25", label: "Reglas ortográficas", helper: "En todos los párrafos del cuerpo del documento se cumple con cada una de las reglas ortográficas", section: "Diagramacion", subsection: "Formato General", answerType: 'yesno' },
  { id: "q26", label: "Redacción y coherencia", helper: "En todos los párrafos del cuerpo del documento la redacción presenta un lenguaje coherente, claro, técnicamente adecuado y organizado, y hay transiciones claras entre los párrafos y las secciones del texto", section: "Diagramacion", subsection: "Formato General", answerType: 'yesno' },

  // Diagramacion → Referencias Bibliográficas (2 questions)
  { id: "q27", label: "Secuencia numérica", helper: "La lista de referencias siempre respeta la secuencia numérica en la que se presentan en el texto", section: "Diagramacion", subsection: "Referencias Bibliográficas", answerType: 'yesno' },
  { id: "q28", label: "Formato APA", helper: "En la lista de referencias siempre se especifica la información en formato APA", section: "Diagramacion", subsection: "Referencias Bibliográficas", answerType: 'yesno' },
  

  // Contenido → Título (2 questions)
  { id: "q29", label: "Título - Claridad y concisión", helper: "Describe el contenido del trabajo de manera clara, concisa, y no excede de quince (15) palabras.", section: "Contenido", subsection: "Título", answerType: 'frequency' },
  { id: "q30", label: "Título - Precisión de variables/categorías", helper: "Contiene los términos precisos de las variables (para estudios cuantitativos) o categorías (para estudios cualitativos) esenciales.", section: "Contenido", subsection: "Título", answerType: 'frequency' },

  // Contenido → Subtítulo (1 question)
  { id: "q31", label: "Subtítulo - Complemento del título", helper: "Complementa el título proporcionando información adicional para precisar el alcance o enfoque de la investigación.", section: "Contenido", subsection: "Subtítulo", answerType: 'frequency' },

  // Contenido → Capítulo 1. Introducción → 1.1 Planteamiento del Problema (6 questions)
  { id: "q32", label: "Planteamiento - General a particular", helper: "El planteamiento se realiza desde lo general a lo particular, basándose en referentes teóricos y empíricos.", section: "Contenido", subsection: "1.1 Planteamiento del problema", answerType: 'frequency' },
  { id: "q33", label: "Planteamiento - Delimitación y precisión", helper: "El planteamiento delimita, define y explica con claridad y precisión el problema.", section: "Contenido", subsection: "1.1 Planteamiento del problema", answerType: 'frequency' },
  { id: "q34", label: "Planteamiento - Causas y hechos", helper: "En el planteamiento se identifican y describen las causas y/o hechos que originan el problema.", section: "Contenido", subsection: "1.1 Planteamiento del problema", answerType: 'frequency' },
  { id: "q35", label: "Planteamiento - Elementos relacionados", helper: "En el planteamiento se relacionan, describen y explican los elementos que han generado el problema y que están interviniendo en el mismo.", section: "Contenido", subsection: "1.1 Planteamiento del problema", answerType: 'frequency' },
  { id: "q36", label: "Planteamiento - Efectos/impactos no deseados", helper: "En el planteamiento se mencionan los efectos y/o impactos no deseados del problema.", section: "Contenido", subsection: "1.1 Planteamiento del problema", answerType: 'frequency' },
  { id: "q37", label: "Planteamiento - Proyecciones/pronósticos", helper: "En el planteamiento se incluyen proyecciones o pronósticos de las variables involucradas en la situación problemática.", section: "Contenido", subsection: "1.1 Planteamiento del problema", answerType: 'frequency' },

  // Contenido → Capítulo 1. Introducción → 1.2 Justificación e impacto (2 questions)
  { id: "q38", label: "Justificación - Razones y utilidad", helper: "Se explican las razones por las cuales es importante y útil llevar a cabo la investigación, argumentando sobre el contexto actual, y el beneficio que aporta el estudio al campo de conocimiento y a la sociedad.", section: "Contenido", subsection: "1.2 Justificación e impacto", answerType: 'frequency' },
  { id: "q39", label: "Justificación - Consecuencias y aportes", helper: "Se analizan las consecuencias y los cambios que podrían derivarse de los resultados de la investigación. Se evalúa el alcance del estudio a nivel científico, social, económico o cultural, considerando los posibles aportes de la investigación en cada una de esas áreas.", section: "Contenido", subsection: "1.2 Justificación e impacto", answerType: 'frequency' },

  // Contenido → Capítulo 1. Introducción → 1.3 Interrogantes de la Investigación (6 questions)
  { id: "q40", label: "Interrogantes - Cinco o más", helper: "Son de tres a cinco.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", answerType: 'frequency' },
  { id: "q41", label: "Interrogantes - Factibles, interesantes, éticas, relevantes", helper: "Son factibles, interesantes, novedosas, éticas y relevantes.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", answerType: 'frequency' },
  { id: "q42", label: "Interrogantes - Lógica del problema", helper: "Son parte de la lógica del problema.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", answerType: 'frequency' },
  { id: "q43", label: "Interrogantes - Claridad y concisión", helper: "Son claras y concisas.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", answerType: 'frequency' },
  { id: "q44", label: "Interrogantes - Límites temporales y espaciales", helper: "Establecen los límites temporales y espaciales del estudio.", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", answerType: 'frequency' },
  { id: "q45", label: "Interrogantes - Respuestas dicotómicas", helper: "Conducen a respuestas dicotómicas (sí/no).", section: "Contenido", subsection: "1.3 Interrogantes de la investigación", answerType: 'frequency' },

  // Contenido → Capítulo 1. Introducción → 1.4.1 Objetivo General (3 questions)
  { id: "q46", label: "Objetivo General - Único", helper: "Es único.", section: "Contenido", subsection: "1.4.1 Objetivo General", answerType: 'frequency' },
  { id: "q47", label: "Objetivo General - Logro general", helper: "Establece a modo general lo que se pretende lograr con la realización de la investigación.", section: "Contenido", subsection: "1.4.1 Objetivo General", answerType: 'frequency' },
  { id: "q48", label: "Objetivo General - Nivel de aplicación", helper: "Pertenece al menos al nivel de aplicación (cuarto nivel) de la taxonomía de Bloom.", section: "Contenido", subsection: "1.4.1 Objetivo General", answerType: 'frequency' },

  // Contenido → Capítulo 1. Introducción → 1.4.2 Objetivos Específicos (6 questions)
  { id: "q49", label: "Objetivos Específicos - Consistencia", helper: "Son consistentes con el objetivo general.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", answerType: 'frequency' },
  { id: "q50", label: "Objetivos Específicos - Correspondencia", helper: "Por cada interrogante de la investigación, existe un objetivo específico.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", answerType: 'frequency' },
  { id: "q51", label: "Objetivos Específicos - Logros parciales", helper: "Establecen los logros parciales que facilitan el control sistemático de la investigación.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", answerType: 'frequency' },
  { id: "q52", label: "Objetivos Específicos - Orden", helper: "Están enumerados en orden de importancia, orden lógico y/o orden temporal.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", answerType: 'frequency' },
  { id: "q53", label: "Objetivos Específicos - Medibles y observables", helper: "Son medibles y observables.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", answerType: 'frequency' },
  { id: "q54", label: "Objetivos Específicos - Niveles inferiores", helper: "Tener niveles inferiores al nivel de la taxonomía de Bloom en que se ubica el objetivo general.", section: "Contenido", subsection: "1.4.2 Objetivos Específicos", answerType: 'frequency' },

  // Contenido → Referencias bibliográficas (2 questions)
  { id: "q55", label: "Referencias - Suficiencia y actualidad", helper: "La documentación utilizada como apoyo al estudio es suficiente, actualizada y acreditada.", section: "Contenido", subsection: "Referencias bibliográficas", answerType: 'frequency' },
  { id: "q56", label: "Referencias - Pertinencia", helper: "Se citaron las obras más pertinentes al campo de conocimiento.", section: "Contenido", subsection: "Referencias bibliográficas", answerType: 'frequency' },
];

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
