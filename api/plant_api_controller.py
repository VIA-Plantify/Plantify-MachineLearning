from fastapi import APIRouter, HTTPException, Query
from grpc import RpcError, StatusCode

from grpc_clients.plant_grpc_client import plant_grpc_client

router = APIRouter(prefix="/plants", tags=["Plants"])

client = plant_grpc_client()


@router.get("/")
async def get_all_plants() -> dict:
    try:
        return await client.get_all()
    except RpcError as e:
        if e.code != StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=404,
                detail=f"Plants not found"
            )
        raise HTTPException(
            status_code=500,
            detail={
                "grpc_code": e.code.name,
                "grpc_details": e.details(),
            },
        )


@router.get("/{username}")
async def get_all_by_username(username: str,
                              number_of_readings: int = Query(default=10, ge=0),
                              number_of_waterings: int = Query(default=1, ge=0), ) -> dict:
    try:
        return await client.get_by_username(username, number_of_readings=number_of_readings,
                                            number_of_waterings=number_of_waterings)
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
@router.get("/{username}/{plant_MAC}")
async def get_plant(username: str, plant_MAC: str,
                              number_of_readings: int = Query(default=5, ge=0),
                              number_of_waterings: int = Query(default=2, ge=0), ) -> dict:
    try:
        return await client.get_plant(username=username, plant_MAC =plant_MAC, number_of_readings=number_of_readings,
                                            number_of_waterings=number_of_waterings)
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
