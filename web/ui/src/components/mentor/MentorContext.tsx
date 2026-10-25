import { createContext, useCallback, useContext, useMemo, useRef, useState, type MutableRefObject, type ReactNode } from "react";
import type { LearningMode, MentorDatasetContext, MentorLessonContext } from "@/lib/api";

/* What "where the learner currently is" means to the mentor. App.tsx already
   tracks screen/dataset/level state for routing, so it also computes this and
   pushes it in here - no other screen needs to be touched to wire the
   mentor up. */
export type MentorTaskContext = {
  lesson?: MentorLessonContext;
  dataset?: MentorDatasetContext;
  code?: string;
  output?: string;
  error?: string;
};

/* A lesson screen can let the mentor treat a typed message as an answer attempt
   (e.g. "type your fix"). It returns true when it handled the text, in which case
   the mentor does not also send it as a question. */
export type AttemptHandler = (text: string) => Promise<boolean>;

type MentorState = {
  open: boolean;
  setOpen: (v: boolean) => void;
  task: MentorTaskContext;
  setTask: (patch: Partial<MentorTaskContext>) => void;
  attemptHandlerRef: MutableRefObject<AttemptHandler | null>;
  /** True while a screen has registered an attempt handler (drives the input placeholder). */
  canAttempt: boolean;
  registerAttemptHandler: (h: AttemptHandler | null) => void;
  mode: LearningMode;
  setMode: (m: LearningMode) => void;
  /** True only once the learner has picked a mode themselves; until then the
   *  server chooses one from who they are and how the lesson is going. */
  modeChosen: boolean;
  hintsUsed: number;
  bumpHints: () => void;
  attemptCount: number;
  bumpAttempts: () => void;
  mistakes: string[];
  addMistake: (m: string) => void;
  recentActions: string[];
  logAction: (a: string) => void;
};

const MentorCtx = createContext<MentorState | null>(null);

export function MentorProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [task, setTaskState] = useState<MentorTaskContext>({});
  const [mode, setModeState] = useState<LearningMode>("assisted");
  const [modeChosen, setModeChosen] = useState(false);
  const attemptHandlerRef = useRef<AttemptHandler | null>(null);
  const [canAttempt, setCanAttempt] = useState(false);
  const registerAttemptHandler = useCallback((h: AttemptHandler | null) => {
    attemptHandlerRef.current = h;
    setCanAttempt(h !== null);
  }, []);
  const setMode = useCallback((m: LearningMode) => {
    setModeState(m);
    setModeChosen(true);
  }, []);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [attemptCount, setAttemptCount] = useState(0);
  const [mistakes, setMistakes] = useState<string[]>([]);
  const [recentActions, setRecentActions] = useState<string[]>([]);

  const bumpHints = useCallback(() => setHintsUsed((n) => n + 1), []);
  const bumpAttempts = useCallback(() => setAttemptCount((n) => n + 1), []);
  const addMistake = useCallback((m: string) => setMistakes((ms) => [...ms, m].slice(-10)), []);
  const logAction = useCallback((a: string) => setRecentActions((as) => [...as, a].slice(-10)), []);

  // Merges rather than replaces, so a screen can push just {code}/{output}/
  // {error} without clobbering the {lesson, dataset} App.tsx already set for
  // the current screen. A new lesson id shouldn't inherit the last one's
  // hint/attempt tally.
  const setTask = useCallback((patch: Partial<MentorTaskContext>) => {
    setTaskState((prev) => {
      const next = { ...prev, ...patch };
      if ("lesson" in patch && patch.lesson?.id !== prev.lesson?.id) {
        setHintsUsed(0);
        setAttemptCount(0);
      }
      return next;
    });
  }, []);

  const value = useMemo<MentorState>(
    () => ({
      open,
      setOpen,
      task,
      setTask,
      attemptHandlerRef,
      canAttempt,
      registerAttemptHandler,
      mode,
      setMode,
      modeChosen,
      hintsUsed,
      bumpHints,
      attemptCount,
      bumpAttempts,
      mistakes,
      addMistake,
      recentActions,
      logAction,
    }),
    [open, task, setTask, canAttempt, registerAttemptHandler, mode, setMode, modeChosen, hintsUsed, bumpHints, attemptCount, bumpAttempts, mistakes, addMistake, recentActions, logAction],
  );

  return <MentorCtx.Provider value={value}>{children}</MentorCtx.Provider>;
}

export function useMentor(): MentorState {
  const ctx = useContext(MentorCtx);
  if (!ctx) throw new Error("useMentor must be used within a MentorProvider");
  return ctx;
}
