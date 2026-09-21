const API = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface WorkerRow {
  worker_id: string;
  name: string;
  phone: string;
  current_role: string;
  opted_in: boolean;
  ttm_stage: string;
  target_role_id: string | null;
  pathway_completion: number | null;
  pathway_size: number;
}

export async function fetchWorkers(): Promise<WorkerRow[]> {
  const res = await fetch(`${API}/workers`);
  if (!res.ok) throw new Error(`workers ${res.status}`);
  return res.json();
}

export async function uploadImpactMap(csv: string): Promise<number> {
  const res = await fetch(`${API}/impact-map`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ csv }),
  });
  if (!res.ok) throw new Error(`impact-map ${res.status}`);
  const body = await res.json();
  return body.ingested ?? 0;
}

export async function inviteWorkers(rows: WorkerRow[]): Promise<void> {
  const res = await fetch(`${API}/invite`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      workers: rows.map((w) => ({
        worker_id: w.worker_id, name: w.name, phone: w.phone,
      })),
    }),
  });
  if (!res.ok) throw new Error(`invite ${res.status}`);
}
