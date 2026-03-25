/**
 * 统一 API 客户端
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

async function request<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }

  return resp.json();
}

export const api = {
  get: <T = any>(path: string) => request<T>(path),
  post: <T = any>(path: string, body?: any) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T = any>(path: string, body?: any) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T = any>(path: string) =>
    request<T>(path, { method: "DELETE" }),
};

// ── Auth ──
export async function login(phone: string, password: string) {
  const res = await api.post("/api/auth/login", { phone, password });
  if (res.data?.access_token) setToken(res.data.access_token);
  return res;
}

export async function register(phone: string, password: string, inviteCode = "") {
  const res = await api.post("/api/auth/register", {
    phone,
    password,
    invite_code: inviteCode,
  });
  if (res.data?.access_token) setToken(res.data.access_token);
  return res;
}

// ── Pipeline ──
export async function createPipeline(keyword: string, platforms: string[], config = {}) {
  return api.post("/api/pipeline/create", { keyword, platforms, config });
}

export async function runPipeline(pipelineId: string) {
  return api.post(`/api/pipeline/${pipelineId}/run`);
}

export async function getPipelineStatus(pipelineId: string) {
  return api.get(`/api/pipeline/${pipelineId}/status`);
}

export async function approveStep(pipelineId: string, stepId: string, edits?: any) {
  return api.post(`/api/pipeline/${pipelineId}/step/${stepId}/approve`, { edits });
}

export async function retryStep(pipelineId: string, stepId: string) {
  return api.patch(`/api/pipeline/${pipelineId}/step/${stepId}/retry`);
}

export async function listPipelines() {
  return api.get("/api/pipeline/list");
}

// ── Stores ──
export async function listStores() {
  return api.get("/api/stores/list");
}

export async function createStore(data: { name: string; platform: string; store_url?: string; operation_mode?: string }) {
  return api.post("/api/stores/create", data);
}

export async function updateStore(storeId: string, data: Record<string, any>) {
  return api.patch(`/api/stores/${storeId}`, data);
}

export async function deleteStore(storeId: string) {
  return api.delete(`/api/stores/${storeId}`);
}

export async function saveCredential(storeId: string, data: { platform: string; credential_type?: string; data: Record<string, any> }) {
  return api.post(`/api/stores/${storeId}/credential`, data);
}

// ── Onboarding ──
export async function completeOnboarding(data: {
  platforms: string[];
  risk_level?: string;
  categories?: string[];
  automation_level?: string;
}) {
  return api.post("/api/onboarding/complete", data);
}

// ── Autopilot ──
export async function getAutopilotSettings(storeId?: string) {
  const query = storeId ? `?store_id=${storeId}` : "";
  return api.get(`/api/autopilot/settings${query}`);
}

export async function setGlobalMode(mode: "auto" | "review", storeId?: string) {
  const query = storeId ? `?store_id=${storeId}` : "";
  return api.post(`/api/autopilot/global-mode${query}`, { mode });
}

export async function setModuleMode(moduleId: string, mode: "auto" | "review", storeId?: string) {
  const query = storeId ? `?store_id=${storeId}` : "";
  return api.post(`/api/autopilot/module-mode${query}`, { module_id: moduleId, mode });
}

// ── Content ──
export async function generateContent(data: {
  product_info: string; platform?: string; style_id?: string; style?: string; notes?: string;
}) {
  return api.post("/api/content/generate", data);
}

export async function listContents() {
  return api.get("/api/content/list");
}

export async function submitFeedback(contentId: string, vote: number, editNotes?: string) {
  return api.post(`/api/content/${contentId}/feedback`, { vote, edit_notes: editNotes });
}

export async function getContentStyles(platform?: string, category?: string) {
  const params = new URLSearchParams();
  if (platform) params.set("platform", platform);
  if (category) params.set("category", category);
  const query = params.toString() ? `?${params}` : "";
  return api.get(`/api/content/styles${query}`);
}

export async function selectStyle(platform: string, styleId: string) {
  return api.post("/api/content/styles/select", { platform, style_id: styleId });
}

export async function getPreferences() {
  return api.get("/api/content/preferences");
}

export async function updatePreferences(prefs: Record<string, any>) {
  return api.post("/api/content/preferences", prefs);
}

export async function getMemoryStats() {
  return api.get("/api/content/agent/memory-stats");
}

// ── SSE ──
export function subscribePipeline(
  pipelineId: string,
  onData: (data: any) => void,
  onDone?: () => void
): () => void {
  const token = getToken();
  const url = `${API_BASE}/api/pipeline/${pipelineId}/stream`;

  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onData(data);
      if (["completed", "failed", "paused"].includes(data.status)) {
        eventSource.close();
        onDone?.();
      }
    } catch {}
  };

  eventSource.onerror = () => {
    eventSource.close();
    onDone?.();
  };

  // Return cleanup function
  return () => eventSource.close();
}
