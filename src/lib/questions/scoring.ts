
import { Question } from './questions';

export const MAX_SCORE = 20;
export const PASSING_SCORE = 15;

export type PassStatus = 'Pass' | 'Fail';

export function calculateScore(
  ratings: Record<string, number | string>,
  questions: Question[]
): number {
  let score = 0;
  
  // Filter questions that are actually in the ratings
  // We assume questions passed here are the ones being evaluated
  
  for (const question of questions) {
    const ratingRaw = ratings[question.id];
    const rating = typeof ratingRaw === 'number' ? ratingRaw : Number(ratingRaw) || 0;
    
    // Logic: Yes (2) = 5 points, No (1) = 0 points.
    // If answerType is not yesno, we might need different logic.
    // For now, user specified 0-20 scale and we have 4 questions.
    
    if (question.answerType === 'yesno') {
      if (rating === 2) { // Yes
        score += 5;
      }
      // No (1) adds 0
    } else {
      // Fallback or other logic if we add more question types later
      // For example, if we had 20 questions, maybe each is 1 point.
      // But for the current 4 questions, 5 points each makes sense.
    }
  }
  
  return score;
}

export function getPassStatus(score: number): PassStatus {
  return score >= PASSING_SCORE ? 'Pass' : 'Fail';
}
