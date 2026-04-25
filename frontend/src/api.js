const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export async function fetchFires(hours = 24, minFrp = 0) {
  const res = await fetch(`${API_BASE}/fires?hours=${hours}&min_frp=${minFrp}`);
  if (!res.ok) throw new Error('Failed to fetch fires');
  return res.json();
}

export async function fetchPlumes(hours = 24) {
  const res = await fetch(`${API_BASE}/fires/plumes?hours=${hours}`);
  if (!res.ok) throw new Error('Failed to fetch plumes');
  return res.json();
}

export async function fetchRiskScores(hours = 24) {
  const res = await fetch(`${API_BASE}/districts/risk-scores?hours=${hours}`);
  if (!res.ok) throw new Error('Failed to fetch risk scores');
  return res.json();
}

export async function fetchAlerts() {
  const res = await fetch(`${API_BASE}/alerts?unacknowledged_only=true`);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
}

export async function fetchDistricts() {
  const res = await fetch(`${API_BASE}/districts`);
  if (!res.ok) throw new Error('Failed to fetch districts');
  return res.json();
}
