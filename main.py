
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import re


app = FastAPI(title="Builder Backend v4 - Merged Final")


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
    return {"status": "ok", "service": "builder-backend-v4-merged"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "builder-backend-v4-merged",
        "features": {
            "mutate": True,
            "generate_code": True,
            "system_planner": True,
            "persistence_aware": True,
        },
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
        "summary": f"For this setup, plan for about {battery_ah}Ah of battery and {solar_watts}W of solar."
    }


class MutateRequest(BaseModel):
    prompt: str
    current_layout: Dict[str, Any] = Field(default_factory=dict)
    active_modules: List[str] = Field(default_factory=list)
    feature_state: Dict[str, Any] = Field(default_factory=dict)
    systems: List[str] = Field(default_factory=list)
    complexity: str = "starter"
    architecture: Dict[str, Any] = Field(default_factory=dict)
    persistence_mode: str = ""


class GenerateCodeRequest(BaseModel):
    prompt: str
    app_type: str = ""
    builder_mode: str = ""
    style: str = "dark glass"
    routes: List[Dict[str, Any]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    systems: List[str] = Field(default_factory=list)
    complexity: str = "starter"
    architecture: Dict[str, Any] = Field(default_factory=dict)
    persistence_mode: str = ""
    project_name: str = ""
    include_backend: bool = True


def slugify(text: str, fallback: str = "generated-app") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or fallback


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


def recommend_modules(prompt: str, app_type: str) -> List[str]:
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
    if re.search(r"(affiliate|amazon|monetize|shop)", p):
        modules.add("affiliate_suggestions")
    if re.search(r"(export|report|download|pdf|zip)", p):
        modules.add("export_report")
    if re.search(r"(sidebar|navigation|rail)", p):
        modules.add("sidebar_navigation")
    if re.search(r"(notes|brainstorm|scratch)", p):
        modules.add("notes_panel")
    if re.search(r"(dashboard|crm|saas)", p):
        modules.add("dashboard_shell")
    if re.search(r"(split|two column|2 column|2-column)", p):
        modules.add("split_workspace")
    if re.search(r"(preview|runner|sandbox)", p):
        modules.add("preview_runner")
    return sorted(modules)


def infer_systems(prompt: str, app_type: str, builder_mode: str, selected: Optional[List[str]] = None) -> List[str]:
    systems = set(selected or [])
    p = prompt.lower()

    if app_type == "admin panel":
        systems.update({"dashboard", "settings"})
    elif app_type == "assistant app":
        systems.update({"ai-tools", "storage", "settings"})
    elif app_type == "content app":
        systems.update({"dashboard", "storage", "settings"})
    else:
        systems.update({"tools", "storage"})

    if builder_mode == "battery-planner":
        systems.update({"tools", "storage"})

    if re.search(r"(auth|login|signin|sign in|account|user profile|signup|register)", p):
        systems.add("auth")
    if re.search(r"(billing|payment|paywall|stripe|subscription|pro plan|pricing)", p):
        systems.add("billing")
    if re.search(r"(dashboard|analytics|admin|panel|overview)", p):
        systems.add("dashboard")
    if re.search(r"(save|history|database|data|reports|records|folder|saved)", p):
        systems.add("storage")
    if re.search(r"(settings|preferences|profile)", p):
        systems.add("settings")
    if re.search(r"(scan|ai|assistant|chat|diagnostic|copilot|vision)", p):
        systems.add("ai-tools")
    if re.search(r"(tool|calculator|planner|converter)", p):
        systems.add("tools")
    if re.search(r"(portal|admin|staff|dealer|tech|role)", p):
        systems.add("roles")

    return sorted(systems)


def infer_complexity(prompt: str, incoming: str = "") -> str:
    c = (incoming or "").strip().lower()
    if c in {"starter", "mvp", "product"}:
        return c
    p = prompt.lower()
    if re.search(r"(full product|complete product|saas|production|multi page|auth|billing|dashboard)", p):
        return "product"
    if re.search(r"(mvp|prototype|working app|save data)", p):
        return "mvp"
    return "starter"


def infer_persistence_mode(prompt: str, systems: List[str], complexity: str, requested: str = "") -> str:
    req = (requested or "").strip().lower()
    if req in {"localstorage", "sqlite", "supabase"}:
        return req
    p = prompt.lower()
    if "billing" in systems or re.search(r"(cloud|supabase|online users|real auth|shared data)", p):
        return "supabase" if complexity == "product" else "sqlite"
    if "auth" in systems or "storage" in systems:
        return "sqlite" if complexity in {"mvp", "product"} else "localstorage"
    return "localstorage"


def build_architecture(prompt: str, app_type: str, builder_mode: str, systems: List[str], complexity: str, persistence_mode: str, incoming: Dict[str, Any]) -> Dict[str, Any]:
    arch = dict(incoming or {})
    arch.setdefault("frontend", "react-vite")
    arch.setdefault("backend", "fastapi")
    arch.setdefault("styling", "css")
    arch.setdefault("routing", "react-router-dom")
    arch.setdefault("state", "react-state")
    arch["app_type"] = app_type
    arch["builder_mode"] = builder_mode
    arch["complexity"] = complexity
    arch["systems"] = systems
    arch["persistence"] = persistence_mode
    arch["api"] = "fastapi-json"
    arch["preview"] = "live-preview-runner"
    return arch


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
        "panels": {
            "sidebar": list(current_layout.get("panels", {}).get("sidebar", ["builder", "results", "modules", "mutations", "systems"])),
            "mainTop": list(current_layout.get("panels", {}).get("mainTop", ["brain", "command", "quickActions"])),
            "mainBottom": list(current_layout.get("panels", {}).get("mainBottom", ["planner", "results", "preview"])),
            "inspector": list(current_layout.get("panels", {}).get("inspector", ["status", "affiliate", "notes", "architecture"])),
        },
    }
    p = prompt.lower()
    if re.search(r"(dashboard|crm|saas)", p):
        layout["mode"] = "dashboard"
        layout["shell"] = "dashboard"
        layout["sidebar"] = True
        layout["split"] = True
        layout["inspector"] = True
        layout["previewStyle"] = "dashboard"
    if re.search(r"(assistant|copilot|agent)", p):
        layout["mode"] = "workspace"
        layout["shell"] = "classic"
        layout["split"] = True
        layout["inspector"] = True
    if re.search(r"(content|editor|writer|studio)", p):
        layout["mode"] = "workspace"
        layout["shell"] = "classic"
        layout["split"] = True
        layout["inspector"] = True
    if re.search(r"(focus preview|preview first|canvas focus)", p):
        layout["mode"] = "focus"
        layout["shell"] = "focus"
        layout["split"] = True
        layout["previewStyle"] = "spotlight"
    if re.search(r"(dense|compact)", p):
        layout["dense"] = True
    if re.search(r"(spacious|comfortable|relaxed)", p):
        layout["dense"] = False
    if re.search(r"(add sidebar|sidebar|navigation)", p):
        layout["sidebar"] = True
    if re.search(r"(add inspector|inspector|right panel)", p):
        layout["inspector"] = True
    if re.search(r"(split|two column|2 column|2-column)", p):
        layout["split"] = True
    return layout


def build_file_tree(app_type: str, builder_mode: str, prompt: str, systems: List[str], persistence_mode: str) -> List[Dict[str, Any]]:
    base = [
        {"path": "frontend/src/App.jsx", "kind": "file", "role": "root app"},
        {"path": "frontend/src/main.jsx", "kind": "file", "role": "entry"},
        {"path": "frontend/src/styles/app.css", "kind": "file", "role": "global styles"},
        {"path": "frontend/src/components", "kind": "folder", "role": "ui components"},
        {"path": "frontend/src/pages", "kind": "folder", "role": "pages"},
        {"path": "frontend/src/lib", "kind": "folder", "role": "helpers"},
        {"path": "backend", "kind": "folder", "role": "api server"},
        {"path": "backend/main.py", "kind": "file", "role": "backend app"},
    ]

    if app_type == "admin panel":
        base += [
            {"path": "frontend/src/pages/DashboardPage.jsx", "kind": "file", "role": "dashboard page"},
            {"path": "frontend/src/components/Sidebar.jsx", "kind": "file", "role": "navigation"},
            {"path": "frontend/src/components/KpiCard.jsx", "kind": "file", "role": "metrics card"},
            {"path": "frontend/src/components/InspectorPanel.jsx", "kind": "file", "role": "details panel"},
        ]
    elif app_type == "assistant app":
        base += [
            {"path": "frontend/src/pages/AssistantPage.jsx", "kind": "file", "role": "assistant page"},
            {"path": "frontend/src/components/ChatShell.jsx", "kind": "file", "role": "chat interface"},
            {"path": "frontend/src/components/ToolRail.jsx", "kind": "file", "role": "tools rail"},
            {"path": "frontend/src/components/MemoryPanel.jsx", "kind": "file", "role": "memory / notes"},
        ]
    elif app_type == "content app":
        base += [
            {"path": "frontend/src/pages/StudioPage.jsx", "kind": "file", "role": "content studio"},
            {"path": "frontend/src/components/EditorShell.jsx", "kind": "file", "role": "editor"},
            {"path": "frontend/src/components/PreviewPanel.jsx", "kind": "file", "role": "content preview"},
            {"path": "frontend/src/components/NotesPanel.jsx", "kind": "file", "role": "notes"},
        ]
    else:
        base += [
            {"path": "frontend/src/pages/ToolPage.jsx", "kind": "file", "role": "tool page"},
            {"path": "frontend/src/components/CalculatorForm.jsx", "kind": "file", "role": "tool input"},
            {"path": "frontend/src/components/ResultsPanel.jsx", "kind": "file", "role": "tool output"},
            {"path": "frontend/src/components/ExportActions.jsx", "kind": "file", "role": "export controls"},
        ]

    if builder_mode == "battery-planner":
        base += [
            {"path": "frontend/src/lib/batteryMath.js", "kind": "file", "role": "calculation logic"},
            {"path": "frontend/src/components/ApplianceTable.jsx", "kind": "file", "role": "appliance rows"},
        ]

    if "auth" in systems:
        base += [
            {"path": "frontend/src/pages/LoginPage.jsx", "kind": "file", "role": "authentication"},
            {"path": "frontend/src/pages/RegisterPage.jsx", "kind": "file", "role": "registration"},
            {"path": "frontend/src/lib/auth.js", "kind": "file", "role": "auth helpers"},
            {"path": "backend/routes/auth.py", "kind": "file", "role": "auth endpoints"},
        ]
    if "storage" in systems:
        base += [
            {"path": "frontend/src/lib/storage.js", "kind": "file", "role": "storage helpers"},
            {"path": "backend/routes/storage.py", "kind": "file", "role": "storage endpoints"},
        ]
    if "billing" in systems:
        base += [
            {"path": "frontend/src/pages/PricingPage.jsx", "kind": "file", "role": "pricing"},
            {"path": "backend/routes/billing.py", "kind": "file", "role": "billing endpoints"},
        ]
    if "settings" in systems:
        base += [
            {"path": "frontend/src/pages/SettingsPage.jsx", "kind": "file", "role": "settings"},
        ]
    if "ai-tools" in systems:
        base += [
            {"path": "frontend/src/pages/ScanPage.jsx", "kind": "file", "role": "ai scan / diagnostics"},
            {"path": "backend/routes/ai_tools.py", "kind": "file", "role": "ai tool endpoints"},
        ]
    if persistence_mode == "sqlite":
        base += [
            {"path": "backend/db.py", "kind": "file", "role": "sqlite helpers"},
        ]
    if persistence_mode == "supabase":
        base += [
            {"path": "backend/supabase_client.py", "kind": "file", "role": "supabase helpers"},
            {"path": "backend/supabase_schema.sql", "kind": "file", "role": "database schema"},
        ]

    return base


def build_routes(app_type: str, prompt: str, systems: Optional[List[str]] = None) -> List[Dict[str, str]]:
    systems = systems or []
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
    if "auth" in systems or re.search(r"(auth|login|signin|sign in)", prompt.lower()):
        routes.append({"path": "/login", "component": "LoginPage", "reason": "auth entry"})
    if "billing" in systems:
        routes.append({"path": "/pricing", "component": "PricingPage", "reason": "billing / plans"})
    if "settings" in systems and not any(r["path"] == "/settings" for r in routes):
        routes.append({"path": "/settings", "component": "SettingsPage", "reason": "user preferences"})
    if "ai-tools" in systems:
        routes.append({"path": "/scan", "component": "ScanPage", "reason": "ai tool flow"})
    return routes


def build_components(app_type: str, prompt: str, systems: Optional[List[str]] = None) -> List[Dict[str, str]]:
    systems = systems or []
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
        base += [
            {"name": "ProtectedRoute", "purpose": "route protection"},
            {"name": "AuthCard", "purpose": "auth forms"},
        ]
    if "billing" in systems:
        base.append({"name": "PricingCard", "purpose": "plan selection"})
    if "ai-tools" in systems:
        base.append({"name": "ScanUploader", "purpose": "ai upload flow"})
    return base


def build_mutation_summary(layout: Dict[str, Any], modules: List[str], app_type: str, builder_mode: str, systems: List[str], complexity: str, persistence_mode: str) -> List[str]:
    summary = [
        f"App type detected: {app_type}",
        f"Builder mode detected: {builder_mode}",
        f"Layout shell: {layout['shell']}",
        f"Preview style: {layout['previewStyle']}",
        f"Active modules planned: {len(modules)}",
        f"Systems planned: {', '.join(systems) if systems else 'none'}",
        f"Complexity mode: {complexity}",
        f"Persistence mode: {persistence_mode}",
    ]
    if layout.get("sidebar"):
        summary.append("Sidebar enabled")
    if layout.get("split"):
        summary.append("Split workspace enabled")
    if layout.get("inspector"):
        summary.append("Inspector enabled")
    return summary


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
button, input, textarea { font: inherit; }
.app-shell {
  min-height: 100vh;
  padding: 24px;
  display: grid;
  gap: 18px;
}
.panel {
  border: 1px solid var(--panel-border);
  background: var(--panel);
  border-radius: 20px;
  padding: 18px;
}
.row {
  display: grid;
  gap: 18px;
}
.row.two {
  grid-template-columns: 260px 1fr;
}
.row.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  padding: 8px 12px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255,255,255,0.04);
  color: var(--muted);
}
.primary-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font-weight: 700;
  cursor: pointer;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #07111f;
}
.muted { color: var(--muted); }
.card-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}
.card {
  border: 1px solid rgba(148,163,184,.14);
  border-radius: 16px;
  padding: 16px;
  background: rgba(255,255,255,0.03);
}
.input {
  width: 100%;
  border-radius: 14px;
  border: 1px solid rgba(148,163,184,.16);
  background: rgba(255,255,255,.04);
  color: var(--text);
  padding: 12px 14px;
}
@media (max-width: 900px) {
  .row.two, .row.three {
    grid-template-columns: 1fr;
  }
}
""".strip()


def main_jsx() -> str:
    return """
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./styles/app.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""".strip()


def root_app_code(app_type: str, prompt: str) -> str:
    page_name = {
        "admin panel": "DashboardPage",
        "assistant app": "AssistantPage",
        "content app": "StudioPage",
        "tool app": "ToolPage",
    }.get(app_type, "ToolPage")

    return f"""
import React from "react";
import {{ {page_name} }} from "./pages/{page_name}.jsx";

export default function App() {{
  return <{page_name} />;
}}
""".strip()


def dashboard_page_code(prompt: str) -> str:
    return f"""
import React from "react";
import {{ Sidebar }} from "../components/Sidebar.jsx";
import {{ KpiCard }} from "../components/KpiCard.jsx";
import {{ InspectorPanel }} from "../components/InspectorPanel.jsx";

export function DashboardPage() {{
  return (
    <div className="app-shell">
      <div className="panel">
        <div className="pill">Admin dashboard</div>
        <h1>CRM Dashboard</h1>
        <p className="muted">{prompt}</p>
      </div>

      <div className="row two">
        <Sidebar />
        <div className="row">
          <div className="card-grid">
            <KpiCard title="Revenue" value="$24.5k" />
            <KpiCard title="Pipeline" value="42 deals" />
            <KpiCard title="Tickets" value="18 open" />
          </div>
          <div className="panel">
            <h2>Workspace</h2>
            <p className="muted">This generated dashboard gives you a clean admin shell to continue building from.</p>
          </div>
        </div>
      </div>

      <InspectorPanel />
    </div>
  );
}}
""".strip()


def assistant_page_code(prompt: str) -> str:
    return f"""
import React from "react";
import {{ ChatShell }} from "../components/ChatShell.jsx";
import {{ ToolRail }} from "../components/ToolRail.jsx";
import {{ MemoryPanel }} from "../components/MemoryPanel.jsx";

export function AssistantPage() {{
  return (
    <div className="app-shell">
      <div className="panel">
        <div className="pill">Assistant workspace</div>
        <h1>AI Assistant</h1>
        <p className="muted">{prompt}</p>
      </div>

      <div className="row two">
        <ToolRail />
        <ChatShell />
      </div>

      <MemoryPanel />
    </div>
  );
}}
""".strip()


def studio_page_code(prompt: str) -> str:
    return f"""
import React from "react";
import {{ EditorShell }} from "../components/EditorShell.jsx";
import {{ PreviewPanel }} from "../components/PreviewPanel.jsx";
import {{ NotesPanel }} from "../components/NotesPanel.jsx";

export function StudioPage() {{
  return (
    <div className="app-shell">
      <div className="panel">
        <div className="pill">Content studio</div>
        <h1>Content App</h1>
        <p className="muted">{prompt}</p>
      </div>

      <div className="row two">
        <EditorShell />
        <PreviewPanel />
      </div>

      <NotesPanel />
    </div>
  );
}}
""".strip()


def tool_page_code(prompt: str, battery_mode: bool) -> str:
    extra = '<p className="muted">Battery-focused starter logic can be added next.</p>' if battery_mode else '<p className="muted">This is a clean generated tool starter.</p>'
    return f"""
import React from "react";
import {{ CalculatorForm }} from "../components/CalculatorForm.jsx";
import {{ ResultsPanel }} from "../components/ResultsPanel.jsx";
import {{ ExportActions }} from "../components/ExportActions.jsx";

export function ToolPage() {{
  return (
    <div className="app-shell">
      <div className="panel">
        <div className="pill">Tool workspace</div>
        <h1>Tool / Calculator</h1>
        <p className="muted">{prompt}</p>
        {extra}
      </div>

      <div className="row two">
        <CalculatorForm />
        <ResultsPanel />
      </div>

      <ExportActions />
    </div>
  );
}}
""".strip()


def sidebar_code() -> str:
    return """
import React from "react";

export function Sidebar() {
  return (
    <aside className="panel">
      <h3>Navigation</h3>
      <div className="card-grid">
        <div className="card">Overview</div>
        <div className="card">Customers</div>
        <div className="card">Deals</div>
        <div className="card">Reports</div>
      </div>
    </aside>
  );
}
""".strip()


def kpi_card_code() -> str:
    return """
import React from "react";

export function KpiCard({ title, value }) {
  return (
    <div className="card">
      <div className="pill">{title}</div>
      <h3>{value}</h3>
    </div>
  );
}
""".strip()


def inspector_code() -> str:
    return """
import React from "react";

export function InspectorPanel() {
  return (
    <section className="panel">
      <h3>Inspector</h3>
      <p className="muted">Use this space for details, selected records, and quick controls.</p>
    </section>
  );
}
""".strip()


def chat_shell_code() -> str:
    return """
import React from "react";

export function ChatShell() {
  return (
    <section className="panel">
      <h3>Conversation</h3>
      <div className="card">Assistant response area</div>
      <input className="input" placeholder="Ask something..." />
    </section>
  );
}
""".strip()


def tool_rail_code() -> str:
    return """
import React from "react";

export function ToolRail() {
  return (
    <aside className="panel">
      <h3>Tools</h3>
      <div className="card-grid">
        <div className="card">Search</div>
        <div className="card">Actions</div>
        <div className="card">History</div>
      </div>
    </aside>
  );
}
""".strip()


def memory_panel_code() -> str:
    return """
import React from "react";

export function MemoryPanel() {
  return (
    <section className="panel">
      <h3>Memory</h3>
      <p className="muted">Save notes, pinned answers, and reusable context here.</p>
    </section>
  );
}
""".strip()


def editor_shell_code() -> str:
    return """
import React from "react";

export function EditorShell() {
  return (
    <section className="panel">
      <h3>Editor</h3>
      <textarea className="input" rows={12} defaultValue="Start writing here..." />
    </section>
  );
}
""".strip()


def preview_panel_code() -> str:
    return """
import React from "react";

export function PreviewPanel() {
  return (
    <section className="panel">
      <h3>Preview</h3>
      <div className="card">Live preview area</div>
    </section>
  );
}
""".strip()


def notes_panel_code() -> str:
    return """
import React from "react";

export function NotesPanel() {
  return (
    <section className="panel">
      <h3>Notes</h3>
      <textarea className="input" rows={6} defaultValue="Draft notes..." />
    </section>
  );
}
""".strip()


def calculator_form_code() -> str:
    return """
import React from "react";

export function CalculatorForm() {
  return (
    <section className="panel">
      <h3>Inputs</h3>
      <div className="row">
        <input className="input" placeholder="Value 1" />
        <input className="input" placeholder="Value 2" />
        <button className="primary-btn">Calculate</button>
      </div>
    </section>
  );
}
""".strip()


def results_panel_code() -> str:
    return """
import React from "react";

export function ResultsPanel() {
  return (
    <section className="panel">
      <h3>Results</h3>
      <div className="card">Calculated output will appear here.</div>
    </section>
  );
}
""".strip()


def export_actions_code() -> str:
    return """
import React from "react";

export function ExportActions() {
  return (
    <section className="panel">
      <h3>Export</h3>
      <div className="row">
        <button className="primary-btn">Export JSON</button>
        <button className="primary-btn">Export PDF</button>
      </div>
    </section>
  );
}
""".strip()


def login_page_code() -> str:
    return """
import React from "react";

export function LoginPage() {
  return (
    <div className="app-shell">
      <section className="panel">
        <h1>Login</h1>
        <div className="row">
          <input className="input" placeholder="Email" />
          <input className="input" placeholder="Password" type="password" />
          <button className="primary-btn">Sign in</button>
        </div>
      </section>
    </div>
  );
}
""".strip()


def register_page_code() -> str:
    return """
import React from "react";

export function RegisterPage() {
  return (
    <div className="app-shell">
      <section className="panel">
        <h1>Create account</h1>
        <div className="row">
          <input className="input" placeholder="Name" />
          <input className="input" placeholder="Email" />
          <input className="input" placeholder="Password" type="password" />
          <button className="primary-btn">Create account</button>
        </div>
      </section>
    </div>
  );
}
""".strip()


def settings_page_code() -> str:
    return """
import React from "react";

export function SettingsPage() {
  return (
    <div className="app-shell">
      <section className="panel">
        <div className="pill">Settings</div>
        <h1>Preferences</h1>
        <p className="muted">Manage profile, appearance, and app defaults here.</p>
      </section>
    </div>
  );
}
""".strip()


def pricing_page_code() -> str:
    return """
import React from "react";

export function PricingPage() {
  return (
    <div className="app-shell">
      <section className="panel">
        <div className="pill">Billing</div>
        <h1>Plans</h1>
        <div className="card-grid">
          <div className="card"><h3>Starter</h3><p className="muted">$0</p></div>
          <div className="card"><h3>Pro</h3><p className="muted">$19/mo</p></div>
        </div>
      </section>
    </div>
  );
}
""".strip()


def scan_page_code() -> str:
    return """
import React from "react";

export function ScanPage() {
  return (
    <div className="app-shell">
      <section className="panel">
        <div className="pill">AI Tools</div>
        <h1>Scan / Diagnose</h1>
        <input className="input" type="file" />
        <div className="card" style={{ marginTop: 12 }}>Results and AI analysis will appear here.</div>
      </section>
    </div>
  );
}
""".strip()


def auth_code() -> str:
    return """
export function signIn(email, password) {
  return { ok: true, email, token: "demo-token" };
}

export function saveSession(session) {
  localStorage.setItem("demo_session", JSON.stringify(session));
}

export function readSession() {
  try {
    return JSON.parse(localStorage.getItem("demo_session") || "null");
  } catch {
    return null;
  }
}
""".strip()


def storage_code() -> str:
    return """
const KEY = "builder_generated_items";

export function readItems() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "[]");
  } catch {
    return [];
  }
}

export function saveItems(items) {
  localStorage.setItem(KEY, JSON.stringify(items || []));
}
""".strip()


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


def appliance_table_code() -> str:
    return """
import React from "react";

export function ApplianceTable() {
  return (
    <section className="panel">
      <h3>Appliances</h3>
      <div className="card">RV Fridge · Lights · Fan</div>
    </section>
  );
}
""".strip()


def package_json(app_type: str, systems: List[str]) -> str:
    deps = {
        "react": "^18.3.1",
        "react-dom": "^18.3.1",
    }
    if systems:
        deps["react-router-dom"] = "^6.26.1"
    return json.dumps({
        "name": "builder-generated-frontend",
        "private": True,
        "version": "0.0.1",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": deps,
        "devDependencies": {
            "vite": "^5.4.2"
        }
    }, indent=2)


def vite_config_code() -> str:
    return """
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  }
});
""".strip()


def index_html_code() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Builder Generated App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""".strip()


def frontend_gitignore() -> str:
    return """
node_modules
dist
.env
""".strip()


def backend_requirements(persistence_mode: str, systems: List[str]) -> str:
    pkgs = ["fastapi", "uvicorn", "pydantic"]
    if persistence_mode == "supabase":
        pkgs.append("supabase")
    return "\n".join(pkgs)


def backend_env_example(persistence_mode: str) -> str:
    lines = [
        "PORT=8000",
        "FRONTEND_ORIGIN=http://localhost:5173",
    ]
    if persistence_mode == "supabase":
        lines += [
            "SUPABASE_URL=your-project-url",
            "SUPABASE_KEY=your-service-key",
        ]
    return "\n".join(lines)


def backend_main_stub(persistence_mode: str, systems: List[str]) -> str:
    extra_imports = []
    extra_routes = []
    if "auth" in systems:
        extra_imports.append("from routes.auth import router as auth_router")
        extra_routes.append("app.include_router(auth_router, prefix='/api/auth', tags=['auth'])")
    if "storage" in systems:
        extra_imports.append("from routes.storage import router as storage_router")
        extra_routes.append("app.include_router(storage_router, prefix='/api/storage', tags=['storage'])")
    if "billing" in systems:
        extra_imports.append("from routes.billing import router as billing_router")
        extra_routes.append("app.include_router(billing_router, prefix='/api/billing', tags=['billing'])")
    if "ai-tools" in systems:
        extra_imports.append("from routes.ai_tools import router as ai_tools_router")
        extra_routes.append("app.include_router(ai_tools_router, prefix='/api/ai-tools', tags=['ai-tools'])")

    db_hint = ""
    if persistence_mode == "sqlite":
        db_hint = "\n# SQLite helper available in db.py\n"
    elif persistence_mode == "supabase":
        db_hint = "\n# Supabase helper available in supabase_client.py\n"

    return f"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
{chr(10).join(extra_imports)}

app = FastAPI(title="Generated App Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {{"status": "ok"}}
{db_hint}
{chr(10).join(extra_routes)}
""".strip()


def route_auth_py() -> str:
    return """
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class LoginPayload(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(payload: LoginPayload):
    return {"ok": True, "token": "demo-token", "email": payload.email}

@router.post("/register")
def register(payload: LoginPayload):
    return {"ok": True, "message": "Account created", "email": payload.email}
""".strip()


def route_storage_py(persistence_mode: str) -> str:
    engine = "sqlite" if persistence_mode == "sqlite" else ("supabase" if persistence_mode == "supabase" else "localstorage-compatible")
    return f"""
from fastapi import APIRouter

router = APIRouter()

_ITEMS = []

@router.get("/items")
def list_items():
    return {{"ok": True, "engine": "{engine}", "items": _ITEMS}}

@router.post("/seed")
def seed_items():
    _ITEMS.clear()
    _ITEMS.extend([
        {{"id": 1, "title": "First item"}},
        {{"id": 2, "title": "Second item"}}
    ])
    return {{"ok": True, "count": len(_ITEMS)}}
""".strip()


def route_billing_py() -> str:
    return """
from fastapi import APIRouter

router = APIRouter()

@router.get("/plans")
def plans():
    return {
        "ok": True,
        "plans": [
            {"id": "starter", "price": 0},
            {"id": "pro", "price": 19}
        ]
    }
""".strip()


def route_ai_tools_py() -> str:
    return """
from fastapi import APIRouter

router = APIRouter()

@router.post("/scan")
def scan():
    return {"ok": True, "message": "AI scan endpoint placeholder"}
""".strip()


def db_py() -> str:
    return """
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("app.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL)")
    conn.commit()
    conn.close()
""".strip()


def supabase_client_py() -> str:
    return """
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_supabase_config():
    return {"url": SUPABASE_URL, "key_present": bool(SUPABASE_KEY)}
""".strip()


def supabase_schema_sql() -> str:
    return """
create table if not exists profiles (
  id uuid primary key,
  email text,
  created_at timestamptz default now()
);

create table if not exists records (
  id bigint generated always as identity primary key,
  title text not null,
  created_at timestamptz default now()
);
""".strip()


def readme_md(project_name: str, app_type: str, builder_mode: str, systems: List[str], persistence_mode: str) -> str:
    systems_text = ", ".join(systems) if systems else "none"
    return f"""
# {project_name}

Generated with your AI Builder.

## App profile
- App type: {app_type}
- Builder mode: {builder_mode}
- Systems: {systems_text}
- Persistence: {persistence_mode}

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
""".strip()


def build_system_files(systems: List[str], persistence_mode: str) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    if "auth" in systems:
        files += [
            {"path": "frontend/src/pages/LoginPage.jsx", "language": "javascript", "content": login_page_code()},
            {"path": "frontend/src/pages/RegisterPage.jsx", "language": "javascript", "content": register_page_code()},
            {"path": "frontend/src/lib/auth.js", "language": "javascript", "content": auth_code()},
            {"path": "backend/routes/auth.py", "language": "python", "content": route_auth_py()},
        ]
    if "storage" in systems:
        files += [
            {"path": "frontend/src/lib/storage.js", "language": "javascript", "content": storage_code()},
            {"path": "backend/routes/storage.py", "language": "python", "content": route_storage_py(persistence_mode)},
        ]
    if "billing" in systems:
        files += [
            {"path": "frontend/src/pages/PricingPage.jsx", "language": "javascript", "content": pricing_page_code()},
            {"path": "backend/routes/billing.py", "language": "python", "content": route_billing_py()},
        ]
    if "settings" in systems:
        files += [
            {"path": "frontend/src/pages/SettingsPage.jsx", "language": "javascript", "content": settings_page_code()},
        ]
    if "ai-tools" in systems:
        files += [
            {"path": "frontend/src/pages/ScanPage.jsx", "language": "javascript", "content": scan_page_code()},
            {"path": "backend/routes/ai_tools.py", "language": "python", "content": route_ai_tools_py()},
        ]
    return files


def build_persistence_files(persistence_mode: str, systems: List[str]) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = [
        {"path": "backend/requirements.txt", "language": "text", "content": backend_requirements(persistence_mode, systems)},
        {"path": "backend/.env.example", "language": "text", "content": backend_env_example(persistence_mode)},
    ]
    if persistence_mode == "sqlite":
        files.append({"path": "backend/db.py", "language": "python", "content": db_py()})
    if persistence_mode == "supabase":
        files += [
            {"path": "backend/supabase_client.py", "language": "python", "content": supabase_client_py()},
            {"path": "backend/supabase_schema.sql", "language": "sql", "content": supabase_schema_sql()},
        ]
    return files


def base_frontend_support_files(project_name: str, app_type: str, builder_mode: str, systems: List[str], persistence_mode: str) -> List[Dict[str, Any]]:
    return [
        {"path": "frontend/package.json", "language": "json", "content": package_json(app_type, systems)},
        {"path": "frontend/vite.config.js", "language": "javascript", "content": vite_config_code()},
        {"path": "frontend/index.html", "language": "html", "content": index_html_code()},
        {"path": "frontend/.gitignore", "language": "text", "content": frontend_gitignore()},
        {"path": "README.md", "language": "markdown", "content": readme_md(project_name, app_type, builder_mode, systems, persistence_mode)},
    ]


def dedupe_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for file in files:
        seen[file["path"]] = file
    return list(seen.values())


def generate_code_bundle(prompt: str, app_type: str, builder_mode: str, style: str) -> List[Dict[str, Any]]:
    files = [
        {"path": "frontend/src/main.jsx", "language": "javascript", "content": main_jsx()},
        {"path": "frontend/src/App.jsx", "language": "javascript", "content": root_app_code(app_type, prompt)},
        {"path": "frontend/src/styles/app.css", "language": "css", "content": app_css(style)},
    ]

    if app_type == "admin panel":
        files += [
            {"path": "frontend/src/pages/DashboardPage.jsx", "language": "javascript", "content": dashboard_page_code(prompt)},
            {"path": "frontend/src/components/Sidebar.jsx", "language": "javascript", "content": sidebar_code()},
            {"path": "frontend/src/components/KpiCard.jsx", "language": "javascript", "content": kpi_card_code()},
            {"path": "frontend/src/components/InspectorPanel.jsx", "language": "javascript", "content": inspector_code()},
        ]
    elif app_type == "assistant app":
        files += [
            {"path": "frontend/src/pages/AssistantPage.jsx", "language": "javascript", "content": assistant_page_code(prompt)},
            {"path": "frontend/src/components/ChatShell.jsx", "language": "javascript", "content": chat_shell_code()},
            {"path": "frontend/src/components/ToolRail.jsx", "language": "javascript", "content": tool_rail_code()},
            {"path": "frontend/src/components/MemoryPanel.jsx", "language": "javascript", "content": memory_panel_code()},
        ]
    elif app_type == "content app":
        files += [
            {"path": "frontend/src/pages/StudioPage.jsx", "language": "javascript", "content": studio_page_code(prompt)},
            {"path": "frontend/src/components/EditorShell.jsx", "language": "javascript", "content": editor_shell_code()},
            {"path": "frontend/src/components/PreviewPanel.jsx", "language": "javascript", "content": preview_panel_code()},
            {"path": "frontend/src/components/NotesPanel.jsx", "language": "javascript", "content": notes_panel_code()},
        ]
    else:
        files += [
            {"path": "frontend/src/pages/ToolPage.jsx", "language": "javascript", "content": tool_page_code(prompt, builder_mode == "battery-planner")},
            {"path": "frontend/src/components/CalculatorForm.jsx", "language": "javascript", "content": calculator_form_code()},
            {"path": "frontend/src/components/ResultsPanel.jsx", "language": "javascript", "content": results_panel_code()},
            {"path": "frontend/src/components/ExportActions.jsx", "language": "javascript", "content": export_actions_code()},
        ]

    if re.search(r"(auth|login|signin|sign in)", prompt.lower()):
        files += [
            {"path": "frontend/src/pages/LoginPage.jsx", "language": "javascript", "content": login_page_code()},
            {"path": "frontend/src/lib/auth.js", "language": "javascript", "content": auth_code()},
        ]

    if builder_mode == "battery-planner":
        files += [
            {"path": "frontend/src/lib/batteryMath.js", "language": "javascript", "content": battery_math_code()},
            {"path": "frontend/src/components/ApplianceTable.jsx", "language": "javascript", "content": appliance_table_code()},
        ]

    return files


@app.post("/mutate")
def mutate(payload: MutateRequest):
    prompt = payload.prompt.strip()
    app_type = infer_app_type(prompt)
    builder_mode = infer_builder_mode(prompt)
    summary_style = infer_summary_style(prompt)
    complexity = infer_complexity(prompt, payload.complexity)
    systems = infer_systems(prompt, app_type, builder_mode, payload.systems)
    persistence_mode = infer_persistence_mode(prompt, systems, complexity, payload.persistence_mode)
    architecture = build_architecture(prompt, app_type, builder_mode, systems, complexity, persistence_mode, payload.architecture)
    modules = recommend_modules(prompt, app_type)
    layout = build_layout(prompt, payload.current_layout)
    file_tree = build_file_tree(app_type, builder_mode, prompt, systems, persistence_mode)
    routes = build_routes(app_type, prompt, systems)
    components = build_components(app_type, prompt, systems)
    summary = build_mutation_summary(layout, modules, app_type, builder_mode, systems, complexity, persistence_mode)

    return {
        "ok": True,
        "prompt": prompt,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "summary_style": summary_style,
        "complexity": complexity,
        "systems": systems,
        "persistence_mode": persistence_mode,
        "architecture": architecture,
        "layout_changes": layout,
        "module_changes": {"enable": modules, "disable": []},
        "file_tree": file_tree,
        "routes": routes,
        "components": components,
        "mutation_summary": summary,
        "next_best_actions": [
            "materialize files",
            "regenerate routes",
            "add inspector",
            "focus preview",
            "generate code",
        ],
    }


@app.post("/generate-code")
def generate_code(payload: GenerateCodeRequest):
    prompt = payload.prompt.strip()
    app_type = payload.app_type or infer_app_type(prompt)
    builder_mode = payload.builder_mode or infer_builder_mode(prompt)
    style = payload.style or "dark glass"
    complexity = infer_complexity(prompt, payload.complexity)
    systems = infer_systems(prompt, app_type, builder_mode, payload.systems)
    persistence_mode = infer_persistence_mode(prompt, systems, complexity, payload.persistence_mode)
    architecture = build_architecture(prompt, app_type, builder_mode, systems, complexity, persistence_mode, payload.architecture)
    project_name = payload.project_name.strip() or slugify(prompt[:60], "builder-project")

    files = generate_code_bundle(prompt, app_type, builder_mode, style)
    files += build_system_files(systems, persistence_mode)
    files += build_persistence_files(persistence_mode, systems)
    files += base_frontend_support_files(project_name, app_type, builder_mode, systems, persistence_mode)
    if payload.include_backend:
        files.append({"path": "backend/main.py", "language": "python", "content": backend_main_stub(persistence_mode, systems)})

    files = dedupe_files(files)

    routes = payload.routes or build_routes(app_type, prompt, systems)
    components = payload.components or build_components(app_type, prompt, systems)

    return {
        "ok": True,
        "prompt": prompt,
        "project_name": project_name,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "style": style,
        "complexity": complexity,
        "systems": systems,
        "persistence_mode": persistence_mode,
        "architecture": architecture,
        "generated_files": files,
        "files": files,
        "routes": routes,
        "components": components,
        "entry_file": "frontend/src/main.jsx",
        "app_file": "frontend/src/App.jsx",
        "summary": f"Generated {len(files)} files for a {app_type} in {builder_mode} mode with {persistence_mode} persistence.",
    }
