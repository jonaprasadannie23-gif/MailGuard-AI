import {
  DashboardData,
  DatasetSummary,
  DatasetStatistics,
  ChiSquareAnalysis,
  TrainingStatus,
  EvaluationData,
  PredictionResult,
  PredictionRecord,
} from '../types';

// In production, VITE_API_URL is the Render backend origin (no trailing slash,
// no /api suffix). We strip any stray trailing slashes then always append /api
// so every request goes to https://mailguard-ai-oyh4.onrender.com/api/<endpoint>.
// In local dev VITE_API_URL is unset; we fall back to '/api' and the Vite
// dev-server proxy forwards it to Flask on localhost:5000.
const _rawBase = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '');
const API_BASE = _rawBase ? `${_rawBase}/api` : '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errMessage = `Request failed with status ${res.status}`;
    try {
      const errData = await res.json();
      if (errData.error) errMessage = errData.error;
      else if (errData.message) errMessage = errData.message;
    } catch {
      // fallback to status text
    }
    throw new Error(errMessage);
  }
  return res.json();
}

const TOKEN_KEY = 'probmail_backend_token_v1';

export function getStoredAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredAuthToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // ignore
  }
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const token = getStoredAuthToken();
  const headers = new Headers(init?.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(url, {
      ...init,
      headers,
    });
  } catch (err: any) {
    throw new Error(`Failed to connect to backend server (${url}): ${err.message || 'Network error'}. Please ensure the backend is running.`);
  }
  return handleResponse<T>(res);
}

export const api = {
  // Auth Session Sync
  async createAuthSession(
    userId: string,
    email: string,
    credentials?: {
      passwordHash?: string;
      salt?: string;
      name?: string;
      role?: string;
    }
  ): Promise<{ token: string; user: any }> {
    const res = await requestJson<{ status: string; token: string; user: any }>(`${API_BASE}/auth/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        email,
        password_hash: credentials?.passwordHash,
        salt: credentials?.salt,
        name: credentials?.name,
        role: credentials?.role,
      }),
    });
    setStoredAuthToken(res.token);
    return res;
  },

  clearAuthSession(): void {
    setStoredAuthToken(null);
  },

  async registerUser(payload: {
    name: string;
    email: string;
    password?: string;
    password_hash?: string;
    salt?: string;
    role?: string;
    user_id?: string;
  }): Promise<{ status: string; message: string; token: string; user: any }> {
    const res = await requestJson<{ status: string; message: string; token: string; user: any }>(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.token) {
      setStoredAuthToken(res.token);
    }
    return res;
  },

  async loginUser(credentials: {
    email: string;
    password?: string;
    password_hash?: string;
  }): Promise<{ status: string; token: string; user: any }> {
    const res = await requestJson<{ status: string; token: string; user: any }>(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    if (res.token) {
      setStoredAuthToken(res.token);
    }
    return res;
  },

  async getRegisteredUsers(): Promise<{ status: string; users: any[] }> {
    return requestJson<{ status: string; users: any[] }>(`${API_BASE}/auth/users`);
  },

  // Shared Backend Mailbox (Authenticated Cross-Browser Persistence)
  async sendMailboxMessage(payload: {
    recipient_email: string;
    recipient_name?: string;
    subject: string;
    body: string;
    draft_id?: string;
  }): Promise<{ status: string; message: string; mail: any }> {
    return requestJson<{ status: string; message: string; mail: any }>(`${API_BASE}/mailbox/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },

  async getInboxMessages(): Promise<{ status: string; count: number; messages: any[] }> {
    return requestJson<{ status: string; count: number; messages: any[] }>(`${API_BASE}/mailbox/inbox`);
  },

  async getSpamMessages(): Promise<{ status: string; count: number; messages: any[] }> {
    return requestJson<{ status: string; count: number; messages: any[] }>(`${API_BASE}/mailbox/spam`);
  },

  async getSentMessages(): Promise<{ status: string; count: number; messages: any[] }> {
    return requestJson<{ status: string; count: number; messages: any[] }>(`${API_BASE}/mailbox/sent`);
  },

  async getSentRecipients(): Promise<{ status: string; recipients: { email: string; name: string }[] }> {
    return requestJson<{ status: string; recipients: { email: string; name: string }[] }>(`${API_BASE}/mailbox/recipients`);
  },

  async getDrafts(): Promise<{ status: string; count: number; drafts: any[] }> {
    return requestJson<{ status: string; count: number; drafts: any[] }>(`${API_BASE}/mailbox/drafts`);
  },

  async saveDraft(payload: {
    id?: string;
    recipient_email?: string;
    recipient_name?: string;
    subject?: string;
    body?: string;
  }): Promise<{ status: string; message: string; draft: any }> {
    return requestJson<{ status: string; message: string; draft: any }>(`${API_BASE}/mailbox/drafts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },

  async deleteDraft(draftId: string): Promise<{ status: string; message: string }> {
    return requestJson<{ status: string; message: string }>(`${API_BASE}/mailbox/drafts/${encodeURIComponent(draftId)}`, {
      method: 'DELETE',
    });
  },

  async markMailboxRead(mailId: string): Promise<{ status: string; message: string }> {
    return requestJson<{ status: string; message: string }>(`${API_BASE}/mailbox/${encodeURIComponent(mailId)}/read`, {
      method: 'POST',
    });
  },

  async toggleMailboxStar(mailId: string): Promise<{ status: string; message: string }> {
    return requestJson<{ status: string; message: string }>(`${API_BASE}/mailbox/${encodeURIComponent(mailId)}/star`, {
      method: 'POST',
    });
  },

  async toggleMailboxSpam(mailId: string): Promise<{ status: string; message: string }> {
    return requestJson<{ status: string; message: string }>(`${API_BASE}/mailbox/${encodeURIComponent(mailId)}/toggle-spam`, {
      method: 'POST',
    });
  },

  async deleteMailboxMessage(mailId: string): Promise<{ status: string; message: string }> {
    return requestJson<{ status: string; message: string }>(`${API_BASE}/mailbox/${encodeURIComponent(mailId)}`, {
      method: 'DELETE',
    });
  },

  // Health
  async getHealth(): Promise<{ status: string; service: string; model_loaded: boolean }> {
    return requestJson<{ status: string; service: string; model_loaded: boolean }>(`${API_BASE}/health`);
  },

  // Dashboard
  async getDashboard(): Promise<DashboardData> {
    return requestJson<DashboardData>(`${API_BASE}/dashboard`);
  },

  // Dataset
  async getDatasetSummary(): Promise<{ is_loaded: boolean; summary?: DatasetSummary }> {
    return requestJson<{ is_loaded: boolean; summary?: DatasetSummary }>(`${API_BASE}/dataset/summary`);
  },

  async loadSampleDataset(): Promise<{ status: string; message: string; summary: DatasetSummary }> {
    return requestJson<{ status: string; message: string; summary: DatasetSummary }>(`${API_BASE}/dataset/load-sample`, {
      method: 'POST',
    });
  },

  async uploadDataset(formData: FormData): Promise<{ status: string; message: string; summary: DatasetSummary }> {
    return requestJson<{ status: string; message: string; summary: DatasetSummary }>(`${API_BASE}/dataset/upload`, {
      method: 'POST',
      body: formData,
    });
  },

  async remapColumns(mappings: {
    text_column: string;
    label_column: string;
    subject_column?: string;
  }): Promise<{ status: string; summary: DatasetSummary }> {
    return requestJson<{ status: string; summary: DatasetSummary }>(`${API_BASE}/dataset/remap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mappings),
    });
  },

  // Analytics
  async getStatistics(): Promise<{ is_available: boolean; filename?: string; statistics: DatasetStatistics }> {
    return requestJson<{ is_available: boolean; filename?: string; statistics: DatasetStatistics }>(`${API_BASE}/analytics/statistics`);
  },

  async getChiSquare(k: number = 50): Promise<{ is_available: boolean; filename?: string; analysis: ChiSquareAnalysis }> {
    return requestJson<{ is_available: boolean; filename?: string; analysis: ChiSquareAnalysis }>(`${API_BASE}/analytics/chi-square?k=${k}`);
  },

  // Model Training
  async startTraining(params: {
    k_best: number;
    test_size: number;
    alpha: number;
    max_features: number;
  }): Promise<{ status: string; message: string }> {
    return requestJson<{ status: string; message: string }>(`${API_BASE}/model/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
  },

  async getTrainingStatus(): Promise<TrainingStatus> {
    return requestJson<TrainingStatus>(`${API_BASE}/model/status`);
  },

  async getEvaluation(): Promise<EvaluationData> {
    return requestJson<EvaluationData>(`${API_BASE}/model/evaluation`);
  },

  // Prediction / Scanner
  async predictEmail(payload: { subject?: string; body?: string; record_history?: boolean; recordHistory?: boolean }): Promise<PredictionResult> {
    return requestJson<PredictionResult>(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },

  async predictEmailFile(formData: FormData): Promise<PredictionResult> {
    return requestJson<PredictionResult>(`${API_BASE}/predict`, {
      method: 'POST',
      body: formData,
    });
  },

  // Prediction History
  async getHistory(): Promise<{ status: string; count: number; statistics: any; predictions: PredictionRecord[] }> {
    return requestJson<{ status: string; count: number; statistics: any; predictions: PredictionRecord[] }>(`${API_BASE}/predictions/history`);
  },

  async getPredictionDetail(id: number): Promise<{ status: string; prediction: PredictionRecord }> {
    return requestJson<{ status: string; prediction: PredictionRecord }>(`${API_BASE}/predictions/${id}`);
  },

  async clearHistory(): Promise<{ status: string; message: string; deleted_count: number }> {
    return requestJson<{ status: string; message: string; deleted_count: number }>(`${API_BASE}/predictions/history`, {
      method: 'DELETE',
    });
  },

  // PDF Reports
  async downloadScanReport(payload: Record<string, any>): Promise<Blob> {
    const token = getStoredAuthToken();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let res: Response;
    try {
      res = await fetch(`${API_BASE}/predict/report`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
    } catch (err: any) {
      throw new Error(`Failed to connect to backend server: ${err.message || 'Network error'}`);
    }
    if (!res.ok) {
      let errMessage = `Failed to generate PDF report (status ${res.status})`;
      try {
        const errData = await res.json();
        if (errData.error) errMessage = errData.error;
      } catch {
        // fallback
      }
      throw new Error(errMessage);
    }
    return res.blob();
  },

  async downloadScanReportById(id: number): Promise<Blob> {
    const token = getStoredAuthToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let res: Response;
    try {
      res = await fetch(`${API_BASE}/predict/report/${id}`, { headers });
    } catch (err: any) {
      throw new Error(`Failed to connect to backend server: ${err.message || 'Network error'}`);
    }
    if (!res.ok) {
      let errMessage = `Failed to generate PDF report (status ${res.status})`;
      try {
        const errData = await res.json();
        if (errData.error) errMessage = errData.error;
      } catch {
        // fallback
      }
      throw new Error(errMessage);
    }
    return res.blob();
  },
};

export function triggerFileDownload(blob: Blob, filename: string) {
  const pdfBlob = blob.type === 'application/pdf' ? blob : new Blob([blob], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(pdfBlob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    try {
      if (document.body.contains(a)) {
        document.body.removeChild(a);
      }
      window.URL.revokeObjectURL(url);
    } catch {
      // ignore
    }
  }, 2000);
}
