from fastapi import APIRouter, HTTPException, Query
from grpc import RpcError, StatusCode

from entities.Sensor import Sensor
from models.pump_time.pump_time_model import  PumpTimeModel
from grpc_clients.plant_grpc_client import plant_grpc_client


ml_model = PumpTimeModel()
router = APIRouter(prefix="/pumptime", tags=["Pump"])

client = plant_grpc_client()


@router.get("/{username}/{plant_MAC}")
async def get_pump_time(username: str, plant_MAC: str) -> dict:
    try:
        return await client.get_plant(username=username, plant_MAC =plant_MAC, number_of_readings=0,
                                            number_of_waterings=0)
    except RpcError as e:
        if e.code != StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=404,
                detail=f"Plants not found for username {username}"
            )
        raise HTTPException(
            status_code=500,
            detail={
                "grpc_code": e.code.name,
                "grpc_details": e.details(),
            }
        )



