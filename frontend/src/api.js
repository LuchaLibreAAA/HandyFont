/**
 * Centralized API service for the HandyFont backend.
 * All API calls go through here to avoid hardcoded URLs.
 */

const API_BASE = 'http://localhost:8000';

export const api = {
  /** Download the handwriting template PDF */
  getTemplateDownloadUrl() {
    return `${API_BASE}/api/template/download`;
  },

  /** Upload a filled template image */
  async uploadTemplate(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/template/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }

    return response.json();
  },

  /** Check if the font has been built for a session */
  async getFontStatus(sessionId) {
    const response = await fetch(`${API_BASE}/api/render/status/${sessionId}`);
    if (!response.ok) {
      throw new Error('Failed to check font status');
    }
    return response.json();
  },

  /** Render text with the custom font */
  async renderText({ text, sessionId, paperStyle, penColor, jitterIntensity }) {
    const response = await fetch(`${API_BASE}/api/render`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        session_id: sessionId,
        paper_style: paperStyle,
        pen_color: penColor,
        jitter_intensity: jitterIntensity,
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Rendering failed');
    }

    return response.json();
  },

  /** Get the preview image URL for a render */
  getPreviewUrl(previewPath) {
    return `${API_BASE}${previewPath}`;
  },

  /** Get the export/download URL for a render */
  getExportUrl(renderId, format = 'png') {
    return `${API_BASE}/api/render/export/${renderId}?format=${format}`;
  },
};
