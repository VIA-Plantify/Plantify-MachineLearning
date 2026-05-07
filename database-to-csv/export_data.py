import csv
import os
import psycopg2

# Connect to PostgreSQL TODO: get from grpc getAllPlants()
conn = psycopg2.connect(
    host='host.docker.internal',
    port=55432,
    database='plantify',
    user='dev',
    password='plantifydev'
)
cursor = conn.cursor()

# Query the Users table
cursor.execute('SELECT * FROM "Users";')

# Write to CSV
with open("users.csv", "w", newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    # Get column names from cursor description
    csv_writer.writerow([i[0] for i in cursor.description])
    csv_writer.writerows(cursor)

conn.close()
print("✓ Successfully exported users.csv")