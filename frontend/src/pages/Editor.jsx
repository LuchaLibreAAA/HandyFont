import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Settings, Play, Type, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../api';

export default function EditorPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = location.state?.sessionId;

  const [text, setText] = useState('');
  const [generating, setGenerating] = useState(false);
  const [paperStyle, setPaperStyle] = useState('lined');
  const [penColor, setPenColor] = useState('#1a1a6b');
  const [jitter, setJitter] = useState(50);
  const [fontReady, setFontReady] = useState(false);
  const [fontChecking, setFontChecking] = useState(true);
  const pollRef = useRef(null);

  // Redirect to home if no session
  useEffect(() => {
    if (!sessionId) {
      navigate('/', { replace: true });
    }
  }, [sessionId, navigate]);

  // Poll for font status
  useEffect(() => {
    if (!sessionId) return;

    let cancelled = false;

    const checkFont = async () => {
      try {
        const data = await api.getFontStatus(sessionId);
        if (!cancelled) {
          if (data.font_ready) {
            setFontReady(true);
            setFontChecking(false);
          }
        }
      } catch (err) {
        console.error('Font status check failed:', err);
      }
    };

    // Check immediately
    checkFont();

    // Then poll every 2 seconds until ready
    pollRef.current = setInterval(() => {
      if (!fontReady && !cancelled) {
        checkFont();
      }
    }, 2000);

    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [sessionId, fontReady]);

  // Stop polling when font is ready
  useEffect(() => {
    if (fontReady && pollRef.current) {
      clearInterval(pollRef.current);
    }
  }, [fontReady]);

  const handleGenerate = async () => {
    if (!text.trim()) return;
    setGenerating(true);

    try {
      const data = await api.renderText({
        text,
        sessionId,
        paperStyle,
        penColor,
        jitterIntensity: jitter / 50.0,
      });

      setGenerating(false);
      navigate('/preview', { state: { renderData: data, sessionId } });
    } catch (err) {
      console.error(err);
      setGenerating(false);
      alert(err.message || 'Failed to render text.');
    }
  };

  if (!sessionId) return null;

  return (
    <div className="grid md:grid-cols-3 gap-8 mt-8 animate-fade-in">
      {/* Text Editor Panel */}
      <div className="md:col-span-2 glass-card h-[600px] flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-primary">
            <Type className="w-5 h-5" />
            <h2 className="font-semibold text-lg">Text Editor</h2>
          </div>
          {/* Font status indicator */}
          <div className="flex items-center gap-2 text-sm">
            {fontChecking && !fontReady ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                <span className="text-amber-400">Building font...</span>
              </>
            ) : fontReady ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-green-400">Font ready</span>
              </>
            ) : (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-textMuted" />
                <span className="text-textMuted">Checking font...</span>
              </>
            )}
          </div>
        </div>
        <textarea
          className="flex-1 w-full bg-background/50 border border-border rounded-xl p-4 text-white focus:outline-none focus:border-primary resize-none"
          placeholder="Type or paste your text here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        ></textarea>
        <div className="flex justify-between items-center mt-3 text-xs text-textMuted">
          <span>{text.length} characters</span>
          {!fontReady && (
            <span>You can still generate — a fallback font will be used while your custom font builds.</span>
          )}
        </div>
      </div>

      {/* Settings Panel */}
      <div className="glass-card flex flex-col h-fit">
        <div className="flex items-center gap-2 mb-6 text-primary">
          <Settings className="w-5 h-5" />
          <h2 className="font-semibold text-lg">Style Settings</h2>
        </div>

        <div className="space-y-6">
          {/* Paper Style */}
          <div>
            <label className="block text-sm font-medium text-textMuted mb-3">Paper Style</label>
            <div className="grid grid-cols-3 gap-2">
              {['blank', 'lined', 'grid'].map((style) => (
                <button
                  key={style}
                  onClick={() => setPaperStyle(style)}
                  className={`border p-2 text-sm rounded-lg capitalize transition-all ${
                    paperStyle === style
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border hover:border-primary/50 text-textMuted'
                  }`}
                >
                  {style}
                </button>
              ))}
            </div>
          </div>

          {/* Pen Color */}
          <div>
            <label className="block text-sm font-medium text-textMuted mb-3">Pen Color</label>
            <div className="flex gap-3">
              {[
                { color: '#1a1a6b', label: 'Blue' },
                { color: '#000000', label: 'Black' },
                { color: '#4b5563', label: 'Gray' },
                { color: '#7c2d12', label: 'Brown' },
              ].map(({ color, label }) => (
                <button
                  key={color}
                  onClick={() => setPenColor(color)}
                  title={label}
                  className={`w-8 h-8 rounded-full transition-all ${
                    penColor === color
                      ? 'ring-2 ring-primary ring-offset-2 ring-offset-background scale-110'
                      : 'hover:scale-105'
                  }`}
                  style={{ backgroundColor: color }}
                ></button>
              ))}
            </div>
          </div>

          {/* Jitter Slider */}
          <div>
            <label className="block text-sm font-medium text-textMuted mb-3">
              Random Jitter
              <span className="ml-2 text-primary">{(jitter / 50).toFixed(1)}x</span>
            </label>
            <input
              type="range" min="0" max="150"
              value={jitter}
              onChange={(e) => setJitter(Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-textMuted mt-1">
              <span>Neat</span>
              <span>Messy</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={!text.trim() || generating}
          className={`btn-primary w-full mt-8 flex items-center justify-center gap-2 ${
            (!text.trim() || generating) ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {generating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Rendering...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              Generate Image
            </>
          )}
        </button>
      </div>
    </div>
  );
}
