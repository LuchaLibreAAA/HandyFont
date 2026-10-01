import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileDown, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../api';

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFile = (selectedFile) => {
    if (selectedFile && (selectedFile.type === 'image/png' || selectedFile.type === 'image/jpeg')) {
      setFile(selectedFile);
      setError(null);
      setUploadResult(null);
    } else {
      setError('Please select a PNG or JPEG image.');
    }
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);

    try {
      const data = await api.uploadTemplate(file);
      setUploadResult(data);
      setUploading(false);
    } catch (err) {
      console.error(err);
      setUploading(false);
      setError(err.message || 'Failed to upload. Make sure the backend server is running.');
    }
  };

  const handleContinue = () => {
    if (uploadResult) {
      navigate('/editor', { state: { sessionId: uploadResult.session_id } });
    }
  };

  const qualityEntries = uploadResult
    ? Object.entries(uploadResult.character_quality)
    : [];
  const goodCount = qualityEntries.filter(([, v]) => v === 'good').length;
  const needsRedoCount = qualityEntries.filter(([, v]) => v === 'needs_redo').length;

  return (
    <div className="max-w-2xl mx-auto mt-12 animate-fade-in">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-bold mb-4">Digitize your handwriting</h2>
        <p className="text-textMuted text-lg">Download the template, fill it out, and upload it to generate your custom font.</p>
      </div>

      <div className="glass-card mb-8">
        {/* Step 1: Download Template */}
        <div className="flex items-center justify-between p-4 bg-primary/10 rounded-xl mb-6">
          <div className="flex items-center gap-4">
            <div className="bg-primary p-3 rounded-lg">
              <FileDown className="text-white w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">1. Download Template</h3>
              <p className="text-sm text-textMuted">Print this PDF and fill the boxes.</p>
            </div>
          </div>
          <a
            href={api.getTemplateDownloadUrl()}
            className="btn-primary"
            target="_blank"
            rel="noreferrer"
          >
            Download PDF
          </a>
        </div>

        {/* Step 2: Upload */}
        <div
          className={`border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 ${
            dragActive
              ? 'border-primary bg-primary/10 scale-[1.02]'
              : 'border-border hover:border-primary/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            id="template-upload"
            className="hidden"
            accept="image/png,image/jpeg"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          <label htmlFor="template-upload" className="cursor-pointer flex flex-col items-center">
            {file ? (
              <div className="flex flex-col items-center">
                <CheckCircle className="w-12 h-12 text-green-500 mb-4" />
                <span className="font-medium text-lg">{file.name}</span>
                <span className="text-sm text-textMuted mt-2">Click to change file</span>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <UploadCloud className={`w-12 h-12 mb-4 ${dragActive ? 'text-white' : 'text-primary'}`} />
                <span className="font-medium text-lg">2. Upload filled template</span>
                <span className="text-sm text-textMuted mt-2">Drag and drop or click to browse</span>
              </div>
            )}
          </label>
        </div>

        {/* Error message */}
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}
      </div>

      {/* Quality Results */}
      {uploadResult && (
        <div className="glass-card mb-8 animate-fade-in">
          <h3 className="font-semibold text-lg mb-4">Extraction Results</h3>
          <div className="flex gap-4 mb-4">
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm">{goodCount} characters extracted</span>
            </div>
            {needsRedoCount > 0 && (
              <div className="flex items-center gap-2 text-amber-400">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">{needsRedoCount} need redo</span>
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {qualityEntries.map(([char, quality]) => (
              <span
                key={char}
                className={`inline-flex items-center justify-center w-9 h-9 rounded-lg text-sm font-mono border ${
                  quality === 'good'
                    ? 'border-green-500/30 bg-green-500/10 text-green-400'
                    : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
                }`}
              >
                {char}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex justify-end gap-3">
        {!uploadResult ? (
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className={`btn-primary px-8 flex items-center gap-2 ${(!file || uploading) ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing...
              </>
            ) : (
              'Extract Characters'
            )}
          </button>
        ) : (
          <button
            onClick={handleContinue}
            className="btn-primary px-8"
          >
            Continue to Editor →
          </button>
        )}
      </div>
    </div>
  );
}
