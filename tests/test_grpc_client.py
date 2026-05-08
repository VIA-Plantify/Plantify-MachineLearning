from unittest.mock import AsyncMock, patch

import pytest

from grpc_clients.plant_grpc_client import plant_grpc_client

@pytest.mark.asyncio
async def test_get_all_returns_plants():

    fake_response = {
        "plants": [
            {
                "name": "Monstera"
            }
        ]
    }

    with patch(
        "grpc_clients.plant_grpc_client.MessageToDict",
        return_value=fake_response
    ):

        with patch(
            "grpc_clients.plant_grpc_client.plant_service.PlantServiceProtoStub"
        ) as mock_stub:

            mock_stub_instance = mock_stub.return_value

            mock_stub_instance.GetAllPlants = AsyncMock()

            client = plant_grpc_client()

            result = await client.get_all()

            assert result == fake_response

@pytest.mark.asyncio
async def test_get_plant_returns_single_plant():

    fake_response = {
        "name": "Snake Plant",
        "plantMAC": "AA:BB:CC"
    }

    with patch(
        "grpc_clients.plant_grpc_client.MessageToDict",
        return_value=fake_response
    ):

        with patch(
            "grpc_clients.plant_grpc_client.plant_service.PlantServiceProtoStub"
        ) as mock_stub:

            mock_stub_instance = mock_stub.return_value

            mock_stub_instance.Get = AsyncMock()

            client = plant_grpc_client()

            result = await client.get_plant(
                plant_MAC="AA:BB:CC",
                username="carolina",
                number_of_readings=10,
                number_of_waterings=5
            )

            assert result["name"] == "Snake Plant"
            assert result["plantMAC"] == "AA:BB:CC"