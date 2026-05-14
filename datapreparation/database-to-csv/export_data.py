import csv
import json
import ast
from grpc import RpcError
from grpc_clients.plant_grpc_client import plant_grpc_client
from typing import Any, Dict, List
import asyncio

client = plant_grpc_client()

def parse_nested_string(value: str) -> Any:
    if not isinstance(value, str):
        return value
    try:
        # Try JSON first
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        try:
            # Try Python literal eval for dict/list strings
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

def export_plants(plants: List[Dict]) -> None:
    if not plants:
        print("Plants list is empty")
        return

    #excluded so it doesn't go into plants.csv
    excluded_fields = {
        'previousSensorReadings',
        'previousWateringReadings',
        'sensorData',
        'watering'
    }

    all_keys = set()
    for plant in plants:
        for key in plant.keys():
            if key not in excluded_fields:
                all_keys.add(key)

    all_keys = sorted(list(all_keys))

    with open("exported_plants.csv", "w", newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=all_keys)
        csv_writer.writeheader()
        for plant in plants:
            row = {key: plant.get(key, '') for key in all_keys}
            csv_writer.writerow(row)

    print(f"✓ Successfully exported {len(plants)} plants to exported_plants.csv")

def export_waterings(waterings: List[Dict]) -> None:
    if not waterings:
        print("No waterings data available")
        return

    all_keys = set()
    for watering in waterings:
        all_keys.update(watering.keys())

    all_keys = sorted(list(all_keys))

    with open("exported_waterings.csv", "w", newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=all_keys)
        csv_writer.writeheader()
        for watering in waterings:
            row = {key: watering.get(key, '') for key in all_keys}
            csv_writer.writerow(row)
    print(f"✓ Successfully exported {len(waterings)} waterings to exported_waterings.csv")


def export_sensordatas(sensordatas: List[Dict]) -> None:
    if not sensordatas:
        print("No sensor data available")
        return

    all_keys = set()
    for sensordata in sensordatas:
        all_keys.update(sensordata.keys())

    all_keys = sorted(list(all_keys))

    with open("exported_sensor_datas.csv", "w", newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=all_keys)
        csv_writer.writeheader()
        for sensordata in sensordatas:
            row = {key: sensordata.get(key, '') for key in all_keys}
            csv_writer.writerow(row)
    print(f"✓ Successfully exported {len(sensordatas)} sensor data entries to exported_sensor_datas.csv")


async def export_all_data() -> None:
    try:
        result = await client.get_all()
        if not result:
            print("No data available")
            return

        plants = result.get('plants', [])
        waterings = result.get('waterings', [])
        sensordatas = result.get('sensordatas', [])

        #extract nested waterings and sensor datas from plants
        for plant in plants:
            if 'previousWateringReadings' in plant:
                prev_water = parse_nested_string(plant['previousWateringReadings'])
                if isinstance(prev_water, dict) and 'Readings' in prev_water:
                    waterings.extend(prev_water['Readings'])

            if 'previousSensorReadings' in plant:
                prev_sensor = parse_nested_string(plant['previousSensorReadings'])
                if isinstance(prev_sensor, dict) and 'Readings' in prev_sensor:
                    sensordatas.extend(prev_sensor['Readings'])

            if 'sensorData' in plant:
                current_sensor = parse_nested_string(plant['sensorData'])
                if isinstance(current_sensor, dict):
                    sensordatas.append(current_sensor)

            if 'watering' in plant:
                current_water = parse_nested_string(plant['watering'])
                if isinstance(current_water, dict):
                    waterings.append(current_water)

        export_plants(plants)
        export_waterings(waterings)
        export_sensordatas(sensordatas)

    except RpcError as e:
        print(f"gRPC error exporting data: {e}")
    except Exception as e:
        print(f"Error exporting data: {e}")

async def main():
    print("Starting data export via gRPC...")
    await export_all_data()
    print("✓ Export completed")

if __name__ == "__main__":
    asyncio.run(main())