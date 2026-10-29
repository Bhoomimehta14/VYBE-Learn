import { useEffect, useState } from "react";
import { Quiz } from "@/components/lesson/Quiz";
import { StudyCards, type StudyCard } from "@/components/lesson/StudyCards";
import { api, type QuizQuestion, type QuizResult } from "@/lib/api";

/* Flashcards first, then a short multiple-choice quiz, for the stages that used to end
   in "just data" (EDA, ML foundations, modeling). Quiz is injected for modeling, which
   already had its own questions; the other two use the generic /practice endpoints. */
export function Practice({
  stage,
  fetchQuestions,
  submitAnswers,
  onPointsChange,
  onDone,
}: {
  stage: "eda" | "foundations" | "model";
  fetchQuestions?: () => Promise<{ questions: QuizQuestion[] }>;
  submitAnswers?: (answers: Record<string, string>) => Promise<QuizResult>;
  onPointsChange?: (points: number) => void;
  onDone: () => void;
}) {
  const [cards, setCards] = useState<StudyCard[] | null>(null);
  const [phase, setPhase] = useState<"cards" | "quiz">("cards");

  useEffect(() => {
    api
      .practiceCards(stage)
      .then((r) => setCards(r.cards))
      .catch(() => setPhase("quiz"));
  }, [stage]);

  if (phase === "cards") {
    if (!cards) return <p className="mt-6 text-sm text-ink-soft">Getting your flashcards ready...</p>;
    return <StudyCards cards={cards} doneLabel="Take the quick quiz" onDone={() => setPhase("quiz")} />;
  }

  return (
    <Quiz
      resetKey={`practice-${stage}`}
      fetchQuestions={fetchQuestions ?? (() => api.practiceQuiz(stage))}
      submitAnswers={submitAnswers ?? ((answers) => api.submitPracticeQuiz(stage, answers))}
      onDone={(points) => {
        onPointsChange?.(points);
        onDone();
      }}
    />
  );
}
