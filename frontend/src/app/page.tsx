"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchWorkers, inviteWorkers, uploadImpactMap, WorkerRow } from "@/lib/api";

const STAGE_COLORS: Record<string, string> = {
  precontemplation: "#e0e0e0",
  contemplation: "#ffe08a",
  preparation: "#a5d8ff",
  action: "#b2f2bb",
};

export default function Home() {
  const [workers, setWorkers] = useState<WorkerRow[]>([]);
  const [status, setStatus] = useState("");

  const refresh = useCallback(async () => {
    try {
      setWorkers(await fetchWorkers());
    } catch {
      setStatus("Could not load workers. Is the API deployed? Set NEXT_PUBLIC_API_URL.");
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const ingested = await uploadImpactMap(await file.text());
      setStatus(`Impact map ingested: ${ingested} workers`);
      await refresh();
    } catch {
      setStatus("Upload failed. Check the API is reachable and the CSV format.");
    }
  }

  async function onInvite() {
    try {
      await inviteWorkers(workers);
      setStatus("SMS invites queued");
    } catch {
      setStatus("Invite failed. Check the API is reachable.");
    }
  }

  return (
    <main>
      <h1>NextShift HR Dashboard</h1>
      <p>{status}</p>
      <input type="file" accept=".csv" onChange={onUpload} />
      <button onClick={onInvite}>Send SMS invites to all</button>
      <table>
        <thead>
          <tr><th>Worker</th><th>Role</th><th>Phone</th><th>Stage</th><th>Opted in</th></tr>
        </thead>
        <tbody>
          {workers.map((w) => (
            <tr key={w.worker_id}>
              <td>{w.name}</td>
              <td>{w.current_role}</td>
              <td>{w.phone}</td>
              <td>
                <span style={{
                  background: STAGE_COLORS[w.ttm_stage] ?? "#eee",
                  padding: "2px 8px", borderRadius: 8,
                }}>{w.ttm_stage}</span>
              </td>
              <td>{w.opted_in ? "yes" : "no"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
