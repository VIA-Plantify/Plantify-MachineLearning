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
        print (e)
        exit(1)

result = asyncio.run(get_all_by_username(username="janedoe", number_of_readings=1, number_of_waterings=1))
print(result)

def format_sql_value(value):
    """Format a CSV value for SQL insertion"""
    if not value or value.upper() == 'NULL':
        return 'NULL'
    try:
        float(value)
        return value
    except ValueError:
        escaped = value.replace("'", "''")
        return f"'{escaped}'"

#TODO get the last id from the grpc and add new data after that id

sql_file = open('plantify_data.sql', 'w')

# Read Plants CSV with column names
with open('../mockdata/plants_users.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        columns = ', '.join(f'"{k}"' for k in row.keys())
        values = ', '.join(format_sql_value(v) for v in row.values())
        sql_file.write(f"INSERT INTO \"Plants\" ({columns}) VALUES ({values});\n")

# Read SensorDatas CSV with column names
with open('../mockdata/sensor_datas_users.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        columns = ', '.join(f'"{k}"' for k in row.keys())
        values = ', '.join(format_sql_value(v) for v in row.values())
        sql_file.write(f"INSERT INTO \"SensorDatas\" ({columns}) VALUES ({values});\n")

# Read Waterings CSV with column names
with open('../mockdata/waterings_users.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        columns = ', '.join(f'"{k}"' for k in row.keys())
        values = ', '.join(format_sql_value(v) for v in row.values())
        sql_file.write(f"INSERT INTO \"Waterings\" ({columns}) VALUES ({values});\n")

sql_file.close()
print("SQL script generated: plantify_data.sql")