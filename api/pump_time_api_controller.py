from fastapi import APIRouter, HTTPException, Query
from grpc import RpcError, StatusCode

from entities.Sensor import Sensor
from models.pump_time.pump_time_model import  PumpTimeModel
from grpc_clients.plant_grpc_client import plant_grpc_client


ml_model = PumpTimeModel()
router = APIRouter(prefix="/pumptime", tags=["Pump"])

client = plant_grpc_client()
predictor = PumpTimeModel()

@router.get("/{username}/{plant_MAC}")
async def get_pump_time(username: str, plant_MAC: str):
    try:
        plant_data = await client.get_plant(
            username=username,
            plant_MAC=plant_MAC,
            number_of_readings=1,
            number_of_waterings=1
        )

        # Map and predict
        model_input = map_plant_data_to_model_input(plant_data)
        predicted_seconds = predictor.predict(**model_input)

        return predicted_seconds

    except Exception as e:
        # your existing error handling...
        raise HTTPException(status_code=500, detail=str(e))

def map_plant_data_to_model_input(plant_data: dict) -> dict:
    """
    Maps the gRPC returned plant data to the format expected by PumpTimeModel.predict()
    """
    sensor = plant_data["sensorData"]
    watering = plant_data["watering"]
    optimal = plant_data

    return {
        "temperature": sensor["Temperature"],
        "air_humidity": sensor["AirHumidity"],
        "soil_humidity": sensor["SoilHumidity"],
        "light_intensity": sensor["LightIntensity"],
        "sensor_timestamp": sensor["Timestamp"],
        "last_water_timestamp": watering["LastWaterTime"],

        "optimal_temperature": optimal["optimalTemperature"],
        "optimal_air_humidity": optimal["optimalAirHumidity"],
        "optimal_soil_humidity": optimal["optimalSoilHumidity"],
        "optimal_light_intensity": optimal["optimalLightIntensity"],
    }


