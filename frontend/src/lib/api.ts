const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL ?? 'http://localhost:8000';

function buildUrl(path: string) {
  return `${API_BASE_URL.replace(/\/$/, '')}${path}`;
}

async function ensureSuccess(response: Response): Promise<Response> {
  if (response.ok) {
    return response;
  }

  let message = 'Une erreur inattendue est survenue.';
  try {
    const data = await response.json();
    if (typeof data?.detail === 'string') {
      message = data.detail;
    }
  } catch (error) {
    // Ignore JSON parse errors and fall back to status text
  }

  if (response.statusText) {
    message = message || response.statusText;
  }

  throw new Error(message || 'Requête échouée.');
}

export async function inspectBcf(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await ensureSuccess(
    await fetch(buildUrl('/bcf/inspect'), {
      method: 'POST',
      body: formData,
    })
  );

  return response.json() as Promise<{
    project: Record<string, unknown>;
    topics: Array<{
      guid: string;
      title: string;
      status: string;
      priority: string;
      author: string;
      createdAt: string;
      comments: Array<{ guid?: string; author: string; date: string; text: string }>;
      viewpoints: string[];
      snapshot: string | null;
    }>;
  }>;
}

export async function mergeBcfs(files: File[]) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const response = await ensureSuccess(
    await fetch(buildUrl('/bcf/merge'), {
      method: 'POST',
      body: formData,
    })
  );

  const disposition = response.headers.get('Content-Disposition') ?? '';
  let filename = 'merged.bcfzip';
  const match = /filename\*=UTF-8''([^;]+)/i.exec(disposition)
    || /filename="?([^";]+)"?/i.exec(disposition);
  if (match && match[1]) {
    try {
      filename = decodeURIComponent(match[1]);
    } catch (error) {
      filename = match[1];
    }
  }

  const blob = await response.blob();
  return { blob, filename };
}

export const apiClient = {
  inspectBcf,
  mergeBcfs,
};
