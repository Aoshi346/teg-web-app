
import { 
  Question, 
  DIAGRAMACION_SCORES, 
  CONTENIDO_SCORES,
  TESIS_DIAGRAMACION_SCORES,
  TESIS_CONTENIDO_SCORES 
} from './questions';

export const MAX_SCORE = 20;
export const PASSING_SCORE = 14;

export type PassStatus = 'Pass' | 'Fail';

/**
 * Get the exact point value for a question based on document type, section and answer
 */
export function getPointValue(
  question: Question,
  answerValue: number
): number {
  const section = question.section?.toLowerCase() || '';
  const isDiagramacion = section.includes('diagramacion') || section.includes('diagramación');
  const isTesis = question.documentType === 'Tesis';
  
  // Select the appropriate score table based on document type and section
  let scores;
  if (isTesis) {
    scores = isDiagramacion ? TESIS_DIAGRAMACION_SCORES : TESIS_CONTENIDO_SCORES;
  } else {
    scores = isDiagramacion ? DIAGRAMACION_SCORES : CONTENIDO_SCORES;
  }

  switch (question.answerType) {
    case 'yesno':
      // 1=No, 2=Sí
      return answerValue === 2 ? scores.yesno.yes : scores.yesno.no;

    case 'ternary':
      // 1=No, 2=Medianamente, 3=Sí
      if ('ternary' in scores) {
        switch (answerValue) {
          case 3: return scores.ternary.yes;
          case 2: return scores.ternary.medianamente;
          default: return scores.ternary.no;
        }
      }
      return 0;

    case 'ternary_na':
      // 1=No, 2=Medianamente, 3=Sí, 4=No se incluyó, 5=No hay subtítulo (q76)
      if ('ternary_na' in scores) {
        const ternaryNaScores = (scores as typeof TESIS_CONTENIDO_SCORES).ternary_na;
        switch (answerValue) {
          case 3: return ternaryNaScores.yes;
          case 2: return ternaryNaScores.medianamente;
          case 4: return ternaryNaScores.noseincluyo;
          case 5: return ternaryNaScores.noaplica;
          default: return ternaryNaScores.no;
        }
      }
      return 0;

    case 'ternary_info':
      // 1=No, 2=Medianamente, 3=Sí, 4=No se incluyó
      if ('ternary_info' in scores) {
        const ternaryInfoScores = (scores as typeof TESIS_CONTENIDO_SCORES).ternary_info;
        switch (answerValue) {
          case 3: return ternaryInfoScores.yes;
          case 2: return ternaryInfoScores.medianamente;
          case 4: return ternaryInfoScores.noseincluyo;
          default: return ternaryInfoScores.no;
        }
      }
      return 0;

    case 'frequency':
      // 1=Nunca, 2=A veces, 3=Siempre, 4=No aplica
      if ('frequency' in scores) {
        switch (answerValue) {
          case 3: return scores.frequency.siempre;
          case 2: return scores.frequency.aveces;
          case 4: return scores.frequency.noaplica;
          default: return scores.frequency.nunca;
        }
      }
      return 0;

    case 'ternary_defense':
      // 1=Deficiente, 2=Satisfactorio, 3=Excelente — section-independent
      switch (answerValue) {
        case 3: return 1.0;
        case 2: return 0.5;
        case 1: return 0.2;
        default: return 0;
      }

    case 'quaternary_defense': {
      const sec = (question.section || '').toLowerCase();
      if (sec.includes('tecnic') || sec.includes('técnic')) {
        switch (answerValue) {
          case 1: return 0.2;
          case 2: return 0.5;
          case 3: return 0.8;
          case 4: return 1.0;
          default: return 0;
        }
      }
      if (sec.includes('divulgativ')) {
        switch (answerValue) {
          case 1: return 0.4;
          case 2: return 1.0;
          case 3: return 1.6;
          case 4: return 2.0;
          default: return 0;
        }
      }
      return 0;
    }

    case 'quintary':
      // 1=Deficiente → 5=Excelente, factor 0.2 per level
      return answerValue >= 1 && answerValue <= 5 ? answerValue * 0.2 : 0;

    default:
      return 0;
  }
}

/**
 * Calculate the total score based on exact point values per question
 */
export function calculateScore(
  ratings: Record<string, number | string>,
  questions: Question[]
): number {
  let totalEarned = 0;
  
  for (const question of questions) {
    if (question.answerType === 'text') continue;

    const ratingRaw = ratings[question.id];
    const val = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    
    totalEarned += getPointValue(question, val);
  }

  // Round to 2 decimal places
  return Math.round(totalEarned * 100) / 100;
}

export function getPassStatus(score: number): PassStatus {
  return score >= PASSING_SCORE ? 'Pass' : 'Fail';
}

/**
 * Section scores result
 */
export interface SectionScores {
  total: number;
  diagramacion: number;
  contenido: number;
}

// ---------------------------------------------------------------------------
// TEG Entrega del Tomo — scoring engine
// ---------------------------------------------------------------------------

export const TEG_ENTREGA_PASSING_SCORE = 14;
export const TEG_ENTREGA_MAX_DISPLAY = 20;

export const TEG_ENTREGA_SECTION_WEIGHTS = {
  diagramacion: 0.25,
  seccion1: 0.30,
  seccion2: 0.67,
  seccion3: 0.25,
  seccion4: 0.56,
  seccion5: 0.83,
  seccion_final: 0.5,
} as const;

export interface TegEntregaFactibilidad {
  isFactible: boolean;
  includesModelo: boolean;
}

export interface TegEntregaSectionScores {
  total: number;
  diagramacion: number;
  seccion1: number;
  seccion2: number;
  seccion3: number;
  seccion4: number;
  seccion5: number;
  seccion_final: number;
  seccion6_penalty: number;
}

/**
 * Mapea el `section` literal de una pregunta al identificador interno del bucket
 * de sección ponderada. Devuelve null si la sección no corresponde a ningún
 * bucket (p.ej. Sección 6, que se trata vía factibilidad y no vía scoring).
 */
function sectionToBucket(section: string | undefined): keyof typeof TEG_ENTREGA_SECTION_WEIGHTS | null {
  switch (section) {
    case 'Diagramación': return 'diagramacion';
    case 'Sección 1 (Capítulo 1)': return 'seccion1';
    case 'Sección 2 (Capítulo 2)': return 'seccion2';
    case 'Sección 3 (Capítulo 3)': return 'seccion3';
    case 'Sección 4 (Capítulo 4)': return 'seccion4';
    case 'Sección 5 (Capítulo 5)': return 'seccion5';
    case 'Sección Final': return 'seccion_final';
    default: return null;
  }
}

/**
 * Calcula el puntaje total de la evaluación TEG Entrega del Tomo.
 * Aplica el peso por sección, la penalización de Sección 6 y clampea a 20.
 */
export function calculateTegEntregaScore(
  ratings: Record<string, number | string>,
  questions: Question[],
  factibilidad: TegEntregaFactibilidad
): number {
  const sectionAccum: Partial<Record<keyof typeof TEG_ENTREGA_SECTION_WEIGHTS, number>> = {};

  for (const question of questions) {
    const bucket = sectionToBucket(question.section);
    if (!bucket) continue;

    const ratingRaw = ratings[question.id];
    const val = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    const points = getPointValue(question, val);
    sectionAccum[bucket] = (sectionAccum[bucket] ?? 0) + points;
  }

  let rawTotal = 0;
  for (const [bucket, subtotal] of Object.entries(sectionAccum) as [keyof typeof TEG_ENTREGA_SECTION_WEIGHTS, number][]) {
    rawTotal += subtotal * TEG_ENTREGA_SECTION_WEIGHTS[bucket];
  }

  const penalty = (factibilidad.isFactible && !factibilidad.includesModelo) ? -2 : 0;
  rawTotal += penalty;

  const clamped = Math.min(rawTotal, 20);
  return Math.round(clamped * 10000) / 10000;
}

/**
 * Calcula el puntaje desglosado por sección para la evaluación TEG Entrega del Tomo.
 */
export function calculateTegEntregaSectionScores(
  ratings: Record<string, number | string>,
  questions: Question[],
  factibilidad: TegEntregaFactibilidad
): TegEntregaSectionScores {
  const sectionAccum: Partial<Record<keyof typeof TEG_ENTREGA_SECTION_WEIGHTS, number>> = {};

  for (const question of questions) {
    const bucket = sectionToBucket(question.section);
    if (!bucket) continue;

    const ratingRaw = ratings[question.id];
    const val = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    const points = getPointValue(question, val);
    sectionAccum[bucket] = (sectionAccum[bucket] ?? 0) + points;
  }

  const diagramacion = Math.round(((sectionAccum.diagramacion ?? 0) * TEG_ENTREGA_SECTION_WEIGHTS.diagramacion) * 100) / 100;
  const seccion1 = Math.round(((sectionAccum.seccion1 ?? 0) * TEG_ENTREGA_SECTION_WEIGHTS.seccion1) * 100) / 100;
  const seccion2 = Math.round(((sectionAccum.seccion2 ?? 0) * TEG_ENTREGA_SECTION_WEIGHTS.seccion2) * 100) / 100;
  const seccion3 = Math.round(((sectionAccum.seccion3 ?? 0) * TEG_ENTREGA_SECTION_WEIGHTS.seccion3) * 100) / 100;
  const seccion4 = Math.round(((sectionAccum.seccion4 ?? 0) * TEG_ENTREGA_SECTION_WEIGHTS.seccion4) * 100) / 100;
  const seccion5 = Math.round(((sectionAccum.seccion5 ?? 0) * TEG_ENTREGA_SECTION_WEIGHTS.seccion5) * 100) / 100;
  const seccion_final = Math.round(((sectionAccum.seccion_final ?? 0) * TEG_ENTREGA_SECTION_WEIGHTS.seccion_final) * 100) / 100;

  const seccion6_penalty = (factibilidad.isFactible && !factibilidad.includesModelo) ? -2 : 0;

  // Compute total from the raw accumulators (not from the 2dp-rounded section values)
  // to avoid compounding rounding errors. This matches calculateTegEntregaScore exactly.
  let rawTotal = 0;
  for (const [bucket, subtotal] of Object.entries(sectionAccum) as [keyof typeof TEG_ENTREGA_SECTION_WEIGHTS, number][]) {
    rawTotal += subtotal * TEG_ENTREGA_SECTION_WEIGHTS[bucket];
  }
  rawTotal += seccion6_penalty;
  const total = Math.round(Math.min(rawTotal, 20) * 10000) / 10000;

  return {
    total,
    diagramacion,
    seccion1,
    seccion2,
    seccion3,
    seccion4,
    seccion5,
    seccion_final,
    seccion6_penalty,
  };
}

export function getTegEntregaPassStatus(score: number): PassStatus {
  return score >= TEG_ENTREGA_PASSING_SCORE ? 'Pass' : 'Fail';
}

// ---------------------------------------------------------------------------
// TEG Defensa Oral — scoring engine
// ---------------------------------------------------------------------------

export const TEG_DEFENSA_PASSING_SCORE = 14;
export const TEG_DEFENSA_MAX_DISPLAY = 20;

export interface TegDefensaSectionScores {
  total: number;
  tecnica: number;
  divulgativa: number;
}

/**
 * Calcula el puntaje total de la evaluación TEG Defensa Oral.
 * Suma los puntos por sección (Técnica + Divulgativa) y clampea a 20.
 */
export function calculateTegDefensaScore(
  ratings: Record<string, number | string>,
  questions: Question[]
): number {
  let tecnica = 0;
  let divulgativa = 0;

  for (const question of questions) {
    const ratingRaw = ratings[question.id];
    const val = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    const points = getPointValue(question, val);
    const sec = (question.section || '').toLowerCase();

    if (sec.includes('tecnic') || sec.includes('técnic')) {
      tecnica += points;
    } else if (sec.includes('divulgativ')) {
      divulgativa += points;
    }
  }

  const total = Math.min(tecnica + divulgativa, 20);
  return Math.round(total * 100) / 100;
}

/**
 * Calcula el puntaje desglosado por sección para la evaluación TEG Defensa Oral.
 */
export function calculateTegDefensaSectionScores(
  ratings: Record<string, number | string>,
  questions: Question[]
): TegDefensaSectionScores {
  let tecnicaRaw = 0;
  let divulgativaRaw = 0;

  for (const question of questions) {
    const ratingRaw = ratings[question.id];
    const val = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    const points = getPointValue(question, val);
    const sec = (question.section || '').toLowerCase();

    if (sec.includes('tecnic') || sec.includes('técnic')) {
      tecnicaRaw += points;
    } else if (sec.includes('divulgativ')) {
      divulgativaRaw += points;
    }
  }

  const tecnica = Math.round(tecnicaRaw * 100) / 100;
  const divulgativa = Math.round(divulgativaRaw * 100) / 100;
  const total = Math.round(Math.min(tecnicaRaw + divulgativaRaw, 20) * 100) / 100;

  return { total, tecnica, divulgativa };
}

export function getTegDefensaPassStatus(score: number): PassStatus {
  return score >= TEG_DEFENSA_PASSING_SCORE ? 'Pass' : 'Fail';
}

/**
 * Calculate scores broken down by section (Diagramación vs Contenido)
 */
export function calculateSectionScores(
  ratings: Record<string, number | string>,
  questions: Question[]
): SectionScores {
  let diagramacionEarned = 0;
  let contenidoEarned = 0;
  
  for (const question of questions) {
    if (question.answerType === 'text') continue;

    const ratingRaw = ratings[question.id];
    const val = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    
    const points = getPointValue(question, val);
    const section = question.section?.toLowerCase() || '';
    
    if (section.includes('diagramacion') || section.includes('diagramación')) {
      diagramacionEarned += points;
    } else if (section.includes('contenido')) {
      contenidoEarned += points;
    }
  }

  const result = {
    total: Math.round((diagramacionEarned + contenidoEarned) * 100) / 100,
    diagramacion: Math.round(diagramacionEarned * 100) / 100,
    contenido: Math.round(contenidoEarned * 100) / 100,
  };
  
  return result;
}
