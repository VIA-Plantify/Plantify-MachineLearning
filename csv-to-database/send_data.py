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

#TODO get the last id from the grpc and add new data after that id, and save it in sql file; NO connection to the db

sql_file = open('plantify_data.sql', 'w')

# Read CSV file and pipe it to PostgreSQL
with open('../mockdata/plants_users.csv', 'r') as f:
    reader = csv.reader(f)
    headers = next(reader)  # Skip header row
    for row in reader:
        # Format values: handle strings with quotes, numbers as-is
        formatted_values = []
        for value in row:
            if value.isdigit() or (value.count('.') == 1 and value.replace('.', '').isdigit()):
                formatted_values.append(value)  # Numbers
            else:
                formatted_values.append(f"'{value}'")  # Strings with quotes

        values_str = ', '.join(formatted_values)
        sql_file.write(f"INSERT INTO \"Plants\" VALUES ({values_str});\n")

# Read SensorDatas CSV and generate INSERT statements
with open('../mockdata/sensor_datas_users.csv', 'r') as f:
    reader = csv.reader(f)
    headers = next(reader)  # Skip header row
    for row in reader:
        formatted_values = []
        for value in row:
            if value.isdigit() or (value.count('.') == 1 and value.replace('.', '').isdigit()):
                formatted_values.append(value)
            else:
                formatted_values.append(f"'{value}'")

        values_str = ', '.join(formatted_values)
        sql_file.write(f"INSERT INTO \"SensorDatas\" VALUES ({values_str});\n")

# Read Waterings CSV and generate INSERT statements
with open('../mockdata/waterings_users.csv', 'r') as f:
    reader = csv.reader(f)
    headers = next(reader)  # Skip header row
    for row in reader:
        formatted_values = []
        for value in row:
            if value.isdigit() or (value.count('.') == 1 and value.replace('.', '').isdigit()):
                formatted_values.append(value)
            else:
                formatted_values.append(f"'{value}'")

        values_str = ', '.join(formatted_values)
        sql_file.write(f"INSERT INTO \"Waterings\" VALUES ({values_str});\n")

sql_file.close()
print("SQL script generated: plantify_data.sql")