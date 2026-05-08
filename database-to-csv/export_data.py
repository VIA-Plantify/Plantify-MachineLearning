import csv
from grpc import RpcError
from grpc_clients.plant_grpc_client import plant_grpc_client
import asyncio

client = plant_grpc_client()

async def export_plants_to_csv() -> None:
    try:
        result = await client.get_all()
        if not result or 'plants' not in result:
            print("No plants data available")
            return

        plants = result.get('plants', [])

        if not plants:
            print("Plants list is empty")
            return
        #all unique keys from all plants
        all_keys = set()
        for plant in plants:
            all_keys.update(plant.keys())

        all_keys = sorted(list(all_keys))

        with open("plants.csv", "w", newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=all_keys)
            csv_writer.writeheader()
            for plant in plants:
                #create a row with all keys, filling missing keys with empty strings
                row = {key: plant.get(key, '') for key in all_keys}
                csv_writer.writerow(row)
        print(f"✓ Successfully exported {len(plants)} plants to plants.csv")

    except RpcError as e:
        print(f"gRPC error exporting plants: {e}")
    except Exception as e:
        print(f"Error exporting plants: {e}")

async def main():
    print("Starting plants export via gRPC...")
    await export_plants_to_csv()
    print("✓ Export completed")

if __name__ == "__main__":
    asyncio.run(main())