from datetime import datetime, timedelta
import random
import csv
from typing import List
from entities.Plant import Plant
from entities.Sensor import Sensor
from entities.Watering import Watering


class PlantDataGenerator:
    PLANT_NAMES = [
        "Monstera", "Pothos", "Snake Plant", "Fiddle Leaf Fig", "ZZ Plant",
        "Rubber Plant", "Peace Lily", "Philodendron", "Calathea", "Dracaena",
        "Spider Plant", "Boston Fern", "Succulent", "Cactus", "Orchid"
    ]

    def __init__(
            self,
            plants_per_user: int = 1,
            readings_per_plant: int = 100,
            days_of_data: int = 30,
            waterings_per_plant: int = 10,
            watering_threshold_precent: float = 0.85,
    ):

        self.watering_threshold_precent = watering_threshold_precent
        self.plants_per_user = plants_per_user
        self.readings_per_plant = readings_per_plant
        self.days_of_data = days_of_data
        self.waterings_per_plant = waterings_per_plant
        self.base_timestamp = datetime(2025, 1, 1, 12, 0, 0)

    def generate_users(self) -> List[str]:
        """Generate or load users based on configuration."""
        return ['janedoe','Mario','Carolina',"Patrik","Teo"]

    def generate_mac_address(self) -> str:
        return f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:" \
               f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:" \
               f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}"

    def generate_plant_optimal_values(self) -> dict:
        return {
            "optimal_temperature": round(random.uniform(18, 26), 1),  # 18-26°C
            "optimal_air_humidity": round(random.uniform(40, 70), 1),  # 40-70%
            "optimal_soil_humidity": round(random.uniform(50, 80), 1),  # 50-80%
            "optimal_light_intensity": round(random.uniform(300, 800), 1)  # 300-800 lux
        }

    def generate_sensor_readings(self, plant_mac: str, optimal_values: dict) -> List[Sensor]:
        readings = []

        for i in range(self.readings_per_plant):
            temp_variation = random.gauss(0, optimal_values["optimal_temperature"] * 0.1)
            temperature = max(0, optimal_values["optimal_temperature"] + temp_variation)

            air_humidity_variation = random.gauss(0, optimal_values["optimal_air_humidity"] * 0.1)
            air_humidity = max(0, min(100, optimal_values["optimal_air_humidity"] + air_humidity_variation))

            soil_humidity_variation = random.gauss(0, optimal_values["optimal_soil_humidity"] * 0.1)
            soil_humidity = max(0, min(100, optimal_values["optimal_soil_humidity"] + soil_humidity_variation))

            light_intensity_variation = random.gauss(0, optimal_values["optimal_light_intensity"] * 0.15)
            light_intensity = max(0, optimal_values["optimal_light_intensity"] + light_intensity_variation)

            timestamp = self.base_timestamp + timedelta(hours=i)

            reading = Sensor(
                plant_mac=plant_mac,
                temperature=round(temperature, 2),
                air_humidity=round(air_humidity, 2),
                soil_humidity=round(soil_humidity, 2),
                light_intensity=round(light_intensity, 2),
                timestamp=timestamp
            )
            readings.append(reading)

        return readings

    def generate_waterings(
            self,
            plant_mac: str,
            sensor_readings: List[Sensor],
            optimal_values: dict
    ) -> List[Watering]:

        waterings = []

        # get the plant's optimal soil humidity
        optimal_soil = optimal_values["optimal_soil_humidity"]

        # plant needs watering when soil drops below 85% of optimal (less stricter threshold so we have more watering data)
        watering_threshold = optimal_soil * self.watering_threshold_precent
        first = sensor_readings[0]
        waterings.append(Watering(
            plant_mac=plant_mac,
            last_water_time=first.timestamp,
            predicted_future_water_time=first.timestamp + timedelta(days=3),
            water_level=100.0,
            pump_time_in_seconds=10
        ))
        for reading in sensor_readings:

            # check if soil humidity is too low
            if reading.soil_humidity <= watering_threshold:
                # generate random water tank level
                water_level = round(
                    random.uniform(60, 100),
                    2
                )

                # calculate how long the pump should run
                # minimum 5 seconds
                pump_time = int(max(5, (optimal_soil - reading.soil_humidity) * 2))

                # predict next watering time
                predicted_future_water_time = (
                        reading.timestamp +
                        timedelta(days=random.uniform(2, 5))
                )

                # create watering object
                watering = Watering(
                    plant_mac=plant_mac,

                    last_water_time=reading.timestamp,

                    predicted_future_water_time=predicted_future_water_time,

                    water_level=water_level,
                    pump_time_in_seconds=pump_time
                )

                waterings.append(watering)

        return waterings

    def generate_plant(self, username: str) -> Plant:
        optimal_values = self.generate_plant_optimal_values()
        mac = self.generate_mac_address()
        sensor_readings = self.generate_sensor_readings(mac, optimal_values)
        waterings = self.generate_waterings(
            mac,
            sensor_readings,
            optimal_values
        )

        plant_data = Plant(
            MAC=mac,
            username=username,
            optimal_temperature=optimal_values["optimal_temperature"],
            optimal_air_humidity=optimal_values["optimal_air_humidity"],
            optimal_soil_humidity=optimal_values["optimal_soil_humidity"],
            optimal_light_intensity=optimal_values["optimal_light_intensity"],
            sensors=sensor_readings,
            waterings=waterings,
            name=random.choice(self.PLANT_NAMES)
        )

        return plant_data

    def generate_all_plants(self) -> List[Plant]:
        plants = []
        users = self.generate_users()

        for username in users:
            for _ in range(self.plants_per_user):
                plant = self.generate_plant(username)
                plants.append(plant)

        return plants

    @staticmethod
    def export_plants_csv(plants: List[Plant], filename: str = "plants.csv"):

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            writer.writerow([
                'MAC',
                'Name',
                'Username',
                'OptimalTemperature',
                'OptimalAirHumidity',
                'OptimalSoilHumidity',
                'OptimalLightIntensity'
            ])

            for plant in plants:
                writer.writerow([
                    plant.MAC,
                    plant.name,
                    plant.username,
                    plant.optimal_temperature,
                    plant.optimal_air_humidity,
                    plant.optimal_soil_humidity,
                    plant.optimal_light_intensity
                ])

    @staticmethod
    def export_sensor_datas_csv(plants: List[Plant], filename: str = "sensor_datas.csv"):

        with open(filename, 'w', newline='', encoding='utf-8') as f:

            writer = csv.writer(f)

            writer.writerow([
                'PlantMAC',
                'Temperature',
                'AirHumidity',
                'SoilHumidity',
                'LightIntensity',
                'Timestamp'
            ])

            for plant in plants:

                for reading in plant.sensors:
                    writer.writerow([
                        plant.MAC,
                        reading.temperature,
                        reading.air_humidity,
                        reading.soil_humidity,
                        reading.light_intensity,
                        reading.timestamp.isoformat()
                    ])

    @staticmethod
    def export_waterings_csv(plants: List[Plant], filename: str = "waterings.csv"):

        with open(filename, 'w', newline='', encoding='utf-8') as f:

            writer = csv.writer(f)

            writer.writerow([
                'PlantMAC',
                'PredictedFutureWaterTime',
                'LastWaterTime',
                'WaterLevel',
                'PumpTimeInSeconds'
            ])

            for plant in plants:

                for watering in plant.waterings:
                    writer.writerow([
                        plant.MAC,
                        watering.predicted_future_water_time.isoformat(),
                        watering.last_water_time.isoformat(),
                        watering.water_level,
                        watering.pump_time_in_seconds
                    ])


def main():
    random.seed(42)

    PLANTS_PER_USER = 3
    READINGS_PER_PLANT = 10000
    DAYS_OF_DATA = 365
    WATERINGS_PER_PLANT = 1000

    generator = PlantDataGenerator(
        plants_per_user=PLANTS_PER_USER,
        readings_per_plant=READINGS_PER_PLANT,
        days_of_data=DAYS_OF_DATA,
        waterings_per_plant=WATERINGS_PER_PLANT,
        watering_threshold_precent= 0.80
    )

    plants = generator.generate_all_plants()

    generator.export_plants_csv(plants)
    generator.export_sensor_datas_csv(plants)
    generator.export_waterings_csv(plants)


if __name__ == "__main__":
    main()
