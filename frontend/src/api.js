export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  let data = null;
  try {
    data = await response.json();
  } catch {
    if (!response.ok) {
      throw new Error(`Service unavailable (${response.status}). Please verify the backend is running on port 8000.`);
    }
    throw new Error('Invalid response received from the server.');
  }
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : 'Please check the fields and try again.');
  return data;
}

export async function uploadFile(path, formData) {
  const response = await fetch(`/api${path}`, {
    method: 'POST',
    body: formData,
  });
  let data = null;
  try {
    data = await response.json();
  } catch {
    if (!response.ok) {
      throw new Error(`Upload failed (${response.status}). Please verify the backend is running on port 8000.`);
    }
    throw new Error('Invalid response received from the server.');
  }
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : 'Upload failed.');
  return data;
}

export const percentage = value => value == null ? '—' : `${(value * 100).toFixed(1)}%`;
export const timeLabel = value => value ? new Date(value).toLocaleString() : '—';
