"use client";
import { useState } from "react";
import { api, useApi } from "@/lib/api";
import { Card, ErrorBox, Loading, PageHeader } from "@/components/ui";

/* eslint-disable @typescript-eslint/no-explicit-any */
const STATUSES = ["saved", "applied", "interview", "offer", "rejected"];

export default function ApplicationsPage() {
  const { data, error, loading, reload } = useApi<any[]>("/applications");
  const [err, setErr] = useState<string | null>(null);

  async function patch(id: number, body: object) {
    setErr(null);
    try { await api(`/applications/${id}`, { method: "PATCH", body }); reload(); }
    catch (e) { setErr(e instanceof Error ? e.message : "Update failed."); }
  }
  async function remove(id: number) {
    if (!window.confirm("Stop tracking this application?")) return;
    setErr(null);
    try { await api(`/applications/${id}`, { method: "DELETE" }); reload(); }
    catch (e) { setErr(e instanceof Error ? e.message : "Delete failed."); }
  }

  return (
    <>
      <PageHeader title="Applications" subtitle="Track where each application stands." />
      <ErrorBox error={error ?? err} />
      {loading ? <Loading /> : (
        <>
          <div className="grid grid-3">
            {["applied", "interview", "offer"].map((s) => (
              <Card key={s}><strong>{data?.filter((a) => a.status === s).length ?? 0}</strong><p className="muted small" style={{ margin: 0 }}>{s}</p></Card>
            ))}
          </div>
          <Card>
            {!data?.length ? <p className="muted">Nothing tracked yet. Use the Track button on any job.</p> : (
              <table>
                <thead><tr><th>Role</th><th>Status</th><th>Notes</th><th></th></tr></thead>
                <tbody>
                  {data.map((a) => (
                    <tr key={a.id}>
                      <td><strong>{a.title}</strong><div className="muted small">{a.company} · {a.location}</div></td>
                      <td>
                        <label className="sr-only" htmlFor={`s${a.id}`}>Status for {a.title}</label>
                        <select id={`s${a.id}`} value={a.status} onChange={(e) => patch(a.id, { status: e.target.value })}>
                          {STATUSES.map((s) => <option key={s}>{s}</option>)}
                        </select>
                      </td>
                      <td>
                        <label className="sr-only" htmlFor={`n${a.id}`}>Notes for {a.title}</label>
                        <input id={`n${a.id}`} defaultValue={a.notes} maxLength={1000} onBlur={(e) => e.target.value !== a.notes && patch(a.id, { notes: e.target.value })} />
                      </td>
                      <td><button className="btn btn-ghost btn-small" onClick={() => remove(a.id)}>Remove</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </>
      )}
    </>
  );
}
