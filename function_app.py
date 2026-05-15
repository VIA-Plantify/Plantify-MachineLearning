from dataclasses import asdict
from fastapi import FastAPI
import azure.functions as func
from api.plant_api_controller import router as plant_router

app = FastAPI(title="Plantify ML API")
app.include_router(plant_router)

main = func.AsgiFunctionApp(app = app, http_auth_level=func.AuthLevel.ANONYMOUS)
