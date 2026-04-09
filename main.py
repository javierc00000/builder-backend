from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import re

BACKEND_NAME = "builder-backend"
BACKEND_VERSION = "idea-orchestration-v1"

app = FastAPI(title="Builder Backend - Auth System Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://builder-frontend.javierc00000.workers.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "status": "ok",
        "service": BACKEND_NAME,
        "version": BACKEND_VERSION,
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": BACKEND_NAME,
        "version": BACKEND_VERSION,
    }


class ApplianceItem(BaseModel):
    name: str = ""
    watts: float = 0
    hours: float = 0


class BatteryPlanRequest(BaseModel):
    appliances: List[ApplianceItem] = Field(default_factory=list)
    battery_voltage: float = 12
    autonomy_days: float = 1
    sun_hours: float = 4
    system_loss: float = 0.2


@app.post("/battery-plan")
def battery_plan(payload: BatteryPlanRequest):
    daily_wh = sum(max(item.watts, 0) * max(item.hours, 0) for item in payload.appliances)
    adjusted_daily_wh = daily_wh * (1 + max(payload.system_loss, 0))
    battery_ah = round((adjusted_daily_wh * max(payload.autonomy_days, 1)) / max(payload.battery_voltage, 1), 1)
    solar_watts = round(adjusted_daily_wh / max(payload.sun_hours, 1), 1)
    return {
        "daily_wh": round(daily_wh, 1),
        "adjusted_daily_wh": round(adjusted_daily_wh, 1),
        "battery_ah": battery_ah,
        "solar_watts": solar_watts,
        "summary": f"For this setup, plan for about {battery_ah}Ah of battery and {solar_watts}W of solar.",
    }


class MutateRequest(BaseModel):
    prompt: str
    current_layout: Dict[str, Any] = Field(default_factory=dict)
    active_modules: List[str] = Field(default_factory=list)
    feature_state: Dict[str, Any] = Field(default_factory=dict)
    systems: List[str] = Field(default_factory=list)
    complexity: str = "mvp"
    architecture: Dict[str, Any] = Field(default_factory=dict)
    current_files: List[Dict[str, Any]] = Field(default_factory=list)
    protected_systems: List[str] = Field(default_factory=list)
    mutation_mode: str = "safe"


class GenerateCodeRequest(BaseModel):
    prompt: str
    app_type: str = ""
    builder_mode: str = ""
    style: str = "dark glass"
    routes: List[Dict[str, Any]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    systems: List[str] = Field(default_factory=list)
    complexity: str = "mvp"
    architecture: Dict[str, Any] = Field(default_factory=dict)
    persistence: str = ""


# ---------- inference ----------
def infer_app_type(prompt: str) -> str:
    p = prompt.lower()
    if re.search(r"(admin|dashboard|crm|analytics|panel|saas)", p):
        return "admin panel"
    if re.search(r"(assistant|chat|copilot|agent|support bot)", p):
        return "assistant app"
    if re.search(r"(content|editor|blog|cms|writer|studio)", p):
        return "content app"
    return "tool app"


def infer_builder_mode(prompt: str) -> str:
    p = prompt.lower()
    if re.search(r"(battery|solar|power|inverter|camping)", p):
        return "battery-planner"
    if re.search(r"(dashboard|crm|analytics|saas)", p):
        return "dashboard-builder"
    if re.search(r"(landing|marketing|website)", p):
        return "site-builder"
    if re.search(r"(content|editor|blog|cms)", p):
        return "content-builder"
    return "general-builder"


def infer_summary_style(prompt: str) -> str:
    p = prompt.lower()
    if re.search(r"(detail|deeper|full|complete|advanced)", p):
        return "detailed"
    if re.search(r"(simple|quick|fast|short)", p):
        return "concise"
    return "balanced"


def infer_systems(prompt: str, app_type: str, requested: List[str]) -> List[str]:
    detected = set(s.lower() for s in requested)
    p = prompt.lower()

    if app_type in {"admin panel", "assistant app", "content app", "tool app"}:
        detected.add("dashboard")

    if re.search(r"(auth|login|register|signin|sign in|signup|sign up|account|user)", p):
        detected.add("auth")
    if re.search(r"(save|saved|history|database|db|records|storage|folders|reports)", p):
        detected.add("storage")
    if re.search(r"(billing|stripe|subscription|paywall|pro plan|membership)", p):
        detected.add("billing")
    if re.search(r"(ai|scan|diagnostic|chat|assistant|vision|openai)", p):
        detected.add("ai-tools")
    if re.search(r"(settings|profile|preferences)", p):
        detected.add("settings")

    if app_type == "admin panel":
        detected.update({"dashboard", "settings"})
    if app_type == "assistant app":
        detected.update({"ai-tools", "settings"})

    return sorted(detected)


def infer_persistence(prompt: str, systems: List[str], complexity: str, explicit: str) -> str:
    if explicit:
        return explicit.lower()
    p = prompt.lower()
    if "billing" in systems or re.search(r"(supabase|cloud|multi-user|saas)", p):
        return "supabase"
    if "auth" in systems or "storage" in systems or complexity.lower() in {"mvp", "product"}:
        return "sqlite"
    return "localstorage"


# ---------- layout / mutate helpers ----------
def recommend_modules(prompt: str, app_type: str, systems: List[str]) -> List[str]:
    p = prompt.lower()
    modules = {
        "results_summary",
        "save_results",
        "status_panel",
        "active_features_panel",
        "quick_actions",
        "live_preview",
    }
    if app_type == "admin panel":
        modules.update({"dashboard_shell", "sidebar_navigation", "split_workspace"})
    if app_type == "assistant app":
        modules.update({"split_workspace", "notes_panel"})
    if app_type == "content app":
        modules.update({"notes_panel", "split_workspace"})
    if app_type == "tool app":
        modules.update({"split_workspace"})
    if re.search(r"(battery|solar|power|calculator|tool)", p):
        modules.add("calculator_engine")
    if "auth" in systems:
        modules.add("auth_guard")
    if "storage" in systems:
        modules.add("data_manager")
    if "billing" in systems:
        modules.add("billing_panel")
    if "ai-tools" in systems:
        modules.add("ai_toolrail")
    return sorted(modules)


def build_layout(prompt: str, current_layout: Dict[str, Any]) -> Dict[str, Any]:
    layout = {
        "mode": current_layout.get("mode", "workspace"),
        "shell": current_layout.get("shell", "classic"),
        "sidebar": current_layout.get("sidebar", False),
        "split": current_layout.get("split", False),
        "topbar": current_layout.get("topbar", True),
        "inspector": current_layout.get("inspector", False),
        "cards": current_layout.get("cards", True),
        "dense": current_layout.get("dense", False),
        "previewStyle": current_layout.get("previewStyle", "wireframe"),
    }
    p = prompt.lower()
    if re.search(r"(dashboard|crm|saas)", p):
        layout.update({
            "mode": "dashboard",
            "shell": "dashboard",
            "sidebar": True,
            "split": True,
            "inspector": True,
            "previewStyle": "dashboard",
        })
    if re.search(r"(assistant|copilot|agent|chat)", p):
        layout.update({"split": True, "inspector": True})
    if re.search(r"(content|editor|writer|studio)", p):
        layout.update({"split": True, "inspector": True})
    if re.search(r"(dense|compact)", p):
        layout["dense"] = True
    if re.search(r"(spacious|comfortable|relaxed)", p):
        layout["dense"] = False
    return layout


def build_file_tree(app_type: str, builder_mode: str, prompt: str, systems: List[str], persistence: str) -> List[Dict[str, Any]]:
    base = [
        {"path": "frontend/src/App.jsx", "kind": "file", "role": "root app"},
        {"path": "frontend/src/main.jsx", "kind": "file", "role": "entry"},
        {"path": "frontend/src/styles/app.css", "kind": "file", "role": "global styles"},
        {"path": "frontend/src/components", "kind": "folder", "role": "ui components"},
        {"path": "frontend/src/pages", "kind": "folder", "role": "pages"},
        {"path": "frontend/src/lib", "kind": "folder", "role": "helpers"},
        {"path": "backend/main.py", "kind": "file", "role": "generated backend"},
    ]
    if "auth" in systems:
        base += [
            {"path": "frontend/src/pages/LoginPage.jsx", "kind": "file", "role": "login page"},
            {"path": "frontend/src/pages/RegisterPage.jsx", "kind": "file", "role": "register page"},
            {"path": "frontend/src/lib/auth.js", "kind": "file", "role": "auth client"},
            {"path": "frontend/src/components/ProtectedRoute.jsx", "kind": "file", "role": "route protection"},
            {"path": "backend/auth.py", "kind": "file", "role": "auth api"},
        ]
    if persistence == "sqlite":
        base += [
            {"path": "backend/database.py", "kind": "file", "role": "sqlite helpers"},
            {"path": "backend/data_store.py", "kind": "file", "role": "storage layer"},
        ]
    if persistence == "supabase":
        base += [{"path": "backend/supabase_schema.sql", "kind": "file", "role": "cloud schema"}]
    if builder_mode == "battery-planner":
        base += [{"path": "frontend/src/lib/batteryMath.js", "kind": "file", "role": "calculation logic"}]
    return base


def build_routes(app_type: str, prompt: str, systems: List[str]) -> List[Dict[str, str]]:
    routes = [{"path": "/", "component": "App", "reason": "root route"}]
    if app_type == "admin panel":
        routes += [
            {"path": "/dashboard", "component": "DashboardPage", "reason": "main admin workspace"},
            {"path": "/settings", "component": "SettingsPage", "reason": "workspace settings"},
        ]
    elif app_type == "assistant app":
        routes += [
            {"path": "/assistant", "component": "AssistantPage", "reason": "assistant shell"},
            {"path": "/history", "component": "HistoryPage", "reason": "saved conversations"},
        ]
    elif app_type == "content app":
        routes += [
            {"path": "/studio", "component": "StudioPage", "reason": "content workspace"},
            {"path": "/preview", "component": "PreviewPage", "reason": "content preview"},
        ]
    else:
        routes += [
            {"path": "/tool", "component": "ToolPage", "reason": "primary tool surface"},
            {"path": "/results", "component": "ResultsPage", "reason": "output view"},
        ]
    if "auth" in systems:
        routes += [
            {"path": "/login", "component": "LoginPage", "reason": "auth entry"},
            {"path": "/register", "component": "RegisterPage", "reason": "account creation"},
        ]
    return routes


def build_components(app_type: str, systems: List[str]) -> List[Dict[str, str]]:
    base = [
        {"name": "CommandBar", "purpose": "captures builder commands"},
        {"name": "LivePreview", "purpose": "renders structural preview"},
        {"name": "StatusBadge", "purpose": "shows api and workspace status"},
    ]
    if app_type == "admin panel":
        base += [
            {"name": "Sidebar", "purpose": "left navigation"},
            {"name": "KpiCard", "purpose": "metric summaries"},
            {"name": "InspectorPanel", "purpose": "details and controls"},
        ]
    elif app_type == "assistant app":
        base += [
            {"name": "ChatShell", "purpose": "conversation interface"},
            {"name": "ToolRail", "purpose": "assistant tools"},
            {"name": "MemoryPanel", "purpose": "session memory"},
        ]
    elif app_type == "content app":
        base += [
            {"name": "EditorShell", "purpose": "writing interface"},
            {"name": "PreviewPanel", "purpose": "live content preview"},
            {"name": "NotesPanel", "purpose": "draft notes"},
        ]
    else:
        base += [
            {"name": "CalculatorForm", "purpose": "tool inputs"},
            {"name": "ResultsPanel", "purpose": "tool outputs"},
            {"name": "ExportActions", "purpose": "download/export actions"},
        ]
    if "auth" in systems:
        base.append({"name": "ProtectedRoute", "purpose": "protect private routes"})
    return base


def build_mutation_summary(layout: Dict[str, Any], modules: List[str], app_type: str, builder_mode: str, systems: List[str], persistence: str) -> List[str]:
    summary = [
        f"App type detected: {app_type}",
        f"Builder mode detected: {builder_mode}",
        f"Layout shell: {layout['shell']}",
        f"Preview style: {layout['previewStyle']}",
        f"Active modules planned: {len(modules)}",
        f"Systems planned: {', '.join(systems) if systems else 'base only'}",
        f"Persistence planned: {persistence}",
    ]
    if layout.get("sidebar"):
        summary.append("Sidebar enabled")
    if layout.get("split"):
        summary.append("Split workspace enabled")
    if layout.get("inspector"):
        summary.append("Inspector enabled")
    return summary


# ---------- shared generated frontend ----------
def app_css(style_name: str) -> str:
    return """
:root {
  color-scheme: dark;
  --bg: #07111f;
  --panel: rgba(13, 25, 43, 0.88);
  --panel-border: rgba(148, 163, 184, 0.16);
  --text: #e5eefc;
  --muted: #93a4bf;
  --accent: #66d9ef;
  --accent-2: #8b5cf6;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, system-ui, Arial, sans-serif;
  background: radial-gradient(circle at top, #12203a, #07111f 55%);
  color: var(--text);
}
a { color: inherit; text-decoration: none; }
button, input, textarea { font: inherit; }
.app-shell { min-height: 100vh; padding: 24px; display: grid; gap: 18px; }
.panel { border: 1px solid var(--panel-border); background: var(--panel); border-radius: 20px; padding: 18px; }
.row { display: grid; gap: 18px; }
.row.two { grid-template-columns: 260px 1fr; }
.card-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
.card { border: 1px solid rgba(148,163,184,.14); border-radius: 16px; padding: 16px; background: rgba(255,255,255,0.03); }
.input { width: 100%; border-radius: 14px; border: 1px solid rgba(148,163,184,.16); background: rgba(255,255,255,.04); color: var(--text); padding: 12px 14px; }
.primary-btn { border: none; border-radius: 999px; padding: 12px 18px; font-weight: 700; cursor: pointer; background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #07111f; }
.secondary-btn { border: 1px solid rgba(148,163,184,.2); border-radius: 999px; padding: 12px 18px; cursor: pointer; background: rgba(255,255,255,.05); color: var(--text); }
.pill { display: inline-flex; align-items: center; gap: 8px; border-radius: 999px; padding: 8px 12px; border: 1px solid rgba(148, 163, 184, 0.18); background: rgba(255,255,255,0.04); color: var(--muted); }
.muted { color: var(--muted); }
@media (max-width: 900px) { .row.two { grid-template-columns: 1fr; } }
""".strip()


def main_jsx() -> str:
    return """
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import "./styles/app.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
""".strip()


def app_router_code(app_type: str, systems: List[str]) -> str:
    main_page = {
        "admin panel": "DashboardPage",
        "assistant app": "AssistantPage",
        "content app": "StudioPage",
        "tool app": "ToolPage",
    }.get(app_type, "ToolPage")
    imports = [f'import {{ {main_page} }} from "./pages/{main_page}.jsx";']
    routes = [f'<Route path="/" element={{<{main_page} />}} />']

    if "auth" in systems:
        imports += [
            'import { LoginPage } from "./pages/LoginPage.jsx";',
            'import { RegisterPage } from "./pages/RegisterPage.jsx";',
            'import { ProtectedRoute } from "./components/ProtectedRoute.jsx";',
            'import { AuthProvider } from "./lib/auth.js";',
        ]
        protected_root = f'<Route path="/app" element={{<ProtectedRoute><{main_page} /></ProtectedRoute>}} />'
        routes = [protected_root] + routes + [
            '<Route path="/login" element={<LoginPage />} />',
            '<Route path="/register" element={<RegisterPage />} />',
        ]
        provider_open = '<AuthProvider>'
        provider_close = '</AuthProvider>'
    else:
        provider_open = ''
        provider_close = ''

    imports_block = "\n".join(imports)
    routes_block = "\n        ".join(routes)
    return f'''
import React from "react";
import {{ Routes, Route }} from "react-router-dom";
{imports_block}

export default function App() {{
  return (
    {provider_open}
      <Routes>
        {routes_block}
      </Routes>
    {provider_close}
  );
}}
'''.strip()


def dashboard_page_code(prompt: str) -> str:
    return f'''
import React from "react";

export function DashboardPage() {{
  return (
    <div className="app-shell">
      <section className="panel">
        <div className="pill">Dashboard</div>
        <h1>Product Dashboard</h1>
        <p className="muted">{prompt}</p>
      </section>
      <section className="card-grid">
        <div className="card"><h3>Users</h3><p className="muted">Connected system area</p></div>
        <div className="card"><h3>Saved Data</h3><p className="muted">Persistence-ready workspace</p></div>
        <div className="card"><h3>AI Tools</h3><p className="muted">Generated modules can plug in here</p></div>
      </section>
    </div>
  );
}}
'''.strip()


def assistant_page_code(prompt: str) -> str:
    return f'''
import React from "react";

export function AssistantPage() {{
  return (
    <div className="app-shell">
      <section className="panel">
        <div className="pill">Assistant</div>
        <h1>AI Assistant Workspace</h1>
        <p className="muted">{prompt}</p>
      </section>
      <section className="row two">
        <div className="panel"><h3>Tools</h3><p className="muted">Upload, scan, history, actions</p></div>
        <div className="panel"><h3>Conversation</h3><input className="input" placeholder="Ask something..." /></div>
      </section>
    </div>
  );
}}
'''.strip()


def studio_page_code(prompt: str) -> str:
    return f'''
import React from "react";

export function StudioPage() {{
  return (
    <div className="app-shell">
      <section className="panel">
        <div className="pill">Studio</div>
        <h1>Content Studio</h1>
        <p className="muted">{prompt}</p>
      </section>
      <section className="row two">
        <div className="panel"><h3>Editor</h3><textarea className="input" rows={{12}} defaultValue="Start writing here..." /></div>
        <div className="panel"><h3>Preview</h3><div className="card">Live content preview</div></div>
      </section>
    </div>
  );
}}
'''.strip()


def tool_page_code(prompt: str, battery_mode: bool) -> str:
    helper = "Battery-focused starter logic included." if battery_mode else "This is a clean generated tool starter."
    return f'''
import React from "react";

export function ToolPage() {{
  return (
    <div className="app-shell">
      <section className="panel">
        <div className="pill">Tool</div>
        <h1>Tool / Calculator</h1>
        <p className="muted">{prompt}</p>
        <p className="muted">{helper}</p>
      </section>
      <section className="row two">
        <div className="panel"><h3>Inputs</h3><input className="input" placeholder="Value 1" /></div>
        <div className="panel"><h3>Results</h3><div className="card">Calculated output will appear here.</div></div>
      </section>
    </div>
  );
}}
'''.strip()


def login_page_code() -> str:
    return r'''
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth.js";

export function LoginPage() {
  const navigate = useNavigate();
  const { login, loading, error } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });

  async function handleSubmit(event) {
    event.preventDefault();
    const result = await login(form.email, form.password);
    if (result.ok) navigate("/app");
  }

  return (
    <div className="app-shell">
      <section className="panel" style={{ maxWidth: 520, margin: "0 auto", width: "100%" }}>
        <div className="pill">Auth</div>
        <h1>Sign in</h1>
        <p className="muted">Use your account to access the private app workspace.</p>
        <form className="row" onSubmit={handleSubmit}>
          <input className="input" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="input" placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <button className="primary-btn" disabled={loading}>{loading ? "Signing in..." : "Sign in"}</button>
        </form>
        {error ? <p className="muted">{error}</p> : null}
        <p className="muted">No account? <Link to="/register">Create one</Link></p>
      </section>
    </div>
  );
}
'''.strip()


def register_page_code() -> str:
    return r'''
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth.js";

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, loading, error } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  async function handleSubmit(event) {
    event.preventDefault();
    const result = await register(form);
    if (result.ok) navigate("/app");
  }

  return (
    <div className="app-shell">
      <section className="panel" style={{ maxWidth: 520, margin: "0 auto", width: "100%" }}>
        <div className="pill">Auth</div>
        <h1>Create account</h1>
        <form className="row" onSubmit={handleSubmit}>
          <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="input" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="input" placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <button className="primary-btn" disabled={loading}>{loading ? "Creating..." : "Create account"}</button>
        </form>
        {error ? <p className="muted">{error}</p> : null}
        <p className="muted">Already have an account? <Link to="/login">Sign in</Link></p>
      </section>
    </div>
  );
}
'''.strip()


def protected_route_code() -> str:
    return r'''
import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../lib/auth.js";

export function ProtectedRoute({ children }) {
  const { user, booting } = useAuth();
  if (booting) return <div className="app-shell"><section className="panel">Loading...</section></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
'''.strip()


def auth_client_code() -> str:
    return r'''
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("app_token") || "");
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("app_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [loading, setLoading] = useState(false);
  const [booting, setBooting] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function boot() {
      if (!token) {
        setBooting(false);
        return;
      }
      try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error("Session expired");
        const data = await response.json();
        setUser(data.user);
      } catch (err) {
        localStorage.removeItem("app_token");
        localStorage.removeItem("app_user");
        setToken("");
        setUser(null);
      } finally {
        setBooting(false);
      }
    }
    boot();
  }, [token]);

  function persist(sessionToken, sessionUser) {
    setToken(sessionToken);
    setUser(sessionUser);
    localStorage.setItem("app_token", sessionToken);
    localStorage.setItem("app_user", JSON.stringify(sessionUser));
  }

  async function login(email, password) {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Login failed");
      persist(data.token, data.user);
      return { ok: true };
    } catch (err) {
      setError(err.message || "Login failed");
      return { ok: false };
    } finally {
      setLoading(false);
    }
  }

  async function register(payload) {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Registration failed");
      persist(data.token, data.user);
      return { ok: true };
    } catch (err) {
      setError(err.message || "Registration failed");
      return { ok: false };
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    setToken("");
    setUser(null);
    localStorage.removeItem("app_token");
    localStorage.removeItem("app_user");
  }

  const value = useMemo(() => ({ user, token, loading, booting, error, login, register, logout }), [user, token, loading, booting, error]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
'''.strip()


def battery_math_code() -> str:
    return """
export function estimateBatteryPlan(items = [], voltage = 12, autonomyDays = 1, sunHours = 4, systemLoss = 0.2) {
  const dailyWh = items.reduce((sum, item) => sum + ((item.watts || 0) * (item.hours || 0)), 0);
  const adjustedDailyWh = dailyWh * (1 + systemLoss);
  const batteryAh = Number(((adjustedDailyWh * autonomyDays) / Math.max(voltage, 1)).toFixed(1));
  const solarWatts = Number((adjustedDailyWh / Math.max(sunHours, 1)).toFixed(1));
  return { dailyWh, adjustedDailyWh, batteryAh, solarWatts };
}
""".strip()


def api_client_code() -> str:
    return r'''
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("app_token") || "";
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed: ${response.status}`);
  }
  return data;
}

export function listItems() {
  return apiRequest("/api/items");
}

export function createItem(payload) {
  return apiRequest("/api/items", { method: "POST", body: JSON.stringify(payload) });
}
'''.strip()


# ---------- generated backend templates ----------
def generated_backend_main(persistence: str, include_auth: bool) -> str:
    auth_import = "from auth import auth_router\n" if include_auth else ""
    auth_router_include = "app.include_router(auth_router)\n" if include_auth else ""
    return f'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from data_store import list_items, create_item, update_item, delete_item
{auth_import}

app = FastAPI(title="Generated App Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

{auth_router_include}
class ItemIn(BaseModel):
    name: str
    description: str = ""


@app.get("/health")
def health():
    return {{"status": "healthy", "persistence": "{persistence}"}}


@app.get("/api/items")
def get_items():
    return {{"items": list_items()}}


@app.post("/api/items")
def post_item(payload: ItemIn):
    item = create_item(payload.model_dump())
    return {{"ok": True, "item": item}}


@app.put("/api/items/{{item_id}}")
def put_item(item_id: int, payload: ItemIn):
    item = update_item(item_id, payload.model_dump())
    return {{"ok": True, "item": item}}


@app.delete("/api/items/{{item_id}}")
def remove_item(item_id: int):
    delete_item(item_id)
    return {{"ok": True}}
'''.strip()


def generated_requirements(include_auth: bool, persistence: str) -> str:
    deps = ["fastapi", "uvicorn[standard]", "pydantic"]
    if include_auth:
        deps += ["pyjwt", "passlib[bcrypt]"]
    if persistence == "supabase":
        deps.append("supabase")
    return "\n".join(sorted(set(deps)))


def generated_env_example(include_auth: bool, persistence: str) -> str:
    lines = ["PORT=8000"]
    if include_auth:
        lines += ["JWT_SECRET=change-me", "JWT_ALGORITHM=HS256", "TOKEN_EXPIRE_MINUTES=43200"]
    if persistence == "supabase":
        lines += ["SUPABASE_URL=https://your-project.supabase.co", "SUPABASE_KEY=your-service-role-key"]
    return "\n".join(lines)


def generated_data_store_code(persistence: str) -> str:
    if persistence == "localstorage":
        return '''
_items = []
_next_id = 1

def list_items():
    return _items

def create_item(payload):
    global _next_id
    item = {"id": _next_id, **payload}
    _items.append(item)
    _next_id += 1
    return item

def update_item(item_id, payload):
    for item in _items:
        if item["id"] == item_id:
            item.update(payload)
            return item
    return {"id": item_id, **payload}

def delete_item(item_id):
    global _items
    _items = [item for item in _items if item["id"] != item_id]
'''.strip()
    return '''
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("app.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT DEFAULT ''
    )
    """)
    conn.commit()
    conn.close()


def list_items():
    init_db()
    conn = get_conn()
    rows = conn.execute("SELECT id, name, description FROM items ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_item(payload):
    init_db()
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO items (name, description) VALUES (?, ?)",
        (payload.get("name", ""), payload.get("description", "")),
    )
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return {"id": item_id, **payload}


def update_item(item_id, payload):
    init_db()
    conn = get_conn()
    conn.execute(
        "UPDATE items SET name = ?, description = ? WHERE id = ?",
        (payload.get("name", ""), payload.get("description", ""), item_id),
    )
    conn.commit()
    conn.close()
    return {"id": item_id, **payload}


def delete_item(item_id):
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
'''.strip()


def generated_auth_backend_code(persistence: str) -> str:
    if persistence == "localstorage":
        return '''
import os
import time
import hashlib
import hmac
import base64
import json
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
_users = []

class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginInput(BaseModel):
    email: EmailStr
    password: str


def make_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def sign_token(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(JWT_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def read_token(token: str) -> dict:
    try:
        body, sig = token.split(".", 1)
        expected = hmac.new(JWT_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        return json.loads(base64.urlsafe_b64decode(body + "==").decode())
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_user_from_header(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    payload = read_token(authorization.split(" ", 1)[1])
    for user in _users:
        if user["id"] == payload.get("sub"):
            return {k: v for k, v in user.items() if k != "password_hash"}
    raise HTTPException(status_code=401, detail="User not found")

@auth_router.post("/register")
def register(payload: RegisterInput):
    for user in _users:
        if user["email"].lower() == payload.email.lower():
            raise HTTPException(status_code=400, detail="Email already in use")
    user = {
        "id": len(_users) + 1,
        "name": payload.name,
        "email": payload.email.lower(),
        "password_hash": make_hash(payload.password),
    }
    _users.append(user)
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    token = sign_token({"sub": user["id"], "iat": int(time.time())})
    return {"ok": True, "user": safe_user, "token": token}

@auth_router.post("/login")
def login(payload: LoginInput):
    for user in _users:
        if user["email"] == payload.email.lower() and user["password_hash"] == make_hash(payload.password):
            safe_user = {k: v for k, v in user.items() if k != "password_hash"}
            token = sign_token({"sub": user["id"], "iat": int(time.time())})
            return {"ok": True, "user": safe_user, "token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@auth_router.get("/me")
def me(authorization: str | None = Header(default=None)):
    return {"user": get_user_from_header(authorization)}
'''.strip()

    return '''
import os
import sqlite3
import jwt
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "43200"))
DB_PATH = Path(__file__).with_name("app.db")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginInput(BaseModel):
    email: EmailStr
    password: str


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_users():
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


def create_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload.get("sub", 0))
    conn = get_conn()
    user = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(user)

@auth_router.post("/register")
def register(payload: RegisterInput):
    init_users()
    conn = get_conn()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (payload.email.lower(),)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already in use")
    password_hash = pwd_context.hash(payload.password)
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (payload.name, payload.email.lower(), password_hash, datetime.utcnow().isoformat()),
    )
    conn.commit()
    user_id = cur.lastrowid
    user = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    token = create_token(user_id)
    return {"ok": True, "user": dict(user), "token": token}

@auth_router.post("/login")
def login(payload: LoginInput):
    init_users()
    conn = get_conn()
    row = conn.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (payload.email.lower(),),
    ).fetchone()
    conn.close()
    if not row or not pwd_context.verify(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(row["id"])
    return {
        "ok": True,
        "user": {"id": row["id"], "name": row["name"], "email": row["email"]},
        "token": token,
    }

@auth_router.get("/me")
def me(authorization: str | None = Header(default=None)):
    return {"user": get_current_user(authorization)}
'''.strip()


def generated_supabase_schema() -> str:
    return '''
create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  name text not null,
  created_at timestamptz default now()
);

create table if not exists public.items (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text default '',
  user_id uuid references public.users(id) on delete cascade,
  created_at timestamptz default now()
);
'''.strip()


def generated_readme(app_type: str, systems: List[str], persistence: str) -> str:
    return f'''# Generated App

This project was generated by your Builder AI.

## App type
- {app_type}

## Systems
- {', '.join(systems) if systems else 'base only'}

## Persistence
- {persistence}

## Frontend
```bash
cd frontend
npm install
npm run dev
```

## Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
'''.strip()


def generated_package_json() -> str:
    return '''
{
  "name": "generated-builder-app",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0"
  },
  "devDependencies": {
    "vite": "^5.4.10"
  }
}
'''.strip()


def generated_vite_index_html() -> str:
    return '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Generated Builder App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''.strip()


def generated_frontend_env() -> str:
    return 'VITE_API_BASE=http://localhost:8000'


def generated_gitignore() -> str:
    return '''
node_modules/
dist/
__pycache__/
*.pyc
.env
backend/app.db
'''.strip()


# ---------- generator ----------
def generate_code_bundle(prompt: str, app_type: str, builder_mode: str, style: str, systems: List[str], persistence: str, complexity: str) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = [
        {"path": "frontend/src/main.jsx", "language": "javascript", "content": main_jsx()},
        {"path": "frontend/src/App.jsx", "language": "javascript", "content": app_router_code(app_type, systems)},
        {"path": "frontend/src/styles/app.css", "language": "css", "content": app_css(style)},
        {"path": "frontend/package.json", "language": "json", "content": generated_package_json()},
        {"path": "frontend/index.html", "language": "html", "content": generated_vite_index_html()},
        {"path": "frontend/.env.example", "language": "env", "content": generated_frontend_env()},
        {"path": ".gitignore", "language": "text", "content": generated_gitignore()},
        {"path": "README.md", "language": "markdown", "content": generated_readme(app_type, systems, persistence)},
        {"path": "backend/main.py", "language": "python", "content": generated_backend_main(persistence, "auth" in systems)},
        {"path": "backend/data_store.py", "language": "python", "content": generated_data_store_code(persistence)},
        {"path": "backend/requirements.txt", "language": "text", "content": generated_requirements("auth" in systems, persistence)},
        {"path": "backend/.env.example", "language": "env", "content": generated_env_example("auth" in systems, persistence)},
        {"path": "frontend/src/lib/api.js", "language": "javascript", "content": api_client_code()},
    ]

    if app_type == "admin panel":
        files.append({"path": "frontend/src/pages/DashboardPage.jsx", "language": "javascript", "content": dashboard_page_code(prompt)})
    elif app_type == "assistant app":
        files.append({"path": "frontend/src/pages/AssistantPage.jsx", "language": "javascript", "content": assistant_page_code(prompt)})
    elif app_type == "content app":
        files.append({"path": "frontend/src/pages/StudioPage.jsx", "language": "javascript", "content": studio_page_code(prompt)})
    else:
        files.append({"path": "frontend/src/pages/ToolPage.jsx", "language": "javascript", "content": tool_page_code(prompt, builder_mode == "battery-planner")})

    if "auth" in systems:
        files += [
            {"path": "frontend/src/pages/LoginPage.jsx", "language": "javascript", "content": login_page_code()},
            {"path": "frontend/src/pages/RegisterPage.jsx", "language": "javascript", "content": register_page_code()},
            {"path": "frontend/src/components/ProtectedRoute.jsx", "language": "javascript", "content": protected_route_code()},
            {"path": "frontend/src/lib/auth.js", "language": "javascript", "content": auth_client_code()},
            {"path": "backend/auth.py", "language": "python", "content": generated_auth_backend_code(persistence)},
        ]

    if builder_mode == "battery-planner":
        files.append({"path": "frontend/src/lib/batteryMath.js", "language": "javascript", "content": battery_math_code()})

    if persistence == "supabase":
        files.append({"path": "backend/supabase_schema.sql", "language": "sql", "content": generated_supabase_schema()})

    meta = {
        "app_type": app_type,
        "builder_mode": builder_mode,
        "systems": systems,
        "persistence": persistence,
        "complexity": complexity,
        "file_count": len(files),
    }
    files.append({"path": ".builder-meta.json", "language": "json", "content": str(meta).replace("'", '"')})

    return files


# ---------- system-safe mutation helpers ----------
def classify_mutation_scope(prompt: str, systems: List[str]) -> str:
    p = prompt.lower()
    if re.search(r"(color|theme|dark mode|light mode|spacing|font|ui|style|responsive|mobile)", p):
        return "ui-only"
    if re.search(r"(login|register|auth|account|session|protected route)", p):
        return "auth-only"
    if re.search(r"(database|storage|save|history|records|api|endpoint|crud)", p):
        return "data-only"
    if re.search(r"(route|page|navigation|sidebar|dashboard)", p):
        return "navigation-and-pages"
    if len(systems) > 2:
        return "multi-system"
    return "targeted"


def detect_target_systems(prompt: str, fallback_systems: List[str]) -> List[str]:
    p = prompt.lower()
    targets: List[str] = []
    checks = [
        ("auth", r"(auth|login|register|account|user|session|protected)"),
        ("storage", r"(storage|database|save|saved|history|records|crud|api|endpoint)"),
        ("billing", r"(billing|stripe|subscription|paywall|plan|pricing)"),
        ("ai-tools", r"(ai|scan|diagnostic|chat|assistant|vision|openai)"),
        ("settings", r"(settings|profile|preferences)"),
        ("dashboard", r"(dashboard|sidebar|navigation|layout|page|pages)"),
    ]
    for name, pattern in checks:
        if re.search(pattern, p):
            targets.append(name)
    if re.search(r"(theme|dark mode|light mode|responsive|mobile|style|spacing|font|ui)", p):
        targets.append("ui")
    # keep targets that exist or are ui
    final = []
    for t in targets:
        if t == "ui" or t in fallback_systems or t in {"dashboard", "settings", "auth", "storage", "billing", "ai-tools"}:
            final.append(t)
    return sorted(set(final)) or ["ui"]


def build_preserve_rules(systems: List[str], target_systems: List[str], protected_systems: List[str]) -> Dict[str, Any]:
    protected = sorted(set(protected_systems + [s for s in systems if s not in target_systems and s != "ui"]))
    file_patterns = [
        "frontend/src/lib/api.js",
        "backend/main.py",
        "README.md",
        ".builder-meta.json",
    ]
    if "auth" in protected:
        file_patterns += [
            "frontend/src/lib/auth.js",
            "frontend/src/components/ProtectedRoute.jsx",
            "frontend/src/pages/LoginPage.jsx",
            "frontend/src/pages/RegisterPage.jsx",
            "backend/auth.py",
        ]
    if "storage" in protected:
        file_patterns += [
            "backend/data_store.py",
            "backend/database.py",
            "backend/supabase_schema.sql",
            "frontend/src/lib/api.js",
        ]
    return {
        "protected_systems": protected,
        "preserve_file_patterns": sorted(set(file_patterns)),
        "forbidden_operations": ["delete-protected-files", "rewrite-unrelated-systems", "drop-routes-without-replacement"],
    }


def build_safe_file_operations(prompt: str, app_type: str, target_systems: List[str], systems: List[str]) -> List[Dict[str, Any]]:
    p = prompt.lower()
    ops: List[Dict[str, Any]] = []
    if "ui" in target_systems:
        ops += [
            {"type": "update", "path": "frontend/src/styles/app.css", "reason": "apply style-safe mutation", "system": "ui"},
            {"type": "update", "path": "frontend/src/App.jsx", "reason": "adjust shell or routing wrappers without deleting core systems", "system": "ui"},
        ]
    if "auth" in target_systems:
        ops += [
            {"type": "update", "path": "frontend/src/lib/auth.js", "reason": "adjust auth client safely", "system": "auth"},
            {"type": "update", "path": "frontend/src/components/ProtectedRoute.jsx", "reason": "preserve route protection while mutating auth", "system": "auth"},
            {"type": "update", "path": "backend/auth.py", "reason": "mutate auth backend only", "system": "auth"},
        ]
    if "storage" in target_systems:
        ops += [
            {"type": "update", "path": "frontend/src/lib/api.js", "reason": "extend api client safely", "system": "storage"},
            {"type": "update", "path": "backend/data_store.py", "reason": "preserve persistence while changing data flow", "system": "storage"},
            {"type": "update", "path": "backend/main.py", "reason": "add or extend CRUD endpoints only", "system": "storage"},
        ]
    if "dashboard" in target_systems or re.search(r"(page|pages|sidebar|dashboard|navigation)", p):
        page_path = {
            "admin panel": "frontend/src/pages/DashboardPage.jsx",
            "assistant app": "frontend/src/pages/AssistantPage.jsx",
            "content app": "frontend/src/pages/StudioPage.jsx",
            "tool app": "frontend/src/pages/ToolPage.jsx",
        }.get(app_type, "frontend/src/pages/ToolPage.jsx")
        ops += [
            {"type": "update", "path": page_path, "reason": "mutate primary page without touching unrelated systems", "system": "dashboard"},
            {"type": "update", "path": "frontend/src/App.jsx", "reason": "preserve routes while adding page-level changes", "system": "dashboard"},
        ]
    if "billing" in target_systems:
        ops += [
            {"type": "create_or_update", "path": "frontend/src/pages/BillingPage.jsx", "reason": "add billing ui safely", "system": "billing"},
            {"type": "create_or_update", "path": "backend/billing.py", "reason": "add billing backend without touching auth or storage", "system": "billing"},
        ]
    if "ai-tools" in target_systems:
        ops += [
            {"type": "create_or_update", "path": "frontend/src/pages/ScanPage.jsx", "reason": "add ai feature surface safely", "system": "ai-tools"},
            {"type": "create_or_update", "path": "backend/ai_tools.py", "reason": "isolate ai backend changes", "system": "ai-tools"},
        ]
    if not ops:
        ops = [{"type": "update", "path": "frontend/src/App.jsx", "reason": "generic safe mutation fallback", "system": "ui"}]
    return ops


def build_mutation_guardrails(scope: str, target_systems: List[str], preserve_rules: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mode": "system-safe",
        "scope": scope,
        "target_systems": target_systems,
        "must_preserve": preserve_rules["preserve_file_patterns"],
        "must_not_break": [
            "existing routes remain reachable",
            "auth flows remain intact unless auth is targeted",
            "persistence layer remains compatible unless storage is targeted",
            "api client contracts stay stable unless storage is targeted",
        ],
        "recommended_apply_order": [
            "analyze-target-systems",
            "lock-protected-files",
            "patch-target-files",
            "verify-routes",
            "verify-auth-and-data-flow",
        ],
    }


@app.post("/mutate")
def mutate(payload: MutateRequest):
    prompt = payload.prompt.strip()
    app_type = infer_app_type(prompt)
    builder_mode = infer_builder_mode(prompt)
    summary_style = infer_summary_style(prompt)
    systems = infer_systems(prompt, app_type, payload.systems)
    persistence = infer_persistence(prompt, systems, payload.complexity, "")
    modules = recommend_modules(prompt, app_type, systems)
    layout = build_layout(prompt, payload.current_layout)
    file_tree = build_file_tree(app_type, builder_mode, prompt, systems, persistence)
    routes = build_routes(app_type, prompt, systems)
    components = build_components(app_type, systems)
    summary = build_mutation_summary(layout, modules, app_type, builder_mode, systems, persistence)

    return {
        "ok": True,
        "prompt": prompt,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "summary_style": summary_style,
        "systems": systems,
        "persistence": persistence,
        "layout_changes": layout,
        "module_changes": {"enable": modules, "disable": []},
        "file_tree": file_tree,
        "routes": routes,
        "components": components,
        "mutation_summary": summary,
        "next_best_actions": [
            "materialize files",
            "generate auth system",
            "regenerate routes",
            "connect persistence",
            "generate code",
        ],
    }


@app.post("/generate-code")
def generate_code(payload: GenerateCodeRequest):
    prompt = payload.prompt.strip()
    app_type = payload.app_type or infer_app_type(prompt)
    builder_mode = payload.builder_mode or infer_builder_mode(prompt)
    style = payload.style or "dark glass"
    systems = infer_systems(prompt, app_type, payload.systems)
    persistence = infer_persistence(prompt, systems, payload.complexity, payload.persistence)
    files = generate_code_bundle(prompt, app_type, builder_mode, style, systems, persistence, payload.complexity)
    routes = payload.routes or build_routes(app_type, prompt, systems)
    components = payload.components or build_components(app_type, systems)

    return {
        "ok": True,
        "prompt": prompt,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "style": style,
        "systems": systems,
        "persistence": persistence,
        "complexity": payload.complexity,
        "generated_files": files,
        "files": files,
        "routes": routes,
        "components": components,
        "entry_file": "frontend/src/main.jsx",
        "app_file": "frontend/src/App.jsx",
        "summary": f"Generated {len(files)} files for a {app_type} in {builder_mode} mode with {', '.join(systems) if systems else 'base systems'} and {persistence} persistence.",
    }


# ---------- idea-to-app orchestration ----------
from uuid import uuid4
from datetime import datetime


class OrchestrateRequest(BaseModel):
    prompt: str
    project_id: str = ""
    mode: str = "auto"  # auto | create | update
    current_files: List[Dict[str, Any]] = Field(default_factory=list)
    systems: List[str] = Field(default_factory=list)
    complexity: str = "mvp"
    style: str = "dark glass"
    architecture: Dict[str, Any] = Field(default_factory=dict)
    app_type: str = ""
    builder_mode: str = ""
    persistence: str = ""
    routes: List[Dict[str, Any]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)


PROJECT_STORE: Dict[str, Dict[str, Any]] = {}


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def normalize_file_list(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    seen = set()
    for item in files or []:
        path = str(item.get("path", "")).strip()
        if not path:
            continue
        key = path.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(
            {
                "path": path,
                "language": item.get("language", infer_language_from_path(path)),
                "content": item.get("content", ""),
            }
        )
    return cleaned


def infer_language_from_path(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".py"):
        return "python"
    if lower.endswith(".jsx") or lower.endswith(".js"):
        return "javascript"
    if lower.endswith(".css"):
        return "css"
    if lower.endswith(".json"):
        return "json"
    if lower.endswith(".md"):
        return "markdown"
    if lower.endswith(".html"):
        return "html"
    if lower.endswith(".sql"):
        return "sql"
    return "text"


def infer_complexity(prompt: str, requested: str = "") -> str:
    value = (requested or "").strip().lower()
    if value in {"starter", "mvp", "product"}:
        return value
    p = prompt.lower()
    if re.search(r"(complete app|full app|production|product|saas|portal|platform|multi page|multi-page)", p):
        return "product"
    if re.search(r"(prototype|starter|simple app|simple tool|quick demo)", p):
        return "starter"
    return "mvp"


def default_architecture(app_type: str, systems: List[str], persistence: str) -> Dict[str, Any]:
    frontend = "react-vite"
    backend = "fastapi"
    state = "local project state"
    auth = "jwt" if "auth" in systems else "none"
    if persistence == "supabase":
        state = "supabase"
        auth = "supabase+jwt" if "auth" in systems else "supabase"
    elif persistence == "sqlite":
        state = "sqlite+api"
    elif persistence == "localstorage":
        state = "localstorage"
    return {
        "frontend": frontend,
        "backend": backend,
        "state": state,
        "auth": auth,
        "app_shell": app_type,
    }


def choose_orchestration_mode(requested_mode: str, project_id: str, existing: Dict[str, Any]) -> str:
    mode = (requested_mode or "auto").strip().lower()
    if mode in {"create", "update"}:
        return mode
    if project_id and existing:
        return "update"
    return "create"


def merge_architecture(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(existing or {})
    for key, value in (incoming or {}).items():
        if value not in ("", None, [], {}):
            merged[key] = value
    return merged


def make_project_name(prompt: str, app_type: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", prompt).strip()
    parts = [p for p in text.split() if p][:6]
    if not parts:
        parts = app_type.split()
    return " ".join(word.capitalize() for word in parts)[:60] or "Generated App"


def slugify_name(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return value or "generated-app"


def build_preview_model(app_type: str, systems: List[str], routes: List[Dict[str, Any]], files: List[Dict[str, Any]]) -> Dict[str, Any]:
    page_paths = [r.get("path", "/") for r in routes]
    key_files = [f.get("path", "") for f in files[:12]]
    return {
        "shell": app_type,
        "routes": page_paths,
        "systems": systems,
        "key_files": key_files,
        "preview_ready": True,
    }


def build_project_state_record(
    *,
    project_id: str,
    prompt: str,
    mode: str,
    app_type: str,
    builder_mode: str,
    systems: List[str],
    complexity: str,
    persistence: str,
    style: str,
    architecture: Dict[str, Any],
    routes: List[Dict[str, Any]],
    components: List[Dict[str, Any]],
    files: List[Dict[str, Any]],
    previous_versions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    project_name = make_project_name(prompt, app_type)
    return {
        "project_id": project_id,
        "project_name": project_name,
        "project_slug": slugify_name(project_name),
        "prompt": prompt,
        "mode": mode,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "systems": systems,
        "complexity": complexity,
        "persistence": persistence,
        "style": style,
        "architecture": architecture,
        "routes": routes,
        "components": components,
        "files": files,
        "preview": build_preview_model(app_type, systems, routes, files),
        "version_count": len(previous_versions) + 1,
        "updated_at": now_iso(),
        "versions": previous_versions + [
            {
                "version": len(previous_versions) + 1,
                "prompt": prompt,
                "updated_at": now_iso(),
                "file_count": len(files),
                "systems": list(systems),
            }
        ],
    }


def extend_project_from_prompt(base_project: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    existing_systems = list(base_project.get("systems", []))
    app_type = base_project.get("app_type") or infer_app_type(prompt)
    builder_mode = base_project.get("builder_mode") or infer_builder_mode(prompt)
    extra_systems = infer_systems(prompt, app_type, existing_systems)
    systems = sorted(set(existing_systems + extra_systems))
    complexity = infer_complexity(prompt, base_project.get("complexity", "mvp"))
    persistence = infer_persistence(prompt, systems, complexity, base_project.get("persistence", ""))
    style = base_project.get("style", "dark glass")
    architecture = default_architecture(app_type, systems, persistence)
    architecture = merge_architecture(architecture, base_project.get("architecture", {}))
    routes = build_routes(app_type, prompt, systems)
    components = build_components(app_type, systems)
    files = generate_code_bundle(prompt, app_type, builder_mode, style, systems, persistence, complexity)
    return {
        "app_type": app_type,
        "builder_mode": builder_mode,
        "systems": systems,
        "complexity": complexity,
        "persistence": persistence,
        "style": style,
        "architecture": architecture,
        "routes": routes,
        "components": components,
        "files": normalize_file_list(files),
    }


def create_project_from_idea(payload: OrchestrateRequest) -> Dict[str, Any]:
    prompt = payload.prompt.strip()
    app_type = payload.app_type or infer_app_type(prompt)
    builder_mode = payload.builder_mode or infer_builder_mode(prompt)
    systems = infer_systems(prompt, app_type, payload.systems)
    complexity = infer_complexity(prompt, payload.complexity)
    persistence = infer_persistence(prompt, systems, complexity, payload.persistence)
    style = payload.style or "dark glass"
    architecture = default_architecture(app_type, systems, persistence)
    architecture = merge_architecture(architecture, payload.architecture)
    routes = payload.routes or build_routes(app_type, prompt, systems)
    components = payload.components or build_components(app_type, systems)
    files = payload.current_files or generate_code_bundle(prompt, app_type, builder_mode, style, systems, persistence, complexity)
    files = normalize_file_list(files)
    project_id = payload.project_id or str(uuid4())
    return build_project_state_record(
        project_id=project_id,
        prompt=prompt,
        mode="create",
        app_type=app_type,
        builder_mode=builder_mode,
        systems=systems,
        complexity=complexity,
        persistence=persistence,
        style=style,
        architecture=architecture,
        routes=routes,
        components=components,
        files=files,
        previous_versions=[],
    )


def update_existing_project(project: Dict[str, Any], payload: OrchestrateRequest) -> Dict[str, Any]:
    prompt = payload.prompt.strip()
    extended = extend_project_from_prompt(project, prompt)
    architecture = merge_architecture(extended["architecture"], payload.architecture)
    return build_project_state_record(
        project_id=project["project_id"],
        prompt=prompt,
        mode="update",
        app_type=extended["app_type"],
        builder_mode=extended["builder_mode"],
        systems=extended["systems"],
        complexity=extended["complexity"],
        persistence=extended["persistence"],
        style=extended["style"],
        architecture=architecture,
        routes=payload.routes or extended["routes"],
        components=payload.components or extended["components"],
        files=payload.current_files or extended["files"],
        previous_versions=project.get("versions", []),
    )


@app.post("/orchestrate")
def orchestrate(payload: OrchestrateRequest):
    prompt = payload.prompt.strip()
    existing = PROJECT_STORE.get(payload.project_id, {}) if payload.project_id else {}
    mode = choose_orchestration_mode(payload.mode, payload.project_id, existing)

    if mode == "create":
        project = create_project_from_idea(payload)
    else:
        if not existing:
            project = create_project_from_idea(payload)
            mode = "create"
        else:
            project = update_existing_project(existing, payload)

    PROJECT_STORE[project["project_id"]] = project

    orchestration_summary = [
        f"Mode: {mode}",
        f"App type: {project['app_type']}",
        f"Builder mode: {project['builder_mode']}",
        f"Systems: {', '.join(project['systems']) or 'none'}",
        f"Persistence: {project['persistence']}",
        f"Complexity: {project['complexity']}",
        f"Files ready: {len(project['files'])}",
        f"Project versions: {project['version_count']}",
    ]

    return {
        "ok": True,
        "project_id": project["project_id"],
        "project_name": project["project_name"],
        "project_slug": project["project_slug"],
        "mode": mode,
        "prompt": prompt,
        "app_type": project["app_type"],
        "builder_mode": project["builder_mode"],
        "systems": project["systems"],
        "complexity": project["complexity"],
        "persistence": project["persistence"],
        "style": project["style"],
        "architecture": project["architecture"],
        "routes": project["routes"],
        "components": project["components"],
        "files": project["files"],
        "generated_files": project["files"],
        "entry_file": "frontend/src/main.jsx",
        "app_file": "frontend/src/App.jsx",
        "preview": project["preview"],
        "project_state": {
            "project_id": project["project_id"],
            "version_count": project["version_count"],
            "updated_at": project["updated_at"],
            "systems": project["systems"],
            "persistence": project["persistence"],
        },
        "orchestration_summary": orchestration_summary,
        "next_best_actions": [
            "preview current app",
            "apply focused mutation",
            "download project zip",
            "add deploy configuration",
        ],
    }


@app.get("/project-state/{project_id}")
def project_state(project_id: str):
    project = PROJECT_STORE.get(project_id)
    if not project:
        return {"ok": False, "error": "project_not_found", "project_id": project_id}
    return {
        "ok": True,
        "project_id": project["project_id"],
        "project_name": project["project_name"],
        "project_slug": project["project_slug"],
        "app_type": project["app_type"],
        "builder_mode": project["builder_mode"],
        "systems": project["systems"],
        "complexity": project["complexity"],
        "persistence": project["persistence"],
        "style": project["style"],
        "architecture": project["architecture"],
        "routes": project["routes"],
        "components": project["components"],
        "files": project["files"],
        "preview": project["preview"],
        "versions": project["versions"],
        "updated_at": project["updated_at"],
    }


@app.get("/projects")
def list_projects():
    items = []
    for project in PROJECT_STORE.values():
        items.append(
            {
                "project_id": project["project_id"],
                "project_name": project["project_name"],
                "project_slug": project["project_slug"],
                "app_type": project["app_type"],
                "systems": project["systems"],
                "persistence": project["persistence"],
                "version_count": project["version_count"],
                "updated_at": project["updated_at"],
            }
        )
    items.sort(key=lambda item: item["updated_at"], reverse=True)
    return {"ok": True, "count": len(items), "projects": items}
