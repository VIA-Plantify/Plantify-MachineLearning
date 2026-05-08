import csv
import psycopg2
from grpc import RpcError, StatusCode
from grpc_clients.plant_grpc_client import plant_grpc_client
import asyncio

client = plant_grpc_client()

async def get_all_by_username(username: str,
                              number_of_readings: int,
                              number_of_waterings: int) -> dict:
    try:
        return await client.get_by_username(username, number_of_readings=number_of_readings,
                                            number_of_waterings=number_of_waterings)
    except RpcError as e:
        exit(1)

result = asyncio.run(get_all_by_username(username="janedoe", number_of_readings=1, number_of_waterings=1))
print(result)

async def get_max_ids() -> dict:
    try:
        result = await client.get_all()
        max_watering_id = 0
        max_sensor_id = 0
        #nested in plants
        if 'plants' in result:
            for plant in result['plants']:
                #last sensor data id from current sensorData
                if 'sensorData' in plant and plant['sensorData']:
                    sensor = plant['sensorData']
                    if 'Id' in sensor:
                        max_sensor_id = max(max_sensor_id, int(sensor['Id']))
                #last sensor data id from previousSensorReadings
                if 'previousSensorReadings' in plant and plant['previousSensorReadings']:
                    for sensor in plant['previousSensorReadings']:
                        if 'Id' in sensor:
                            max_sensor_id = max(max_sensor_id, int(sensor['Id']))
                #last watering id from current watering
                if 'watering' in plant and plant['watering']:
                    watering = plant['watering']
                    if 'Id' in watering:
                        max_watering_id = max(max_watering_id, int(watering['Id']))
                #last watering id from previousWateringReadings
                if 'previousWateringReadings' in plant and plant['previousWateringReadings']:
                    for watering in plant['previousWateringReadings']:
                        if 'Id' in watering:
                            max_watering_id = max(max_watering_id, int(watering['Id']))
        return {
            'max_watering_id': max_watering_id,
            'max_sensor_id': max_sensor_id
        }
    except RpcError as e:
        return {
            'max_watering_id': 0,
            'max_sensor_id': 0
        }

def format_sql_value(value):
    if not value or value.upper() == 'NULL':
        return 'NULL'
    try:
        float(value)
        return value
    except ValueError:
        escaped = value.replace("'", "''")
        return f"'{escaped}'"

def increment_id_in_row(row, id_column, current_max_id):
    if id_column in row and row[id_column]:
        try:
            row[id_column] = str(int(row[id_column]) + current_max_id)
        except ValueError:
            pass
    return row

async def main():
    #get the last ids
    max_ids = await get_max_ids()
    max_watering_id = max_ids['max_watering_id']
    max_sensor_id = max_ids['max_sensor_id']

    print(f"Last watering ID: {max_watering_id}")
    print(f"Last sensor data ID: {max_sensor_id}")

    sql_file = open('plantify_data.sql', 'w')

    # Read Plants CSV with column names
    with open('../mockdata/plants.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            columns = ', '.join(f'"{k}"' for k in row.keys())
            values = ', '.join(format_sql_value(v) for v in row.values())
            sql_file.write(f"INSERT INTO \"Plants\" ({columns}) VALUES ({values});\n")

    # Read SensorDatas CSV with column names and increment IDs
    with open('../mockdata/sensor_datas.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = increment_id_in_row(row, 'id', max_sensor_id)
            columns = ', '.join(f'"{k}"' for k in row.keys())
            values = ', '.join(format_sql_value(v) for v in row.values())
            sql_file.write(f"INSERT INTO \"SensorDatas\" ({columns}) VALUES ({values});\n")

    # Read Waterings CSV with column names and increment IDs
    with open('../mockdata/waterings.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = increment_id_in_row(row, 'id', max_watering_id)
            columns = ', '.join(f'"{k}"' for k in row.keys())
            values = ', '.join(format_sql_value(v) for v in row.values())
            sql_file.write(f"INSERT INTO \"Waterings\" ({columns}) VALUES ({values});\n")

    sql_file.close()

if __name__ == "__main__":
    asyncio.run(main())