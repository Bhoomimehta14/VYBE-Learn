import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Mascot } from "@/components/Mascot";
import { Button } from "@/components/ui/Button";
import { api, type LearningMode, type MentorAction, type MentorResponse } from "@/lib/api";
import { useMentor } from "@/components/mentor/MentorContext";
import { useNotes } from "@/components/notes/NotesContext";

type MentorMsgKind = "chat" | "hint" | "warning" | "explanation" | "success";
type MentorTag = { intent: string | null; stuck: boolean; mode: LearningMode; reason: string };
type MentorMsg = { from: "you" | "mentor"; text: string; kind: MentorMsgKind; grounded?: boolean; tag?: MentorTag };

const INTENT_LABELS: Record<string, string> = {
  concept_question: "Concept question",
  hint_request: "Hint request",
  stuck_frustrated: "Sounds stuck",
  why_wrong: "Why it was wrong",
  next_step: "What's next",
  example_request: "Example",
  off_topic: "Off topic",
};

/* The server's `level.reason` is written for developers; this says the same
   thing to the learner. */
function reasonLine(res: MentorResponse, picked: boolean): string {
  const mode = MODE_LABELS_LOWER[res.mode];
  if (picked && res.level?.reason.includes("you chose")) return `Why ${mode}: you picked this mode.`;
  const parts: string[] = [];
  if (res.level?.band === "new") parts.push("you said you're new to this");
  else if (res.level?.band === "basics") parts.push("you know the basics");
  else if (res.level?.band === "confident") parts.push("you said you're confident");
  if (res.level?.reason.includes("hints or attempts")) parts.push("you've needed a few hints");
  if (res.intent?.intent === "stuck_frustrated") parts.push("your message sounded stuck, so this reply is gentler");
  if (res.level?.reason.includes("mastery")) parts.push("how the lesson is going");
  return parts.length ? `Why ${mode}: ${parts.join(", ")}.` : `Mode: ${mode}.`;
}

const SUGGESTED_ACTIONS: { action: MentorAction; label: string }[] = [
  { action: "explain", label: "Explain this" },
  { action: "hint", label: "Give me a hint" },
  { action: "example", label: "Show an example" },
];

/* The mentor docks in the right half of the page instead of floating over it:
   App.tsx pads the page by DOCK_PUSH while it is open, so nothing is covered.
   Below the lg breakpoint there is no room for a split, so it is a full sheet. */
export const DOCK_WIDTH = "lg:w-[min(50vw,520px)]";
export const DOCK_PUSH = "lg:pr-[min(50vw,520px)]";

const MODES: LearningMode[] = ["guided", "assisted", "independent"];

const MODE_LABELS: Record<LearningMode, string> = {
  guided: "Guided",
  assisted: "Assisted",
  independent: "Independent",
};
const MODE_LABELS_LOWER: Record<LearningMode, string> = {
  guided: "guided",
  assisted: "assisted",
  independent: "independent",
};

function kindOf(action?: MentorAction): MentorMsgKind {
  if (action === "hint") return "hint";
  if (action === "why_wrong") return "warning";
  if (action === "explain" || action === "example" || action === "explain_output" || action === "next_step") {
    return "explanation";
  }
  return "chat";
}

function bubbleClass(kind: MentorMsgKind): string {
  switch (kind) {
    case "hint":
      return "border-points/40 bg-points/10";
    case "warning":
      return "border-fail/40 bg-fail/10";
    case "success":
      return "border-pass/40 bg-pass/10";
    case "explanation":
      return "border-hero/40 bg-hero/10";
    default:
      return "border-line bg-bg";
  }
}

/* The platform-wide AI Mentor: a floating button + slide-out panel, mounted
   once in App.tsx. Reuses the same Card/Button/Mascot/Night-Signal tokens as
   the rest of the app instead of introducing a new visual style - this is an
   overlay, not a redesign, so it works the same regardless of which screen
   (or which screen's own header layout) is currently showing underneath it. */
export function AiMentor() {
  const {
    open, setOpen, task, mode, setMode, modeChosen, hintsUsed, bumpHints, attemptCount, bumpAttempts,
    mistakes, recentActions, logAction, attemptHandlerRef, canAttempt,
  } = useMentor();
  const { addNote } = useNotes();
  const [messages, setMessages] = useState<MentorMsg[]>([
    {
      from: "mentor",
      text: "Hi, I'm your AI Mentor. Ask me anything about the lesson or dataset you're on, or tap one of the prompts below.",
      kind: "chat",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState<boolean | null>(null);
  // The mode the server last used; shown on the selector until the learner picks their own.
  const [serverMode, setServerMode] = useState<LearningMode | null>(null);
  const [openReason, setOpenReason] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const send = async (action?: MentorAction, textOverride?: string) => {
    const text = (textOverride ?? input).trim();
    if (busy || (!text && !action)) return;

    if (text) {
      setMessages((m) => [...m, { from: "you", text, kind: "chat" }]);
      setInput("");
    }
    if (action === "hint") bumpHints();
    logAction(action ?? "chat_message");
    setBusy(true);

    try {
      // On a lesson that takes typed answers, a message naming a real option is an
      // attempt: the screen scores it, and it is not also sent as a question.
      if (text && !action && attemptHandlerRef.current && (await attemptHandlerRef.current(text))) {
        bumpAttempts();
        setMessages((m) => [
          ...m,
          { from: "mentor", text: "Got it, I scored that as your answer. The result is on the page.", kind: "success" },
        ]);
        return;
      }
      const res = await api.mentor({
        user_message: text,
        action,
        current_lesson: task.lesson,
        dataset: task.dataset,
        current_code: task.code,
        last_output: task.output,
        last_error: task.error,
        attempt_count: attemptCount,
        hints_used: hintsUsed,
        learning_mode: modeChosen ? mode : undefined,
        previous_mistakes: mistakes,
        recent_actions: recentActions,
      });
      setLive(res.grounded);
      if (!modeChosen) setServerMode(res.mode);
      // Offline replies get no tag: it would suggest personalisation that didn't happen.
      const tag: MentorTag | undefined = res.grounded
        ? {
            intent: res.intent ? res.intent.intent : null,
            stuck: res.intent?.intent === "stuck_frustrated",
            mode: res.mode,
            reason: reasonLine(res, modeChosen),
          }
        : undefined;
      setMessages((m) => [...m, { from: "mentor", text: res.reply, kind: kindOf(action), grounded: res.grounded, tag }]);
    } catch {
      setMessages((m) => [
        ...m,
        { from: "mentor", text: "Couldn't reach the mentor just now - try again in a moment.", kind: "warning" },
      ]);
    } finally {
      setBusy(false);
      requestAnimationFrame(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }));
    }
  };

  const shownMode = modeChosen ? mode : (serverMode ?? mode);
  const contextLine = [task.lesson?.title ?? "Not on a lesson yet", task.dataset?.name].filter(Boolean).join(" · ");
  const modeNote = modeChosen
    ? "You picked this mode."
    : serverMode
      ? "Set for you from what you told us. Tap a mode to choose your own."
      : "The mentor sets this for you until you pick one.";

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open AI Mentor"
          className="fixed right-4 top-20 z-40 flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-ink-soft shadow-lg transition-colors hover:border-hero hover:text-ink"
        >
          <Mascot className="h-5 w-5" />
          Ask the mentor
        </button>
      )}

      <AnimatePresence>
        {open && (
          <motion.aside
            initial={{ x: 420, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 420, opacity: 0 }}
            transition={{ type: "spring", stiffness: 320, damping: 34 }}
            aria-label="AI Mentor"
            className={`fixed inset-y-0 right-0 z-40 flex w-full flex-col border-l border-line bg-surface ${DOCK_WIDTH}`}
          >
            {/* Header: the mode is a small control here, not a block of its own */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2.5">
              <div className="flex items-center gap-2">
                <Mascot className="h-7 w-7 shrink-0" />
                <span className="text-sm font-semibold text-ink">AI Mentor</span>
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    busy ? "animate-pulse bg-points" : live === false ? "bg-ink-soft" : "bg-pass"
                  }`}
                  aria-hidden
                />
              </div>
              <div className="flex items-center gap-3">
                <div role="group" aria-label="Support level" title={modeNote} className="flex gap-1">
                  {MODES.map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setMode(m)}
                      aria-pressed={shownMode === m}
                      className={`rounded-full border px-2.5 py-0.5 text-[11px] transition-colors ${
                        shownMode === m
                          ? "border-hero text-ink"
                          : "border-line text-ink-soft hover:border-hero hover:text-ink"
                      }`}
                    >
                      {MODE_LABELS[m]}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  aria-label="Close mentor"
                  className="text-lg leading-none text-ink-soft hover:text-ink"
                >
                  &times;
                </button>
              </div>
            </div>

            {/* One line of context instead of three rows */}
            <div className="truncate border-b border-line px-3 py-1.5 text-[11px] text-ink-soft" title={contextLine}>
              {contextLine}
            </div>

            {/* Conversation: takes all the space that is left */}
            <div ref={scrollRef} className="flex-1 space-y-2.5 overflow-y-auto px-3 py-3">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.from === "you" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[88%] rounded-md border px-3 py-2 text-sm ${
                      m.from === "you" ? "border-hero bg-hero text-white" : `text-ink ${bubbleClass(m.kind)}`
                    }`}
                  >
                    {m.text}
                    {m.from === "mentor" && m.grounded === false && (
                      <div className="mt-1 text-[10px] text-fail">not personalized live yet</div>
                    )}
                    {m.tag && (
                      <div className="mt-2">
                        <div className="flex flex-wrap items-center gap-1.5">
                          {m.tag.intent && (
                            <button
                              type="button"
                              onClick={() => setOpenReason(openReason === i ? null : i)}
                              aria-expanded={openReason === i}
                              className={`rounded-full border px-2 py-0.5 text-[11px] hover:text-ink ${
                                m.tag.stuck
                                  ? "border-points/40 bg-points/10 text-points hover:border-points"
                                  : "border-line text-ink-soft hover:border-hero"
                              }`}
                            >
                              {INTENT_LABELS[m.tag.intent] ?? m.tag.intent}
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => setOpenReason(openReason === i ? null : i)}
                            aria-expanded={openReason === i}
                            className="rounded-full border border-line px-2 py-0.5 text-[11px] text-ink-soft hover:border-hero hover:text-ink"
                          >
                            {MODE_LABELS[m.tag.mode]}
                          </button>
                        </div>
                        {openReason === i && <p className="mt-1 text-[10px] text-ink-soft">{m.tag.reason}</p>}
                      </div>
                    )}
                    {m.from === "mentor" && m.kind !== "success" && (
                      <button
                        type="button"
                        onClick={() => addNote(m.text, task.lesson?.title ?? "AI Mentor")}
                        className="mt-1.5 block text-[10px] font-semibold text-ink-soft hover:text-hero"
                      >
                        Save to notes
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {busy && <p className="text-xs text-ink-soft">thinking&hellip;</p>}
            </div>

            {/* A few quick prompts; the code-aware ones only appear when there is something to send */}
            <div className="flex flex-wrap gap-1.5 px-3 pb-2 pt-1">
              {SUGGESTED_ACTIONS.map((a) => (
                <button
                  key={a.action}
                  type="button"
                  disabled={busy}
                  onClick={() => send(a.action)}
                  className="rounded-full border border-line bg-bg px-3 py-1 text-[11px] font-medium text-ink-soft transition-colors hover:border-hero hover:text-ink disabled:opacity-40"
                >
                  {a.label}
                </button>
              ))}
              {task.code && (
                <button
                  type="button"
                  onClick={() => send("explain", "Can you walk me through this code?")}
                  className="rounded-full border border-line px-3 py-1 text-[11px] text-ink-soft hover:border-hero hover:text-ink"
                >
                  Send current code
                </button>
              )}
              {task.error && (
                <button
                  type="button"
                  onClick={() => send("why_wrong", "I hit this error, can you help me understand it?")}
                  className="rounded-full border border-line px-3 py-1 text-[11px] text-ink-soft hover:border-hero hover:text-ink"
                >
                  Send last error
                </button>
              )}
              {task.output && (
                <button
                  type="button"
                  onClick={() => send("explain_output", "What does this output mean?")}
                  className="rounded-full border border-line px-3 py-1 text-[11px] text-ink-soft hover:border-hero hover:text-ink"
                >
                  Send last output
                </button>
              )}
            </div>

            {/* Input */}
            <div className="flex gap-2 border-t border-line p-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder={canAttempt ? "Ask a question, or type your fix" : "Ask your mentor anything..."}
                rows={2}
                disabled={busy}
                className="flex-1 resize-none rounded-md border border-line bg-bg px-3 py-2 text-sm text-ink outline-none focus-visible:border-hero disabled:opacity-50"
              />
              <Button variant="flat" disabled={!input.trim() || busy} onClick={() => send()}>
                Send
              </Button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
}
