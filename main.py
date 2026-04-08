from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import re


app = FastAPI(title="Builder Backend v3 - Code Generator")


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
    return {"status": "ok", "service": "builder-backend-v3"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "builder-backend-v3"}


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


class GenerateCodeRequest(BaseModel):
    prompt: str
    app_type: str = ""
    builder_mode: str = ""
    style: str = "dark glass"
    routes: List[Dict[str, Any]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)


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
    if re.search(r"(export|report|download|pdf)", p):
        modules.add("export_report")
    if re.search(r"(sidebar|navigation|rail)", p):
        modules.add("sidebar_navigation")
    if re.search(r"(notes|brainstorm|scratch)", p):
        modules.add("notes_panel")
    if re.search(r"(dashboard|crm|saas)", p):
        modules.add("dashboard_shell")
    if re.search(r"(split|two column|2 column|2-column)", p):
        modules.add("split_workspace")
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
        "panels": {
            "sidebar": list(current_layout.get("panels", {}).get("sidebar", ["builder", "results", "modules", "mutations"])),
            "mainTop": list(current_layout.get("panels", {}).get("mainTop", ["brain", "command", "quickActions"])),
            "mainBottom": list(current_layout.get("panels", {}).get("mainBottom", ["planner", "results", "preview"])),
            "inspector": list(current_layout.get("panels", {}).get("inspector", ["status", "affiliate", "notes"])),
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


def build_file_tree(app_type: str, builder_mode: str, prompt: str) -> List[Dict[str, Any]]:
    base = [
        {"path": "src/App.jsx", "kind": "file", "role": "root app"},
        {"path": "src/main.jsx", "kind": "file", "role": "entry"},
        {"path": "src/styles/app.css", "kind": "file", "role": "global styles"},
        {"path": "src/components", "kind": "folder", "role": "ui components"},
        {"path": "src/pages", "kind": "folder", "role": "pages"},
        {"path": "src/lib", "kind": "folder", "role": "helpers"},
    ]
    if app_type == "admin panel":
        base += [
            {"path": "src/pages/DashboardPage.jsx", "kind": "file", "role": "dashboard page"},
            {"path": "src/components/Sidebar.jsx", "kind": "file", "role": "navigation"},
            {"path": "src/components/KpiCard.jsx", "kind": "file", "role": "metrics card"},
            {"path": "src/components/InspectorPanel.jsx", "kind": "file", "role": "details panel"},
        ]
    elif app_type == "assistant app":
        base += [
            {"path": "src/pages/AssistantPage.jsx", "kind": "file", "role": "assistant page"},
            {"path": "src/components/ChatShell.jsx", "kind": "file", "role": "chat interface"},
            {"path": "src/components/ToolRail.jsx", "kind": "file", "role": "tools rail"},
            {"path": "src/components/MemoryPanel.jsx", "kind": "file", "role": "memory / notes"},
        ]
    elif app_type == "content app":
        base += [
            {"path": "src/pages/StudioPage.jsx", "kind": "file", "role": "content studio"},
            {"path": "src/components/EditorShell.jsx", "kind": "file", "role": "editor"},
            {"path": "src/components/PreviewPanel.jsx", "kind": "file", "role": "content preview"},
            {"path": "src/components/NotesPanel.jsx", "kind": "file", "role": "notes"},
        ]
    else:
        base += [
            {"path": "src/pages/ToolPage.jsx", "kind": "file", "role": "tool page"},
            {"path": "src/components/CalculatorForm.jsx", "kind": "file", "role": "tool input"},
            {"path": "src/components/ResultsPanel.jsx", "kind": "file", "role": "tool output"},
            {"path": "src/components/ExportActions.jsx", "kind": "file", "role": "export controls"},
        ]
    if builder_mode == "battery-planner":
        base += [
            {"path": "src/lib/batteryMath.js", "kind": "file", "role": "calculation logic"},
            {"path": "src/components/ApplianceTable.jsx", "kind": "file", "role": "appliance rows"},
        ]
    if re.search(r"(auth|login|signin|sign in)", prompt.lower()):
        base += [
            {"path": "src/pages/LoginPage.jsx", "kind": "file", "role": "authentication"},
            {"path": "src/lib/auth.js", "kind": "file", "role": "auth helpers"},
        ]
    return base


def build_routes(app_type: str, prompt: str) -> List[Dict[str, str]]:
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
    if re.search(r"(auth|login|signin|sign in)", prompt.lower()):
        routes.append({"path": "/login", "component": "LoginPage", "reason": "auth entry"})
    return routes


def build_components(app_type: str, prompt: str) -> List[Dict[str, str]]:
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
    return base


def build_mutation_summary(layout: Dict[str, Any], modules: List[str], app_type: str, builder_mode: str) -> List[str]:
    summary = [
        f"App type detected: {app_type}",
        f"Builder mode detected: {builder_mode}",
        f"Layout shell: {layout['shell']}",
        f"Preview style: {layout['previewStyle']}",
        f"Active modules planned: {len(modules)}",
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
button, input { font: inherit; }
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
import {page_name} from "./pages/{page_name}.jsx";

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


def auth_code() -> str:
    return """
export function signIn(email, password) {
  return { ok: true, email, token: "demo-token" };
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


def generate_code_bundle(prompt: str, app_type: str, builder_mode: str, style: str) -> List[Dict[str, Any]]:
    files = [
        {"path": "src/main.jsx", "language": "javascript", "content": main_jsx()},
        {"path": "src/App.jsx", "language": "javascript", "content": root_app_code(app_type, prompt)},
        {"path": "src/styles/app.css", "language": "css", "content": app_css(style)},
    ]

    if app_type == "admin panel":
        files += [
            {"path": "src/pages/DashboardPage.jsx", "language": "javascript", "content": dashboard_page_code(prompt)},
            {"path": "src/components/Sidebar.jsx", "language": "javascript", "content": sidebar_code()},
            {"path": "src/components/KpiCard.jsx", "language": "javascript", "content": kpi_card_code()},
            {"path": "src/components/InspectorPanel.jsx", "language": "javascript", "content": inspector_code()},
        ]
    elif app_type == "assistant app":
        files += [
            {"path": "src/pages/AssistantPage.jsx", "language": "javascript", "content": assistant_page_code(prompt)},
            {"path": "src/components/ChatShell.jsx", "language": "javascript", "content": chat_shell_code()},
            {"path": "src/components/ToolRail.jsx", "language": "javascript", "content": tool_rail_code()},
            {"path": "src/components/MemoryPanel.jsx", "language": "javascript", "content": memory_panel_code()},
        ]
    elif app_type == "content app":
        files += [
            {"path": "src/pages/StudioPage.jsx", "language": "javascript", "content": studio_page_code(prompt)},
            {"path": "src/components/EditorShell.jsx", "language": "javascript", "content": editor_shell_code()},
            {"path": "src/components/PreviewPanel.jsx", "language": "javascript", "content": preview_panel_code()},
            {"path": "src/components/NotesPanel.jsx", "language": "javascript", "content": notes_panel_code()},
        ]
    else:
        files += [
            {"path": "src/pages/ToolPage.jsx", "language": "javascript", "content": tool_page_code(prompt, builder_mode == "battery-planner")},
            {"path": "src/components/CalculatorForm.jsx", "language": "javascript", "content": calculator_form_code()},
            {"path": "src/components/ResultsPanel.jsx", "language": "javascript", "content": results_panel_code()},
            {"path": "src/components/ExportActions.jsx", "language": "javascript", "content": export_actions_code()},
        ]

    if re.search(r"(auth|login|signin|sign in)", prompt.lower()):
        files += [
            {"path": "src/pages/LoginPage.jsx", "language": "javascript", "content": login_page_code()},
            {"path": "src/lib/auth.js", "language": "javascript", "content": auth_code()},
        ]

    if builder_mode == "battery-planner":
        files += [
            {"path": "src/lib/batteryMath.js", "language": "javascript", "content": battery_math_code()},
            {"path": "src/components/ApplianceTable.jsx", "language": "javascript", "content": appliance_table_code()},
        ]

    return files


@app.post("/mutate")
def mutate(payload: MutateRequest):
    prompt = payload.prompt.strip()
    app_type = infer_app_type(prompt)
    builder_mode = infer_builder_mode(prompt)
    summary_style = infer_summary_style(prompt)
    modules = recommend_modules(prompt, app_type)
    layout = build_layout(prompt, payload.current_layout)
    file_tree = build_file_tree(app_type, builder_mode, prompt)
    routes = build_routes(app_type, prompt)
    components = build_components(app_type, prompt)
    summary = build_mutation_summary(layout, modules, app_type, builder_mode)

    return {
        "ok": True,
        "prompt": prompt,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "summary_style": summary_style,
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

    files = generate_code_bundle(prompt, app_type, builder_mode, style)
    routes = payload.routes or build_routes(app_type, prompt)
    components = payload.components or build_components(app_type, prompt)

    return {
        "ok": True,
        "prompt": prompt,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "style": style,
        "generated_files": files,
        "routes": routes,
        "components": components,
        "entry_file": "src/main.jsx",
        "app_file": "src/App.jsx",
        "summary": f"Generated {len(files)} starter files for a {app_type} in {builder_mode} mode.",
    }
