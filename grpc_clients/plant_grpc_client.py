import sys
from pathlib import Path

generated_path = Path(__file__).resolve().parents[1] / "generated"
sys.path.insert(0, str(generated_path))

import grpc
import plant_pb2_grpc as plant_service
import plant_pb2 as plant_proto
import sensors_pb2 as sensors_proto
import watering_pb2 as watering_pb2

from config.settings import settings


class plant_grpc_client():
    async def get_by_username(self, username: str, number_of_readings: int, number_of_waterings: int) -> dict:
        async with grpc.aio.insecure_channel(settings.grpc_address) as channel:
            return True

    async def get_all(self) -> dict:
        async with grpc.aio.insecure_channel(settings.grpc_address) as channel:
            return True

    async def get_plant(self, plant_MAC: str, username: str,
                        number_of_readings: int, number_of_waterings: int) -> dict:
        return True
