
import { 
  Question, 
  DIAGRAMACION_SCORES, 
  CONTENIDO_SCORES,
  TESIS_DIAGRAMACION_SCORES,
  TESIS_CONTENIDO_SCORES 
} from './questions';

export const MAX_SCORE = 20;
export const PASSING_SCORE = 10;

export type PassStatus = 'Pass' | 'Fail';

/**
 * Get the exact point value for a question based on document type, section and answer
 */
function getPointValue(
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

/**
 * Calculate scores broken down by section (Diagramación vs Contenido)
 */
export function calculateSectionScores(
  ratings: Record<string, number | string>,
  questions: Question[]
): SectionScores {
  let diagramacionEarned = 0;
  let contenidoEarned = 0;
  
  console.log('[DEBUG] calculateSectionScores called with', questions.length, 'questions');
  
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
  
  console.log('[DEBUG] Section scores result:', result);
  
  return result;
}
