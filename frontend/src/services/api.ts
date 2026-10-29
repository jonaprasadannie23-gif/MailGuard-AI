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

// In production, VITE_API_URL is set to the Render backend origin.
// Strip trailing slashes then append /api to get the full base.
// Falls back to '/api' for local dev (Vite proxy handles it).
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

export const api = {
  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<{ status: string; service: string; model_loaded: boolean }>(res);
  },

  // Dashboard
  async getDashboard(): Promise<DashboardData> {
    const res = await fetch(`${API_BASE}/dashboard`);
    return handleResponse<DashboardData>(res);
  },

  // Dataset
  async getDatasetSummary(): Promise<{ is_loaded: boolean; summary?: DatasetSummary }> {
    const res = await fetch(`${API_BASE}/dataset/summary`);
    return handleResponse<{ is_loaded: boolean; summary?: DatasetSummary }>(res);
  },

  async loadSampleDataset(): Promise<{ status: string; message: string; summary: DatasetSummary }> {
    const res = await fetch(`${API_BASE}/dataset/load-sample`, { method: 'POST' });
    return handleResponse<{ status: string; message: string; summary: DatasetSummary }>(res);
  },

  async uploadDataset(formData: FormData): Promise<{ status: string; message: string; summary: DatasetSummary }> {
    const res = await fetch(`${API_BASE}/dataset/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<{ status: string; message: string; summary: DatasetSummary }>(res);
  },

  async remapColumns(mappings: { text_column: string; label_column: string; subject_column?: string }): Promise<{ status: string; summary: DatasetSummary }> {
    const res = await fetch(`${API_BASE}/dataset/remap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mappings),
    });
    return handleResponse<{ status: string; summary: DatasetSummary }>(res);
  },

  // Analytics
  async getStatistics(): Promise<{ is_available: boolean; filename?: string; statistics: DatasetStatistics }> {
    const res = await fetch(`${API_BASE}/analytics/statistics`);
    return handleResponse<{ is_available: boolean; filename?: string; statistics: DatasetStatistics }>(res);
  },

  async getChiSquare(k: number = 50): Promise<{ is_available: boolean; filename?: string; analysis: ChiSquareAnalysis }> {
    const res = await fetch(`${API_BASE}/analytics/chi-square?k=${k}`);
    return handleResponse<{ is_available: boolean; filename?: string; analysis: ChiSquareAnalysis }>(res);
  },

  // Model Training
  async startTraining(params: { k_best: number; test_size: number; alpha: number; max_features: number }): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/model/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return handleResponse<{ status: string; message: string }>(res);
  },

  async getTrainingStatus(): Promise<TrainingStatus> {
    const res = await fetch(`${API_BASE}/model/status`);
    return handleResponse<TrainingStatus>(res);
  },

  async getEvaluation(): Promise<EvaluationData> {
    const res = await fetch(`${API_BASE}/model/evaluation`);
    return handleResponse<EvaluationData>(res);
  },

  // Prediction / Scanner
  async predictEmail(payload: { subject?: string; body?: string }): Promise<PredictionResult> {
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<PredictionResult>(res);
  },

  async predictEmailFile(formData: FormData): Promise<PredictionResult> {
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<PredictionResult>(res);
  },

  // Prediction History
  async getHistory(): Promise<{ status: string; count: number; statistics: any; predictions: PredictionRecord[] }> {
    const res = await fetch(`${API_BASE}/predictions/history`);
    return handleResponse<{ status: string; count: number; statistics: any; predictions: PredictionRecord[] }>(res);
  },

  async getPredictionDetail(id: number): Promise<{ status: string; prediction: PredictionRecord }> {
    const res = await fetch(`${API_BASE}/predictions/${id}`);
    return handleResponse<{ status: string; prediction: PredictionRecord }>(res);
  },

  async clearHistory(): Promise<{ status: string; message: string; deleted_count: number }> {
    const res = await fetch(`${API_BASE}/predictions/history`, {
      method: 'DELETE',
    });
    return handleResponse<{ status: string; message: string; deleted_count: number }>(res);
  },

  // PDF Reports
  async downloadScanReport(payload: Record<string, any>): Promise<Blob> {
    const res = await fetch(`${API_BASE}/predict/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
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
    const res = await fetch(`${API_BASE}/predict/report/${id}`);
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
  // Ensure the blob is tagged with application/pdf MIME type
  const pdfBlob = blob.type === 'application/pdf' ? blob : new Blob([blob], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(pdfBlob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  // Delay cleanup so the browser's download manager can finish reading the object URL
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
