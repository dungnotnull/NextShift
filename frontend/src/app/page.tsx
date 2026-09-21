"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchWorkers, inviteWorkers, uploadImpactMap, WorkerRow } from "@/lib/api";

const STAGE_CLASS: Record<string, string> = {
  precontemplation: "var(--stage-precontemplation)",
  contemplation: "var(--stage-contemplation)",
  preparation: "var(--stage-preparation)",
  action: "var(--stage-action)",
};

const PRETTY_ROLE: Record<string, string> = {
  warehouse_associate: "Warehouse Associate",
  inventory_clerk: "Inventory Clerk",
  robot_fleet_operator: "Robot Fleet Operator",
  customer_care_specialist: "Customer Care Specialist",
  automation_support_technician: "Automation Support Technician",
};

function prettyRole(roleId: string | null | undefined): string {
  if (!roleId) return "";
  return PRETTY_ROLE[roleId] ?? roleId.replace(/_/g, " ");
}

export default function Home() {
  const [workers, setWorkers] = useState<WorkerRow[]>([]);
  const [status, setStatus] = useState("");
  const [isErr, setIsErr] = useState(false);
  const [busy, setBusy] = useState<"none" | "upload" | "invite">("none");

  const refresh = useCallback(async () => {
    try {
      setWorkers(await fetchWorkers());
    } catch {
      setStatus("Cannot reach the API. Set NEXT_PUBLIC_API_URL and redeploy.");
      setIsErr(true);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    setBusy("upload");
    try {
      const ingested = await uploadImpactMap(await file.text());
      setStatus(`Impact map ingested — ${ingested} workers.`);
      setIsErr(false);
      await refresh();
    } catch {
      setStatus("Upload failed. Check the API is reachable and the CSV format.");
      setIsErr(true);
    } finally {
      setBusy("none");
    }
  }

  async function onInvite() {
    setBusy("invite");
    try {
      await inviteWorkers(workers);
      setStatus("SMS invites queued — workers reply on WhatsApp.");
      setIsErr(false);
    } catch {
      setStatus("Invite failed. Check the API is reachable.");
      setIsErr(true);
    } finally {
      setBusy("none");
    }
  }

  const inTransition = workers.filter((w) => w.ttm_stage !== "precontemplation").length;
  const onPathways = workers.filter((w) => w.target_role_id).length;
  const milestones = workers.filter((w) => w.pathway_completion === 1).length;

  return (
    <main className="shell">
      <header className="topbar">
        <div className="wordmark">
          <span className="block mono">NEXT</span>
          <span className="rest">SHIFT</span>
        </div>
        <div className="meta">
          <span className="live"><span className="dot" /> Live</span>
        </div>
      </header>
      <p className="subtitle">
        Automation impact console — <strong>Velocity Logistics</strong> · turning displacement into internal advancement
      </p>

      <section className="stats">
        <div className="stat">
          <div className="value">{workers.length}</div>
          <div className="label mono">Workers mapped</div>
        </div>
        <div className="stat">
          <div className="value hi">{inTransition}</div>
          <div className="label mono">In transition</div>
        </div>
        <div className="stat">
          <div className="value">{onPathways}</div>
          <div className="label mono">On pathways</div>
        </div>
        <div className="stat">
          <div className="value">{milestones}</div>
          <div className="label mono">Milestones reached</div>
        </div>
      </section>

      <section className="actions">
        <label className="btn">
          {busy === "upload" ? "Uploading…" : "Upload impact map (CSV)"}
          <input className="file-hidden" type="file" accept=".csv" onChange={onUpload} disabled={busy !== "none"} />
        </label>
        <button className="btn primary" onClick={onInvite} disabled={busy !== "none" || workers.length === 0}>
          {busy === "invite" ? "Sending…" : "Send SMS invites →"}
        </button>
        {status && <span className={`statusline mono ${isErr ? "err" : ""}`}>{status}</span>}
      </section>

      {workers.length === 0 ? (
        <section className="empty">
          <h2 className="title">No workers mapped yet</h2>
          <p className="hint">Upload the Automation Impact Map to see every affected worker and their way forward.</p>
          <div className="steps">
            <div className="step">
              <div className="num mono">01 — MAP</div>
              <div className="what">Upload impact map</div>
              <div className="why">CSV of affected roles and the people in them.</div>
            </div>
            <div className="step">
              <div className="num mono">02 — INVITE</div>
              <div className="what">Send SMS invites</div>
              <div className="why">One text, no app needed. Workers continue on WhatsApp.</div>
            </div>
            <div className="step">
              <div className="num mono">03 — SHIFT</div>
              <div className="what">Watch progress grow</div>
              <div className="why">Daily micro-lessons fill the cells until the milestone email lands.</div>
            </div>
          </div>
        </section>
      ) : (
        <table className="roster">
          <thead>
            <tr>
              <th>Worker</th>
              <th>Journey</th>
              <th>Stage</th>
              <th>Pathway progress</th>
              <th>Opt-in</th>
            </tr>
          </thead>
          <tbody>
            {workers.map((w, i) => {
              const size = w.pathway_size || 0;
              const done = w.pathway_completion != null
                ? Math.round(w.pathway_completion * size) : 0;
              const full = w.pathway_completion === 1;
              return (
                <tr className="row" key={w.worker_id} style={{ animationDelay: `${0.05 + i * 0.06}s` }}>
                  <td>
                    <div className="who">
                      <span className="name">{w.name}</span>
                      <span className="id">{w.worker_id} · {w.phone}</span>
                    </div>
                  </td>
                  <td>
                    <div className="roleflow">
                      <span>{prettyRole(w.current_role)}</span>
                      {w.target_role_id && (
                        <>
                          <span className="arrow">→</span>
                          <span className="target">{prettyRole(w.target_role_id)}</span>
                        </>
                      )}
                      {!w.target_role_id && <span className="target none">· awaiting pathway</span>}
                    </div>
                  </td>
                  <td>
                    <span
                      className="stage"
                      style={{ background: STAGE_CLASS[w.ttm_stage] ?? "var(--paper-deep)" }}
                    >
                      {w.ttm_stage}
                    </span>
                  </td>
                  <td>
                    {w.pathway_completion == null ? (
                      <span className="pct">—</span>
                    ) : (
                      <div className="cells">
                        <div className="cellrow">
                          {Array.from({ length: size }).map((_, idx) => (
                            <span key={idx} className={`cell${idx < done ? " done" : ""}`} />
                          ))}
                        </div>
                        <span className={`pct${full ? " full" : ""}`}>
                          {full ? "COMPLETE 100%" : `${Math.round(w.pathway_completion * 100)}%`}
                        </span>
                      </div>
                    )}
                  </td>
                  <td>
                    <span className={`optin ${w.opted_in ? "yes" : "no"}`} title={w.opted_in ? "opted in" : "not opted in"} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <footer className="footer">
        <span>NextShift · AWS CDS Agentic AI Hackathon</span>
        <span>SMS → WhatsApp → AgentCore → SES</span>
      </footer>
    </main>
  );
}
