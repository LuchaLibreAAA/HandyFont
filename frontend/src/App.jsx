import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { PenTool } from 'lucide-react';
import UploadPage from './pages/Upload';
import EditorPage from './pages/Editor';
import PreviewPage from './pages/Preview';
import './App.css';

function Layout({ children }) {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen p-4 md:p-8 max-w-5xl mx-auto">
      <header className="flex items-center gap-3 mb-10 cursor-pointer" onClick={() => navigate('/')}>
        <div className="bg-primary/20 p-2 rounded-xl">
          <PenTool className="text-primary w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Handy<span className="text-primary">Font</span></h1>
      </header>
      <main>
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/editor" element={<EditorPage />} />
          <Route path="/preview" element={<PreviewPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
