from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import re
import json
import os
from pathlib import Path

try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None

app = FastAPI(title="Builder Backend v6 - Data Flow Generator")

KNOWLEDGE_STORE_PATH = Path(__file__).with_name("builder_knowledge_store.json")

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
    return {"status": "ok", "service": "builder-backend-v6"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "builder-backend-v6",
        "data_flow": True,
        "rv_monetization": True,
        "workspace_edit": bool(get_workspace_root()),
    }


@app.get("/knowledge-store")
def knowledge_store(limit: int = 12):
    items = load_global_knowledge_store()
    topics = []
    seen_topics = set()
    for item in items:
        topic = str(item.get("topic") or "").strip()
        if topic and topic not in seen_topics:
            seen_topics.add(topic)
            topics.append(topic)
    return {
        "ok": True,
        "count": len(items),
        "items": items[: max(1, min(limit, 50))],
        "top_topics": topics[:8],
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


class MutateRequest(BaseModel):
    prompt: str
    current_layout: Dict[str, Any] = Field(default_factory=dict)
    active_modules: List[str] = Field(default_factory=list)
    feature_state: Dict[str, Any] = Field(default_factory=dict)
    project_memory: Dict[str, Any] = Field(default_factory=dict)
    system_planner: Dict[str, Any] = Field(default_factory=dict)
    system_prompt: str = ""
    systems: List[str] = Field(default_factory=list)
    complexity: str = ""
    architecture: Dict[str, Any] = Field(default_factory=dict)


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
    project_memory: Dict[str, Any] = Field(default_factory=dict)
    feature_state: Dict[str, Any] = Field(default_factory=dict)
    system_planner: Dict[str, Any] = Field(default_factory=dict)
    system_prompt: str = ""
    persistence: str = ""
    rv_template_key: str = "rv_power"
    rv_camping_profile: str = "weekend"
    monetization_config: Dict[str, Any] = Field(default_factory=dict)


class OrchestrateRequest(BaseModel):
    prompt: str
    project_id: str = ""
    app_type: str = ""
    builder_mode: str = ""
    style: str = "dark glass"
    routes: List[Dict[str, Any]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    current_files: List[Dict[str, Any]] = Field(default_factory=list)
    current_layout: Dict[str, Any] = Field(default_factory=dict)
    active_modules: List[str] = Field(default_factory=list)
    feature_state: Dict[str, Any] = Field(default_factory=dict)
    project_memory: Dict[str, Any] = Field(default_factory=dict)
    system_planner: Dict[str, Any] = Field(default_factory=dict)
    system_prompt: str = ""
    systems: List[str] = Field(default_factory=list)
    complexity: str = ""
    architecture: Dict[str, Any] = Field(default_factory=dict)
    persistence: str = ""
    rv_template_key: str = "rv_power"
    rv_camping_profile: str = "weekend"
    monetization_config: Dict[str, Any] = Field(default_factory=dict)


class ChatAgentRequest(BaseModel):
    message: str
    project_id: str = ""
    current_prompt: str = ""
    project_memory: Dict[str, Any] = Field(default_factory=dict)
    feature_state: Dict[str, Any] = Field(default_factory=dict)
    generated_files: List[Dict[str, Any]] = Field(default_factory=list)
    routes: List[Dict[str, Any]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    system_planner: Dict[str, Any] = Field(default_factory=dict)
    chat_mode: str = "evolve"
    reply_preference: str = "balanced"
    recent_messages: List[Dict[str, str]] = Field(default_factory=list)


class RepoEditRequest(BaseModel):
    prompt: str
    current_files: List[Dict[str, Any]] = Field(default_factory=list)
    app_type: str = ""
    builder_mode: str = ""
    style: str = "dark glass"
    target_scope: str = "fullstack"
    project_memory: Dict[str, Any] = Field(default_factory=dict)
    feature_state: Dict[str, Any] = Field(default_factory=dict)
    system_planner: Dict[str, Any] = Field(default_factory=dict)
    systems: List[str] = Field(default_factory=list)
    complexity: str = ""
    architecture: Dict[str, Any] = Field(default_factory=dict)
    persistence: str = ""


class WorkspaceEditRequest(RepoEditRequest):
    workspace_subdir: str = ""

class RvMonetizationRequest(BaseModel):
    template_key: str = "rv_power"
    camping_profile: str = "weekend"
    battery_ah: float = 0
    solar_watts: float = 0
    inverter_watts: float = 0
    monthly_price: float = 9.99
    yearly_price: float = 69.99
    affiliate_tag_ca: str = "rvinspector03-20"
    affiliate_tag_us: str = "rvinspectorpr-20"



def build_rv_monetization_plan(template_key: str, camping_profile: str, battery_ah: float, solar_watts: float, inverter_watts: float, monthly_price: float, yearly_price: float, affiliate_tag_ca: str, affiliate_tag_us: str) -> Dict[str, Any]:
    battery_ah = max(battery_ah, 0)
    solar_watts = max(solar_watts, 0)
    inverter_watts = max(inverter_watts, 0)
    featured_products = []
    if battery_ah >= 170:
        featured_products.append({"title": "200Ah LiFePO4 Battery Bank", "slug": "200ah-lifepo4-battery-bank"})
    elif battery_ah >= 90:
        featured_products.append({"title": "100Ah LiFePO4 Battery", "slug": "100ah-lifepo4-battery"})
    if solar_watts >= 360:
        featured_products.append({"title": "400W Solar Expansion Kit", "slug": "400w-solar-expansion-kit"})
    elif solar_watts >= 180:
        featured_products.append({"title": "200W Solar Starter Kit", "slug": "200w-solar-starter-kit"})
    if inverter_watts >= 2400:
        featured_products.append({"title": "3000W Pure Sine Inverter", "slug": "3000w-pure-sine-inverter"})
    elif inverter_watts >= 1500:
        featured_products.append({"title": "2000W Pure Sine Inverter", "slug": "2000w-pure-sine-inverter"})
    featured_products.append({"title": "Battery Monitor + Shunt", "slug": "battery-monitor-shunt"})

    profile_label = {
        "weekend": "Weekend",
        "boondock": "Boondock",
        "summer": "Hot Weather",
        "shoulder": "Shoulder Season",
    }.get(camping_profile, camping_profile.title() or "Weekend")
    estimated_aov = max(199, round((battery_ah * 1.2) + (solar_watts * 0.35) + (inverter_watts * 0.12)))
    commission_low = round(estimated_aov * 0.03)
    commission_high = round(estimated_aov * 0.06)
    return {
        "template_key": template_key,
        "camping_profile": profile_label,
        "subscription": {
            "monthly_price": monthly_price,
            "yearly_price": yearly_price,
            "trial_days": 7,
            "positioning": f"Offer saved plans, premium RV guidance, and exported reports for ${monthly_price:.2f}/mo or ${yearly_price:.2f}/yr.",
        },
        "affiliate": {
            "affiliate_tag_ca": affiliate_tag_ca,
            "affiliate_tag_us": affiliate_tag_us,
            "estimated_commission_range": f"${commission_low}-${commission_high}",
            "featured_products": featured_products,
        },
        "paywall_hooks": [
            "Saved RV plans and scan history",
            "Printable premium export",
            "Advanced diagnostics / sizing guidance",
        ],
    }




def monetization_data_code(plan: Dict[str, Any]) -> str:
    plan_json = json.dumps(plan, indent=2)
    return f"""
export const monetizationPlan = {plan_json};

export const featuredProducts = monetizationPlan.featuredProducts || [];
export const paywallHooks = monetizationPlan.paywallHooks || [];
""".strip()


def monetization_panel_code() -> str:
    return """
import React from "react";
import { monetizationPlan, featuredProducts, paywallHooks } from "../lib/monetization.js";

export function MonetizationPanel() {
  return (
    <section className="panel monetization-panel">
      <div className="module-top">
        <div>
          <div className="pill">Premium RV upgrade</div>
          <h3 style={{ margin: "10px 0 6px" }}>{monetizationPlan.headline || "Upgrade your RV setup"}</h3>
          <p className="muted">{monetizationPlan.subscription?.pitch || "Unlock deeper planning and premium RV help."}</p>
        </div>
        <div className="pricing-stack">
          <div className="price-chip">${monetizationPlan.subscription?.monthlyPrice || 9.99}/mo</div>
          <div className="price-chip">${monetizationPlan.subscription?.yearlyPrice || 69.99}/yr</div>
          <div className="price-chip">{monetizationPlan.subscription?.trialDays || 7}-day trial</div>
        </div>
      </div>

      <div className="card-grid" style={{ marginTop: 12 }}>
        {paywallHooks.map((hook) => (
          <div key={hook} className="card">
            <strong>{hook}</strong>
            <div className="muted" style={{ marginTop: 6 }}>Premium conversion hook included in this generated app.</div>
          </div>
        ))}
      </div>

      <div className="card-grid" style={{ marginTop: 12 }}>
        {featuredProducts.map((item) => (
          <div key={item.slug || item.title} className="card">
            <strong>{item.title}</strong>
            <div className="muted" style={{ marginTop: 6 }}>{item.fit}</div>
            <div className="module-top" style={{ marginTop: 10 }}>
              <span className="pill">{item.cta || "Affiliate-ready"}</span>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <a className="pill" href={item.affiliateUrlCa} target="_blank" rel="noreferrer">Amazon.ca</a>
                <a className="pill" href={item.affiliateUrlUs} target="_blank" rel="noreferrer">Amazon.com</a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
""".strip()


def monetization_styles_css() -> str:
    return """
.monetization-panel {
  border-color: rgba(102, 217, 239, 0.22);
  box-shadow: inset 0 0 0 1px rgba(102, 217, 239, 0.08);
}
.pricing-stack {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.price-chip {
  border-radius: 999px;
  padding: 10px 14px;
  font-weight: 700;
  color: #07111f;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
}
""".strip()

@app.post("/rv-monetization-plan")
def rv_monetization_plan(payload: RvMonetizationRequest):
    return {
        "ok": True,
        "monetization": build_rv_monetization_plan(
            payload.template_key,
            payload.camping_profile,
            payload.battery_ah,
            payload.solar_watts,
            payload.inverter_watts,
            payload.monthly_price,
            payload.yearly_price,
            payload.affiliate_tag_ca,
            payload.affiliate_tag_us,
        ),
    }


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


def normalize_chat_mode(mode: str, has_generated_app: bool) -> str:
    if mode == "mutate" and has_generated_app:
        return "mutate"
    return "evolve"


def is_suggestion_request(message: str) -> bool:
    return bool(re.search(r"(suggest|recommend|idea|ideas|what should|what can|help me choose|best option)", message))


def is_explanation_request(message: str) -> bool:
    return bool(re.search(r"(why|how does|how do|what is|explain|walk me through|show me what|can it|can you|could you|does it|will it|is it able)", message))


def is_question_message(message: str) -> bool:
    stripped = str(message or "").strip()
    if not stripped:
        return False
    if "?" in stripped:
        return True
    return bool(re.match(r"^(can|could|would|will|does|do|is|are|am|should|what|why|how|when|where)\b", stripped))


def is_followup_question(message: str, recent_messages: List[Dict[str, str]]) -> bool:
    stripped = str(message or "").strip().lower()
    if not stripped:
        return False
    if is_question_message(stripped):
        return True
    if len(stripped.split()) > 5 or not recent_messages:
        return False
    return bool(re.fullmatch(r"(why|how|what about that|what about this|and backend|and frontend|what next|can it|does it|will it)", stripped))


def normalize_reply_preference(preference: str) -> str:
    normalized = str(preference or "balanced").strip().lower()
    if normalized in {"answer", "clarify", "apply", "balanced"}:
        return normalized
    return "balanced"


def summarize_recent_context(recent_messages: List[Dict[str, str]]) -> str:
    parts: List[str] = []
    for item in recent_messages[-4:]:
        role = str(item.get("role") or "user").strip().lower()
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        label = "You" if role == "user" else "Builder"
        parts.append(f"{label}: {text}")
    return " ".join(parts)


def build_followup_actions(response_type: str, has_generated_app: bool) -> List[Dict[str, str]]:
    if response_type == "answer":
        return [
            {"label": "Tell me more", "prompt": "tell me more about that", "mode": "evolve"},
            {"label": "Ask what you need", "prompt": "ask me what details you need first", "mode": "evolve"},
            {"label": "Apply this now", "prompt": "apply that now", "mode": "mutate" if has_generated_app else "evolve"},
        ]
    if response_type == "explain":
        return [
            {"label": "Make it simpler", "prompt": "make that simpler", "mode": "evolve"},
            {"label": "What do you recommend?", "prompt": "what do you recommend next", "mode": "evolve"},
            {"label": "Apply this plan", "prompt": "apply that plan now", "mode": "mutate" if has_generated_app else "evolve"},
        ]
    if response_type == "clarify":
        return [
            {"label": "Ask me the questions", "prompt": "ask me the questions one by one", "mode": "evolve"},
            {"label": "Keep it simple", "prompt": "keep the first version simple", "mode": "evolve"},
            {"label": "Show a starter idea", "prompt": "show me a good starter idea", "mode": "evolve"},
        ]
    return []


def is_mutation_request(message: str) -> bool:
    return bool(re.search(r"(add|remove|change|update|edit|fix|improve|make it|turn it into|refactor|polish|redesign)", message))


def needs_research(message: str) -> bool:
    return bool(re.search(r"(research|search|look up|find information|find info|documentation|docs|latest|compare|comparison|best library|best package|which library|which package|sdk|integration guide|api docs)", message))


def is_affirmative(message: str) -> bool:
    return bool(re.fullmatch(r"\s*(yes|yeah|yep|sure|ok|okay|do it|sounds good|please do)\s*", message))


def is_negative(message: str) -> bool:
    return bool(re.fullmatch(r"\s*(no|nope|nah|not now|skip it|dont|don't)\s*", message))


def infer_decisions_from_message(message: str, previous_memory: Dict[str, Any]) -> Dict[str, Any]:
    lowered = message.lower().strip()
    decisions = dict(previous_memory.get("decisions") or {})
    unresolved_questions = list(previous_memory.get("unresolved_questions") or [])

    if re.search(r"(login|auth|account|sign in|signin|user account|protected)", lowered):
        decisions["auth_required"] = True
    elif re.search(r"(public|open to everyone|no login|without login|guest only)", lowered):
        decisions["auth_required"] = False

    if re.search(r"(billing|subscription|stripe|paid plan|premium|checkout)", lowered):
        decisions["billing_enabled"] = True
    elif re.search(r"(free only|no billing|without billing|no payments|dont charge|don't charge)", lowered):
        decisions["billing_enabled"] = False

    if re.search(r"(dashboard|admin|portal|crm|saas)", lowered):
        decisions["product_shape"] = "dashboard"
    elif re.search(r"(landing page|marketing page|homepage)", lowered):
        decisions["product_shape"] = "landing"
    elif re.search(r"(tool|calculator|estimator)", lowered):
        decisions["product_shape"] = "tool"
    elif re.search(r"(assistant|chat app|copilot|agent)", lowered):
        decisions["product_shape"] = "assistant"

    if unresolved_questions and (is_affirmative(lowered) or is_negative(lowered)):
        current_question = unresolved_questions[0].lower()
        answer_value = is_affirmative(lowered)
        if "sign in" in current_question or "open to everyone" in current_question:
            decisions["auth_required"] = answer_value
        elif "payments" in current_question or "subscriptions" in current_question:
            decisions["billing_enabled"] = answer_value
        elif "simple tool" in current_question or "saas-style" in current_question:
            decisions["product_shape"] = "tool" if answer_value else decisions.get("product_shape", "dashboard")

    return decisions


def apply_decisions_to_systems(systems: List[str], decisions: Dict[str, Any]) -> List[str]:
    resolved = set(systems)
    if decisions.get("auth_required") is True:
        resolved.add("auth")
    if decisions.get("auth_required") is False and "auth" in resolved:
        resolved.discard("auth")
    if decisions.get("billing_enabled") is True:
        resolved.add("billing")
    if decisions.get("billing_enabled") is False and "billing" in resolved:
        resolved.discard("billing")
    shape = decisions.get("product_shape")
    if shape == "dashboard":
        resolved.add("dashboard")
    if shape == "assistant":
        resolved.add("ai-tools")
    return sorted(resolved)


def apply_decisions_to_product(app_type: str, builder_mode: str, decisions: Dict[str, Any]) -> tuple[str, str]:
    shape = decisions.get("product_shape")
    next_app_type = app_type
    next_builder_mode = builder_mode
    if shape == "dashboard":
        next_app_type = "admin panel"
        next_builder_mode = "dashboard-builder"
    elif shape == "assistant":
        next_app_type = "assistant app"
        next_builder_mode = "general-builder"
    elif shape == "landing":
        next_app_type = "tool app"
        next_builder_mode = "site-builder"
    elif shape == "tool":
        next_app_type = "tool app"
        if next_builder_mode == "dashboard-builder":
            next_builder_mode = "general-builder"
    return next_app_type, next_builder_mode


def build_research_query(message: str, app_type: str, builder_mode: str) -> str:
    parts = [message.strip()]
    if app_type:
        parts.append(app_type)
    if builder_mode:
        parts.append(builder_mode)
    parts.append("web app development best practices")
    return " ".join(part for part in parts if part)


def normalize_repo_scope(scope: str) -> str:
    normalized = str(scope or "").strip().lower()
    if normalized in {"frontend", "backend", "fullstack"}:
        return normalized
    if normalized in {"full-stack", "full_stack", "frontend-and-backend", "frontend+backend"}:
        return "fullstack"
    return "fullstack"


def normalize_repo_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for index, item in enumerate(files or []):
        path = str((item or {}).get("path") or f"file-{index + 1}.txt").lstrip("/")
        normalized.append({
            "path": path,
            "content": str((item or {}).get("content") or ""),
            "language": (item or {}).get("language") or "text",
        })
    return normalized


def matches_repo_scope(path: str, scope: str) -> bool:
    lower = str(path or "").lower()
    normalized_scope = normalize_repo_scope(scope)
    is_backend = lower.startswith("backend/") or lower.endswith(".py") or lower.endswith("requirements.txt") or lower.endswith(".sql")
    is_frontend = lower.startswith("frontend/") or lower.startswith("src/") or lower.endswith(".jsx") or lower.endswith(".tsx") or lower.endswith(".js") or lower.endswith(".ts") or lower.endswith(".css") or lower.endswith("index.html")
    if normalized_scope == "frontend":
        return is_frontend and not is_backend
    if normalized_scope == "backend":
        return is_backend and not lower.startswith("frontend/")
    return is_frontend or is_backend or lower in {"readme.md", ".env.example", ".gitignore"}


def merge_repo_edit_files(current_files: List[Dict[str, Any]], generated_files: List[Dict[str, Any]], target_scope: str) -> tuple[List[Dict[str, Any]], List[str]]:
    normalized_current = normalize_repo_files(current_files)
    normalized_generated = normalize_repo_files(generated_files)
    merged: Dict[str, Dict[str, Any]] = {item["path"]: item for item in normalized_current}
    changed_paths: List[str] = []

    for generated in normalized_generated:
        path = generated["path"]
        if not matches_repo_scope(path, target_scope):
            continue
        previous = merged.get(path)
        merged[path] = generated
        if previous is None or previous.get("content") != generated.get("content"):
            changed_paths.append(path)

    return list(merged.values()), sorted(set(changed_paths))


def get_workspace_root() -> Optional[Path]:
    raw_root = str(os.getenv("BUILDER_WORKSPACE_ROOT", "")).strip()
    if not raw_root:
        return None
    root = Path(raw_root).expanduser().resolve()
    return root if root.exists() and root.is_dir() else None


def resolve_workspace_target(root: Path, workspace_subdir: str = "") -> Path:
    relative = str(workspace_subdir or "").strip().replace("\\", "/").strip("/")
    target = (root / relative).resolve() if relative else root.resolve()
    if target != root and root not in target.parents:
        raise ValueError("Workspace target must stay inside the configured workspace root.")
    return target


def write_workspace_files(root: Path, files: List[Dict[str, Any]], changed_paths: List[str]) -> Dict[str, Any]:
    written: List[str] = []
    backup_entries: List[Dict[str, Any]] = []
    file_map = {str(item.get("path") or ""): item for item in normalize_repo_files(files)}
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_root = root / ".builder-backups" / timestamp
    manifest_rel_path = f".builder-backups/{timestamp}/manifest.json"
    for relative_path in changed_paths:
        file_entry = file_map.get(relative_path)
        if not file_entry:
            continue
        destination = (root / relative_path).resolve()
        if destination != root and root not in destination.parents:
            raise ValueError(f"Refusing to write outside workspace root: {relative_path}")
        if destination.exists():
            backup_target = (backup_root / relative_path).resolve()
            backup_target.parent.mkdir(parents=True, exist_ok=True)
            backup_target.write_text(destination.read_text(encoding="utf-8"), encoding="utf-8")
            backup_entries.append({
                "path": relative_path,
                "backup_path": str(Path(".builder-backups") / timestamp / relative_path).replace("\\", "/"),
                "status": "updated",
            })
        else:
            backup_entries.append({
                "path": relative_path,
                "backup_path": "",
                "status": "created",
            })
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(str(file_entry.get("content") or ""), encoding="utf-8")
        written.append(relative_path)
    manifest_path = (root / manifest_rel_path).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "files": backup_entries,
    }, indent=2), encoding="utf-8")
    return {
        "written_files": written,
        "backup_manifest": manifest_rel_path,
        "backup_entries": backup_entries,
        "backup_count": len([item for item in backup_entries if item.get("backup_path")]),
    }


def run_research(query: str, max_results: int = 5) -> Dict[str, Any]:
    if not DDGS:
        return {
            "available": False,
            "query": query,
            "findings": [],
            "error": "Web research is unavailable until duckduckgo-search is installed on the backend.",
        }

    try:
        findings: List[Dict[str, str]] = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                findings.append({
                    "title": item.get("title") or "Untitled result",
                    "url": item.get("href") or "",
                    "snippet": item.get("body") or "",
                })
        return {
            "available": True,
            "query": query,
            "findings": findings,
            "error": "",
        }
    except Exception as error:
        return {
            "available": False,
            "query": query,
            "findings": [],
            "error": str(error),
        }


def summarize_research(research: Dict[str, Any], app_type: str, builder_mode: str) -> str:
    findings = research.get("findings") or []
    if findings:
        top_titles = ", ".join(item.get("title", "source") for item in findings[:3])
        return (
            f"I researched that for a {app_type} in {builder_mode} mode. "
            f"Top references point to: {top_titles}. "
            "Use the findings below to choose the path you want, then I can apply it."
        )
    return (
        "I tried to research that, but the backend could not fetch external results right now. "
        f"Reason: {research.get('error') or 'unknown research error'}."
    )


def infer_research_focus(text: str) -> str:
    lowered = text.lower()
    focus_patterns = [
        ("auth", r"(auth|login|sign in|signin|oauth|session|clerk|nextauth|authjs|supabase auth|firebase auth)"),
        ("billing", r"(billing|stripe|subscription|checkout|payments|pricing|paywall)"),
        ("database", r"(database|db|storage|supabase|postgres|sqlite|persistence|saved data)"),
        ("ai", r"(ai|assistant|chat|llm|openai|anthropic|rag|embedding|tool calling)"),
        ("mobile", r"(mobile|responsive|tablet|touch)"),
        ("ui", r"(ui|design|layout|navigation|sidebar|dashboard)"),
        ("deployment", r"(deploy|deployment|hosting|render|vercel|cloudflare|docker)"),
    ]
    for label, pattern in focus_patterns:
        if re.search(pattern, lowered):
            return label
    return "general"


def build_research_recommendation(research: Optional[Dict[str, Any]], has_generated_app: bool, systems: List[str], app_type: str) -> Dict[str, str]:
    if not research or not research.get("findings"):
        return {}

    query = str(research.get("query") or "this topic").strip()
    findings = list(research.get("findings") or [])
    top_titles = [str(item.get("title") or "").strip() for item in findings[:2] if item.get("title")]
    source_line = ", ".join(top_titles) if top_titles else "the saved research"
    combined_text = " ".join(
        [
            query,
            *top_titles,
            *[str(item.get("snippet") or "") for item in findings[:3]],
        ]
    )
    focus = infer_research_focus(combined_text)
    system_line = ", ".join(systems[:3]) if systems else "core project systems"

    if focus == "auth":
        prompt = "Add authentication using the strongest researched approach, with protected routes, account state, and a simple sign-in flow. Keep the implementation practical for this project."
        label = "Apply researched auth"
        rationale_points = [
            "The research focus is authentication, so the next change should be login and access control rather than unrelated UI work.",
            f"This project already points toward {system_line}, which benefits from a clear account boundary.",
            f"The strongest matching sources were {source_line}, so I am using that direction instead of guessing.",
        ]
    elif focus == "billing":
        prompt = "Add billing using the strongest researched approach, including pricing, checkout entry points, and clear paid-tier wiring for this project."
        label = "Apply researched billing"
        rationale_points = [
            "The research focus is billing, so the recommendation targets pricing and checkout flow directly.",
            f"This project already depends on {system_line}, so billing should connect to the current product structure rather than be added as an isolated screen.",
            f"The strongest matching sources were {source_line}, which gives the recommendation a concrete base.",
        ]
    elif focus == "database":
        prompt = "Add persistent storage using the strongest researched approach, with practical schema choices, saved data flow, and project-safe defaults."
        label = "Apply researched storage"
        rationale_points = [
            "The research focus is storage, so persistence is the highest-value next step.",
            f"This project already uses or plans {system_line}, which makes saved data more useful than another surface-level feature.",
            f"The recommendation is anchored in {source_line} rather than a generic stack guess.",
        ]
    elif focus == "ai":
        prompt = "Add the researched AI implementation approach, including chat flow, tool integration, and the simplest production-ready structure for this project."
        label = "Apply researched AI"
        rationale_points = [
            "The research focus is AI implementation, so the recommendation prioritizes chat flow and tool wiring.",
            f"That fits the current project direction around {system_line} better than a broad rewrite.",
            f"The strongest matching sources were {source_line}, so the choice is evidence-backed.",
        ]
    elif focus == "mobile":
        prompt = "Improve this project for mobile using the strongest researched responsive approach, focusing on layout, navigation, spacing, and touch-friendly controls."
        label = "Apply researched mobile improvements"
        rationale_points = [
            "The research focus is mobile usability, so the recommendation targets layout and navigation instead of adding new business logic.",
            f"That is a practical improvement for the current systems: {system_line}.",
            f"The choice is based on {source_line}, not a generic responsive checklist.",
        ]
    elif focus == "ui":
        prompt = "Refine the interface using the strongest researched UI approach, improving navigation, readability, layout hierarchy, and user flow without overbuilding it."
        label = "Apply researched UI"
        rationale_points = [
            "The research focus is interface quality, so the recommendation targets readability and navigation first.",
            f"That supports the current system mix of {system_line} without forcing a product-direction change.",
            f"The recommendation follows {source_line}, which gives it a stronger basis than personal taste alone.",
        ]
    elif focus == "deployment":
        prompt = "Prepare this project using the strongest researched deployment approach, including environment setup, hosting assumptions, and production-safe project structure."
        label = "Apply researched deployment plan"
        rationale_points = [
            "The research focus is deployment, so the recommendation targets hosting and production setup directly.",
            f"That is a better next move for the current project systems: {system_line}.",
            f"The choice is grounded in {source_line}, which reduces blind deployment decisions.",
        ]
    else:
        if has_generated_app:
            prompt = f"Use the strongest option from the saved research about {query} and apply it to the current project in a practical way."
            label = "Apply researched recommendation"
        else:
            prompt = f"Build the first version of this project using the strongest option from the saved research about {query}, keeping the result focused and practical."
            label = "Build from researched recommendation"
        rationale_points = [
            f"The research topic is {query}, so I am using that as the basis for the next change.",
            f"The current project shape around {system_line} makes this recommendation more relevant than a generic starter template.",
            f"The strongest matching sources were {source_line}, so the recommendation is tied to saved evidence.",
        ]

    mode = "mutate" if has_generated_app else "evolve"
    explanation = " ".join(rationale_points)
    return {
        "label": label,
        "prompt": prompt,
        "mode": mode,
        "reason": f"Based on {source_line}.",
        "explanation": explanation,
        "query": query,
        "focus": focus,
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def knowledge_key(item: Dict[str, Any]) -> str:
    return str(item.get("url") or item.get("title") or item.get("summary") or item.get("topic") or "").strip().lower()


def compute_knowledge_score(item: Dict[str, Any]) -> float:
    source_count = max(int(item.get("source_count") or 1), 1)
    use_count = max(int(item.get("use_count") or 0), 0)
    summary = str(item.get("summary") or "")
    topic = str(item.get("topic") or "")
    url = str(item.get("url") or "")
    score = 12 + min(source_count, 8) * 8 + min(use_count, 12) * 5
    if url:
        score += 4
    if topic:
        score += 2
    if len(summary) >= 120:
        score += 4
    elif summary:
        score += 2
    return round(float(score), 1)


def normalize_knowledge_item(item: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "topic": str(item.get("topic") or "research").strip(),
        "title": str(item.get("title") or "Untitled result").strip(),
        "url": str(item.get("url") or "").strip(),
        "summary": str(item.get("summary") or "").strip(),
        "source_count": max(int(item.get("source_count") or 1), 1),
        "use_count": max(int(item.get("use_count") or 0), 0),
        "learned_at": str(item.get("learned_at") or utc_now_iso()),
        "updated_at": str(item.get("updated_at") or item.get("learned_at") or utc_now_iso()),
    }
    normalized["score"] = compute_knowledge_score(normalized)
    return normalized


def combine_knowledge_item(existing: Dict[str, Any], new_item: Dict[str, Any]) -> Dict[str, Any]:
    existing_normalized = normalize_knowledge_item(existing)
    new_normalized = normalize_knowledge_item(new_item)
    topic_parts: List[str] = []
    for topic in [existing_normalized.get("topic"), new_normalized.get("topic")]:
        cleaned = str(topic or "").strip()
        if cleaned and cleaned not in topic_parts:
            topic_parts.append(cleaned)
    combined = {
        "topic": " | ".join(topic_parts[:3]) or "research",
        "title": new_normalized.get("title") or existing_normalized.get("title") or "Untitled result",
        "url": new_normalized.get("url") or existing_normalized.get("url") or "",
        "summary": max(
            [existing_normalized.get("summary") or "", new_normalized.get("summary") or ""],
            key=len,
        ),
        "source_count": max(int(existing_normalized.get("source_count") or 1), 1) + max(int(new_normalized.get("source_count") or 1), 1),
        "use_count": max(int(existing_normalized.get("use_count") or 0), 0) + max(int(new_normalized.get("use_count") or 0), 0),
        "learned_at": existing_normalized.get("learned_at") or new_normalized.get("learned_at") or utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    combined["score"] = compute_knowledge_score(combined)
    return combined


def sort_knowledge_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_items = [normalize_knowledge_item(item) for item in items if knowledge_key(item)]
    return sorted(
        normalized_items,
        key=lambda item: (
            float(item.get("score") or 0),
            int(item.get("use_count") or 0),
            int(item.get("source_count") or 0),
            str(item.get("updated_at") or ""),
        ),
        reverse=True,
    )


def load_global_knowledge_store() -> List[Dict[str, str]]:
    try:
        if not KNOWLEDGE_STORE_PATH.exists():
            return []
        data = json.loads(KNOWLEDGE_STORE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return sort_knowledge_items(data)
    except Exception:
        return []


def save_global_knowledge_store(items: List[Dict[str, str]]) -> None:
    try:
        KNOWLEDGE_STORE_PATH.write_text(json.dumps(sort_knowledge_items(items), indent=2), encoding="utf-8")
    except Exception:
        return


def merge_knowledge_items(existing: List[Dict[str, str]], additions: List[Dict[str, str]], max_items: int) -> List[Dict[str, str]]:
    by_key: Dict[str, Dict[str, Any]] = {}
    for item in existing:
        normalized = normalize_knowledge_item(item)
        key = knowledge_key(normalized)
        if key:
            by_key[key] = normalized
    for item in additions:
        normalized = normalize_knowledge_item(item)
        key = knowledge_key(normalized)
        if not key:
            continue
        if key in by_key:
            by_key[key] = combine_knowledge_item(by_key[key], normalized)
        else:
            by_key[key] = normalized
    return sort_knowledge_items(list(by_key.values()))[:max_items]


def mark_knowledge_usage(items: List[Dict[str, str]], hits: List[Dict[str, str]], increment: int = 1) -> List[Dict[str, str]]:
    hit_keys = {knowledge_key(item) for item in hits if knowledge_key(item)}
    if not hit_keys:
        return sort_knowledge_items(items)
    updated: List[Dict[str, Any]] = []
    now = utc_now_iso()
    for item in items:
        normalized = normalize_knowledge_item(item)
        if knowledge_key(normalized) in hit_keys:
            normalized["use_count"] = max(int(normalized.get("use_count") or 0), 0) + increment
            normalized["updated_at"] = now
            normalized["score"] = compute_knowledge_score(normalized)
        updated.append(normalized)
    return sort_knowledge_items(updated)


def research_findings_to_knowledge(research: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not research or not research.get("findings"):
        return []
    return [
        {
            "topic": research.get("query") or "research",
            "title": item.get("title") or "Untitled result",
            "url": item.get("url") or "",
            "summary": item.get("snippet") or "",
            "source_count": 1,
            "use_count": 0,
            "learned_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        for item in (research.get("findings") or [])
    ]


def update_knowledge_bank(previous_memory: Dict[str, Any], research: Optional[Dict[str, Any]], max_items: int = 18) -> List[Dict[str, str]]:
    existing = list(previous_memory.get("knowledge_items") or [])
    if not research or not research.get("findings"):
        return existing[:max_items]
    return merge_knowledge_items(existing, research_findings_to_knowledge(research), max_items)


def find_relevant_knowledge(message: str, knowledge_items: List[Dict[str, str]], max_hits: int = 3) -> List[Dict[str, str]]:
    tokens = [token for token in re.findall(r"[a-z0-9_\-]+", message.lower()) if len(token) > 2]
    if not tokens:
        return []

    matches: List[tuple[float, Dict[str, str]]] = []
    for item in knowledge_items:
        normalized = normalize_knowledge_item(item)
        haystack = " ".join([
            str(normalized.get("topic") or "").lower(),
            str(normalized.get("title") or "").lower(),
            str(normalized.get("summary") or "").lower(),
        ])
        overlap = sum(1 for token in set(tokens) if token in haystack)
        if overlap:
            relevance = overlap * 10 + float(normalized.get("score") or 0)
            matches.append((relevance, normalized))
    matches.sort(key=lambda entry: entry[0], reverse=True)
    return [item for _, item in matches[:max_hits]]


def build_project_advice(app_type: str, builder_mode: str, systems: List[str], decisions: Dict[str, Any], has_generated_app: bool) -> Dict[str, List[Dict[str, str]]]:
    upgrades: List[Dict[str, str]] = []
    cautions: List[Dict[str, str]] = []
    better_options: List[Dict[str, str]] = []
    is_calculator_tool = app_type == "tool app" and builder_mode == "battery-planner"

    if "auth" not in systems and app_type in {"admin panel", "assistant app"}:
        upgrades.append({"label": "Add login", "reason": "Protected workspaces usually need accounts, saved state, and project ownership."})
    if "storage" in systems and "billing" not in systems and has_generated_app:
        upgrades.append({"label": "Add paid tier", "reason": "Once users can save data, premium export, team features, or higher limits become realistic upgrades."})
    if builder_mode != "site-builder" and not is_calculator_tool and (has_generated_app or app_type in {"assistant app", "content app", "admin panel"}):
        upgrades.append({"label": "Add marketing page", "reason": "A strong landing page makes the project easier to explain, test, and ship."})

    if decisions.get("billing_enabled") is True and decisions.get("auth_required") is False:
        cautions.append({"label": "Avoid paid flow without accounts", "reason": "Billing without login makes access recovery and entitlement checks messy."})
    if app_type == "tool app" and "dashboard" in systems and not has_generated_app:
        cautions.append({"label": "Do not overbuild v1", "reason": "Starting with a full dashboard before the core tool works can slow the first release."})
    if builder_mode == "site-builder" and "billing" in systems:
        cautions.append({"label": "Keep the site simple first", "reason": "Landing pages usually convert better before you add subscriptions, portals, or complex app state."})

    if (decisions.get("product_shape") == "tool" or is_calculator_tool) and "dashboard" in systems:
        better_options.append({"label": "Start with a single focused tool", "reason": "Ship one excellent calculator or workflow first, then add dashboard history later."})
    if decisions.get("auth_required") is False and app_type == "assistant app":
        better_options.append({"label": "Use guest mode first", "reason": "Let users try the assistant instantly, then add account save features after value is proven."})
    if "billing" not in systems and has_generated_app:
        better_options.append({"label": "Add premium exports instead of full subscriptions", "reason": "That is often a simpler first monetization step than a full billing system."})

    return {
        "upgrades": upgrades[:3],
        "cautions": cautions[:3],
        "better_options": better_options[:3],
    }


def build_generation_project_memory(payload_prompt: str, project_memory: Dict[str, Any], app_type: str, builder_mode: str, systems: List[str], has_generated_app: bool) -> Dict[str, Any]:
    previous_memory = dict(project_memory or {})
    decisions = dict(previous_memory.get("decisions") or {})
    advice = build_project_advice(app_type, builder_mode, systems, decisions, has_generated_app)
    global_knowledge_count = len(load_global_knowledge_store())
    return {
        **previous_memory,
        "project_summary": payload_prompt or previous_memory.get("project_summary", ""),
        "app_type": app_type,
        "builder_mode": builder_mode,
        "systems": systems,
        "has_generated_app": has_generated_app,
        "decisions": decisions,
        "advice": advice,
        "latest_research": previous_memory.get("latest_research") or {},
        "knowledge_items": list(previous_memory.get("knowledge_items") or []),
        "global_knowledge_count": global_knowledge_count,
        "unresolved_questions": [],
    }


def resolve_builder_state(
    prompt: str,
    project_memory: Dict[str, Any],
    feature_state: Optional[Dict[str, Any]] = None,
    system_planner: Optional[Dict[str, Any]] = None,
    app_type: str = "",
    builder_mode: str = "",
    systems: Optional[List[str]] = None,
) -> tuple[str, str, List[str], str]:
    feature_state = feature_state or {}
    system_planner = system_planner or {}
    previous_memory = project_memory or {}

    resolved_app_type = (
        app_type
        or feature_state.get("appType")
        or previous_memory.get("app_type")
        or infer_app_type(prompt)
    )
    resolved_builder_mode = (
        builder_mode
        or feature_state.get("builderMode")
        or previous_memory.get("builder_mode")
        or infer_builder_mode(prompt)
    )
    resolved_systems = (
        systems
        or system_planner.get("systems")
        or previous_memory.get("systems")
        or infer_systems(prompt, resolved_app_type)
    )
    resolved_complexity = (
        system_planner.get("complexity")
        or "mvp"
    )
    return resolved_app_type, resolved_builder_mode, list(resolved_systems or []), resolved_complexity


def build_project_id(raw_project_id: str) -> str:
    cleaned = str(raw_project_id or "").strip()
    if cleaned:
        return cleaned
    return f"proj-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def build_clarifying_questions(message: str, app_type: str, systems: List[str], decisions: Dict[str, Any]) -> List[str]:
    questions: List[str] = []
    is_calculator_tool = app_type == "tool app" and bool(re.search(r"(battery|solar|inverter|calculator|estimate|power needed)", message))
    if is_calculator_tool:
        if decisions.get("product_shape") is None:
            questions.append("Should this stay a simple calculator, or do you also want saved plans later?")
        elif not re.search(r"(appliance|device|load|watts|hours)", message):
            questions.append("Should users enter individual appliances, or just total power usage?")
        return questions[:1]
    if decisions.get("auth_required") is None and not re.search(r"(login|auth|account|sign in|signup|user)", message):
        questions.append("Should users sign in, or should this stay open to everyone?")
    if decisions.get("billing_enabled") is None and "billing" not in systems and not re.search(r"(stripe|billing|subscription|paid|premium)", message):
        questions.append("Do you want payments or subscriptions in the first version?")
    if decisions.get("product_shape") is None and app_type == "tool app" and not re.search(r"(dashboard|admin|landing|chat|assistant|content|cms)", message):
        questions.append("Should this be a simple tool, a dashboard, or a full SaaS-style app?")
    return questions[:1]


def build_suggested_actions(app_type: str, has_generated_app: bool, systems: List[str], builder_mode: str, research_recommendation: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []
    is_rv_calculator = app_type == "tool app" and builder_mode == "battery-planner"
    if research_recommendation and research_recommendation.get("prompt"):
        actions.append({
            "label": research_recommendation.get("label") or "Apply researched recommendation",
            "prompt": research_recommendation.get("prompt") or "",
            "mode": research_recommendation.get("mode") or ("mutate" if has_generated_app else "evolve"),
        })

    if not has_generated_app:
        starter_prompt = {
            "assistant app": "Build an AI assistant app with chat, saved history, and a tool panel",
            "admin panel": "Build an admin dashboard with login, sidebar, analytics cards, and settings",
            "content app": "Build a content studio with editor, preview, saved drafts, and notes",
        }.get(app_type, "Build a web app with homepage, dashboard, login, and saved data")
        if is_rv_calculator:
            starter_prompt = "Build an RV solar and battery calculator with appliance inputs, runtime estimates, inverter sizing, and simple result cards"
        actions.append({"label": "Build first version", "prompt": starter_prompt, "mode": "evolve"})

    if has_generated_app:
        if is_rv_calculator:
            actions.append({"label": "Add saved plans", "prompt": "Add saved RV plans and history so users can keep past calculations", "mode": "mutate"})
            actions.append({"label": "Add PDF report", "prompt": "Add a printable report for solar, battery, and inverter sizing results", "mode": "mutate"})
            actions.append({"label": "Add appliance presets", "prompt": "Add common RV appliance presets with default watts and hours", "mode": "mutate"})
        else:
            actions.append({"label": "Add login", "prompt": "Add login, protected routes, and account state", "mode": "mutate"})
            actions.append({"label": "Improve mobile", "prompt": "Make the current app mobile friendly with cleaner spacing and navigation", "mode": "mutate"})
    else:
        if is_rv_calculator:
            actions.append({"label": "Add saved plans later", "prompt": "Keep it simple first, then add saved RV plans and history later", "mode": "evolve"})
        else:
            actions.append({"label": "SaaS starter", "prompt": "Build a SaaS web app with landing page, login, dashboard, billing, and settings", "mode": "evolve"})

    if app_type != "assistant app" and not is_rv_calculator:
        actions.append({"label": "AI assistant mode", "prompt": "Turn this into an AI assistant app with chat, tools, saved history, and a dashboard", "mode": "evolve" if not has_generated_app else "mutate"})
    if "billing" not in systems and not is_rv_calculator:
        actions.append({"label": "Add billing", "prompt": "Add billing, pricing, and a paid plan upgrade flow", "mode": "mutate" if has_generated_app else "evolve"})
    if builder_mode != "site-builder" and not is_rv_calculator:
        actions.append({"label": "Marketing page", "prompt": "Add a premium landing page and stronger marketing sections", "mode": "mutate" if has_generated_app else "evolve"})

    return actions[:4]


def personalize_improvement_reason(base_reason: str, message: str, previous_memory: Optional[Dict[str, Any]] = None) -> str:
    lowered = str(message or "").lower()
    previous_memory = previous_memory or {}
    decisions = dict(previous_memory.get("decisions") or {})
    unresolved = list(previous_memory.get("unresolved_questions") or [])
    project_summary = str(previous_memory.get("project_summary") or "").strip()
    if re.search(r"(login|auth|account|sign in)", lowered):
        return f"{base_reason} You already asked about login or accounts, so this matches the current direction."
    if re.search(r"(dashboard|report|analytics|saved|history)", lowered):
        return f"{base_reason} It also fits the saved data and dashboard direction you mentioned."
    if re.search(r"(mobile|phone|responsive|tablet)", lowered):
        return f"{base_reason} You also mentioned mobile needs, so this keeps that moving."
    if re.search(r"(backend|api|database|server)", lowered):
        return f"{base_reason} It also supports the backend work you asked about."
    if re.search(r"(frontend|ui|design|layout|preview)", lowered):
        return f"{base_reason} It also improves the interface direction you asked for."
    if unresolved:
        return f"{base_reason} It also moves the project forward while one detail is still open: {unresolved[0]}"
    if decisions.get("auth_required") is False:
        return f"{base_reason} This also respects your choice to keep the first version open without login."
    if decisions.get("billing_enabled") is False:
        return f"{base_reason} This also respects your choice to keep billing out of the first version."
    if project_summary:
        return f"{base_reason} It stays aligned with the project you described: {project_summary[:120]}"
    return base_reason


def build_next_improvement_action(
    app_type: str,
    has_generated_app: bool,
    systems: List[str],
    builder_mode: str,
    message: str = "",
    previous_memory: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    previous_memory = previous_memory or {}
    decisions = dict(previous_memory.get("decisions") or {})
    is_rv_calculator = app_type == "tool app" and builder_mode == "battery-planner"
    if not has_generated_app:
        starter_prompt = {
            "assistant app": "Build a simple AI assistant with chat, saved history, and one clean workspace",
            "admin panel": "Build a simple admin dashboard with login, sidebar, and key overview cards",
            "content app": "Build a simple content studio with editor, preview, and saved drafts",
        }.get(app_type, "Build a simple first version with one main screen, saved data, and a clear next step")
        if is_rv_calculator:
            starter_prompt = "Build a simple RV power calculator with appliance inputs, solar sizing, battery runtime, and inverter sizing"
        return {
            "label": "Best next improvement",
            "reason": personalize_improvement_reason("Start with the core RV calculator first so users can size solar, battery, and inverter power right away.", message, previous_memory) if is_rv_calculator else personalize_improvement_reason("Start with one focused first version before adding extra features.", message, previous_memory),
            "prompt": starter_prompt,
            "mode": "evolve",
        }

    if is_rv_calculator and "storage" in systems:
        return {
            "label": "Best next improvement",
            "reason": personalize_improvement_reason("Saved plans are the strongest next step because people often compare multiple RV setups before buying parts.", message, previous_memory),
            "prompt": "Add saved RV plans and history so users can compare multiple solar and battery setups",
            "mode": "mutate",
        }
    if is_rv_calculator:
        return {
            "label": "Best next improvement",
            "reason": personalize_improvement_reason("Appliance presets make the calculator feel smarter and faster for RV owners.", message, previous_memory),
            "prompt": "Add common RV appliance presets with default watts, hours, and quick-add controls",
            "mode": has_generated_app and "mutate" or "evolve",
        }

    if "auth" not in systems and app_type in {"assistant app", "admin panel", "content app"} and decisions.get("auth_required") is not False:
        return {
            "label": "Best next improvement",
            "reason": personalize_improvement_reason("This project will feel more complete once people can sign in and save their work.", message, previous_memory),
            "prompt": "Add login, protected routes, and account state",
            "mode": "mutate",
        }
    if "billing" not in systems and decisions.get("billing_enabled") is not False:
        return {
            "label": "Best next improvement",
            "reason": personalize_improvement_reason("A simple upgrade path is often the cleanest next product step after the core app works.", message, previous_memory),
            "prompt": "Add a simple paid upgrade path with pricing and billing entry points",
            "mode": "mutate",
        }
    if builder_mode != "site-builder":
        return {
            "label": "Best next improvement",
            "reason": personalize_improvement_reason("Mobile polish usually improves the app quickly without changing the core product idea.", message, previous_memory),
            "prompt": "Improve the app for mobile with cleaner spacing, navigation, and touch-friendly layout",
            "mode": "mutate",
        }
    return {
        "label": "Best next improvement",
        "reason": personalize_improvement_reason("A clearer landing page is the simplest next improvement for a site-first product.", message, previous_memory),
        "prompt": "Improve the landing page with clearer sections, stronger copy, and better conversion flow",
        "mode": "mutate",
    }


def merge_action_lists(*action_groups: List[Dict[str, str]], limit: int = 5) -> List[Dict[str, str]]:
    merged: List[Dict[str, str]] = []
    seen_keys = set()
    for group in action_groups:
        for action in group or []:
            label = str(action.get("label") or "").strip()
            prompt = str(action.get("prompt") or "").strip()
            mode = str(action.get("mode") or "evolve").strip()
            reason = str(action.get("reason") or "").strip()
            if not label or not prompt:
                continue
            key = (label.lower(), prompt.lower(), mode.lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)
            merged.append({"label": label, "prompt": prompt, "mode": mode, "reason": reason})
            if len(merged) >= limit:
                return merged
    return merged


def build_project_memory(payload: ChatAgentRequest, app_type: str, builder_mode: str, systems: List[str], has_generated_app: bool, questions: List[str], suggested_actions: List[Dict[str, str]], research: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    previous_memory = dict(payload.project_memory or {})
    decisions = infer_decisions_from_message(payload.message, previous_memory)
    advice = build_project_advice(app_type, builder_mode, systems, decisions, has_generated_app)
    knowledge_items = update_knowledge_bank(previous_memory, research)
    global_knowledge_count = len(load_global_knowledge_store())
    latest_research = research or previous_memory.get("latest_research") or {}
    research_recommendation = build_research_recommendation(latest_research, has_generated_app, systems, app_type)
    project_summary = payload.current_prompt or previous_memory.get("project_summary") or payload.message
    if len(payload.message.split()) > 3:
        project_summary = payload.message
    return {
        "project_id": payload.project_id or previous_memory.get("project_id", ""),
        "project_summary": project_summary,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "systems": systems,
        "has_generated_app": has_generated_app,
        "last_user_request": payload.message,
        "decisions": decisions,
        "advice": advice,
        "latest_research": latest_research,
        "research_recommendation": research_recommendation,
        "knowledge_items": knowledge_items,
        "global_knowledge_count": global_knowledge_count,
        "unresolved_questions": questions,
        "last_suggested_actions": suggested_actions[:3],
    }


def build_memory_summary(memory: Dict[str, Any]) -> str:
    systems = memory.get("systems") or []
    decisions = memory.get("decisions") or {}
    system_line = ", ".join(systems[:4]) if systems else "the basic app setup"
    unresolved = memory.get("unresolved_questions") or []
    unresolved_line = f" I am still waiting on {len(unresolved)} detail(s)." if unresolved else ""
    decision_parts = []
    if decisions.get("auth_required") is True:
        decision_parts.append("login is included")
    elif decisions.get("auth_required") is False:
        decision_parts.append("no login yet")
    if decisions.get("billing_enabled") is True:
        decision_parts.append("billing is included")
    elif decisions.get("billing_enabled") is False:
        decision_parts.append("billing is not in v1")
    if decisions.get("product_shape"):
        decision_parts.append(f"shape is {decisions['product_shape']}")
    decision_line = f" Current choices: {', '.join(decision_parts)}." if decision_parts else ""
    advice = memory.get("advice") or {}
    advice_count = sum(len(advice.get(key) or []) for key in ["upgrades", "cautions", "better_options"])
    advice_line = f" I have {advice_count} suggestion(s) ready." if advice_count else ""
    research = memory.get("latest_research") or {}
    research_line = " Research is saved." if research.get("findings") else ""
    recommendation = memory.get("research_recommendation") or {}
    recommendation_line = " I already have a recommended next step." if recommendation.get("prompt") else ""
    knowledge_count = len(memory.get("knowledge_items") or [])
    knowledge_line = f" I saved {knowledge_count} helpful note(s)." if knowledge_count else ""
    global_knowledge_count = memory.get("global_knowledge_count") or 0
    global_line = f" Global knowledge items: {global_knowledge_count}." if global_knowledge_count else ""
    return (
        f"This looks like a {memory.get('app_type', 'tool app')} in {memory.get('builder_mode', 'general-builder')} mode. "
        f"Right now I am tracking {system_line}.{decision_line}{advice_line}{research_line}{recommendation_line}{knowledge_line}{global_line}{unresolved_line}"
    )


def build_status_summary(response_type: str, ready_to_apply: bool, apply_mode: str, question_count: int) -> str:
    if response_type == "answer":
        return "Answered. You can keep asking questions or apply a change when ready."
    if response_type == "clarify":
        if question_count:
            return f"I need {question_count} quick detail(s) before I build the next step."
        return "I need a little more detail before I build the next step."
    if response_type == "suggest":
        return "I shared a few good next-step ideas you can choose from."
    if response_type == "research":
        return "I checked the topic and saved a practical next step for you."
    if response_type == "explain":
        return "I explained the plan in simple terms."
    if ready_to_apply:
        return f"Ready to apply in {apply_mode} mode when you want."
    return "You can keep talking or pick one of the quick actions."


def shorten_chat_reply(message: str, max_sentences: int = 2) -> str:
    text = str(message or "").strip()
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    compact_parts = [part.strip() for part in parts if part.strip()]
    if len(compact_parts) <= max_sentences:
        return " ".join(compact_parts)
    return " ".join(compact_parts[:max_sentences]).strip()


def build_conversational_answer(
    message: str,
    app_type: str,
    builder_mode: str,
    systems: List[str],
    has_generated_app: bool,
    knowledge_hits: List[Dict[str, str]],
    previous_memory: Dict[str, Any],
    recent_messages: List[Dict[str, str]],
) -> str:
    lowered = message.lower()
    system_line = ", ".join(systems[:4]) if systems else "core project systems"
    unresolved = list(previous_memory.get("unresolved_questions") or [])
    recent_context = summarize_recent_context(recent_messages)

    if re.search(r"(conversation|chat|talk|answer|respond|question)", lowered):
        answer = (
            "Yes. You can talk to the builder normally. "
            "It should answer first, ask follow-up questions when needed, and only apply changes when the request is clear."
        )
    elif re.search(r"(frontend|backend|full.?stack|api|database|server)", lowered):
        answer = (
            "Yes. I can talk through a full-stack change first, then target the frontend, the backend, or both. "
            "If workspace editing is enabled, I can write into the configured repo. If not, I update the generated project bundle."
        )
    elif re.search(r"(remember|memory|saved|know about this project)", lowered):
        answer = (
            "I keep the main project context, like app type, builder mode, planned systems, research, and missing details, "
            "so the conversation stays on the same project."
        )
    elif unresolved and re.search(r"(what do you need|what is missing|what else)", lowered):
        answer = (
            f"I am waiting on {len(unresolved)} detail(s) before I apply the next change. "
            f"The first missing point is: {unresolved[0]}"
        )
    elif app_type == "tool app" and builder_mode == "battery-planner":
        answer = (
            "I understand this as an RV power calculator. "
            "The smart core is appliance inputs, solar sizing, battery runtime, and inverter sizing in one simple flow."
        )
    else:
        answer = (
            f"Right now I would treat this as a {app_type} in {builder_mode} mode. "
            f"The main systems are {system_line}. "
            "I can keep answering questions, or turn this into a change when you are ready."
        )

    if recent_context and len(message.split()) <= 5:
        answer += f" Recent context: {recent_context}"

    if knowledge_hits:
        answer += f" I also found {len(knowledge_hits)} saved note(s) that support this answer."
    return answer


def build_agent_reply(payload: ChatAgentRequest) -> Dict[str, Any]:
    message = payload.message.strip()
    lowered = message.lower()
    has_generated_app = bool(payload.generated_files or payload.routes or payload.components or payload.project_id)
    previous_memory = dict(payload.project_memory or {})
    decisions = infer_decisions_from_message(message, previous_memory)
    app_type = payload.feature_state.get("appType") or previous_memory.get("app_type") or infer_app_type(message)
    builder_mode = payload.feature_state.get("builderMode") or previous_memory.get("builder_mode") or infer_builder_mode(message)
    if has_generated_app or previous_memory.get("project_summary"):
        systems = payload.system_planner.get("systems") or previous_memory.get("systems") or infer_systems(message, app_type)
    else:
        systems = infer_systems(message, app_type)
    systems = apply_decisions_to_systems(systems, decisions)
    response_type = "apply"
    assistant_message = ""
    questions: List[str] = []
    ready_to_apply = False
    apply_mode = normalize_chat_mode(payload.chat_mode, has_generated_app)
    apply_prompt = message
    research: Dict[str, Any] = previous_memory.get("latest_research") or {}
    research_recommendation = build_research_recommendation(research, has_generated_app, systems, app_type)
    global_knowledge_items = load_global_knowledge_store()
    combined_knowledge_items = merge_knowledge_items(list(previous_memory.get("knowledge_items") or []), global_knowledge_items, 48)
    knowledge_hits = find_relevant_knowledge(message, combined_knowledge_items)
    reply_preference = normalize_reply_preference(payload.reply_preference)
    recent_messages = list(payload.recent_messages or [])[-6:]
    if knowledge_hits:
        save_global_knowledge_store(mark_knowledge_usage(global_knowledge_items, knowledge_hits))

    vague_build = bool(re.search(r"\b(app|website|web app|platform|tool)\b", lowered)) and len(message.split()) < 7
    if needs_research(lowered):
        response_type = "research"
        ready_to_apply = False
        research = run_research(build_research_query(message, app_type, builder_mode))
        research_recommendation = build_research_recommendation(research, has_generated_app, systems, app_type)
        if research.get("findings"):
            save_global_knowledge_store(
                merge_knowledge_items(
                    load_global_knowledge_store(),
                    research_findings_to_knowledge(research),
                    250,
                )
            )
        assistant_message = summarize_research(research, app_type, builder_mode)
        if research_recommendation.get("prompt"):
            assistant_message += f" I recommend {research_recommendation.get('label', 'the researched option')}. {research_recommendation.get('explanation', '')} I can apply it now if you want."
    elif research_recommendation.get("prompt") and is_affirmative(lowered) and not (previous_memory.get("unresolved_questions") or []):
        response_type = "apply"
        ready_to_apply = True
        apply_mode = research_recommendation.get("mode") or normalize_chat_mode(payload.chat_mode, has_generated_app)
        apply_prompt = research_recommendation.get("prompt") or message
        assistant_message = (
            f"I chose {research_recommendation.get('label', 'the researched option')} for this project. "
            f"{research_recommendation.get('explanation', research_recommendation.get('reason') or '')} "
            "I am applying it now."
        ).strip()
    elif is_suggestion_request(lowered):
        response_type = "suggest"
        ready_to_apply = False
        assistant_message = (
            f"I recommend starting with a {app_type} in {builder_mode} mode. "
            "For v1, keep it focused: a clear homepage, one main workspace, saved data, and one useful upgrade path. "
            "Pick a suggestion, or tell me your niche and I will shape it around that."
        )
        if knowledge_hits:
            assistant_message += f" I am also using {len(knowledge_hits)} saved knowledge item(s) from earlier research on similar topics."
    elif (is_explanation_request(lowered) or is_followup_question(message, recent_messages)) and not is_mutation_request(lowered):
        response_type = "explain"
        ready_to_apply = False
        system_line = ", ".join(systems[:4]) if systems else "storage"
        if app_type == "tool app" and builder_mode == "battery-planner":
            assistant_message = (
                "Right now I would treat this as an RV solar and battery calculator. "
                "The main flow should be appliance inputs, battery runtime, solar sizing, and inverter sizing, then optional saved plans later."
            )
        else:
            assistant_message = (
                f"Right now I would treat this as a {app_type} in {builder_mode} mode. "
                f"The main systems I would plan are {system_line}. "
                "If you want, I can apply that plan now or simplify it first."
            )
        if knowledge_hits:
            assistant_message += " I also found matching saved knowledge that can guide the choice below."
    elif (is_question_message(message) or is_followup_question(message, recent_messages) or reply_preference == "answer") and not is_mutation_request(lowered) and not re.search(r"\b(build|create|make|start|generate)\b", lowered):
        response_type = "answer"
        ready_to_apply = False
        assistant_message = build_conversational_answer(
            message,
            app_type,
            builder_mode,
            systems,
            has_generated_app,
            knowledge_hits,
            previous_memory,
            recent_messages,
        )
    elif not has_generated_app and (vague_build or message in {"app", "website", "build me something", "build app"}):
        response_type = "clarify"
        ready_to_apply = False
        questions = build_clarifying_questions(lowered, app_type, systems, decisions)
        assistant_message = "I can build that, but I need one or two details first so the first version is actually useful."
    elif has_generated_app and is_mutation_request(lowered):
        response_type = "apply"
        ready_to_apply = True
        apply_mode = "mutate"
        assistant_message = "I understand the change and I am ready to apply it to the current project now."
    elif not has_generated_app and re.search(r"(build|create|make|start|generate)", lowered):
        detail_score = sum(
            1
            for pattern in [
                r"(login|auth|account)",
                r"(dashboard|admin|portal)",
                r"(chat|assistant|ai)",
                r"(billing|subscription|pricing)",
                r"(database|saved|history|storage)",
                r"(mobile|responsive)",
            ]
            if re.search(pattern, lowered)
        )
        if detail_score == 0 and len(message.split()) < 12:
            response_type = "clarify"
            ready_to_apply = False
            questions = build_clarifying_questions(lowered, app_type, systems, decisions)
            assistant_message = "I can build the first version, but I need a little more direction so I choose the right screens and systems."
        elif reply_preference == "clarify":
            response_type = "clarify"
            ready_to_apply = False
            questions = build_clarifying_questions(lowered, app_type, systems, decisions)
            assistant_message = "I understand the direction, but I will ask one or two questions first so the first version matches what you want."
        else:
            response_type = "apply"
            ready_to_apply = True
            apply_mode = "evolve"
            assistant_message = "I understand the direction and I am ready to build the first version now."
    elif has_generated_app and reply_preference != "answer":
        response_type = "apply"
        ready_to_apply = True
        apply_mode = "mutate"
        assistant_message = "I can apply that to the current project now."
    else:
        response_type = "clarify"
        ready_to_apply = False
        questions = build_clarifying_questions(lowered, app_type, systems, decisions)
        assistant_message = "Tell me a bit more about the app you want, and I will shape the first version with the right layout and systems."

    suggested_actions = build_suggested_actions(app_type, has_generated_app, systems, builder_mode, research_recommendation)
    next_improvement_action = build_next_improvement_action(app_type, has_generated_app, systems, builder_mode, message, previous_memory)
    followup_actions = build_followup_actions(response_type, has_generated_app)
    suggested_actions = merge_action_lists([next_improvement_action], followup_actions, suggested_actions, limit=5)
    if response_type in {"answer", "clarify", "suggest", "explain", "research"}:
        assistant_message = shorten_chat_reply(assistant_message, 2)
    project_memory = build_project_memory(payload, app_type, builder_mode, systems, has_generated_app, questions, suggested_actions, research)
    advice = project_memory.get("advice") or {"upgrades": [], "cautions": [], "better_options": []}

    return {
        "ok": True,
        "response_type": response_type,
        "assistant_message": assistant_message,
        "status_summary": build_status_summary(response_type, ready_to_apply, apply_mode, len(questions)),
        "questions": questions,
        "suggested_actions": suggested_actions,
        "advice": advice,
        "research_findings": research.get("findings") or [],
        "research_query": research.get("query") or "",
        "knowledge_hits": knowledge_hits,
        "research_recommendation": project_memory.get("research_recommendation") or {},
        "ready_to_apply": ready_to_apply,
        "apply_mode": apply_mode,
        "apply_prompt": apply_prompt,
        "project_memory": project_memory,
        "memory_summary": build_memory_summary(project_memory),
        "analysis": {
            "app_type": app_type,
            "builder_mode": builder_mode,
            "systems": systems,
            "has_generated_app": has_generated_app,
        },
    }


def infer_systems(prompt: str, app_type: str) -> List[str]:
    p = prompt.lower()
    systems = set()
    if app_type == "admin panel":
        systems.update(["dashboard", "storage", "settings"])
    elif app_type == "assistant app":
        systems.update(["ai-tools", "storage", "settings"])
    elif app_type == "content app":
        systems.update(["storage", "settings"])
    else:
        systems.update(["storage"])

    if re.search(r"(battery|solar|power|inverter|calculator|estimate)", p):
        systems.add("tools")

    if re.search(r"(login|auth|account|signin|sign in|register|user)", p):
        systems.add("auth")
    if re.search(r"(billing|subscription|stripe|paywall|pro|premium)", p):
        systems.add("billing")
    if re.search(r"(scan|diagnostic|ai|assistant|chat|analysis)", p):
        systems.add("ai-tools")
    if re.search(r"(admin|team|portal|role|dealer|tech)", p):
        systems.add("admin")
    if re.search(r"(settings|preferences|profile)", p):
        systems.add("settings")
    if re.search(r"(dashboard|stats|analytics|reports)", p):
        systems.add("dashboard")
    return sorted(systems)


def infer_persistence(prompt: str, systems: List[str], complexity: str) -> str:
    p = prompt.lower()
    if "billing" in systems or "auth" in systems or complexity == "product":
        return "supabase"
    if re.search(r"(local|offline|desktop|mvp|sqlite|history|saved)", p) or complexity == "mvp":
        return "sqlite"
    return "localstorage"


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
    if app_type in {"assistant app", "content app", "tool app"}:
        modules.add("split_workspace")
    if app_type in {"assistant app", "content app"}:
        modules.add("notes_panel")
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
        layout.update({"mode": "dashboard", "shell": "dashboard", "sidebar": True, "split": True, "inspector": True, "previewStyle": "dashboard"})
    if re.search(r"(assistant|copilot|agent|content|editor|writer|studio)", p):
        layout.update({"mode": "workspace", "shell": "classic", "split": True, "inspector": True})
    if re.search(r"(focus preview|preview first|canvas focus)", p):
        layout.update({"mode": "focus", "shell": "focus", "split": True, "previewStyle": "spotlight"})
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


def build_file_tree(app_type: str, builder_mode: str, prompt: str, systems: List[str], persistence: str) -> List[Dict[str, Any]]:
    base = [
        {"path": "frontend/src/App.jsx", "kind": "file", "role": "root app"},
        {"path": "frontend/src/main.jsx", "kind": "file", "role": "entry"},
        {"path": "frontend/src/styles/app.css", "kind": "file", "role": "global styles"},
        {"path": "frontend/src/components", "kind": "folder", "role": "ui components"},
        {"path": "frontend/src/pages", "kind": "folder", "role": "pages"},
        {"path": "frontend/src/lib", "kind": "folder", "role": "helpers"},
        {"path": "backend/main.py", "kind": "file", "role": "api server"},
        {"path": "backend/requirements.txt", "kind": "file", "role": "backend deps"},
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
    if "auth" in systems:
        base += [
            {"path": "frontend/src/pages/LoginPage.jsx", "kind": "file", "role": "authentication"},
            {"path": "frontend/src/lib/auth.js", "kind": "file", "role": "auth helpers"},
        ]
    if "storage" in systems:
        base += [
            {"path": "frontend/src/lib/api.js", "kind": "file", "role": "api client"},
            {"path": "frontend/src/hooks/useItems.js", "kind": "file", "role": "data hook"},
            {"path": "backend/data_store.py", "kind": "file", "role": f"{persistence} storage layer"},
        ]
    if builder_mode == "battery-planner":
        base += [
            {"path": "frontend/src/lib/batteryMath.js", "kind": "file", "role": "calculation logic"},
            {"path": "frontend/src/components/ApplianceTable.jsx", "kind": "file", "role": "appliance rows"},
        ]
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
        routes.append({"path": "/login", "component": "LoginPage", "reason": "auth entry"})
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
    if "storage" in systems:
        base.append({"name": "DataList", "purpose": "renders persisted records"})
    if "auth" in systems:
        base.append({"name": "AuthGate", "purpose": "guards protected screens"})
    return base


def build_mutation_summary(layout: Dict[str, Any], modules: List[str], app_type: str, builder_mode: str, systems: List[str], persistence: str) -> List[str]:
    summary = [
        f"App type detected: {app_type}",
        f"Builder mode detected: {builder_mode}",
        f"Layout shell: {layout['shell']}",
        f"Preview style: {layout['previewStyle']}",
        f"Active modules planned: {len(modules)}",
        f"Systems planned: {', '.join(systems) if systems else 'none'}",
        f"Persistence planned: {persistence}",
    ]
    if layout.get("sidebar"):
        summary.append("Sidebar enabled")
    if layout.get("split"):
        summary.append("Split workspace enabled")
    if layout.get("inspector"):
        summary.append("Inspector enabled")
    return summary


def app_css(style_name: str) -> str:
    return ("""
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
.app-shell { min-height: 100vh; padding: 24px; display: grid; gap: 18px; }
.panel { border: 1px solid var(--panel-border); background: var(--panel); border-radius: 20px; padding: 18px; }
.row { display: grid; gap: 18px; }
.row.two { grid-template-columns: 260px 1fr; }
.row.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.pill { display: inline-flex; align-items: center; gap: 8px; border-radius: 999px; padding: 8px 12px; border: 1px solid rgba(148, 163, 184, 0.18); background: rgba(255,255,255,0.04); color: var(--muted); }
.primary-btn { border: none; border-radius: 999px; padding: 12px 18px; font-weight: 700; cursor: pointer; background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #07111f; }
.muted { color: var(--muted); }
.card-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
.card { border: 1px solid rgba(148,163,184,.14); border-radius: 16px; padding: 16px; background: rgba(255,255,255,0.03); }
.input { width: 100%; border-radius: 14px; border: 1px solid rgba(148,163,184,.16); background: rgba(255,255,255,.04); color: var(--text); padding: 12px 14px; }
.list { display: grid; gap: 10px; margin-top: 12px; }
.item { display: flex; justify-content: space-between; gap: 12px; padding: 12px; border: 1px solid rgba(148,163,184,.12); border-radius: 12px; background: rgba(255,255,255,.03); }
@media (max-width: 900px) { .row.two, .row.three { grid-template-columns: 1fr; } }
""" + "\n\n" + monetization_styles_css()).strip()


def main_jsx() -> str:
    return """
import React from \"react\";
import ReactDOM from \"react-dom/client\";
import App from \"./App.jsx\";
import \"./styles/app.css\";

ReactDOM.createRoot(document.getElementById(\"root\")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""".strip()


def root_app_code(app_type: str) -> str:
    page_name = {
        "admin panel": "DashboardPage",
        "assistant app": "AssistantPage",
        "content app": "StudioPage",
        "tool app": "ToolPage",
    }.get(app_type, "ToolPage")
    return f"""
import React from \"react\";
import {{ {page_name} }} from \"./pages/{page_name}.jsx\";

export default function App() {{
  return <{page_name} />;
}}
""".strip()


def dashboard_page_code(prompt: str) -> str:
    return f"""
import React, {{ useEffect, useState }} from \"react\";
import {{ Sidebar }} from \"../components/Sidebar.jsx\";
import {{ KpiCard }} from \"../components/KpiCard.jsx\";
import {{ InspectorPanel }} from \"../components/InspectorPanel.jsx\";
import {{ getItems }} from \"../lib/api.js\";

export function DashboardPage() {{
  const [items, setItems] = useState([]);
  useEffect(() => {{ getItems().then(setItems).catch(() => setItems([])); }}, []);

  return (
    <div className=\"app-shell\">
      <div className=\"panel\">
        <div className=\"pill\">Admin dashboard</div>
        <h1>CRM Dashboard</h1>
        <p className=\"muted\">{prompt}</p>
      </div>
      <div className=\"row two\">
        <Sidebar />
        <div className=\"row\">
          <div className=\"card-grid\">
            <KpiCard title=\"Records\" value={{String(items.length)}} />
            <KpiCard title=\"Status\" value=\"Connected\" />
            <KpiCard title=\"Flow\" value=\"Live API\" />
          </div>
          <div className=\"panel\">
            <h2>Recent records</h2>
            <div className=\"list\">{{items.map(item => <div className=\"item\" key={{item.id}}><span>{{item.title}}</span><span className=\"muted\">{{item.status}}</span></div>)}}</div>
          </div>
        </div>
      </div>
      <InspectorPanel />
      <MonetizationPanel />
    </div>
  );
}}
""".strip()


def assistant_page_code(prompt: str) -> str:
    return f"""
import React, {{ useEffect, useState }} from \"react\";
import {{ ChatShell }} from \"../components/ChatShell.jsx\";
import {{ ToolRail }} from \"../components/ToolRail.jsx\";
import {{ MemoryPanel }} from \"../components/MemoryPanel.jsx\";
import {{ getItems }} from \"../lib/api.js\";

export function AssistantPage() {{
  const [items, setItems] = useState([]);
  useEffect(() => {{ getItems().then(setItems).catch(() => setItems([])); }}, []);

  return (
    <div className=\"app-shell\">
      <div className=\"panel\">
        <div className=\"pill\">Assistant workspace</div>
        <h1>AI Assistant</h1>
        <p className=\"muted\">{prompt}</p>
      </div>
      <div className=\"row two\">
        <ToolRail />
        <ChatShell />
      </div>
      <MemoryPanel />
      <section className=\"panel\">
        <h3>Saved items</h3>
        <div className=\"list\">{{items.map(item => <div className=\"item\" key={{item.id}}><span>{{item.title}}</span><span className=\"muted\">{{item.status}}</span></div>)}}</div>
      </section>
    </div>
  );
}}
""".strip()


def studio_page_code(prompt: str) -> str:
    return f"""
import React, {{ useState }} from \"react\";
import {{ EditorShell }} from \"../components/EditorShell.jsx\";
import {{ PreviewPanel }} from \"../components/PreviewPanel.jsx\";
import {{ NotesPanel }} from \"../components/NotesPanel.jsx\";

export function StudioPage() {{
  const [draft, setDraft] = useState(\"Start writing here...\");

  return (
    <div className=\"app-shell\">
      <div className=\"panel\">
        <div className=\"pill\">Content studio</div>
        <h1>Content App</h1>
        <p className=\"muted\">{prompt}</p>
      </div>
      <div className=\"row two\">
        <EditorShell value={{draft}} onChange={{setDraft}} />
        <PreviewPanel value={{draft}} />
      </div>
      <NotesPanel />
      <MonetizationPanel />
    </div>
  );
}}
""".strip()


def tool_page_code(prompt: str, battery_mode: bool) -> str:
    extra = "Battery-focused starter logic can be added next." if battery_mode else "This is a clean generated tool starter."
    return f"""
import React, {{ useEffect, useState }} from \"react\";
import {{ CalculatorForm }} from \"../components/CalculatorForm.jsx\";
import {{ ResultsPanel }} from \"../components/ResultsPanel.jsx\";
import {{ ExportActions }} from \"../components/ExportActions.jsx\";
import {{ getItems, createItem }} from \"../lib/api.js\";

export function ToolPage() {{
  const [items, setItems] = useState([]);
  const [result, setResult] = useState(null);

  useEffect(() => {{ getItems().then(setItems).catch(() => setItems([])); }}, []);

  async function handleSave() {{
    const created = await createItem({{ title: \"Generated result\", status: \"saved\", value: result || \"pending\" }});
    setItems(prev => [created, ...prev]);
  }}

  return (
    <div className=\"app-shell\">
      <div className=\"panel\">
        <div className=\"pill\">Tool workspace</div>
        <h1>Tool / Calculator</h1>
        <p className=\"muted\">{prompt}</p>
        <p className=\"muted\">{extra}</p>
      </div>
      <div className=\"row two\">
        <CalculatorForm onCalculated={{setResult}} />
        <ResultsPanel result={{result}} onSave={{handleSave}} />
      </div>
      <ExportActions />
      <section className=\"panel\">
        <h3>Saved results</h3>
        <div className=\"list\">{{items.map(item => <div className=\"item\" key={{item.id}}><span>{{item.title}}</span><span className=\"muted\">{{item.status}}</span></div>)}}</div>
      </section>
    </div>
  );
}}
""".strip()


def sidebar_code() -> str:
    return """
import React from \"react\";

export function Sidebar() {
  return (
    <aside className=\"panel\">
      <h3>Navigation</h3>
      <div className=\"card-grid\">
        <div className=\"card\">Overview</div>
        <div className=\"card\">Customers</div>
        <div className=\"card\">Deals</div>
        <div className=\"card\">Reports</div>
      </div>
    </aside>
  );
}
""".strip()


def kpi_card_code() -> str:
    return """
import React from \"react\";

export function KpiCard({ title, value }) {
  return (
    <div className=\"card\">
      <div className=\"pill\">{title}</div>
      <h3>{value}</h3>
    </div>
  );
}
""".strip()


def inspector_code() -> str:
    return """
import React from \"react\";

export function InspectorPanel() {
  return (
    <section className=\"panel\">
      <h3>Inspector</h3>
      <p className=\"muted\">Use this space for details, selected records, and quick controls.</p>
    </section>
  );
}
""".strip()


def chat_shell_code() -> str:
    return """
import React, { useState } from \"react\";

export function ChatShell() {
  const [message, setMessage] = useState(\"\");
  return (
    <section className=\"panel\">
      <h3>Conversation</h3>
      <div className=\"card\">Assistant response area</div>
      <input className=\"input\" value={message} onChange={(e) => setMessage(e.target.value)} placeholder=\"Ask something...\" />
    </section>
  );
}
""".strip()


def tool_rail_code() -> str:
    return """
import React from \"react\";

export function ToolRail() {
  return (
    <aside className=\"panel\">
      <h3>Tools</h3>
      <div className=\"card-grid\">
        <div className=\"card\">Search</div>
        <div className=\"card\">Actions</div>
        <div className=\"card\">History</div>
      </div>
    </aside>
  );
}
""".strip()


def memory_panel_code() -> str:
    return """
import React from \"react\";

export function MemoryPanel() {
  return (
    <section className=\"panel\">
      <h3>Memory</h3>
      <p className=\"muted\">Save notes, pinned answers, and reusable context here.</p>
    </section>
  );
}
""".strip()


def editor_shell_code() -> str:
    return """
import React from \"react\";

export function EditorShell({ value, onChange }) {
  return (
    <section className=\"panel\">
      <h3>Editor</h3>
      <textarea className=\"input\" rows={12} value={value} onChange={(e) => onChange(e.target.value)} />
    </section>
  );
}
""".strip()


def preview_panel_code() -> str:
    return """
import React from \"react\";

export function PreviewPanel({ value }) {
  return (
    <section className=\"panel\">
      <h3>Preview</h3>
      <div className=\"card\">{value}</div>
    </section>
  );
}
""".strip()


def notes_panel_code() -> str:
    return """
import React from \"react\";

export function NotesPanel() {
  return (
    <section className=\"panel\">
      <h3>Notes</h3>
      <textarea className=\"input\" rows={6} defaultValue=\"Draft notes...\" />
    </section>
  );
}
""".strip()


def calculator_form_code() -> str:
    return """
import React, { useState } from \"react\";

export function CalculatorForm({ onCalculated }) {
  const [a, setA] = useState(\"\");
  const [b, setB] = useState(\"\");

  function handleCalculate() {
    const total = Number(a || 0) + Number(b || 0);
    onCalculated?.(total);
  }

  return (
    <section className=\"panel\">
      <h3>Inputs</h3>
      <div className=\"row\">
        <input className=\"input\" placeholder=\"Value 1\" value={a} onChange={(e) => setA(e.target.value)} />
        <input className=\"input\" placeholder=\"Value 2\" value={b} onChange={(e) => setB(e.target.value)} />
        <button className=\"primary-btn\" onClick={handleCalculate}>Calculate</button>
      </div>
    </section>
  );
}
""".strip()


def results_panel_code() -> str:
    return """
import React from \"react\";

export function ResultsPanel({ result, onSave }) {
  return (
    <section className=\"panel\">
      <h3>Results</h3>
      <div className=\"card\">{result === null ? \"Calculated output will appear here.\" : `Result: ${result}`}</div>
      <button className=\"primary-btn\" onClick={onSave}>Save Result</button>
    </section>
  );
}
""".strip()


def export_actions_code() -> str:
    return """
import React from \"react\";

export function ExportActions() {
  return (
    <section className=\"panel\">
      <h3>Export</h3>
      <div className=\"row\">
        <button className=\"primary-btn\">Export JSON</button>
        <button className=\"primary-btn\">Export PDF</button>
      </div>
    </section>
  );
}
""".strip()


def login_page_code() -> str:
    return """
import React, { useState } from \"react\";
import { signIn } from \"../lib/auth.js\";

export function LoginPage() {
  const [email, setEmail] = useState(\"\");
  const [password, setPassword] = useState(\"\");

  function handleSubmit() {
    signIn(email, password);
  }

  return (
    <div className=\"app-shell\">
      <section className=\"panel\">
        <h1>Login</h1>
        <div className=\"row\">
          <input className=\"input\" placeholder=\"Email\" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className=\"input\" placeholder=\"Password\" type=\"password\" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button className=\"primary-btn\" onClick={handleSubmit}>Sign in</button>
        </div>
      </section>
    </div>
  );
}
""".strip()


def auth_code() -> str:
    return """
export function signIn(email, password) {
  const token = `demo-token-${email || \"guest\"}`;
  localStorage.setItem(\"builder_token\", token);
  return { ok: true, email, token };
}

export function getToken() {
  return localStorage.getItem(\"builder_token\") || \"\";
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
import React from \"react\";

export function ApplianceTable() {
  return (
    <section className=\"panel\">
      <h3>Appliances</h3>
      <div className=\"card\">RV Fridge · Lights · Fan</div>
    </section>
  );
}
""".strip()


def api_client_code() -> str:
    return """
const API_BASE = import.meta.env.VITE_API_URL || \"http://localhost:8000\";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { \"Content-Type\": \"application/json\", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export async function getItems() {
  return request(\"/api/items\");
}

export async function createItem(payload) {
  return request(\"/api/items\", { method: \"POST\", body: JSON.stringify(payload) });
}

export async function updateItem(id, payload) {
  return request(`/api/items/${id}`, { method: \"PUT\", body: JSON.stringify(payload) });
}

export async function deleteItem(id) {
  return request(`/api/items/${id}`, { method: \"DELETE\" });
}
""".strip()


def use_items_hook_code() -> str:
    return """
import { useEffect, useState } from \"react\";
import { getItems, createItem, updateItem, deleteItem } from \"../lib/api.js\";

export function useItems() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(\"\");

  async function refresh() {
    try {
      setLoading(true);
      setError(\"\");
      const data = await getItems();
      setItems(data);
    } catch (err) {
      setError(err.message || \"Failed to load items\");
    } finally {
      setLoading(false);
    }
  }

  async function addItem(payload) {
    const created = await createItem(payload);
    setItems((prev) => [created, ...prev]);
    return created;
  }

  async function saveItem(id, payload) {
    const updated = await updateItem(id, payload);
    setItems((prev) => prev.map((item) => item.id === id ? updated : item));
    return updated;
  }

  async function removeItem(id) {
    await deleteItem(id);
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  useEffect(() => { refresh(); }, []);

  return { items, loading, error, refresh, addItem, saveItem, removeItem };
}
""".strip()


def backend_requirements_code(persistence: str) -> str:
    base = ["fastapi", "uvicorn[standard]", "pydantic"]
    if persistence == "sqlite":
        base.append("sqlalchemy")
    if persistence == "supabase":
        base += ["supabase", "python-dotenv"]
    return "\n".join(base)


def backend_env_example_code(persistence: str) -> str:
    lines = ["PORT=8000"]
    if persistence == "supabase":
        lines += ["SUPABASE_URL=your_supabase_url", "SUPABASE_KEY=your_supabase_key"]
    return "\n".join(lines)


def backend_api_code(persistence: str) -> str:
    store_import = "from data_store import list_items, create_item, update_item, delete_item"
    return f'''from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, List
{store_import}

app = FastAPI(title="Generated App Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ItemPayload(BaseModel):
    title: str = "Untitled"
    status: str = "draft"
    value: Any = None
    meta: Dict[str, Any] = Field(default_factory=dict)

@app.get("/health")
def health():
    return {{"status": "ok", "persistence": "{persistence}"}}

@app.get("/api/items")
def get_items():
    return list_items()

@app.post("/api/items")
def post_item(payload: ItemPayload):
    return create_item(payload.model_dump())

@app.put("/api/items/{{item_id}}")
def put_item(item_id: int, payload: ItemPayload):
    updated = update_item(item_id, payload.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated

@app.delete("/api/items/{{item_id}}")
def remove_item(item_id: int):
    deleted = delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {{"ok": True, "id": item_id}}
'''.strip()


def localstorage_backend_store_code() -> str:
    return '''_ITEMS = [
    {"id": 1, "title": "Sample item", "status": "ready", "value": 42, "meta": {}},
    {"id": 2, "title": "Starter record", "status": "draft", "value": None, "meta": {}},
]


def list_items():
    return list(reversed(_ITEMS))


def create_item(payload):
    new_id = max([item["id"] for item in _ITEMS], default=0) + 1
    item = {"id": new_id, **payload}
    _ITEMS.append(item)
    return item


def update_item(item_id, payload):
    for index, item in enumerate(_ITEMS):
        if item["id"] == item_id:
            updated = {"id": item_id, **payload}
            _ITEMS[index] = updated
            return updated
    return None


def delete_item(item_id):
    for index, item in enumerate(_ITEMS):
        if item["id"] == item_id:
            _ITEMS.pop(index)
            return True
    return False
'''.strip()


def sqlite_backend_store_code() -> str:
    return '''import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("app.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init():
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            value TEXT,
            meta TEXT
        )
        """
    )
    conn.commit()
    conn.close()


_init()


def list_items():
    conn = _connect()
    rows = conn.execute("SELECT id, title, status, value, meta FROM items ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_item(payload):
    conn = _connect()
    cursor = conn.execute(
        "INSERT INTO items (title, status, value, meta) VALUES (?, ?, ?, ?)",
        (payload.get("title", "Untitled"), payload.get("status", "draft"), str(payload.get("value")), json.dumps(payload.get("meta", {}))),
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return {"id": item_id, **payload}


def update_item(item_id, payload):
    conn = _connect()
    cursor = conn.execute(
        "UPDATE items SET title = ?, status = ?, value = ?, meta = ? WHERE id = ?",
        (payload.get("title", "Untitled"), payload.get("status", "draft"), str(payload.get("value")), json.dumps(payload.get("meta", {})), item_id),
    )
    conn.commit()
    conn.close()
    if not cursor.rowcount:
        return None
    return {"id": item_id, **payload}


def delete_item(item_id):
    conn = _connect()
    cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return bool(cursor.rowcount)
'''.strip()


def supabase_backend_store_code() -> str:
    return '''import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


def list_items():
    if not client:
        return []
    result = client.table("items").select("*").order("id", desc=True).execute()
    return result.data or []


def create_item(payload):
    if not client:
        return {"id": 1, **payload}
    result = client.table("items").insert(payload).execute()
    return (result.data or [payload])[0]


def update_item(item_id, payload):
    if not client:
        return {"id": item_id, **payload}
    result = client.table("items").update(payload).eq("id", item_id).execute()
    data = result.data or []
    return data[0] if data else None


def delete_item(item_id):
    if not client:
        return True
    client.table("items").delete().eq("id", item_id).execute()
    return True
'''.strip()


def supabase_schema_code() -> str:
    return '''create table if not exists items (
  id bigint generated by default as identity primary key,
  title text not null,
  status text not null default 'draft',
  value text,
  meta jsonb default '{}'::jsonb
);
'''.strip()


def package_json_code() -> str:
    return json.dumps({
        "name": "generated-builder-app",
        "private": True,
        "version": "0.0.1",
        "type": "module",
        "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
        "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
        "devDependencies": {"vite": "^5.4.10"},
    }, indent=2)


def vite_env_example_code() -> str:
    return "VITE_API_URL=http://localhost:8000\n"


def readme_code(app_type: str, persistence: str, systems: List[str]) -> str:
    return f'''# Generated App

## App type
{app_type}

## Systems
{", ".join(systems) if systems else "base"}

## Persistence
{persistence}

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
uvicorn main:app --reload --port 8000
```
'''.strip()


def generate_code_bundle(prompt: str, app_type: str, builder_mode: str, style: str, systems: List[str], persistence: str, monetization_plan: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    files = [
        {"path": "frontend/src/main.jsx", "language": "javascript", "content": main_jsx()},
        {"path": "frontend/src/App.jsx", "language": "javascript", "content": root_app_code(app_type)},
        {"path": "frontend/src/styles/app.css", "language": "css", "content": app_css(style)},
        {"path": "frontend/src/lib/api.js", "language": "javascript", "content": api_client_code()},
        {"path": "frontend/package.json", "language": "json", "content": package_json_code()},
        {"path": "frontend/.env.example", "language": "text", "content": vite_env_example_code()},
        {"path": "backend/main.py", "language": "python", "content": backend_api_code(persistence)},
        {"path": "backend/requirements.txt", "language": "text", "content": backend_requirements_code(persistence)},
        {"path": "backend/.env.example", "language": "text", "content": backend_env_example_code(persistence)},
        {"path": "README.md", "language": "markdown", "content": readme_code(app_type, persistence, systems)},
    ]

    if monetization_plan:
        files += [
            {"path": "frontend/src/lib/monetization.js", "language": "javascript", "content": monetization_data_code(monetization_plan)},
            {"path": "frontend/src/components/MonetizationPanel.jsx", "language": "javascript", "content": monetization_panel_code()},
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

    if "auth" in systems:
        files += [
            {"path": "frontend/src/pages/LoginPage.jsx", "language": "javascript", "content": login_page_code()},
            {"path": "frontend/src/lib/auth.js", "language": "javascript", "content": auth_code()},
        ]

    if "storage" in systems:
        files.append({"path": "frontend/src/hooks/useItems.js", "language": "javascript", "content": use_items_hook_code()})

    if builder_mode == "battery-planner":
        files += [
            {"path": "frontend/src/lib/batteryMath.js", "language": "javascript", "content": battery_math_code()},
            {"path": "frontend/src/components/ApplianceTable.jsx", "language": "javascript", "content": appliance_table_code()},
        ]

    if persistence == "sqlite":
        files.append({"path": "backend/data_store.py", "language": "python", "content": sqlite_backend_store_code()})
    elif persistence == "supabase":
        files.append({"path": "backend/data_store.py", "language": "python", "content": supabase_backend_store_code()})
        files.append({"path": "backend/supabase_schema.sql", "language": "sql", "content": supabase_schema_code()})
    else:
        files.append({"path": "backend/data_store.py", "language": "python", "content": localstorage_backend_store_code()})

    return files


@app.post("/mutate")
def mutate(payload: MutateRequest):
    prompt = payload.prompt.strip()
    decisions = infer_decisions_from_message(prompt, payload.project_memory or {})
    app_type, builder_mode, systems, resolved_complexity = resolve_builder_state(
        prompt,
        payload.project_memory,
        payload.feature_state,
        payload.system_planner,
        systems=payload.systems,
    )
    app_type, builder_mode = apply_decisions_to_product(app_type, builder_mode, decisions)
    summary_style = infer_summary_style(prompt)
    systems = apply_decisions_to_systems(systems, decisions)
    persistence = infer_persistence(prompt, systems, payload.complexity or resolved_complexity)
    modules = recommend_modules(prompt, app_type)
    layout = build_layout(prompt, payload.current_layout)
    file_tree = build_file_tree(app_type, builder_mode, prompt, systems, persistence)
    routes = build_routes(app_type, prompt, systems)
    components = build_components(app_type, systems)
    summary = build_mutation_summary(layout, modules, app_type, builder_mode, systems, persistence)
    project_memory = build_generation_project_memory(prompt, payload.project_memory, app_type, builder_mode, systems, True)

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
        "project_memory": project_memory,
        "next_best_actions": [
            "materialize files",
            "wire api data flow",
            "regenerate routes",
            "generate code",
        ],
    }


@app.post("/generate-code")
def generate_code(payload: GenerateCodeRequest):
    prompt = payload.prompt.strip()
    decisions = infer_decisions_from_message(prompt, payload.project_memory or {})
    app_type, builder_mode, systems, resolved_complexity = resolve_builder_state(
        prompt,
        payload.project_memory,
        payload.feature_state,
        payload.system_planner,
        app_type=payload.app_type,
        builder_mode=payload.builder_mode,
        systems=payload.systems,
    )
    app_type, builder_mode = apply_decisions_to_product(app_type, builder_mode, decisions)
    systems = apply_decisions_to_systems(systems, decisions)
    style = payload.style or "dark glass"
    complexity = payload.complexity or resolved_complexity or "mvp"
    persistence = payload.persistence or infer_persistence(prompt, systems, complexity)
    project_memory = build_generation_project_memory(prompt, payload.project_memory, app_type, builder_mode, systems, True)

    monetization_config = payload.monetization_config or {}
    template_key = payload.rv_template_key or ("rv_power" if builder_mode == "battery-planner" else "rv_diagnostics" if "ai-tools" in systems else "rv_maintenance")
    camping_profile = payload.rv_camping_profile or "weekend"
    monetization = build_rv_monetization_plan(
        template_key,
        camping_profile,
        180 if builder_mode == "battery-planner" else 120,
        400 if builder_mode == "battery-planner" else 220,
        2000 if builder_mode == "battery-planner" else 1500,
        float(monetization_config.get("monthlyPrice", 9.99) or 9.99),
        float(monetization_config.get("yearlyPrice", 69.99) or 69.99),
        str(monetization_config.get("affiliateTagCa", "rvinspector03-20") or "rvinspector03-20"),
        str(monetization_config.get("affiliateTagUs", "rvinspectorpr-20") or "rvinspectorpr-20"),
    )
    files = generate_code_bundle(prompt, app_type, builder_mode, style, systems, persistence, monetization)
    routes = payload.routes or build_routes(app_type, prompt, systems)
    components = payload.components or build_components(app_type, systems)

    return {
        "ok": True,
        "prompt": prompt,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "style": style,
        "systems": systems,
        "complexity": complexity,
        "persistence": persistence,
        "files": files,
        "generated_files": files,
        "routes": routes,
        "components": components,
        "entry_file": "frontend/src/main.jsx",
        "app_file": "frontend/src/App.jsx",
        "backend_entry": "backend/main.py",
        "project_memory": project_memory,
        "data_flow": {
            "frontend_client": "frontend/src/lib/api.js",
            "backend_routes": ["GET /api/items", "POST /api/items", "PUT /api/items/{id}", "DELETE /api/items/{id}"],
            "storage_file": "backend/data_store.py",
        },
        "monetization": monetization,
        "monetization_wired": True,
        "summary": f"Generated {len(files)} files for a {app_type} in {builder_mode} mode with {persistence} persistence and live data flow.",
    }


@app.post("/orchestrate")
def orchestrate(payload: OrchestrateRequest):
    prompt = payload.prompt.strip()
    decisions = infer_decisions_from_message(prompt, payload.project_memory or {})
    app_type, builder_mode, systems, resolved_complexity = resolve_builder_state(
        prompt,
        payload.project_memory,
        payload.feature_state,
        payload.system_planner,
        app_type=payload.app_type,
        builder_mode=payload.builder_mode,
        systems=payload.systems,
    )
    app_type, builder_mode = apply_decisions_to_product(app_type, builder_mode, decisions)
    systems = apply_decisions_to_systems(systems, decisions)
    complexity = payload.complexity or resolved_complexity or "mvp"
    style = payload.style or "dark glass"
    persistence = payload.persistence or infer_persistence(prompt, systems, complexity)
    modules = recommend_modules(prompt, app_type)
    layout = build_layout(prompt, payload.current_layout)
    file_tree = build_file_tree(app_type, builder_mode, prompt, systems, persistence)
    routes = payload.routes or build_routes(app_type, prompt, systems)
    components = payload.components or build_components(app_type, systems)
    summary = build_mutation_summary(layout, modules, app_type, builder_mode, systems, persistence)
    project_memory = build_generation_project_memory(prompt, payload.project_memory, app_type, builder_mode, systems, True)
    project_id = build_project_id(payload.project_id)

    monetization_config = payload.monetization_config or {}
    template_key = payload.rv_template_key or ("rv_power" if builder_mode == "battery-planner" else "rv_diagnostics" if "ai-tools" in systems else "rv_maintenance")
    camping_profile = payload.rv_camping_profile or "weekend"
    monetization = build_rv_monetization_plan(
        template_key,
        camping_profile,
        180 if builder_mode == "battery-planner" else 120,
        400 if builder_mode == "battery-planner" else 220,
        2000 if builder_mode == "battery-planner" else 1500,
        float(monetization_config.get("monthlyPrice", 9.99) or 9.99),
        float(monetization_config.get("yearlyPrice", 69.99) or 69.99),
        str(monetization_config.get("affiliateTagCa", "rvinspector03-20") or "rvinspector03-20"),
        str(monetization_config.get("affiliateTagUs", "rvinspectorpr-20") or "rvinspectorpr-20"),
    )
    files = generate_code_bundle(prompt, app_type, builder_mode, style, systems, persistence, monetization)

    return {
        "ok": True,
        "project_id": project_id,
        "prompt": prompt,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "style": style,
        "systems": systems,
        "complexity": complexity,
        "persistence": persistence,
        "files": files,
        "generated_files": files,
        "routes": routes,
        "components": components,
        "file_tree": file_tree,
        "layout_changes": layout,
        "module_changes": {"enable": modules, "disable": []},
        "mutation_summary": summary,
        "project_memory": project_memory,
        "monetization": monetization,
        "next_best_actions": [
            "materialize files",
            "wire api data flow",
            "export this app for render",
            "improve mobile",
        ],
        "project_state": {
            "project_id": project_id,
            "files": files,
            "routes": routes,
            "components": components,
            "file_tree": file_tree,
            "layout": layout,
            "modules": modules,
        },
        "summary": f"Orchestrated project {project_id} with {len(files)} files for a {app_type} in {builder_mode} mode.",
    }


@app.post("/repo-edit")
def repo_edit(payload: RepoEditRequest):
    prompt = payload.prompt.strip()
    decisions = infer_decisions_from_message(prompt, payload.project_memory or {})
    app_type, builder_mode, systems, resolved_complexity = resolve_builder_state(
        prompt,
        payload.project_memory,
        payload.feature_state,
        payload.system_planner,
        app_type=payload.app_type,
        builder_mode=payload.builder_mode,
        systems=payload.systems,
    )
    app_type, builder_mode = apply_decisions_to_product(app_type, builder_mode, decisions)
    systems = apply_decisions_to_systems(systems, decisions)
    complexity = payload.complexity or resolved_complexity or "product"
    style = payload.style or "dark glass"
    persistence = payload.persistence or infer_persistence(prompt, systems, complexity)
    target_scope = normalize_repo_scope(payload.target_scope)
    routes = build_routes(app_type, prompt, systems)
    components = build_components(app_type, systems)
    file_tree = build_file_tree(app_type, builder_mode, prompt, systems, persistence)
    project_memory = build_generation_project_memory(prompt, payload.project_memory, app_type, builder_mode, systems, True)
    project_memory["preferred_scope"] = "frontend-and-backend" if target_scope == "fullstack" else target_scope
    project_memory["repo_edit_enabled"] = True

    generated_files = generate_code_bundle(prompt, app_type, builder_mode, style, systems, persistence)
    merged_files, changed_paths = merge_repo_edit_files(payload.current_files, generated_files, target_scope)

    return {
        "ok": True,
        "prompt": prompt,
        "app_type": app_type,
        "builder_mode": builder_mode,
        "systems": systems,
        "complexity": complexity,
        "persistence": persistence,
        "target_scope": target_scope,
        "routes": routes,
        "components": components,
        "file_tree": file_tree,
        "generated_files": merged_files,
        "files": merged_files,
        "changed_files": changed_paths,
        "changed_file_count": len(changed_paths),
        "project_memory": project_memory,
        "summary": f"Repo edit prepared {len(changed_paths)} {target_scope} file updates for a {app_type} in {builder_mode} mode.",
    }


@app.post("/workspace-edit")
def workspace_edit(payload: WorkspaceEditRequest):
    workspace_root = get_workspace_root()
    if not workspace_root:
        return {
            "ok": False,
            "error": "Workspace edit is not enabled. Set BUILDER_WORKSPACE_ROOT on the backend.",
            "workspace_edit_enabled": False,
        }

    target_root = resolve_workspace_target(workspace_root, payload.workspace_subdir)
    repo_result = repo_edit(payload)
    if not repo_result.get("ok"):
        return repo_result

    write_result = write_workspace_files(target_root, repo_result.get("files") or [], repo_result.get("changed_files") or [])
    repo_result["workspace_edit_enabled"] = True
    repo_result["workspace_root_configured"] = True
    repo_result["workspace_subdir"] = payload.workspace_subdir or ""
    repo_result["written_files"] = write_result.get("written_files") or []
    repo_result["written_file_count"] = len(repo_result["written_files"])
    repo_result["backup_manifest"] = write_result.get("backup_manifest") or ""
    repo_result["backup_entries"] = write_result.get("backup_entries") or []
    repo_result["backup_count"] = int(write_result.get("backup_count") or 0)
    repo_result["summary"] = (
        f"Workspace edit wrote {repo_result['written_file_count']} files inside the configured workspace root "
        f"for a {repo_result.get('app_type', 'project')} in {repo_result.get('builder_mode', 'builder')} mode."
    )
    return repo_result

@app.post("/chat-agent")
def chat_agent(payload: ChatAgentRequest):
    return build_agent_reply(payload)
