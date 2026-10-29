import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Fade } from "@/components/ui/Fade";

export type StudyCard = { front: string; back: string };

/* A small deck to flip through: tap a card to see its meaning, then go to the next one.
   No scoring, it is just there to make the words stick before the quick quiz. */
export function StudyCards({ cards, onDone, doneLabel }: { cards: StudyCard[]; onDone: () => void; doneLabel: string }) {
  const [i, setI] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const card = cards[i];
  const last = i === cards.length - 1;

  if (!card) {
    onDone();
    return null;
  }

  return (
    <Fade k="study-cards">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
        Flashcards &middot; {i + 1} of {cards.length}
      </p>

      <div className="mt-3 max-w-md [perspective:1200px]">
        <div
          className="relative h-48 w-full transition-transform duration-500 ease-out [transform-style:preserve-3d]"
          style={{ transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)" }}
        >
          <button
            type="button"
            onClick={() => setFlipped(true)}
            className="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-md border border-line bg-surface p-6 text-center [backface-visibility:hidden]"
          >
            <p className="text-2xl font-semibold text-ink">{card.front}</p>
            <span className="text-xs font-semibold uppercase tracking-wide text-hero">Tap to flip</span>
          </button>
          <button
            type="button"
            onClick={() => setFlipped(false)}
            className="absolute inset-0 flex items-center justify-center rounded-md border border-hero/40 bg-hero/5 p-6 text-center [backface-visibility:hidden]"
            style={{ transform: "rotateY(180deg)" }}
          >
            <p className="text-sm leading-relaxed text-ink">{card.back}</p>
          </button>
        </div>
      </div>

      <div className="mt-5 flex items-center gap-3">
        {i > 0 && (
          <Button
            variant="ghost"
            onClick={() => {
              setI(i - 1);
              setFlipped(false);
            }}
          >
            Back
          </Button>
        )}
        <Button
          glow
          onClick={() => {
            if (last) onDone();
            else {
              setI(i + 1);
              setFlipped(false);
            }
          }}
        >
          {last ? doneLabel : "Next card"} <span aria-hidden>&rarr;</span>
        </Button>
      </div>
    </Fade>
  );
}
