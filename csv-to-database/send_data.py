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

# conn = psycopg2.connect(
#     host='host.docker.internal',
#     port=55432,
#     database='plantify',
#     user='dev',
#     password='plantifydev'
# )
# cursor = conn.cursor()
#
# sql_file = open('plantify_data.sql', 'w')
#
# # Read CSV file and pipe it to PostgreSQL
# with open('../mockdata/plants_users.csv', 'r') as f:
#     cursor.copy_expert(
#         '''COPY "Plants"("MAC", "Name", "Username", "OptimalTemperature",
#         "OptimalAirHumidity", "OptimalSoilHumidity", "OptimalLightIntensity")
#         FROM STDIN WITH (FORMAT CSV, HEADER)''',
#         f
#     )
#
# conn.commit()
#
# cursor.execute('SELECT * FROM "Plants";')
# rows = cursor.fetchall()
# for row in rows:
#     sql_file.write(f"INSERT INTO \"Plants\" VALUES {row};\n")
#
# with open('../mockdata/sensor_datas_users.csv', 'r') as f:
#     cursor.copy_expert(
#         '''COPY "SensorDatas"("PlantMAC", "Temperature", "AirHumidity",
#         "SoilHumidity", "LightIntensity", "Timestamp")
#         FROM STDIN WITH (FORMAT CSV, HEADER)''',
#         f
#     )
#
# conn.commit()
#
# cursor.execute('SELECT * FROM "SensorDatas";')
# rows = cursor.fetchall()
# for row in rows:
#     sql_file.write(f"INSERT INTO \"SensorDatas\" VALUES {row};\n")
#
# with open('../mockdata/waterings_users.csv', 'r') as f:
#     cursor.copy_expert(
#         '''COPY "Waterings"("PlantMAC", "PredictedFutureWaterTime", "LastWaterTime",
#         "WaterLevel", "PumpTimeInSeconds")
#         FROM STDIN WITH (FORMAT CSV, HEADER)''',
#         f
#     )
#
# conn.commit()
#
# cursor.execute('SELECT * FROM "Waterings";')
# rows = cursor.fetchall()
# for row in rows:
#     sql_file.write(f"INSERT INTO \"Waterings\" VALUES {row};\n")
#
# sql_file.close()
#
# conn.close()