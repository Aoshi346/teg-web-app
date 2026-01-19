
import { Question } from './questions';

export const MAX_SCORE = 20;
export const PASSING_SCORE = 15;

export type PassStatus = 'Pass' | 'Fail';

export function calculateScore(
  ratings: Record<string, number | string>,
  questions: Question[]
): number {
  let totalEarned = 0;
  let maxPossible = 0;
  
  for (const question of questions) {
    // Skip text questions for scoring
    if (question.answerType === 'text') continue;

    const ratingRaw = ratings[question.id];
    // Convert to number, default to 0 if missing
    const val = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    
    // If val is 0, it means "unanswered" in our current state logic, 
    // but usually validation prevents finding score with unanswered questions.
    // If allowed, 0 counts as 0 points but adds to maxPossible? 
    // Let's assume validation ensures they are answered. 
    // If val is 0, treat as "no points" but "max points" exist.

    let earned = 0;
    let possible = 0;

    switch (question.answerType) {
      case 'yesno':
        // 1=No, 2=Yes. Max weight = 1.
        possible = 1;
        if (val === 2) earned = 1; // Yes
        else earned = 0;           // No
        break;

      case 'frequency':
        // 1=Nunca (0), 2=A veces (0.5), 3=Siempre (1), 4=No aplica (exclude)
        if (val === 4) {
             // No aplica -> Skip this question entirely from scoring
             possible = 0;
             earned = 0;
        } else {
             possible = 1;
             if (val === 3) earned = 1;       // Siempre
             else if (val === 2) earned = 0.5; // A veces
             else earned = 0;                 // Nunca (val 1)
        }
        break;

      case 'stars':
        // 1-5 stars. Map to 0-1 scale? Or just treat as 5 points max.
        // Consistency: Let's treat standard weight as 1.
        // So val 5 = 1, val 1 = 0.2? 
        // Or linear: val / 5.
        possible = 1;
        if (val > 0 && val <= 5) {
            earned = val / 5;
        }
        break;
        
      default:
        possible = 0;
    }

    totalEarned += earned;
    maxPossible += possible;
  }

  if (maxPossible === 0) return 0;

  // Scale to 20 points
  const score = (totalEarned / maxPossible) * 20;
  
  // Return formatted to 2 decimals if needed, but number type usually fine.
  // We can round it closer to typical grades (e.g. 0.5 precision) or just decimals.
  // User asked for "decimals included".
  return Math.round(score * 100) / 100;
}

export function getPassStatus(score: number): PassStatus {
  return score >= PASSING_SCORE ? 'Pass' : 'Fail';
}
