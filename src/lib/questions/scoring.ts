
import { Question, SCORE_MULTIPLIERS } from './questions';

export const MAX_SCORE = 20;
export const PASSING_SCORE = 10; // Changed to 10 as per typical pass/fail threshold

export type PassStatus = 'Pass' | 'Fail';

/**
 * Calculate the score based on weighted questions.
 * 
 * Scoring Logic:
 * - Diagramación questions: 5/28 ≈ 0.1785 points each (total 5 pts, 25% of grade)
 * - Contenido questions: 15/28 ≈ 0.5357 points each (total 15 pts, 75% of grade)
 * 
 * Answer multipliers:
 * - Yes/Always (value 2 for yesno, 3 for frequency): 100% of weight
 * - Sometimes/Average (value 2 for frequency): 50% of weight
 * - No/Never (value 1): 0% of weight
 * - N/A (value 4 for frequency): excluded from calculation
 * 
 * @param ratings - The user's answers keyed by question ID
 * @param questions - The list of questions with their weights
 * @returns The total score out of 20
 */
export function calculateScore(
  ratings: Record<string, number | string>,
  questions: Question[]
): number {
  let totalEarned = 0;
  let totalPossible = 0;
  
  for (const question of questions) {
    // Skip text questions for scoring
    if (question.answerType === 'text') continue;

    const ratingRaw = ratings[question.id];
    const val = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    
    // Get the weight for this question (default to 1 if not specified for backward compatibility)
    const weight = question.weight ?? 1;
    
    let multiplier = SCORE_MULTIPLIERS.none; // Default: 0%
    let includeInCalculation = true;

    switch (question.answerType) {
      case 'yesno':
        // 1=No (0%), 2=Yes (100%)
        if (val === 2) {
          multiplier = SCORE_MULTIPLIERS.full; // 100%
        } else {
          multiplier = SCORE_MULTIPLIERS.none; // 0%
        }
        break;

      case 'frequency':
        // 1=Nunca (0%), 2=A veces (50%), 3=Siempre (100%), 4=No aplica (exclude)
        if (val === 4) {
          // No aplica -> Skip this question entirely from scoring
          includeInCalculation = false;
        } else if (val === 3) {
          multiplier = SCORE_MULTIPLIERS.full; // 100%
        } else if (val === 2) {
          multiplier = SCORE_MULTIPLIERS.partial; // 50%
        } else {
          multiplier = SCORE_MULTIPLIERS.none; // 0%
        }
        break;

      case 'stars':
        // 1-5 stars, linear scale
        if (val > 0 && val <= 5) {
          multiplier = val / 5; // 20%, 40%, 60%, 80%, 100%
        }
        break;
        
      default:
        includeInCalculation = false;
    }

    if (includeInCalculation) {
      totalEarned += weight * multiplier;
      totalPossible += weight;
    }
  }

  // If no questions were answered (edge case), return 0
  if (totalPossible === 0) return 0;

  // For weighted questions where weights sum to 20, this should give us a direct score
  // For backward compatibility (questions without weights), we normalize to 20
  const hasWeights = questions.some(q => q.weight !== undefined);
  
  if (hasWeights) {
    // Weights are designed to sum to 20, so return earned directly
    // But if N/A reduces total possible, scale proportionally
    const scale = MAX_SCORE / totalPossible;
    const score = totalEarned * scale;
    return Math.round(score * 100) / 100;
  } else {
    // Legacy: normalize to 20-point scale
    const score = (totalEarned / totalPossible) * MAX_SCORE;
    return Math.round(score * 100) / 100;
  }
}

export function getPassStatus(score: number): PassStatus {
  return score >= PASSING_SCORE ? 'Pass' : 'Fail';
}

