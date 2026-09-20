import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Bot,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  CircleUserRound,
  Clock3,
  FileUp,
  GraduationCap,
  Home,
  MapPin,
  Menu,
  Network,
  Search,
  Send,
  Settings2,
  Sparkles,
  Target,
  UserRound,
  X,
} from "lucide-react";
import "./styles.css";

const API_BASE_URL = (
  import.meta.env.VITE_API_URL || "https://skillpath-ai-1jzi.onrender.com"
).replace(/\/+$/, "").replace(/\/api$/, "");
type Profile = {
  name: string;
  education: string;
  skills: string[];
  location: string;
  interests: string[];
  target_role: string;
  experience: string;
  resume_text?: string;
};
type Job = {
  id: string;
  title: string;
  company: string;
  location: string;
  work_mode: string;
  salary: string;
  required_skills: string[];
  preferred_skills: string[];
  score?: number;
  matched_skills?: string[];
  missing_skills?: string[];
  semantic_similarity?: number;
  domain?: string;
};
type Course = {
  id: string;
  title: string;
  provider: string;
  skills_taught: string[];
  duration: number;
  duration_unit: string;
  cost: number;
  currency: string;
  is_free: boolean;
  difficulty: string;
  url: string;
};
type Analysis = {
  id: string;
  profile: Profile;
  target_job: Job;
  matches: Job[];
  gap_analysis: {
    missing_required_skills: string[];
    missing_preferred_skills: string[];
    gaps: {
      skill: string;
      requirement: string;
      why: string;
      priority: string;
      next_step: string;
      resource: Course | null;
    }[];
    resources: Course[];
    total_weeks: number;
    total_cost: number;
    coverage_before: { covered: number; total: number };
    coverage_after: { covered: number; total: number };
    weekly_study_hours: number;
    roi_reasoning: string;
  };
  logs: { agent: string; message: string; status: string }[];
};

const demoProfile: Profile = {
  name: "Demo User",
  education: "B.E. Computer Science",
  skills: ["Python", "JavaScript", "HTML", "CSS", "SQL", "Git", "FastAPI"],
  location: "Bengaluru",
  interests: ["Web Development", "Backend Development", "AI"],
  target_role: "Full Stack Developer",
  experience: "0–2 years",
};
const emptyProfile: Profile = {
  name: "",
  education: "",
  skills: [],
  location: "",
  interests: [],
  target_role: "",
  experience: "",
  resume_text: "",
};
const parseListInput = (value: string): string[] => {
  if (!value || !value.trim()) return [];

  const pieces = value
    .split(",")
    .map((item) => item.trim().replace(/\s+/g, " "))
    .filter(Boolean);

  return pieces.length ? pieces : [value.trim().replace(/\s+/g, " ")];
};
const iconFor = (key: string) =>
  ({
    home: <Home size={17} />,
    profile: <UserRound size={17} />,
    jobs: <BriefcaseBusiness size={17} />,
    analysis: <Target size={17} />,
    learning: <GraduationCap size={17} />,
    ai: <Sparkles size={17} />,
    activity: <Activity size={17} />,
  })[key] || <CircleUserRound size={17} />;

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const headers =
    options?.body instanceof FormData
      ? { ...(options?.headers || {}) }
      : { "Content-Type": "application/json", ...(options?.headers || {}) };
  const res = await fetch(`${API_BASE_URL}/api${path}`, { ...options, headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function App() {
  const [authed, setAuthed] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [toast, setToast] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const page = location.pathname.replace("/", "") || "home";
  const notify = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(""), 2600);
  };
  const login = (name?: string) => {
    setAuthed(true);
    setProfile((p) => ({ ...p, name: name || p.name }));
    navigate("/home");
  };
  const updateProfile = (nextProfile: Profile) => {
    setProfile(nextProfile);
    setAnalysis(null);
    localStorage.removeItem("skillpath-selected-job");
  };
  const runAnalysis = async (jobId?: string) => {
    try {
      const r = await api<Analysis>("/analyze", {
        method: "POST",
        body: JSON.stringify({ profile, ...(jobId ? { job_id: jobId } : {}) }),
      });
      setAnalysis(r);
      localStorage.removeItem("skillpath-selected-job");
      notify("Agent workflow complete");
      navigate("/analysis");
    } catch {
      notify("Unable to analyze this job. Check that the backend is running.");
    }
  };
  if (!authed)
    return (
      <Auth
        mode={authMode}
        setMode={setAuthMode}
        onLogin={login}
        onDemo={() => {
          setProfile(demoProfile);
          setAnalysis(null);
          localStorage.removeItem("skillpath-selected-job");
          login("Demo User");
        }}
        notify={notify}
      />
    );
  const go = (p: string) => {
    navigate(`/${p}`);
    setMobileOpen(false);
  };
  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? "open" : ""}`}>
        <div className="brand">
          <div className="logo">
            <Sparkles size={19} />
          </div>
          <span>SkillPath AI</span>
          <button className="mobile-close" onClick={() => setMobileOpen(false)}>
            <X size={18} />
          </button>
        </div>
        <nav className="nav">
          {[
            ["home", "Home"],
            ["profile", "My Profile"],
            ["jobs", "Find Jobs"],
            ["analysis", "Skill Analysis"],
            ["learning", "Learning Path"],
            ["ai", "AI Assistant"],
            ["activity", "Agent Activity"],
          ].map(([key, label]) => (
            <button
              key={key}
              className={page === key ? "active" : ""}
              onClick={() => go(key)}
            >
              {iconFor(key)}
              <label>{label}</label>
            </button>
          ))}
        </nav>
        <div className="quote">
          <b>YOUR CAREER, ONE STEP AT A TIME</b>
          <p>
            “A small step in learning today, a giant leap for your tomorrow.”
          </p>
          <small>Keep building. Keep growing.</small>
        </div>
      </aside>
      <main className="main">
        <header className="top">
          <button className="menu-btn" onClick={() => setMobileOpen(true)}>
            <Menu size={20} />
          </button>
          <div className="search">
            <Search size={15} /> <span>Search jobs, skills, or courses...</span>
            <kbd>Ctrl K</kbd>
          </div>
          <div className="topright">
            <span className="hello">
              Hello, <b>{profile.name || "User"}</b> 👋
            </span>
            <div className="avatar">{(profile.name || "U")[0]}</div>
          </div>
        </header>
        <div className="content">
          {page === "home" && (
            <HomePage profile={profile} go={go} analysis={analysis} />
          )}{" "}
          {page === "profile" && (
            <ProfilePage
              profile={profile}
              setProfile={updateProfile}
              onAnalyze={() => runAnalysis()}
            />
          )}{" "}
          {page === "jobs" && (
            <JobsPage profile={profile} go={go} onAnalyze={runAnalysis} />
          )}{" "}
          {page === "analysis" && (
            <AnalysisPage
              analysis={analysis}
              profile={profile}
              run={runAnalysis}
              go={go}
            />
          )}{" "}
          {page === "learning" && <LearningPage analysis={analysis} />}{" "}
          {page === "ai" && (
            <AIPage profile={profile} analysis={analysis} go={go} notify={notify} />
          )}{" "}
          {page === "activity" && <ActivityPage analysis={analysis} />}
        </div>
      </main>
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

function Auth({
  mode,
  setMode,
  onLogin,
  onDemo,
  notify,
}: {
  mode: "login" | "signup";
  setMode: (x: "login" | "signup") => void;
  onLogin: (name?: string) => void;
  onDemo: () => void;
  notify: (x: string) => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  return (
    <div className="landing-shell">
      <div className="landing-bg" />
      <div className="landing-content">
        <div className="landing-brand">
          <div className="logo">
            <Sparkles size={19} />
          </div>
          <span>SkillPath AI</span>
        </div>
        <div className="landing-grid">
          <div className="landing-copy">
            <div className="eyebrow">CAREER INTELLIGENCE FOR EVERY STEP</div>
            <h1>Turn your skills into a smarter career path.</h1>
            <p>
              Track your strengths, discover your missing skills, and unlock the
              right opportunities with AI-powered guidance.
            </p>
            <div className="landing-stats">
              <div>
                <strong>84%</strong>
                <span>Profile Match</span>
              </div>
              <div>
                <strong>40+</strong>
                <span>Curated roles</span>
              </div>
              <div>
                <strong>6W</strong>
                <span>Suggested path</span>
              </div>
            </div>
          </div>
          <div className="auth-card">
            <div className="auth-header">
              <div>
                <p className="mini-label">Welcome back</p>
                <h2>{mode === "login" ? "Login" : "Create account"}</h2>
              </div>
              <span className="status-dot">● Active</span>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (mode === "signup") {
                  if (password.length < 6) {
                    notify("Password must be 6+ characters");
                    return;
                  }
                  setMode("login");
                  notify("Account created, please log in.");
                  return;
                }
                onLogin(email.split("@")[0] || "User");
              }}
            >
              {mode === "signup" && (
                <>
                  <label className="field-label">Full name</label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your name"
                    required
                  />
                </>
              )}
              <label className="field-label">Email address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
              <label className="field-label">
                {mode === "signup" ? "Create password" : "Password"}
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
              <button className="btn primary landing-btn">
                {mode === "signup" ? "Create my account" : "Sign in"}
              </button>
            </form>
            <button className="demo-btn" onClick={onDemo}>
              <Sparkles size={14} /> Try Demo Profile
            </button>
            <p className="signup-text">
              {mode === "login" ? "New here?" : "Already have an account?"}{" "}
              <a onClick={() => setMode(mode === "login" ? "signup" : "login")}>
                {mode === "login" ? "Create an account" : "Log in"}
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="section">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
function HomePage({
  profile,
  go,
  analysis,
}: {
  profile: Profile;
  go: (x: string) => void;
  analysis: Analysis | null;
}) {
  return (
    <>
      <div className="hero">
        <div className="hero-grid" />
        <div className="hero-copy">
          <div className="eyebrow">AI-POWERED CAREER NAVIGATION</div>
          <h1>
            Your Career Journey
            <br />
            <span className="fade-text">Starts Here.</span>
          </h1>
          <p>
            Discover relevant jobs, understand exactly which skills you're
            missing, and get a personalized learning path — all through one
            intelligent career assistant.
          </p>
          <button className="btn primary" onClick={() => go("profile")}>
            Start Analysis <ArrowRight size={14} />
          </button>
          <button className="btn secondary" onClick={() => go("ai")}>
            Watch AI Demo <Sparkles size={14} />
          </button>
        </div>
        <div className="hero-visual">
          <div className="mount" />
          <div className="person" />
          <div className="sign">
            <span>SKILLS</span>
            <span>OPPORTUNITIES</span>
            <span>GROWTH</span>
            <span>SUCCESS</span>
          </div>
        </div>
      </div>
      <div className="stats">
        <Stat
          label="Curated Job Postings"
          value="40+"
          icon={<BriefcaseBusiness size={18} />}
        />
        <Stat
          label="Learning Resources"
          value="30"
          icon={<GraduationCap size={18} />}
        />
        <Stat label="In-Demand Skills" value="28" icon={<Target size={18} />} />
        <Stat
          label="Profile Match"
          value={
            analysis?.target_job?.score
              ? `${analysis.target_job.score}%`
              : "72%"
          }
          icon={<Sparkles size={18} />}
        />
      </div>
      <Section
        title="Your Career Snapshot"
        subtitle="A quick view of where you stand today."
        action={
          <a onClick={() => go("profile")}>
            Edit Profile <ArrowRight size={12} />
          </a>
        }
      />
      <div className="split">
        <div className="card profile">
          <div className="profile-head">
            <div>
              <div className="profile-name">{profile.name}</div>
              <div className="profile-meta">
                {profile.education}
                <br />
                <MapPin size={12} /> {profile.location}
              </div>
            </div>
            <button
              className="btn secondary small"
              onClick={() => go("profile")}
            >
              Edit
            </button>
          </div>
          <div className="chips">
            {profile.skills.map((s) => (
              <span className="chip" key={s}>
                {s}
              </span>
            ))}
            <span className="chip">+ Add Skill</span>
          </div>
          <div className="profile-facts">
            <span>
              <Clock3 size={13} />
              <b>{profile.experience || "0–2 years"}</b>Experience
            </span>
            <span>
              <Target size={13} />
              <b>{profile.interests[0] || "Web Development"}</b>Interest
            </span>
            <span>
              <MapPin size={13} />
              <b>{profile.location}</b>Preferred
            </span>
          </div>
        </div>
        <div className="card match">
          <div className="match-head">
            <b>Skill Match Overview</b>
            <a onClick={() => go("analysis")}>
              View details <ArrowRight size={12} />
            </a>
          </div>
          <div className="circle">
            <span>
              {analysis?.gap_analysis
                ? Math.round(
                    (analysis.gap_analysis.coverage_before.covered /
                      analysis.gap_analysis.coverage_before.total) *
                      100,
                  )
                : 72}
              %
            </span>
          </div>
          <div className="match-row">
            <span>
              ● Matched{" "}
              <b>{analysis?.gap_analysis?.coverage_before.covered || 8}</b>
            </span>
            <span>
              ● Missing{" "}
              <b>
                {analysis?.gap_analysis?.missing_required_skills.length || 4}
              </b>
            </span>
            <span>
              ● Partial <b>3</b>
            </span>
          </div>
        </div>
      </div>
      <Section
        title="Top Job Matches for You"
        subtitle="Opportunities aligned with your current profile."
        action={
          <a onClick={() => go("jobs")}>
            See All <ArrowRight size={12} />
          </a>
        }
      />
      <div className="jobs">
        {(analysis?.matches || []).slice(0, 3).map((j) => (
          <JobCard job={j} key={j.id} go={go} />
        ))}
        {!analysis && (
          <div className="empty-card">
            Run your first analysis to see personalized roles.
          </div>
        )}
      </div>
    </>
  );
}
function Stat({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="card stat">
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
      </div>
      <div className="icon">{icon}</div>
    </div>
  );
}
function ProfilePage({
  profile,
  setProfile,
  onAnalyze,
}: {
  profile: Profile;
  setProfile: (p: Profile) => void;
  onAnalyze: () => void;
}) {
  const update = (key: keyof Profile, value: any) =>
    setProfile({ ...profile, [key]: value });
  return (
    <>
      <Section
        title="Build Your Profile"
        subtitle="Tell the agents about your current skills and goals."
      />
      <div className="card form">
        <div className="formgrid">
          <Field
            label="Education"
            value={profile.education}
            onChange={(v) => update("education", v)}
          />
          <Field
            label="Experience"
            value={profile.experience}
            onChange={(v) => update("experience", v)}
            select
          />
          <Field
            label="Preferred location"
            value={profile.location}
            onChange={(v) => update("location", v)}
          />
          <ListTagField
            label="Career interest"
            items={profile.interests}
            onChange={(v) => update("interests", v)}
          />
          <Field
            label="Target role"
            value={profile.target_role}
            onChange={(v) => update("target_role", v)}
          />
          <ListTagField
            label="Skills"
            items={profile.skills}
            onChange={(v) => update("skills", v)}
          />
          <div className="field full">
            <label>Resume upload</label>
            <div className="upload">
              <FileUp size={18} />
              <span>Drop a PDF/DOCX resume or browse</span>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  try {
                    const body = new FormData();
                    body.append("file", file);
                    const result = await api<{ profile: Profile }>(
                      "/profile/resume",
                      { method: "POST", body },
                    );
                    setProfile(result.profile);
                  } catch {
                    // The analysis action remains available if extraction fails.
                  }
                }}
              />
            </div>
          </div>
          <Field
            label="Describe your skills"
            value={profile.resume_text || ""}
            onChange={(v) => update("resume_text", v)}
            textarea
          />
        </div>
        <button className="btn primary" onClick={onAnalyze}>
          Analyze My Career Fit <Sparkles size={14} />
        </button>
      </div>
    </>
  );
}
function ListTagField({
  label,
  items,
  onChange,
}: {
  label: string;
  items: string[];
  onChange: (v: string[]) => void;
}) {
  const [draft, setDraft] = useState("");

  const commitCurrent = () => {
    const nextTags = parseListInput(draft);
    if (!nextTags.length) return;

    const merged = [...new Set([...items, ...nextTags])];
    onChange(merged);
    setDraft("");
  };

  return (
    <div className="field full">
      <label>{label}</label>
      <input
        value={draft}
        placeholder={
          items.length ? "Add another item..." : "Type and press comma or Enter..."
        }
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "," || e.key === "Enter") {
            e.preventDefault();
            commitCurrent();
          }

          if (e.key === "Backspace" && !draft && items.length) {
            e.preventDefault();
            onChange(items.slice(0, -1));
          }
        }}
      />
      {items.length > 0 && (
        <div className="tags" style={{ marginTop: 10 }}>
          {items.map((item) => (
            <span className="tag" key={item}>
              {item}
              <button
                type="button"
                aria-label={`Remove ${item}`}
                title={`Remove ${item}`}
                onClick={() => onChange(items.filter((value) => value !== item))}
                style={{ border: 0, background: "transparent", color: "inherit", padding: 0, marginLeft: 4, lineHeight: 1 }}
              >
                <X size={10} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  select,
  textarea,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  select?: boolean;
  textarea?: boolean;
}) {
  return (
    <div className={`field ${textarea ? "full" : ""}`}>
      <label>{label}</label>
      {textarea ? (
        <textarea value={value} onChange={(e) => onChange(e.target.value)} />
      ) : select ? (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option>Student / Fresher</option>
          <option>0–2 years</option>
          <option>2–5 years</option>
          <option>5+ years</option>
        </select>
      ) : (
        <input value={value} onChange={(e) => onChange(e.target.value)} />
      )}
    </div>
  );
}
function JobsPage({
  profile,
  go,
  onAnalyze,
}: {
  profile: Profile;
  go: (x: string) => void;
  onAnalyze: (jobId?: string) => Promise<void>;
}) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    api<Analysis>("/analyze", {
      method: "POST",
      body: JSON.stringify({ profile }),
    })
      .then((result) => {
        setJobs(result.matches || []);
      })
      .catch(() => {
        setJobs([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [
    profile.skills,
    profile.interests,
    profile.education,
    profile.location,
    profile.target_role,
    profile.experience,
    profile.resume_text,
  ]);

  const shown = jobs.filter((j) =>
    JSON.stringify(j).toLowerCase().includes(query.toLowerCase())
  );

  return (
    <>
      <Section
        title="Find Jobs"
        subtitle="Explore jobs matched to your current career profile."
        action={<span className="eyebrow">PERSONALIZED MATCHES</span>}
      />

      <div className="filterbar">
        <div className="input-icon">
          <Search size={15} />
          <input
            placeholder="Filter by title, skill, or company"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <span>{shown.length} matched roles</span>
      </div>

      {loading ? (
        <div className="empty-card">
          Finding jobs for {profile.target_role || "your career profile"}...
        </div>
      ) : shown.length === 0 ? (
        <div className="empty-card">
          No matching jobs found for your current profile.
        </div>
      ) : (
        <div className="jobs">
          {shown.map((j) => (
            <JobCard job={j} key={j.id} go={go} onAnalyze={onAnalyze} />
          ))}
        </div>
      )}
    </>
  );
}
function JobCard({ job, go, onAnalyze }: { job: Job; go: (x: string) => void; onAnalyze?: (jobId?: string) => Promise<void> }) {
  return (
    <div className="card job">
      <div className="jobtop">
        <div>
          <div className="jobtitle">{job.title}</div>
          <div className="company">
            {job.company} · {job.location}
          </div>
        </div>
        {job.score !== undefined && <span className="percent">{job.score}%</span>}
      </div>
      <div className="tags">
        {job.required_skills.slice(0, 5).map((s) => (
          <span className="tag" key={s}>
            {s}
          </span>
        ))}
      </div>
      <div className="job-meta">
        <span>{job.salary}</span>
        <span>{job.work_mode}</span>
      </div>
      <div className="jobfoot">
        <span>
          {job.matched_skills?.length || 0} matched ·{" "}
          {job.missing_skills?.length || 0} gaps
        </span>
        <button
          onClick={() => {
            if (onAnalyze) {
              void onAnalyze(job.id);
              return;
            }
            localStorage.setItem("skillpath-selected-job", job.id);
            go("analysis");
          }}
        >
          Analyze Gap <ArrowRight size={12} />
        </button>
      </div>
    </div>
  );
}
function AnalysisPage({
  analysis,
  profile,
  run,
  go,
}: {
  analysis: Analysis | null;
  profile: Profile;
  run: (id?: string) => void;
  go: (x: string) => void;
}) {
  useEffect(() => {
    const selectedJob = localStorage.getItem("skillpath-selected-job");
    if (selectedJob && analysis?.target_job.id !== selectedJob) run(selectedJob);
  }, [analysis]);
  if (!analysis)
    return (
      <Empty
        title="No analysis yet"
        text="Run the profile workflow to see your real agent result."
        action={
          <button className="btn primary" onClick={() => go("profile")}>
            Build Profile
          </button>
        }
      />
    );
  const g = analysis.gap_analysis;
  return (
    <>
      <Section
        title="Skill Gap Analysis"
        subtitle={`${analysis.target_job.title} · ${analysis.target_job.company} · ${analysis.target_job.location}`}
        action={<span className="eyebrow">AGENT RESULT</span>}
      />
      <div className="analysis">
        <div className="card">
          <div className="analysis-head">
            <div>
              <small>Current match</small>
              <div className="big">{analysis.target_job.score}%</div>
            </div>
            <span className="percent">STRONG FIT</span>
          </div>
          <div className="bar">
            <i style={{ width: `${analysis.target_job.score}%` }} />
          </div>
          <div className="coverage">
            <span>
              Before learning{" "}
              <b>
                {g.coverage_before.covered}/{g.coverage_before.total}
              </b>
            </span>
            <span>
              After learning{" "}
              <b>
                {g.coverage_after.covered}/{g.coverage_after.total}
              </b>
            </span>
          </div>
          {g.gaps.map((x) => (
            <div className="gap" key={x.skill}>
              <span>
                <b>{x.skill}</b>
                <small>
                  {x.requirement} · {x.why}
                </small>
              </span>
              <span className={`pill ${x.priority === "High" ? "no" : "yes"}`}>
                {x.priority}
              </span>
            </div>
          ))}
        </div>
        <div className="card">
          <h3>Why this job matches</h3>
          <p className="muted">
            Matched skills:{" "}
            {analysis.target_job.matched_skills?.join(", ") || "—"}. The
            priority gaps below are grounded in the job requirements and
            selected resources.
          </p>
          <div className="trace">
            {analysis.logs.map((l) => (
              <div key={l.agent}>
                <Check size={13} />
                <span>
                  <b>{l.agent}</b>
                  <small>{l.message}</small>
                </span>
              </div>
            ))}
          </div>
          <button className="btn primary" onClick={() => go("learning")}>
            Build Learning Path <ArrowRight size={14} />
          </button>
        </div>
      </div>
      <Section
        title="Target another role"
        subtitle="Re-run the same profile against a different opportunity."
      />
      <div className="jobs mini-jobs">
        {analysis.matches.slice(0, 6).map((j) => (
          <JobCard key={j.id} job={j} go={go} />
        ))}
      </div>
    </>
  );
}
function LearningPage({ analysis }: { analysis: Analysis | null }) {
  const [free, setFree] = useState(false);
  const [roadmap, setRoadmap] = useState<any>(analysis?.gap_analysis);
  useEffect(() => {
    if (analysis)
      api<any>(`/roadmap/${analysis.id}?free_only=${free}`)
        .then(setRoadmap)
        .catch(() => {});
  }, [analysis, free]);
  if (!analysis)
    return (
      <Empty
        title="No roadmap yet"
        text="Analyze a profile to calculate time-to-ready."
      />
    );
  const g = roadmap || analysis.gap_analysis;
  return (
    <>
      <Section
        title="Your Learning Path"
        subtitle={`A focused plan for ${analysis.target_job.title}.`}
        action={
          <div className="toggle">
            <button
              className={!free ? "selected" : ""}
              onClick={() => setFree(false)}
            >
              ALL
            </button>
            <button
              className={free ? "selected" : ""}
              onClick={() => setFree(true)}
            >
              FREE ONLY
            </button>
          </div>
        }
      />
      <div className="roadmap-summary">
        <div>
          <small>TIME TO READY</small>
          <strong>{g.total_weeks} weeks</strong>
          <p>{g.weekly_study_hours} study hours/week</p>
        </div>
        <div>
          <small>ESTIMATED COST</small>
          <strong className="green">₹{g.total_cost.toLocaleString()}</strong>
          <p>{free ? "Fully free path" : "Free + paid options"}</p>
        </div>
        <div>
          <small>SKILLS CLOSED</small>
          <strong>
            {g.coverage_after.covered - g.coverage_before.covered}
          </strong>
          <p>required gaps addressed</p>
        </div>
      </div>
      <div className="card roadmap-card">
        <div className="roi">
          <Sparkles size={17} />
          <span>{g.roi_reasoning}</span>
        </div>
        {g.resources.map((c: Course, i: number) => (
          <div className="course" key={c.id}>
            <div className="course-index">0{i + 1}</div>
            <div className="course-main">
              <h4>{c.title}</h4>
              <p>
                {c.provider} · {c.skills_taught.join(" · ")}
              </p>
              <span className="tag">{c.difficulty}</span>
            </div>
            <div className="course-side">
              <b>
                {c.duration} {c.duration_unit}
              </b>
              <span>{c.is_free ? "Free" : `₹${c.cost.toLocaleString()}`}</span>
              <a href={c.url} target="_blank">
                View resource <ArrowRight size={12} />
              </a>
            </div>
          </div>
        ))}
        {!g.resources.length && (
          <div className="empty-card">
            No matching resources for the selected filter.
          </div>
        )}
      </div>
    </>
  );
}
function AIPage({
  profile,
  analysis,
  go,
  notify,
}: {
  profile: Profile;
  analysis: Analysis | null;
  go: (x: string) => void;
  notify: (x: string) => void;
}) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>([
    "Hi! 👋 I can help you find jobs, analyze your current skills, identify gaps, and create a personalized learning path.",
  ]);
  const send = async () => {
    if (!input.trim()) return;
    const question = input;
    setMessages((m) => [...m, `You asked: ${question}`]);
    setInput("");
    try {
      const result = await api<{ reply: string }>("/assistant", {
        method: "POST",
        body: JSON.stringify({ message: question, profile, analysis_id: analysis?.id }),
      });
      setMessages((m) => [...m, result.reply]);
    } catch {
      setMessages((m) => [...m, "The assistant is unavailable right now. Try the deterministic workflow from your profile."]);
    }
  };
  return (
    <>
      <Section
        title="AI Career Assistant"
        subtitle="Your conversational entry point into the agent workflow."
      />
      <div className="ai-grid">
        <div className="dark-panel chat">
          <div className="ai-title">
            <div>
              <b>SkillPath AI</b>
              <div className="muted">Your career co-pilot</div>
            </div>
            <span className="online">● Online</span>
          </div>
          <div className="messages">
            {messages.map((m, i) => (
              <div
                className={`bubble ${i % 2 ? "user" : ""}`}
                key={`${m}-${i}`}
              >
                {m}
              </div>
            ))}
          </div>
          <div className="quick">
            <button onClick={() => go("jobs")}>
              <Search size={13} /> Find suitable jobs
            </button>
            <button onClick={() => go("analysis")}>
              <Target size={13} /> Analyze my skills
            </button>
            <button onClick={() => go("learning")}>
              <GraduationCap size={13} /> Suggest learning path
            </button>
            <button onClick={() => notify("Resume analysis agent started")}>
              <FileUp size={13} /> Improve my resume
            </button>
          </div>
          <div className="input-dark">
            <input
              placeholder="What would you like to do today?"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
            />
            <button onClick={send}>
              <Send size={14} />
            </button>
          </div>
        </div>
        <div className="dark-panel">
          <h3>Your Learning Journey</h3>
          <div className="journey">
            {[
              "Complete Profile",
              "Get Job Matches",
              "Analyze Skill Gaps",
              "Get Learning Plan",
              "Become Job Ready",
            ].map((x, i) => (
              <div
                className={`step ${i < 2 ? "done" : i === 2 ? "current" : ""}`}
                key={x}
              >
                <span className="step-dot">
                  {i < 2 ? <Check size={10} /> : i + 1}
                </span>
                <div>
                  <b>{x}</b>
                  <p>
                    {
                      [
                        "Tell us about your skills and goals",
                        "Find relevant opportunities",
                        "Discover missing skills",
                        "Personalized courses and resources",
                        "Track progress toward your goal",
                      ][i]
                    }
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
function ActivityPage({ analysis }: { analysis: Analysis | null }) {
  const [logs, setLogs] = useState(analysis?.logs || []);
  useEffect(() => {
    if (!analysis) return;
    api<{ logs: Analysis["logs"] }>(`/agent-logs/${analysis.id}`)
      .then((result) => setLogs(result.logs))
      .catch(() => setLogs(analysis.logs));
  }, [analysis]);
  return (
    <>
      <Section
        title="Agent Activity"
        subtitle="Execution logs from your latest backend workflow."
      />
      <div className="card activity-list">
        {analysis ? (
          logs.map((l) => (
            <div className="activity-row" key={l.agent}>
              <span className="activity-check">
                <Check size={14} />
              </span>
              <div>
                <b>{l.agent}</b>
                <p>{l.message}</p>
              </div>
              <small>{l.status}</small>
            </div>
          ))
        ) : (
          <Empty
            title="No run yet"
            text="The activity feed will show actual LangGraph workflow events after analysis."
          />
        )}
      </div>
    </>
  );
}
function Empty({
  title,
  text,
  action,
}: {
  title: string;
  text: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty-card large">
      <Network size={28} />
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
