"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, apiBlob, ApiError, token } from "@/lib/api";
import "./cv-view.css";

type CvInfo = { filename: string; size_bytes: number; uploaded_at: string; kind: string; text: string; has_file: boolean };

/** Opens in its own tab from Profile and CV: the original PDF, or the text read from a Word file. */
export default function CvViewer() {
  const router = useRouter();
  const [info, setInfo] = useState<CvInfo | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!token.get()) { router.replace("/login"); return; }
    let url: string | null = null;
    let cancelled = false;
    (async () => {
      try {
        const cv = await api<CvInfo>("/profile/cv");
        if (cancelled) return;
        setInfo(cv);
        document.title = `${cv.filename} · CareerPilot`;
        if (cv.has_file && cv.kind === "pdf") {
          url = URL.createObjectURL(await apiBlob("/profile/cv/file"));
          if (!cancelled) setPdfUrl(url);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "Could not load your CV.");
      }
    })();
    return () => { cancelled = true; if (url) URL.revokeObjectURL(url); };
  }, [router]);

  async function download() {
    if (!info) return;
    setSaving(true);
    try {
      const url = URL.createObjectURL(await apiBlob("/profile/cv/file"));
      const a = document.createElement("a");
      a.href = url;
      a.download = info.filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not download the file.");
    } finally { setSaving(false); }
  }

  const uploaded = info ? new Date(info.uploaded_at).toLocaleString(undefined, { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" }) : "";
  const showText = info && !(pdfUrl && info.kind === "pdf");

  return (
    <div className="cvv">
      <header className="cvv-bar">
        <Link href="/dashboard/profile" className="cvv-brand" aria-label="CareerPilot, back to Profile and CV">
          <img src="/logo.svg" alt="" width={28} height={28} />
          <span>CareerPilot</span>
        </Link>
        <div className="cvv-file">
          <strong>{info?.filename ?? "Your CV"}</strong>
          {info && <span className="muted small">Uploaded {uploaded} · {Math.max(1, Math.round(info.size_bytes / 1024))} KB</span>}
        </div>
        <div className="cvv-actions">
          {info?.has_file && <button type="button" className="btn btn-ghost btn-small" onClick={download} disabled={saving}>{saving ? "Preparing…" : "Download original"}</button>}
          <Link className="btn btn-small" href="/dashboard/profile">Back to profile</Link>
        </div>
      </header>

      <main className="cvv-main">
        {error && <p className="cvv-note" role="alert">{error}</p>}
        {!info && !error && <p className="muted cvv-note">Loading your CV…</p>}
        {info?.kind === "pdf" && info.has_file && !pdfUrl && !error && <p className="muted cvv-note">Opening the PDF…</p>}
        {pdfUrl && (
          <>
            <p className="cvv-note muted small">Not showing? <a href={pdfUrl} target="_blank" rel="noopener noreferrer">Open the PDF on its own</a> or use Download original.</p>
            <iframe className="cvv-pdf" src={pdfUrl} title={`Your CV: ${info?.filename}`} />
          </>
        )}
        {showText && (
          <>
            <p className="cvv-note muted small">
              {!info.has_file
                ? "This CV was uploaded before CareerPilot kept original files, so this is the text it read. Upload it again to view the original."
                : "Browsers can't display Word files, so this is the text CareerPilot read from your CV. Download the original to see its layout."}
            </p>
            <article className="cvv-paper" aria-label="Text read from your CV">{info.text}</article>
          </>
        )}
      </main>
    </div>
  );
}
