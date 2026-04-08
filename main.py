from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

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
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}


class ApplianceItem(BaseModel):
    name: str = ""
    watts: float = 0
    hours: float = 0


class BatteryPlanRequest(BaseModel):
    appliances: List[ApplianceItem] = []
    battery_voltage: float = 12
    autonomy_days: float = 1
    sun_hours: float = 4
    system_loss: float = 0.2


@app.post("/battery-plan")
def battery_plan(payload: BatteryPlanRequest):
    daily_wh = sum(
        max(item.watts, 0) * max(item.hours, 0)
        for item in payload.appliances
    )

    adjusted_daily_wh = daily_wh * (1 + max(payload.system_loss, 0))

    battery_ah = round(
        (adjusted_daily_wh * max(payload.autonomy_days, 1))
        / max(payload.battery_voltage, 1),
        1,
    )

    solar_watts = round(
        adjusted_daily_wh / max(payload.sun_hours, 1),
        1,
    )

    return {
        "daily_wh": round(daily_wh, 1),
        "adjusted_daily_wh": round(adjusted_daily_wh, 1),
        "battery_ah": battery_ah,
        "solar_watts": solar_watts,
        "summary": f"For this setup, plan for about {battery_ah}Ah of battery and {solar_watts}W of solar."
    }
