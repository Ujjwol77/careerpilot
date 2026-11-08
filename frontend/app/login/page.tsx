"use client";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, token } from "@/lib/api";
import { ErrorBox } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (mode === "register" && form.password.length < 8) return setError("Password must be at least 8 characters.");
    setBusy(true);
    try {
      const res = await api(`/auth/${mode}`, { body: mode === "register" ? form : { email: form.email, password: form.password } });
      token.set(res.token);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-wrap">
      <div className="auth-card">
        <div className="brand" style={{ color: "var(--ink)", paddingLeft: 0 }}><img src="/logo.svg" alt="" width={28} height={28} /> CareerPilot</div>
        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p className="muted">Seven collaborating AI agents that match you to jobs, fix your CV, close skill gaps and coach your interviews.</p>
        <div className="card">
          <div className="tabs" role="group" aria-label="Sign in or register">
            <button type="button" aria-pressed={mode === "login"} onClick={() => setMode("login")}>Log in</button>
            <button type="button" aria-pressed={mode === "register"} onClick={() => setMode("register")}>Register</button>
          </div>
          <ErrorBox error={error} />
          <form onSubmit={submit}>
            {mode === "register" && (
              <div className="field"><label htmlFor="name">Full name</label><input id="name" autoComplete="name" value={form.name} onChange={set("name")} /></div>
            )}
            <div className="field"><label htmlFor="email">Email</label><input id="email" type="email" required autoComplete="email" value={form.email} onChange={set("email")} /></div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input id="password" type="password" required minLength={mode === "register" ? 8 : 1} autoComplete={mode === "login" ? "current-password" : "new-password"} value={form.password} onChange={set("password")} />
              {mode === "register" && <span className="muted small">At least 8 characters.</span>}
            </div>
            <button className="btn" disabled={busy} style={{ width: "100%", justifyContent: "center" }}>
              {busy ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
            </button>
          </form>
        </div>
        <p className="muted small">Your CV is stored only to power your own analysis. Contact details are removed before any text is sent to an external AI model.</p>
      </div>
    </main>
  );
}
