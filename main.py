from __future__ import annotations

import io
import json
import os
import re
import textwrap
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class MutateRequest(BaseModel):
    instruction: str = Field(..., min_length=1)
    files: List[Dict[str, Any]] = Field(default_factory=list)
    systems: List[str] = Field(default_factory=list)
    complexity: str = "mvp"
    architecture: Dict[str, Any] = Field(default_factory=dict)
    app_name: Optional[str] = None


class GenerateCodeRequest(BaseModel):
    idea: str = Field(..., min_length=1)
    systems: List[str] = Field(default_factory=list)
    complexity: str = "mvp"
    architecture: Dict[str, Any] = Field(default_factory=dict)
    app_name: Optional[str] = None
    existing_files: List[Dict[str, Any]] = Field(default_factory=list)


@dataclass
class GeneratedFile:
    path: str
    content: str
    kind: str = "code"
    system: str = "core"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "content": self.content,
            "kind": self.kind,
            "system": self.system,
        }


@dataclass
class BuildContext:
    idea: str
    app_name: str
    slug: str
    systems: List[str]
    complexity: str
    architecture: Dict[str, Any]
    frontend: str = "react-vite"
    backend: str = "fastapi"
    storage: str = "local"
    auth: str = "none"
    billing: str = "none"
    ai_mode: str = "mock"
    notes: List[str] = field(default_factory=list)


# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------

app = FastAPI(title="Builder Backend", version="2.0-system-aware")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value or "builder-app"


def title_from_idea(idea: str) -> str:
    cleaned = re.sub(r"\s+", " ", idea).strip()
    cleaned = re.sub(r"^[^a-zA-Z0-9]+", "", cleaned)
    if not cleaned:
        return "Builder App"
    words = cleaned.split(" ")[:4]
    return " ".join(w.capitalize() for w in words)


def normalize_systems(idea: str, systems: List[str]) -> List[str]:
    normalized = {s.strip().lower() for s in systems if s and s.strip()}
    idea_l = idea.lower()

    keywords = {
        "auth": ["auth", "login", "register", "sign in", "account", "user"],
        "dashboard": ["dashboard", "overview", "analytics", "status", "panel"],
        "storage": ["save", "history", "database", "records", "stored", "inventory"],
        "settings": ["settings", "profile", "preferences", "account settings"],
        "billing": ["billing", "subscription", "paywall", "stripe", "payment", "pro"],
        "ai-tools": ["ai", "assistant", "chat", "scan", "diagnostic", "generate", "analyze"],
        "admin": ["admin", "portal", "staff", "dealer", "technician", "moderation"],
        "tools": ["tool", "calculator", "converter", "planner", "estimator"],
    }

    for system, words in keywords.items():
        if any(word in idea_l for word in words):
            normalized.add(system)

    normalized.add("dashboard")
    normalized.add("settings")

    if "ai-tools" in normalized or "tools" in normalized:
        normalized.add("storage")

    ordered = [
        "auth",
        "dashboard",
        "storage",
        "settings",
        "billing",
        "ai-tools",
        "tools",
        "admin",
    ]
    return [s for s in ordered if s in normalized]


def infer_context(req: GenerateCodeRequest) -> BuildContext:
    app_name = (req.app_name or title_from_idea(req.idea)).strip()
    systems = normalize_systems(req.idea, req.systems)
    architecture = req.architecture or {}

    ctx = BuildContext(
        idea=req.idea,
        app_name=app_name,
        slug=slugify(app_name),
        systems=systems,
        complexity=(req.complexity or "mvp").lower(),
        architecture=architecture,
    )

    ctx.frontend = architecture.get("frontend") or "react-vite"
    ctx.backend = architecture.get("backend") or "fastapi"
    ctx.storage = architecture.get("storage") or ("sqlite" if "storage" in systems else "local")
    ctx.auth = architecture.get("auth") or ("demo" if "auth" in systems else "none")
    ctx.billing = architecture.get("billing") or ("stripe-mock" if "billing" in systems else "none")
    ctx.ai_mode = architecture.get("aiMode") or ("mock" if "ai-tools" in systems else "none")

    if ctx.complexity == "product":
        ctx.notes.append("Product mode enabled: generates deeper structure and placeholders for real integrations.")
    elif ctx.complexity == "starter":
        ctx.notes.append("Starter mode enabled: keeps files small and easier to edit.")
    else:
        ctx.notes.append("MVP mode enabled: balanced structure and speed.")

    return ctx


def safe_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def create_zip_bytes(files: List[GeneratedFile]) -> bytes:
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in files:
            zf.writestr(item.path, item.content)
    return memory.getvalue()


def build_readme(ctx: BuildContext) -> str:
    systems = ", ".join(ctx.systems) if ctx.systems else "core"
    return textwrap.dedent(
        f"""
        # {ctx.app_name}

        Generated by the AI Builder system-aware backend.

        ## App summary
        - Idea: {ctx.idea}
        - Complexity: {ctx.complexity}
        - Systems: {systems}
        - Frontend: {ctx.frontend}
        - Backend: {ctx.backend}
        - Storage: {ctx.storage}
        - Auth: {ctx.auth}
        - Billing: {ctx.billing}

        ## Run frontend
        ```bash
        cd frontend
        npm install
        npm run dev
        ```

        ## Run backend
        ```bash
        cd backend
        pip install -r requirements.txt
        uvicorn main:app --reload
        ```

        ## Notes
        {chr(10).join(f"- {n}" for n in ctx.notes)}
        """
    ).strip() + "\n"


def build_frontend_package_json(ctx: BuildContext) -> str:
    deps = {
        "react": "^18.3.1",
        "react-dom": "^18.3.1",
        "react-router-dom": "^6.30.1",
    }
    dev_deps = {
        "vite": "^5.4.19",
        "@vitejs/plugin-react": "^4.7.0",
    }
    return safe_json(
        {
            "name": ctx.slug,
            "private": True,
            "version": "0.1.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
            },
            "dependencies": deps,
            "devDependencies": dev_deps,
        }
    ) + "\n"


def build_frontend_vite_config() -> str:
    return textwrap.dedent(
        """
        import { defineConfig } from 'vite'
        import react from '@vitejs/plugin-react'

        export default defineConfig({
          plugins: [react()],
          server: {
            port: 5173,
          },
        })
        """
    ).strip() + "\n"


def build_frontend_index_html(ctx: BuildContext) -> str:
    return textwrap.dedent(
        f"""
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>{ctx.app_name}</title>
          </head>
          <body>
            <div id="root"></div>
            <script type="module" src="/src/main.jsx"></script>
          </body>
        </html>
        """
    ).strip() + "\n"


def build_frontend_main() -> str:
    return textwrap.dedent(
        """
        import React from 'react'
        import ReactDOM from 'react-dom/client'
        import { BrowserRouter } from 'react-router-dom'
        import App from './App'
        import './styles.css'

        ReactDOM.createRoot(document.getElementById('root')).render(
          <React.StrictMode>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </React.StrictMode>
        )
        """
    ).strip() + "\n"


def build_frontend_styles() -> str:
    return textwrap.dedent(
        """
        :root {
          font-family: Inter, system-ui, sans-serif;
          color: #e5e7eb;
          background: #0b1020;
        }

        * { box-sizing: border-box; }
        body { margin: 0; background: linear-gradient(180deg, #0b1020, #111827); }
        a { color: inherit; text-decoration: none; }
        button { cursor: pointer; }

        .app-shell {
          max-width: 1240px;
          margin: 0 auto;
          padding: 24px;
        }

        .hero, .panel, .card, .route-card {
          border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.04);
          border-radius: 20px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        }

        .hero { padding: 24px; display: grid; gap: 16px; }
        .panel { padding: 18px; }
        .grid { display: grid; gap: 16px; }
        .grid-3 { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
        .grid-2 { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
        .nav { display: flex; flex-wrap: wrap; gap: 10px; margin: 18px 0; }
        .chip {
          padding: 8px 12px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,0.1);
          background: rgba(255,255,255,0.06);
          font-size: 14px;
        }
        .cta {
          padding: 12px 16px;
          border-radius: 14px;
          border: none;
          background: #2563eb;
          color: white;
          font-weight: 700;
        }
        .section-title { font-size: 20px; font-weight: 700; margin: 0 0 12px; }
        .muted { opacity: 0.78; }
        .list { display: grid; gap: 10px; padding-left: 18px; }
        .topbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 14px;
          margin-bottom: 20px;
        }
        .route-list { display: grid; gap: 12px; }
        .route-card { padding: 16px; }
        .mini { font-size: 12px; opacity: 0.7; }
        .stack { display: flex; flex-wrap: wrap; gap: 8px; }
        @media (max-width: 720px) {
          .app-shell { padding: 14px; }
        }
        """
    ).strip() + "\n"


def build_system_registry(ctx: BuildContext) -> str:
    definitions = {
        "auth": {
            "title": "Authentication",
            "summary": "Login, register, session state, and protected routes.",
        },
        "dashboard": {
            "title": "Dashboard",
            "summary": "Overview, recent activity, quick actions, and stats.",
        },
        "storage": {
            "title": "Storage",
            "summary": "Saved items, history, persistence layer, and API data access.",
        },
        "settings": {
            "title": "Settings",
            "summary": "Profile, preferences, environment, and app behavior controls.",
        },
        "billing": {
            "title": "Billing",
            "summary": "Plans, entitlement gates, upgrade prompts, and subscription placeholders.",
        },
        "ai-tools": {
            "title": "AI Tools",
            "summary": "Prompt-powered tools, scans, analysis, or generation workflows.",
        },
        "tools": {
            "title": "Tools",
            "summary": "Calculators, planners, utilities, and guided workflows.",
        },
        "admin": {
            "title": "Admin",
            "summary": "Portal pages, moderation, staff access, and system visibility.",
        },
    }
    active = {key: definitions[key] for key in ctx.systems if key in definitions}
    return "export const systemRegistry = " + safe_json(active) + "\n"


def build_routes_file(ctx: BuildContext) -> str:
    routes: List[Dict[str, str]] = [
        {"path": "/", "label": "Home", "system": "core"},
    ]
    mapping = {
        "dashboard": ("/dashboard", "Dashboard"),
        "auth": ("/auth", "Auth"),
        "storage": ("/library", "Library"),
        "settings": ("/settings", "Settings"),
        "billing": ("/billing", "Billing"),
        "ai-tools": ("/ai-tools", "AI Tools"),
        "tools": ("/tools", "Tools"),
        "admin": ("/admin", "Admin"),
    }
    for system in ctx.systems:
        if system in mapping:
            path, label = mapping[system]
            routes.append({"path": path, "label": label, "system": system})

    return "export const appRoutes = " + safe_json(routes) + "\n"


def build_app_component(ctx: BuildContext) -> str:
    sections = []
    if "dashboard" in ctx.systems:
        sections.append(
            """
            <div className=\"panel\">
              <h2 className=\"section-title\">Dashboard System</h2>
              <div className=\"grid grid-3\">
                <div className=\"card panel\"><strong>Recent activity</strong><div className=\"muted\">Last actions and status updates.</div></div>
                <div className=\"card panel\"><strong>Stats</strong><div className=\"muted\">KPI placeholders connected to backend health and stored data.</div></div>
                <div className=\"card panel\"><strong>Quick actions</strong><div className=\"muted\">Fast launch buttons for the most common workflows.</div></div>
              </div>
            </div>
            """
        )
    if "ai-tools" in ctx.systems:
        sections.append(
            """
            <div className=\"panel\">
              <h2 className=\"section-title\">AI Tools System</h2>
              <div className=\"grid grid-2\">
                <div className=\"card panel\"><strong>Assistant</strong><div className=\"muted\">Prompt-driven workflow placeholder.</div></div>
                <div className=\"card panel\"><strong>Scan / Analyze</strong><div className=\"muted\">Upload, inspect, and return structured results.</div></div>
              </div>
            </div>
            """
        )
    if "storage" in ctx.systems:
        sections.append(
            """
            <div className=\"panel\">
              <h2 className=\"section-title\">Storage System</h2>
              <ul className=\"list\">
                <li>Saved records</li>
                <li>History timeline</li>
                <li>Persistence strategy: API + local fallback</li>
              </ul>
            </div>
            """
        )
    if "billing" in ctx.systems:
        sections.append(
            """
            <div className=\"panel\">
              <h2 className=\"section-title\">Billing System</h2>
              <div className=\"muted\">Plan cards and subscription-gating placeholders are included for future Stripe connection.</div>
            </div>
            """
        )
    if "admin" in ctx.systems:
        sections.append(
            """
            <div className=\"panel\">
              <h2 className=\"section-title\">Admin System</h2>
              <div className=\"muted\">Role-based portal placeholder with monitoring and management sections.</div>
            </div>
            """
        )

    sections_markup = "\n".join(s.strip() for s in sections) or (
        '<div className="panel"><h2 className="section-title">Core App</h2><div className="muted">Starter workspace ready for new systems.</div></div>'
    )

    return textwrap.dedent(
        f"""
        import {{ Link }} from 'react-router-dom'
        import {{ appRoutes }} from './config/routes'
        import {{ systemRegistry }} from './config/systemRegistry'

        const health = {{
          frontend: 'ready',
          backend: '{ctx.backend}',
          storage: '{ctx.storage}',
          auth: '{ctx.auth}',
          billing: '{ctx.billing}',
          ai: '{ctx.ai_mode}',
        }}

        export default function App() {{
          const systems = Object.entries(systemRegistry)

          return (
            <div className="app-shell">
              <div className="topbar">
                <div>
                  <div className="mini">AI Builder • System-aware app</div>
                  <h1>{ctx.app_name}</h1>
                  <div className="muted">{ctx.idea}</div>
                </div>
                <button className="cta">Primary action</button>
              </div>

              <div className="hero">
                <div className="stack">
                  <span className="chip">Complexity: {ctx.complexity}</span>
                  <span className="chip">Frontend: {ctx.frontend}</span>
                  <span className="chip">Backend: {ctx.backend}</span>
                  <span className="chip">Storage: {ctx.storage}</span>
                </div>

                <div className="nav">
                  {{appRoutes.map((route) => (
                    <Link key={{route.path}} to={{route.path}} className="chip">
                      {{route.label}}
                    </Link>
                  ))}}
                </div>
              </div>

              <div style={{{{ height: 16 }}}} />

              <div className="grid grid-2">
                <div className="panel">
                  <h2 className="section-title">Detected systems</h2>
                  <div className="route-list">
                    {{systems.map(([key, value]) => (
                      <div key={{key}} className="route-card">
                        <strong>{{value.title}}</strong>
                        <div className="muted">{{value.summary}}</div>
                        <div className="mini">System key: {{key}}</div>
                      </div>
                    ))}}
                  </div>
                </div>

                <div className="panel">
                  <h2 className="section-title">Project health</h2>
                  <div className="route-list">
                    {{Object.entries(health).map(([k, v]) => (
                      <div key={{k}} className="route-card">
                        <strong>{{k}}</strong>
                        <div className="muted">{{v}}</div>
                      </div>
                    ))}}
                  </div>
                </div>
              </div>

              <div style={{{{ height: 16 }}}} />

              {sections_markup}
            </div>
          )
        }}
        """
    ).strip() + "\n"


def build_backend_main(ctx: BuildContext) -> str:
    lines = [
        "from fastapi import FastAPI",
        "from fastapi.middleware.cors import CORSMiddleware",
        "",
        f"app = FastAPI(title={ctx.app_name!r})",
        "",
        "app.add_middleware(",
        "    CORSMiddleware,",
        "    allow_origins=['*'],",
        "    allow_credentials=True,",
        "    allow_methods=['*'],",
        "    allow_headers=['*'],",
        ")",
        "",
        "@app.get('/health')",
        "def health():",
        "    return {'status': 'ok', 'app': app.title}",
        "",
        "@app.get('/systems')",
        "def systems():",
        f"    return {{'systems': {safe_json(ctx.systems)}}}",
    ]

    if "ai-tools" in ctx.systems:
        lines.extend(
            [
                "",
                "@app.post('/analyze')",
                "def analyze(payload: dict):",
                "    text = payload.get('text') or payload.get('input') or ''",
                "    return {",
                "        'ok': True,",
                "        'mode': 'mock-ai',",
                "        'summary': f'Processed input of length {len(text)}',",
                "        'next_steps': ['Review result', 'Store result', 'Refine prompt'],",
                "    }",
            ]
        )

    if "storage" in ctx.systems:
        lines.extend(
            [
                "",
                "STORE = []",
                "",
                "@app.get('/records')",
                "def list_records():",
                "    return {'items': STORE}",
                "",
                "@app.post('/records')",
                "def create_record(payload: dict):",
                "    STORE.append(payload)",
                "    return {'ok': True, 'count': len(STORE), 'item': payload}",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def build_backend_requirements() -> str:
    return "fastapi\nuvicorn[standard]\npydantic\n\n"


def build_env_example() -> str:
    return textwrap.dedent(
        """
        VITE_API_BASE_URL=http://localhost:8000
        OPENAI_API_KEY=
        DATABASE_URL=
        STRIPE_SECRET_KEY=
        """
    ).strip() + "\n"


def build_gitignore() -> str:
    return textwrap.dedent(
        """
        node_modules/
        dist/
        .venv/
        __pycache__/
        *.pyc
        .env
        .DS_Store
        """
    ).strip() + "\n"


def build_system_plan_json(ctx: BuildContext) -> str:
    plan = {
        "appName": ctx.app_name,
        "idea": ctx.idea,
        "systems": ctx.systems,
        "complexity": ctx.complexity,
        "architecture": {
            "frontend": ctx.frontend,
            "backend": ctx.backend,
            "storage": ctx.storage,
            "auth": ctx.auth,
            "billing": ctx.billing,
            "aiMode": ctx.ai_mode,
        },
        "notes": ctx.notes,
    }
    return safe_json(plan) + "\n"


def build_generated_files(ctx: BuildContext) -> List[GeneratedFile]:
    files: List[GeneratedFile] = []

    files.extend(
        [
            GeneratedFile("README.md", build_readme(ctx), "doc", "core"),
            GeneratedFile(".gitignore", build_gitignore(), "config", "core"),
            GeneratedFile(".env.example", build_env_example(), "config", "core"),
            GeneratedFile("builder/system-plan.json", build_system_plan_json(ctx), "config", "core"),
            GeneratedFile("frontend/package.json", build_frontend_package_json(ctx), "config", "core"),
            GeneratedFile("frontend/vite.config.js", build_frontend_vite_config(), "config", "core"),
            GeneratedFile("frontend/index.html", build_frontend_index_html(ctx), "markup", "core"),
            GeneratedFile("frontend/src/main.jsx", build_frontend_main(), "code", "core"),
            GeneratedFile("frontend/src/styles.css", build_frontend_styles(), "style", "core"),
            GeneratedFile("frontend/src/App.jsx", build_app_component(ctx), "code", "core"),
            GeneratedFile("frontend/src/config/routes.js", build_routes_file(ctx), "code", "core"),
            GeneratedFile("frontend/src/config/systemRegistry.js", build_system_registry(ctx), "code", "core"),
            GeneratedFile("backend/main.py", build_backend_main(ctx), "code", "core"),
            GeneratedFile("backend/requirements.txt", build_backend_requirements(), "config", "core"),
        ]
    )

    if "auth" in ctx.systems:
        files.append(
            GeneratedFile(
                "frontend/src/systems/auth/auth.config.js",
                "export const authConfig = { mode: 'demo', protectedRoutes: ['/settings', '/dashboard'] }\n",
                "code",
                "auth",
            )
        )

    if "billing" in ctx.systems:
        files.append(
            GeneratedFile(
                "frontend/src/systems/billing/plans.js",
                "export const plans = [{ id: 'free', name: 'Free' }, { id: 'pro', name: 'Pro' }]\n",
                "code",
                "billing",
            )
        )

    if "storage" in ctx.systems:
        files.append(
            GeneratedFile(
                "frontend/src/systems/storage/storage.client.js",
                textwrap.dedent(
                    """
                    export async function fetchRecords(apiBase) {
                      const res = await fetch(`${apiBase}/records`)
                      if (!res.ok) throw new Error('Failed to fetch records')
                      return res.json()
                    }
                    """
                ).strip() + "\n",
                "code",
                "storage",
            )
        )

    if "ai-tools" in ctx.systems:
        files.append(
            GeneratedFile(
                "frontend/src/systems/ai/ai.client.js",
                textwrap.dedent(
                    """
                    export async function analyzeInput(apiBase, text) {
                      const res = await fetch(`${apiBase}/analyze`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text }),
                      })
                      if (!res.ok) throw new Error('Failed to analyze input')
                      return res.json()
                    }
                    """
                ).strip() + "\n",
                "code",
                "ai-tools",
            )
        )

    return files


def mutate_files(req: MutateRequest) -> List[Dict[str, Any]]:
    files = req.files or []
    instruction = req.instruction.strip().lower()
    result: List[Dict[str, Any]] = []

    for file in files:
        path = file.get("path", "")
        content = file.get("content", "")
        new_content = content

        if path.endswith("frontend/src/styles.css") and "dark" in instruction:
            if ".theme-dark" not in content:
                new_content += "\n.theme-dark { filter: saturate(1.05); }\n"

        if path.endswith("frontend/src/App.jsx"):
            if "sidebar" in instruction and "Workspace Rail" not in content:
                insert = textwrap.dedent(
                    """
                    <div className=\"panel\" style={{ marginBottom: 16 }}>
                      <h2 className=\"section-title\">Workspace Rail</h2>
                      <div className=\"muted\">Mutation added a simple sidebar placeholder for navigation and tools.</div>
                    </div>
                    """
                ).strip()
                new_content = content.replace('<div style={{ height: 16 }} />', insert + '\n\n              <div style={{ height: 16 }} />', 1)

            if "mobile" in instruction and "Built for smaller screens" not in new_content:
                new_content = new_content.replace(
                    "<div className=\"muted\">{ctx.idea}</div>",
                    "<div className=\"muted\">{ctx.idea}</div>\n                  <div className=\"mini\">Built for smaller screens and touch-first flows.</div>",
                ) if "{ctx.idea}" in new_content else new_content

        file_copy = dict(file)
        file_copy["content"] = new_content
        result.append(file_copy)

    return result


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "builder-backend",
        "version": "2.0-system-aware",
        "routes": ["/health", "/generate-code", "/mutate"],
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "builder-backend",
        "version": "2.0-system-aware",
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/generate-code")
def generate_code(req: GenerateCodeRequest) -> Dict[str, Any]:
    ctx = infer_context(req)
    files = build_generated_files(ctx)
    zip_bytes = create_zip_bytes(files)

    return {
        "ok": True,
        "app_name": ctx.app_name,
        "slug": ctx.slug,
        "systems": ctx.systems,
        "complexity": ctx.complexity,
        "architecture": {
            "frontend": ctx.frontend,
            "backend": ctx.backend,
            "storage": ctx.storage,
            "auth": ctx.auth,
            "billing": ctx.billing,
            "aiMode": ctx.ai_mode,
        },
        "files": [item.to_dict() for item in files],
        "zip": {
            "filename": f"{ctx.slug}.zip",
            "bytes": len(zip_bytes),
        },
        "planner": {
            "systemsDetected": ctx.systems,
            "notes": ctx.notes,
        },
    }


@app.post("/mutate")
def mutate(req: MutateRequest) -> Dict[str, Any]:
    mutated_files = mutate_files(req)
    return {
        "ok": True,
        "instruction": req.instruction,
        "systems": normalize_systems(req.instruction, req.systems),
        "files": mutated_files,
        "summary": {
            "filesChanged": len(mutated_files),
            "complexity": req.complexity,
        },
    }

