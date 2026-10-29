import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { Button } from "@/components/ui/Button";
import { api, type DemoAccount, type Profile } from "@/lib/api";

/* The first screen after "Let's go". Demo-only: the accounts live in the backend
   (data/demo_users.json), are public on purpose, and are shown right here so
   nobody has to guess. Someone with no account can answer three quick questions
   instead. */
export function Login({
  onBack,
  onSuccess,
  onGuest,
}: {
  onBack: () => void;
  onSuccess: (profile: Profile) => void;
  onGuest: () => void;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [accounts, setAccounts] = useState<DemoAccount[] | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .demoAccounts()
      .then((a) => alive && setAccounts(a))
      .catch(() => alive && setAccounts([]));
    return () => {
      alive = false;
    };
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.login(username, password);
      onSuccess(res.profile);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't log in. Try again.");
    } finally {
      setBusy(false);
    }
  };

  const demo = accounts?.[0] ?? (accounts !== null ? { username: "demo", password: "demo123", name: "Demo" } : undefined);

  return (
    <div className="min-h-screen bg-bg">
      <TopBar right="Back to start" />

      <div className="flex min-h-[calc(100vh-88px)] flex-col items-center justify-center px-8">
        <form onSubmit={submit} className="w-full max-w-[380px] border border-white/10 bg-white/[0.025] p-8">
          <h1 className="text-3xl text-ink">Log in</h1>
          <p className="mt-2 text-sm text-ink-soft">Use the demo login below, or answer 3 quick questions instead.</p>

          <label htmlFor="login-username" className="mt-7 block text-xs font-semibold uppercase tracking-wide text-ink-soft">
            Username
          </label>
          <input
            id="login-username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-2 w-full border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-ink outline-none focus-visible:border-hero"
            placeholder="Your username"
          />

          <label htmlFor="login-password" className="mt-5 block text-xs font-semibold uppercase tracking-wide text-ink-soft">
            Password
          </label>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-2 w-full border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-ink outline-none focus-visible:border-hero"
            placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
          />

          {error && <p className="mt-3 text-sm text-fail">{error}</p>}

          <div className="mt-7">
            <Button glow type="submit" disabled={busy || !username || !password} className="w-full justify-center">
              {busy ? "Checking\u2026" : "Log in"} <span aria-hidden>&rarr;</span>
            </Button>
          </div>

          <div className="mt-6 border border-white/10 bg-white/[0.03] px-4 py-3 text-xs text-ink-soft">
            <span className="font-semibold text-ink">Demo login</span> &mdash; a prototype, not a real account
            system.
            {demo ? (
              <>
                <div className="mt-2">
                  Username: <span className="font-semibold text-ink">{demo.username}</span>
                </div>
                <div>
                  Password: <span className="font-semibold text-ink">{demo.password}</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setUsername(demo.username);
                    setPassword(demo.password);
                    setError(null);
                  }}
                  className="mt-2 font-semibold text-hero hover:underline"
                >
                  Fill it in for me
                </button>
              </>
            ) : (
              <div className="mt-2">{accounts === null ? "Loading the demo login\u2026" : "Couldn't load the demo login."}</div>
            )}
          </div>

          <div className="mt-5 flex items-center justify-between">
            <button type="button" onClick={onBack} className="text-sm font-semibold text-ink-soft hover:text-ink">
              &larr; Back
            </button>
            <button type="button" onClick={onGuest} className="text-sm font-semibold text-ink-soft hover:text-ink">
              No account? Answer 3 questions &rarr;
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
