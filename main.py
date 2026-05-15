from dataclasses import asdict

from entities.Plant import Plant
from entities.Sensor import Sensor
from entities.Watering import Watering

from fastapi import FastAPI

from api.plant_api_controller import router as plant_router

app = FastAPI(title="Plantify ML API")

app.include_router(plant_router)


def dummy():
    plant = Plant(username="John", MAC="124123", name="Patrik", optimal_temperature=20, optimal_air_humidity=20,
                  optimal_soil_humidity=20, optimal_light_intensity=1000)
    sensors = list[Sensor]()
    waterings = list[Watering]()
    for i in range(0, 10):
        sensors.append(Sensor(temperature=i, plant_mac=plant.MAC, soil_humidity=i, air_humidity=i, light_intensity=i))
        waterings.append(Watering(plant_mac=plant.MAC, ))
    plant.sensors = sensors
    plant.waterings = waterings
    return plant


@app.get("/")
async def root():
    return ({"message": "Plantify API is running"})

@app.get("/data")
async def dummy_api():
    return asdict(dummy())