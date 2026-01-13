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
  { id: 'Science', label: 'Science', emoji: '🔬' },
  { id: 'Mathematics', label: 'Maths', emoji: '📐' },
  { id: 'Social Science', label: 'Social Studies', emoji: '🌍' },
  { id: 'English', label: 'English', emoji: '📖' },
];

// Available marks
const MARKS_OPTIONS = [1, 2, 3, 5];

// Splash Screen Component
function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    // Start fade out after 2.5 seconds
    const fadeTimer = setTimeout(() => {
      setFadeOut(true);
    }, 2500);

    // Complete after fade animation (3 seconds total)
    const completeTimer = setTimeout(() => {
      onComplete();
    }, 3200);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(completeTimer);
    };
  }, [onComplete]);

  return (
    <div className={`splash-screen ${fadeOut ? 'fade-out' : ''}`}>
      {/* Scrolling Pattern Background */}
      <div className="pattern-bg"></div>
      <div className="pattern-overlay"></div>

      {/* Welcome content */}
      <div className="splash-content">
        <img src="/logo.png" alt="Study Buddy Logo" className="splash-logo-img" />
        <h1 className="splash-title">Study Buddy</h1>
        <p className="splash-subtitle">Your AI Learning Companion</p>
        <div className="splash-loader">
          <div className="splash-loader-dot"></div>
          <div className="splash-loader-dot"></div>
          <div className="splash-loader-dot"></div>
        </div>
      </div>
    </div>
  );
}

// Available classes
const CLASSES = [
  { id: 6, label: 'Class 6' },
  { id: 7, label: 'Class 7' },
  { id: 8, label: 'Class 8' },
  { id: 9, label: 'Class 9' },
  { id: 10, label: 'Class 10' },
  { id: 11, label: 'Class 11' },
  { id: 12, label: 'Class 12' },
];

// Onboarding Screen Component
function OnboardingScreen({ onComplete }: { onComplete: (name: string, classLevel: number, subjects: string[]) => void }) {
  const [step, setStep] = useState(1);
  const [studentName, setStudentName] = useState('');
  const [selectedClass, setSelectedClass] = useState<number | null>(null);
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>([]);
  const [isTailoring, setIsTailoring] = useState(false);

  const toggleSubject = (subjectId: string) => {
    setSelectedSubjects(prev =>
      prev.includes(subjectId)
        ? prev.filter(s => s !== subjectId)
        : [...prev, subjectId]
    );
  };

  const handleContinue = () => {
    if (step === 1 && studentName.trim()) {
      setStep(2);
    } else if (step === 2 && selectedClass) {
      setStep(3);
    } else if (step === 3 && selectedSubjects.length > 0) {
      setIsTailoring(true);
      // Simulate tailoring experience
      setTimeout(() => {
        onComplete(studentName.trim(), selectedClass!, selectedSubjects);
      }, 2500);
    }
  };

  if (isTailoring) {
    return (
      <div className="onboarding-screen tailoring-screen">
        <div className="pattern-bg"></div>
        <div className="pattern-overlay"></div>
        <div className="tailoring-content">
          <div className="progress-bar-container">
            <div className="progress-bar"></div>
          </div>
          <h2 className="tailoring-title">Tailoring your experience...</h2>
          <p className="tailoring-subtitle">Setting up personalized learning just for you</p>
          <div className="tailoring-steps">
            <div className="tailoring-step active">✓ Analyzing preferences</div>
            <div className="tailoring-step">Curating content</div>
            <div className="tailoring-step">Almost ready...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="onboarding-screen">
      <div className="pattern-bg"></div>
      <div className="pattern-overlay"></div>

      <div className="onboarding-content">
        <img src="/logo.png" alt="Study Buddy" className="onboarding-logo" />

        {step === 1 ? (
          <>
            <h2 className="onboarding-title">Hi there! What&apos;s your name?</h2>
            <p className="onboarding-subtitle">Let&apos;s get to know each other</p>

            <input
              type="text"
              className="name-input"
              placeholder="Enter your name..."
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              autoFocus
            />
          </>
        ) : step === 2 ? (
          <>
            <h2 className="onboarding-title">Hey {studentName}! What class are you in?</h2>
            <p className="onboarding-subtitle">Select your current class level</p>

            <div className="class-grid">
              {CLASSES.map(c => (
                <button
                  key={c.id}
                  className={`class-card ${selectedClass === c.id ? 'active' : ''}`}
                  onClick={() => setSelectedClass(c.id)}
                >
                  <span className="class-number">{c.id}</span>
                  <span className="class-label">{c.label}</span>
                </button>
              ))}
            </div>
          </>
        ) : (
          <>
            <h2 className="onboarding-title">What subjects do you study?</h2>
            <p className="onboarding-subtitle">Select all that apply</p>

            <div className="subject-grid">
              {SUBJECTS.map(s => (
                <button
                  key={s.id}
                  className={`subject-card ${selectedSubjects.includes(s.id) ? 'active' : ''}`}
                  onClick={() => toggleSubject(s.id)}
                >
                  <span className="subject-emoji">{s.emoji}</span>
                  <span className="subject-label">{s.label}</span>
                  {selectedSubjects.includes(s.id) && <span className="subject-check">✓</span>}
                </button>
              ))}
            </div>
          </>
        )}

        <button
          className="onboarding-btn"
          disabled={(step === 1 && !studentName.trim()) || (step === 2 && !selectedClass) || (step === 3 && selectedSubjects.length === 0)}
          onClick={handleContinue}
        >
          {step === 3 ? 'Get Started 🚀' : 'Continue →'}
        </button>
      </div>

      {step > 1 && (
        <button className="onboarding-back" onClick={() => setStep(step - 1)}>
          ← Back
        </button>
      )}
    </div>
  );
}

// Internal chat history type
interface ChatMessage {
  role: 'user' | 'model';
  content: string;
  marks?: number;
  sources?: QueryResponse['sources'];
  keywords?: string[];
}

interface ChatSession {
  id: string;
  title: string;
  timestamp: number;
  messages: ChatMessage[];
}

export default function StudyPage() {
  // Screen states
  const [currentScreen, setCurrentScreen] = useState<'splash' | 'onboarding' | 'main'>('splash');
  const [currentView, setCurrentView] = useState<'dashboard' | 'chat'>('dashboard');

  // User preferences
  const [userName, setUserName] = useState<string>('');
  const [userClass, setUserClass] = useState<number>(9);
  const [userSubjects, setUserSubjects] = useState<string[]>(['Science']);

  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [mounted, setMounted] = useState(false);

  // Load theme and check onboarding status on mount
  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
    }

    // Check if user already onboarded
    const onboarded = localStorage.getItem('onboarded');
    const savedName = localStorage.getItem('userName');
    const savedClass = localStorage.getItem('userClass');
    const savedSubjects = localStorage.getItem('userSubjects');

    if (onboarded && savedName && savedClass && savedSubjects) {
      setUserName(savedName);
      setUserClass(parseInt(savedClass));
      setUserSubjects(JSON.parse(savedSubjects));
      setCurrentScreen('main');
    } else {
      const splashShown = sessionStorage.getItem('splashShown');
      if (splashShown) {
        setCurrentScreen('onboarding');
      }
    }
  }, []);

  // Handle splash complete
  const handleSplashComplete = () => {
    sessionStorage.setItem('splashShown', 'true');
    setCurrentScreen('onboarding');
  };

  // Handle onboarding complete
  const handleOnboardingComplete = (name: string, classLevel: number, subjects: string[]) => {
    setUserName(name);
    setUserClass(classLevel);
    setUserSubjects(subjects);
    localStorage.setItem('onboarded', 'true');
    localStorage.setItem('userName', name);
    localStorage.setItem('userClass', classLevel.toString());
    localStorage.setItem('userSubjects', JSON.stringify(subjects));
    setCurrentScreen('main');
    setCurrentView('dashboard');
  };

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
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  // Chat history (View State)
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

  // Follow-up state
  const [followUp, setFollowUp] = useState('');
  const [isFollowUpLoading, setIsFollowUpLoading] = useState(false);

  // Auto-scroll
  useEffect(() => {
    const thread = document.getElementById('answer-thread');
    if (thread) {
      thread.scrollTop = thread.scrollHeight;
    }
  }, [chatHistory, isFollowUpLoading, currentView]);

  // Load chat sessions on subject change
  useEffect(() => {
    if (!mounted) return;
    const key = `chat_sessions_${subject}`;
    const saved = localStorage.getItem(key);
    if (saved) {
      try {
        setSessions(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse sessions", e);
        setSessions([]);
      }
    } else {
      setSessions([]);
    }
    // New chat on subject switch
    setActiveSessionId(null);
    setChatHistory([]);
  }, [subject, mounted]);

  // Save chat sessions
  useEffect(() => {
    if (!mounted) return;
    if (sessions.length > 0) {
      localStorage.setItem(`chat_sessions_${subject}`, JSON.stringify(sessions));
    }
  }, [sessions, subject, mounted]);

  // Load session into view
  const loadSession = (session: ChatSession) => {
    setActiveSessionId(session.id);
    setChatHistory(session.messages);
  };

  // Start New Chat
  const startNewChat = () => {
    setActiveSessionId(null);
    setChatHistory([]);
    setQuestion('');
  };

  // Handle main question submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    setError(null);

    const userMsg: ChatMessage = { role: 'user', content: question.trim() };

    // Session Management
    let currentId = activeSessionId;
    let newSessions = [...sessions];

    if (!currentId) {
      // Create new session
      currentId = Date.now().toString();
      setActiveSessionId(currentId);
      const newSession: ChatSession = {
        id: currentId,
        title: question.trim().substring(0, 40) + (question.trim().length > 40 ? '...' : ''),
        timestamp: Date.now(),
        messages: [userMsg]
      };
      newSessions = [newSession, ...newSessions];
    } else {
      // Update existing
      const idx = newSessions.findIndex(s => s.id === currentId);
      if (idx !== -1) {
        newSessions[idx].messages = [...newSessions[idx].messages, userMsg];
        newSessions[idx].timestamp = Date.now();
        // Move to top
        const s = newSessions.splice(idx, 1)[0];
        newSessions.unshift(s);
      }
    }

    setSessions(newSessions);
    setChatHistory(prev => [...prev, userMsg]); // Update View directly for speed

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          subject,
          marks,
          history: newSessions.find(s => s.id === currentId)?.messages || [userMsg]
        }),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data: QueryResponse = await res.json();

      const modelMsg: ChatMessage = {
        role: 'model',
        content: data.answer,
        marks: data.marks,
        sources: data.sources,
        keywords: data.keywords
      };

      // Update Session with AI response
      setSessions(prev => {
        const up = [...prev];
        const idx = up.findIndex(s => s.id === currentId);
        if (idx !== -1) {
          up[idx].messages = [...up[idx].messages, modelMsg];
        }
        return up;
      });

      setChatHistory(prev => [...prev, modelMsg]);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle follow-up
  const handleFollowUp = async (e: FormEvent) => {
    e.preventDefault();
    if (!followUp.trim() || chatHistory.length === 0) return;

    setIsFollowUpLoading(true);
    setError(null);

    // Add user message immediately
    const userMsg: ChatMessage = { role: 'user', content: followUp.trim() };
    const updatedHistory = [...chatHistory, userMsg];
    setChatHistory(updatedHistory);
    setFollowUp('');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userMsg.content,
          subject,
          marks,
          history: updatedHistory.map(m => ({ role: m.role, content: m.content }))
        }),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data: QueryResponse = await res.json();

      setChatHistory(prev => [
        ...prev,
        {
          role: 'model',
          content: data.answer,
          marks: data.marks,
          sources: data.sources,
          keywords: data.keywords
        }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer');
    } finally {
      setIsFollowUpLoading(false);
    }
  };

  // Format answer text
  const formatAnswer = (text: string) => {
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/^• /gm, '<li>').replace(/(<li>.*?)(?=\n|$)/g, '$1</li>');
    formatted = formatted.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
    return `<p>${formatted}</p>`;
  };

  // Render message
  const renderMessage = (msg: ChatMessage, idx: number) => {
    if (msg.role === 'user') {
      return (
        <div key={idx} className="thread-user-message">
          <div className="user-avatar">👤</div>
          <div className="user-text">{msg.content}</div>
        </div>
      );
    }

    return (
      <div key={idx} className="thread-ai-message">
        <div className="answer-header" style={idx > 1 ? { marginTop: 0, paddingTop: 10, borderTop: 'none' } : {}}>
          {idx === 1 && <h2 className="answer-title">📖 Answer</h2>}
          {msg.marks && (
            <span className="answer-marks-badge">
              {msg.marks} Mark{msg.marks > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div className="answer-body">
          <div dangerouslySetInnerHTML={{ __html: formatAnswer(msg.content) }} />

          {msg.keywords && msg.keywords.length > 0 && (
            <div className="keywords-container">
              <p className="keywords-label">Key Terms:</p>
              <div className="keywords-list">
                {msg.keywords.map((kw, i) => (
                  <span key={i} className="keyword-tag">{kw}</span>
                ))}
              </div>
            </div>
          )}

          {msg.sources && msg.sources.length > 0 && (
            <div className="sources-container">
              <p className="sources-label">📚 Textbook References:</p>
              <div className="sources-list">
                {msg.sources.slice(0, 2).map((source, i) => (
                  <div key={i} className="source-card">
                    <div className="source-header">
                      <span className="source-badge">{source.source_type}</span>
                      <span className="source-meta">
                        {source.chapter ? `Chapter: ${source.chapter}` : ''}
                        {source.topic ? ` • ${source.topic}` : ''}
                      </span>
                    </div>
                    <div className="source-text">
                      "{source.text.substring(0, 90)}{source.text.length > 90 ? '...' : ''}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Navigation Logic
  const navigateToSubject = (subjName: string) => {
    setSubject(subjName);
    setCurrentView('chat');
    setChatHistory([]);
    setQuestion('');
  };

  if (!mounted) return null;
  if (currentScreen === 'splash') return <SplashScreen onComplete={handleSplashComplete} />;
  if (currentScreen === 'onboarding') return <OnboardingScreen onComplete={handleOnboardingComplete} />;

  return (
    <div className="app-container dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          📚 Stubby
        </div>
        <nav className="sidebar-nav">
          <button
            className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            <span className="nav-icon">🏠</span> Home
          </button>
          <button
            className={`nav-item ${currentView === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentView('chat')}
          >
            <span className="nav-icon">💬</span> Study Chat
          </button>
        </nav>

        <div className="sidebar-footer">
          <button onClick={toggleTheme} className="theme-toggle-sidebar">
            {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
          </button>
          <div className="user-profile">
            <div className="avatar-circle">{userName.charAt(0)}</div>
            <div className="user-info">
              <p className="user-name">{userName}</p>
              <p className="user-sub">Class {userClass}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="dashboard-main">
        {currentView === 'dashboard' ? (
          // DASHBOARD
          <div className="dashboard-content">
            <header className="dashboard-header">
              <h1>Hey {userName}, what do you wanna master?</h1>
              <p>Upload anything and get interactive notes, flashcards, quizzes, and more</p>
            </header>

            <div className="study-sets-section">
              <div className="section-header">
                <h2>All Study Sets</h2>
              </div>

              <div className="sets-grid">
                {SUBJECTS.map((s) => (
                  <div
                    key={s.id}
                    className="set-card"
                    onClick={() => navigateToSubject(s.id)}
                  >
                    <div className="set-card-header">
                      <h3>{s.label}</h3>
                      <button className="more-btn">•••</button>
                    </div>

                    <div className="set-stats">
                      <div className="stat-row">
                        <span className="stat-count red">15</span> Unfamiliar
                      </div>
                      <div className="stat-row">
                        <span className="stat-count yellow">5</span> Learning
                      </div>
                      <div className="stat-row">
                        <span className="stat-count green">2</span> Mastered
                      </div>
                    </div>

                    <div className="set-footer">
                      Start Studying →
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // CHAT (Study Mode)
          <div className="chat-view-container">
            <div className="chat-back-header">
              <button onClick={() => setCurrentView('dashboard')} className="back-btn">
                ← Back to Dashboard
              </button>
            </div>

            <div className="chat-layout">
              {/* Left Column: Input + History */}
              <div className="chat-left-column" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                {/* 1. Input Card */}
                <div className="card input-card">
                  <h2 className="card-header">
                    <span className="card-header-icon">✏️</span>
                    {subject} Study Chat
                  </h2>

                  <form onSubmit={handleSubmit}>
                    <div className="form-group">
                      <label className="form-label">Subject</label>
                      <select
                        className="form-select"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                      >
                        {SUBJECTS.map((s) => (
                          <option key={s.id} value={s.id}>{s.emoji} {s.label}</option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Marks</label>
                      <div className="marks-selector">
                        {MARKS_OPTIONS.map((m) => (
                          <button
                            key={m}
                            type="button"
                            className={`marks-pill ${marks === m ? 'active' : ''}`}
                            onClick={() => setMarks(m)}
                          >
                            <span>{m}M</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Question</label>
                      <textarea
                        className="form-textarea"
                        placeholder={`Ask a ${subject} question...`}
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        disabled={isLoading}
                      />
                    </div>

                    <button
                      type="submit"
                      className="btn btn-primary btn-full"
                      disabled={isLoading || !question.trim()}
                    >
                      {isLoading ? 'Thinking...' : 'Get Answer'}
                    </button>

                    {error && <div className="error-message">⚠️ {error}</div>}
                  </form>
                </div>

                {/* 2. History List (Sidebar) */}
                <div className="history-section" style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '12px', padding: '16px', border: '1px solid var(--color-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>PREVIOUS CHATS</h3>
                    <button
                      onClick={startNewChat}
                      style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '4px', background: 'var(--color-accent)', color: 'white', border: 'none', cursor: 'pointer' }}
                    >
                      + New
                    </button>
                  </div>

                  <div className="history-list" style={{ maxHeight: '300px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {sessions.length === 0 && <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>No history yet.</p>}
                    {sessions.map(s => (
                      <button
                        key={s.id}
                        onClick={() => loadSession(s)}
                        style={{
                          textAlign: 'left',
                          padding: '10px',
                          borderRadius: '8px',
                          border: '1px solid',
                          borderColor: activeSessionId === s.id ? 'var(--color-accent)' : 'transparent',
                          background: activeSessionId === s.id ? 'var(--color-accent-light)' : 'rgba(255,255,255,0.05)',
                          color: activeSessionId === s.id ? 'var(--color-accent)' : 'var(--color-text-primary)',
                          cursor: 'pointer',
                          transition: 'all 0.2s'
                        }}
                      >
                        <div style={{ fontSize: '13px', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.title}</div>
                        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                          {new Date(s.timestamp).toLocaleDateString()}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

              </div>

              {/* Right Column - Answer Display */}
              <div className="answer-container">
                <div className="answer-content" id="answer-thread">
                  {isLoading && chatHistory.length === 0 ? (
                    <div className="loading-container">
                      <div className="loading-spinner"></div>
                      <p className="loading-text">Generating your answer...</p>
                    </div>
                  ) : chatHistory.length > 0 ? (
                    <>
                      {chatHistory.map((msg, idx) => {
                        if (idx === 0) return null;
                        return renderMessage(msg, idx);
                      })}

                      {isFollowUpLoading && (
                        <div className="loading-container" style={{ minHeight: 100 }}>
                          <div className="loading-spinner"></div>
                        </div>
                      )}

                      <div className="followup-container">
                        <form onSubmit={handleFollowUp} className="followup-form">
                          <input
                            type="text"
                            className="followup-input"
                            placeholder="Ask a follow-up..."
                            value={followUp}
                            onChange={(e) => setFollowUp(e.target.value)}
                            disabled={isFollowUpLoading}
                          />
                          <button type="submit" className="followup-btn" disabled={!followUp.trim()}>→</button>
                        </form>
                      </div>
                    </>
                  ) : (
                    <div className="answer-empty">
                      <span className="answer-empty-icon">💡</span>
                      <p className="answer-empty-text">Start your {subject} session!</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
