import { useState } from "react";
import { Search, Sparkles, AlertCircle, CheckCircle, ExternalLink, Copy, Check } from "lucide-react";

export default function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  async function analyzeUrl() {
    if (!url.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("https://refactr-al20.onrender.com/analyze/url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setResult({ error: "Failed to connect to backend." });
    } finally {
      setLoading(false);
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) {
      analyzeUrl();
    }
  };

  const copyToClipboard = () => {
    if (result?.ai_analysis) {
      navigator.clipboard.writeText(result.ai_analysis);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const parseAnalysis = (text: string) => {
    const sections = text.split(/(?=🧠|💡)/g).filter(Boolean);
    return sections.map((section, idx) => {
      const isCodeSection = section.includes("```");
      const cleanSection = section.trim();
      
      if (isCodeSection) {
        const codeMatch = cleanSection.match(/```(\w+)?\n([\s\S]*?)```/);
        if (codeMatch) {
          return (
            <div key={idx} className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-semibold text-white">Example Fixes</h3>
              </div>
              <pre className="bg-slate-900 border border-slate-700 rounded-lg p-4 overflow-x-auto">
                <code className="text-sm text-emerald-300">{codeMatch[2].trim()}</code>
              </pre>
            </div>
          );
        }
      }
      
      return (
        <div key={idx} className="mb-6">
          <div className="prose prose-invert max-w-none">
            <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{cleanSection}</p>
          </div>
        </div>
      );
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-96 h-96 bg-purple-500/20 rounded-full blur-3xl -top-48 -left-48 animate-pulse"></div>
        <div className="absolute w-96 h-96 bg-blue-500/20 rounded-full blur-3xl -bottom-48 -right-48 animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10 max-w-4xl mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12 animate-fade-in">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/50">
              <Search className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">
              Refactr
            </h1>
          </div>
          <p className="text-slate-300 text-lg">
            Analyze, debug, and improve your website — powered by AI
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-slate-700/50 mb-8">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full px-6 py-4 bg-slate-900/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              />
              {url && (
                <ExternalLink className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              )}
            </div>
            <button
              onClick={analyzeUrl}
              disabled={loading || !url.trim()}
              className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold rounded-xl transition-all transform hover:scale-105 disabled:hover:scale-100 disabled:cursor-not-allowed shadow-lg shadow-purple-500/50 disabled:shadow-none flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Analyze
                </>
              )}
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-12 shadow-2xl border border-slate-700/50 text-center">
            <div className="w-16 h-16 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-300">Analyzing your website...</p>
          </div>
        )}

        {/* Success Result */}
        {result?.ai_analysis && !loading && (
          <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-slate-700/50 animate-slide-up">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-700">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
                <div>
                  <h2 className="text-xl font-semibold text-white">Analysis Complete</h2>
                  <p className="text-sm text-slate-400">{result.title}</p>
                </div>
              </div>
              <button
                onClick={copyToClipboard}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy
                  </>
                )}
              </button>
            </div>
            
            <div className="space-y-6">
              {parseAnalysis(result.ai_analysis)}
            </div>
          </div>
        )}

        {/* Error State */}
        {result?.error && !loading && (
          <div className="bg-red-900/20 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-red-500/50 animate-slide-up">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="w-6 h-6 text-red-400" />
              <h2 className="text-xl font-semibold text-white">Error</h2>
            </div>
            <p className="text-red-200">{result.error}</p>
          </div>
        )}

        {/* Footer */}
        {!result && !loading && (
          <div className="text-center mt-12 text-slate-400 text-sm">
            <p>Enter any website URL to get AI-powered design feedback</p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes slide-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.6s ease-out;
        }

        .animate-slide-up {
          animation: slide-up 0.5s ease-out;
        }

        .delay-1000 {
          animation-delay: 1s;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
        }

        ::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.5);
        }

        ::-webkit-scrollbar-thumb {
          background: rgba(139, 92, 246, 0.5);
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: rgba(139, 92, 246, 0.7);
        }
      `}</style>
    </div>
  );
}