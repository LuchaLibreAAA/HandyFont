import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Download, ArrowLeft, FileText, RotateCcw } from 'lucide-react';
import { api } from '../api';

export default function PreviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const renderData = location.state?.renderData;
  const sessionId = location.state?.sessionId;

  // Redirect if no render data (e.g. page refresh)
  useEffect(() => {
    if (!renderData) {
      navigate('/', { replace: true });
    }
  }, [renderData, navigate]);

  if (!renderData) {
    return null;
  }

  const previewUrl = api.getPreviewUrl(renderData.preview_url);
  const pngDownloadUrl = api.getExportUrl(renderData.render_id, 'png');
  const pdfDownloadUrl = api.getExportUrl(renderData.render_id, 'pdf');

  const handleBackToEditor = () => {
    navigate('/editor', { state: { sessionId } });
  };

  return (
    <div className="mt-8 animate-fade-in flex flex-col items-center">
      {/* Top bar */}
      <div className="w-full flex justify-between items-center mb-8">
        <button
          onClick={handleBackToEditor}
          className="flex items-center gap-2 text-textMuted hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Editor
        </button>
        <div className="flex gap-3">
          <button
            onClick={handleBackToEditor}
            className="bg-card hover:bg-cardHover border border-border text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            Re-generate
          </button>
          <a
            href={pngDownloadUrl}
            target="_blank"
            rel="noreferrer"
            className="btn-primary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Save PNG
          </a>
          <a
            href={pdfDownloadUrl}
            target="_blank"
            rel="noreferrer"
            className="bg-card hover:bg-cardHover border border-border text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            Save PDF
          </a>
        </div>
      </div>

      {/* Preview Image */}
      <div className="w-full max-w-4xl glass-card p-2 flex justify-center items-center bg-white/5">
        <div className="aspect-[3/4] w-full bg-white rounded-lg shadow-inner overflow-hidden relative flex items-center justify-center">
          <img
            src={previewUrl}
            alt="Generated Handwriting"
            className="w-full h-full object-contain"
          />
        </div>
      </div>
    </div>
  );
}
