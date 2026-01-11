'use client';

import { useState, useEffect, FormEvent } from 'react';

// Types
interface QueryResponse {
  answer: string;
  marks: number;
  subject: string;
  chapter: string | null;
  sources: {
    text: string;
    chapter: string;
    topic: string;
    source_type: string;
    relevance_score: number;
  }[];
  keywords: string[];
}

// Available subjects
const SUBJECTS = [
  { id: 'Science', label: 'Science' },
  { id: 'Mathematics', label: 'Maths' },
  { id: 'Social Science', label: 'Social Studies' },
  { id: 'English', label: 'English' },
];

// Available marks
const MARKS_OPTIONS = [1, 2, 3, 5];

export default function StudyPage() {
  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
  }, []);

  // Toggle theme
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  // Form state
  const [question, setQuestion] = useState('');
  const [subject, setSubject] = useState('Science');
  const [marks, setMarks] = useState(3);

  // Response state
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!question.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      // Use environment variable for API URL (defaults to localhost for dev)
      // IMPORTANT: In production, this must be the Public IP of the EC2 instance
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

      const res = await fetch(`${API_BASE_URL}/api/v1/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          subject,
          marks,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data: QueryResponse = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer');
    } finally {
      setIsLoading(false);
    }
  };

  // Format answer text (convert markdown-like syntax to HTML)
  const formatAnswer = (text: string) => {
    // Convert **bold** to <strong>
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert bullet points
    formatted = formatted.replace(/^• /gm, '<li>').replace(/(<li>.*?)(?=\n|$)/g, '$1</li>');
    // Convert newlines to breaks
    formatted = formatted.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
    return `<p>${formatted}</p>`;
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header" style={{ position: 'relative' }}>
        <button
          onClick={toggleTheme}
          style={{
            position: 'absolute',
            right: 0,
            top: '50%',
            transform: 'translateY(-50%)',
            background: 'var(--color-bg-secondary)',
            border: '2px solid var(--color-border)',
            borderRadius: 'var(--radius-full)',
            padding: '8px 16px',
            cursor: 'pointer',
            fontSize: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: 'var(--color-text-primary)',
          }}
          aria-label="Toggle theme"
        >
          {theme === 'light' ? '🌙' : '☀️'}
          <span style={{ fontSize: '14px' }}>{theme === 'light' ? 'Dark' : 'Light'}</span>
        </button>
        <h1 className="app-logo">📚 Study Buddy</h1>
        <p className="app-tagline">Your CBSE Class 9 Study Assistant</p>
      </header>

      {/* Main Content - Two Column Layout */}
      <main className="main-content">
        {/* Left Column - Question Input */}
        <div className="card">
          <h2 className="card-header">
            <span className="card-header-icon">✏️</span>
            Ask Your Question
          </h2>

          <form onSubmit={handleSubmit}>
            {/* Subject Selection */}
            <div className="form-group">
              <label className="form-label" htmlFor="subject">
                Subject
              </label>
              <select
                id="subject"
                className="form-select"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              >
                {SUBJECTS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Marks Selection */}
            <div className="form-group">
              <label className="form-label">
                How many marks?
              </label>
              <div className="marks-selector">
                {MARKS_OPTIONS.map((m) => (
                  <button
                    key={m}
                    type="button"
                    className={`marks-pill ${marks === m ? 'active' : ''}`}
                    onClick={() => setMarks(m)}
                  >
                    {m} Mark{m > 1 ? 's' : ''}
                  </button>
                ))}
              </div>
            </div>

            {/* Question Input */}
            <div className="form-group">
              <label className="form-label" htmlFor="question">
                Your Question
              </label>
              <textarea
                id="question"
                className="form-textarea"
                placeholder="Type your question here... (e.g., What are the states of matter?)"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={isLoading}
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={isLoading || !question.trim()}
            >
              {isLoading ? (
                <>
                  <span className="loading-spinner" style={{ width: 20, height: 20 }}></span>
                  Thinking...
                </>
              ) : (
                <>
                  📝 Get Answer
                </>
              )}
            </button>

            {/* Error Message */}
            {error && (
              <div className="error-message" style={{ marginTop: 16 }}>
                {error}
              </div>
            )}
          </form>
        </div>

        {/* Right Column - Answer Display */}
        <div className="answer-container">
          <div className="answer-header">
            <h2 className="answer-title">📖 Answer</h2>
            {response && (
              <span className="answer-marks-badge">
                {response.marks} Mark{response.marks > 1 ? 's' : ''}
              </span>
            )}
          </div>

          <div className="answer-content">
            {isLoading ? (
              <div className="answer-empty">
                <div className="loading-spinner" style={{ width: 48, height: 48 }}></div>
                <p className="loading-text">Generating your answer...</p>
              </div>
            ) : response ? (
              <>
                <div
                  dangerouslySetInnerHTML={{ __html: formatAnswer(response.answer) }}
                />

                {/* Keywords */}
                {response.keywords && response.keywords.length > 0 && (
                  <div className="keywords-container">
                    <p className="keywords-label">Key Terms:</p>
                    <div className="keywords-list">
                      {response.keywords.map((kw, idx) => (
                        <span key={idx} className="keyword-tag">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="answer-empty">
                <span className="answer-empty-icon">💡</span>
                <p className="answer-empty-text">
                  Ask a question to get started!
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        Made with 💚 for CBSE Students
      </footer>
    </div>
  );
}
