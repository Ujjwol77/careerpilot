"use client";
import { FormEvent, useEffect, useRef, useState } from "react";
import { api, ApiError, useApi } from "@/lib/api";
import { Card, ErrorBox, Loading, PageHeader, Pill } from "@/components/ui";

const MAX_MB = 5;
const OK_EXT = [".pdf", ".docx"];

export default function ProfilePage() {
  const profile = useApi("/profile");
  const meta = useApi<{ roles: { key: string; label: string }[]; levels: string[] }>("/meta");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [over, setOver] = useState(false);
  const [pending, setPending] = useState<File | null>(null);
  const input = useRef<HTMLInputElement>(null);

  const [prefs, setPrefs] = useState({ target_roles: [] as string[], location: "", min_salary: 0, experience_level: "", goals: "" });
  useEffect(() => { if (profile.data?.preferences) setPrefs(profile.data.preferences); }, [profile.data]);

  function check(file: File): string | null {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!OK_EXT.includes(ext)) return "Only PDF and DOCX files are supported.";
    if (file.size > MAX_MB * 1024 * 1024) return `That file is larger than ${MAX_MB} MB.`;
    if (file.size === 0) return "That file is empty.";
    return null;
  }

  async function send(file: File, overwrite: boolean) {
    setBusy(true); setError(null); setNotice(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const data = await api("/profile/upload", { form, params: { overwrite } });
      profile.setData(data);
      setPending(null);
      setNotice(`CV analysed: ${data.skills.length} skills found.`);
    } catch (e) {
      if (e instanceof ApiError && e.code === "PROFILE_EXISTS") setPending(file);
      else setError(e instanceof Error ? e.message : "Upload failed.");
    } finally { setBusy(false); if (input.current) input.current.value = ""; }
  }

  function pick(file?: File) {
    if (!file) return;
    const problem = check(file);
    if (problem) { setError(problem); return; }
    send(file, false);
  }

  async function savePrefs(e: FormEvent) {
    e.preventDefault();
    setError(null); setNotice(null);
    try {
      const data = await api("/profile/preferences", { method: "PUT", body: { ...prefs, min_salary: Number(prefs.min_salary) || 0 } });
      profile.setData(data);
      setNotice("Preferences saved.");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save."); }
  }

  const toggleRole = (k: string) => setPrefs((p) => ({ ...p, target_roles: p.target_roles.includes(k) ? p.target_roles.filter((r) => r !== k) : [...p.target_roles, k] }));

  if (profile.loading) return <Loading />;
  const p = profile.data;
  const has = p?.has_profile;

  return (
    <>
      <PageHeader title="Profile and CV" subtitle="The Profile Understanding Agent builds your profile from the CV you upload." />
      <ErrorBox error={error} />
      {notice && <div className="alert alert-good" role="status">{notice}</div>}

      <Card title={has ? "Replace your CV" : "Upload your CV"}>
        <div
          className={`dropzone ${over ? "over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setOver(true); }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => { e.preventDefault(); setOver(false); pick(e.dataTransfer.files[0]); }}
        >
          <p><strong>Drop a PDF or DOCX here</strong> (max {MAX_MB} MB)</p>
          <label className="btn" style={{ cursor: "pointer" }}>
            {busy ? "Analysing…" : "Choose file"}
            <input ref={input} type="file" accept=".pdf,.docx" className="sr-only" disabled={busy} onChange={(e) => pick(e.target.files?.[0])} />
          </label>
        </div>
        {pending && (
          <div className="alert alert-warn" role="alertdialog" style={{ marginTop: 14 }}>
            <p>You already have a profile. Replace it with <strong>{pending.name}</strong>? Your skills and matches will be recalculated.</p>
            <div className="row">
              <button className="btn" onClick={() => send(pending, true)} disabled={busy}>Replace profile</button>
              <button className="btn btn-ghost" onClick={() => setPending(null)}>Cancel</button>
            </div>
          </div>
        )}
        <p className="muted small" style={{ marginTop: 12 }}>Your CV is used only for your own analysis. Email addresses and phone numbers are removed before any text goes to an external AI model.</p>
      </Card>

      {has && (
        <>
          <Card title="What the agent understood">
            <p className="muted small">Current file: {p.cv?.filename}</p>
            <p>{p.summary}</p>
            <div className="grid grid-3">
              <div><strong>{p.years_experience}</strong><p className="muted small">years of experience</p></div>
              <div><strong>{(() => {
                const top = (p.inferred_roles as ({ label?: string; role?: string; score?: number } | string)[])
                  .map((r) => typeof r === "string" ? { label: r.replaceAll("_", " "), score: undefined } : { label: r.label ?? r.role?.replaceAll("_", " ") ?? "", score: r.score })
                  .filter((r) => r.label && (r.score === undefined || r.score > 0))
                  .slice(0, 3);
                return top.length ? top.map((r) => r.score === undefined ? r.label : `${r.label} (${r.score}%)`).join(", ") : "-";
              })()}</strong><p className="muted small">roles that fit</p></div>
              <div><strong>{p.skills.length}</strong><p className="muted small">skills detected</p></div>
            </div>
            <h3>Skills</h3>
            <div>{p.skills.map((s: { slug: string; name: string }) => <Pill key={s.slug} tone="brand">{s.name}</Pill>)}</div>
            {p.education?.length > 0 && (<><h3>Education</h3><ul>{p.education.map((e: string, i: number) => <li key={i}>{e}</li>)}</ul></>)}
            {p.experience?.length > 0 && (<><h3>Experience</h3><ul>{p.experience.map((e: { title?: string; period?: string } | string, i: number) => <li key={i}>{typeof e === "string" ? e : `${e.title ?? ""} ${e.period ? `(${e.period})` : ""}`}</li>)}</ul></>)}
          </Card>

          <Card title="Job preferences">
            <form onSubmit={savePrefs}>
              <fieldset style={{ border: 0, padding: 0, margin: "0 0 12px" }}>
                <legend style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Target roles</legend>
                <div className="row">
                  {meta.data?.roles.map((r) => (
                    <label key={r.key} style={{ display: "inline-flex", gap: 6, alignItems: "center", fontWeight: 400 }}>
                      <input type="checkbox" style={{ width: "auto" }} checked={prefs.target_roles.includes(r.key)} onChange={() => toggleRole(r.key)} /> {r.label}
                    </label>
                  ))}
                </div>
              </fieldset>
              <div className="grid grid-3">
                <div className="field"><label htmlFor="loc">Preferred location</label><input id="loc" value={prefs.location} placeholder="e.g. Perth, remote" onChange={(e) => setPrefs({ ...prefs, location: e.target.value })} /></div>
                <div className="field"><label htmlFor="sal">Minimum salary (AUD)</label><input id="sal" type="number" min={0} step={1000} value={prefs.min_salary} onChange={(e) => setPrefs({ ...prefs, min_salary: Number(e.target.value) })} /></div>
                <div className="field">
                  <label htmlFor="lvl">Experience level</label>
                  <select id="lvl" value={prefs.experience_level} onChange={(e) => setPrefs({ ...prefs, experience_level: e.target.value })}>
                    <option value="">Any</option>
                    {meta.data?.levels.map((l) => <option key={l} value={l}>{l}</option>)}
                  </select>
                </div>
              </div>
              <div className="field"><label htmlFor="goals">Career goals</label><textarea id="goals" maxLength={1000} value={prefs.goals} onChange={(e) => setPrefs({ ...prefs, goals: e.target.value })} /></div>
              <button className="btn">Save preferences</button>
            </form>
          </Card>
        </>
      )}
    </>
  );
}
