from datetime import datetime, timedelta
import random
import csv
import math
from pathlib import Path
from typing import List


class Sensor:
    def __init__(self, plant_mac, temperature, air_humidity, soil_humidity,
                 light_intensity, timestamp):
        self.plant_mac = plant_mac
        self.temperature = temperature
        self.air_humidity = air_humidity
        self.soil_humidity = soil_humidity
        self.light_intensity = light_intensity
        self.timestamp = timestamp


class Watering:
    def __init__(self, plant_mac, last_water_time, predicted_future_water_time,
                 water_level, pump_time_in_seconds):
        self.plant_mac = plant_mac
        self.last_water_time = last_water_time
        self.predicted_future_water_time = predicted_future_water_time
        self.water_level = water_level
        self.pump_time_in_seconds = pump_time_in_seconds


class Plant:
    def __init__(self, MAC, username, optimal_temperature, optimal_air_humidity,
                 optimal_soil_humidity, optimal_light_intensity, sensors,
                 waterings, name):
        self.MAC = MAC
        self.username = username
        self.optimal_temperature = optimal_temperature
        self.optimal_air_humidity = optimal_air_humidity
        self.optimal_soil_humidity = optimal_soil_humidity
        self.optimal_light_intensity = optimal_light_intensity
        self.sensors = sensors
        self.waterings = waterings
        self.name = name


PLANT_PROFILES = {
    "Monstera": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (60, 75),
                 "light_range": (400, 750), "watering_interval": (7, 14), "pump_sec_per_pct": 1.8},
    "Pothos": {"temp_range": (15, 29), "air_hum_range": (50, 70), "soil_hum_range": (50, 65),
               "light_range": (150, 550), "watering_interval": (7, 14), "pump_sec_per_pct": 1.5},
    "Snake Plant": {"temp_range": (16, 27), "air_hum_range": (30, 50), "soil_hum_range": (30, 50),
                    "light_range": (80, 350), "watering_interval": (14, 42), "pump_sec_per_pct": 1.0},
    "Fiddle Leaf Fig": {"temp_range": (15, 24), "air_hum_range": (50, 60), "soil_hum_range": (55, 70),
                        "light_range": (450, 850), "watering_interval": (7, 14), "pump_sec_per_pct": 2.0},
    "ZZ Plant": {"temp_range": (18, 26), "air_hum_range": (40, 50), "soil_hum_range": (35, 55),
                 "light_range": (100, 300), "watering_interval": (14, 28), "pump_sec_per_pct": 1.0},
    "Rubber Plant": {"temp_range": (15, 24), "air_hum_range": (40, 60), "soil_hum_range": (50, 65),
                     "light_range": (350, 650), "watering_interval": (7, 14), "pump_sec_per_pct": 1.6},
    "Peace Lily": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (65, 80),
                   "light_range": (200, 450), "watering_interval": (5, 10), "pump_sec_per_pct": 2.0},
    "Philodendron": {"temp_range": (18, 27), "air_hum_range": (60, 70), "soil_hum_range": (55, 70),
                     "light_range": (250, 550), "watering_interval": (7, 14), "pump_sec_per_pct": 1.7},
    "Calathea": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (60, 75),
                 "light_range": (200, 400), "watering_interval": (7, 12), "pump_sec_per_pct": 1.8},
    "Dracaena": {"temp_range": (18, 26), "air_hum_range": (40, 60), "soil_hum_range": (40, 60),
                 "light_range": (180, 450), "watering_interval": (7, 21), "pump_sec_per_pct": 1.4},
    "Spider Plant": {"temp_range": (13, 27), "air_hum_range": (40, 60), "soil_hum_range": (50, 65),
                     "light_range": (250, 600), "watering_interval": (7, 14), "pump_sec_per_pct": 1.5},
    "Boston Fern": {"temp_range": (15, 24), "air_hum_range": (60, 80), "soil_hum_range": (65, 80),
                    "light_range": (250, 500), "watering_interval": (3, 7), "pump_sec_per_pct": 2.2},
    "Succulent": {"temp_range": (15, 29), "air_hum_range": (20, 40), "soil_hum_range": (15, 35),
                  "light_range": (600, 950), "watering_interval": (14, 28), "pump_sec_per_pct": 0.7},
    "Cactus": {"temp_range": (18, 30), "air_hum_range": (10, 30), "soil_hum_range": (10, 25),
               "light_range": (750, 1023), "watering_interval": (21, 42), "pump_sec_per_pct": 0.5},
    "Orchid": {"temp_range": (18, 24), "air_hum_range": (50, 70), "soil_hum_range": (40, 60),
               "light_range": (400, 750), "watering_interval": (7, 14), "pump_sec_per_pct": 1.3},
}


class PlantDataGenerator:
    PLANT_NAMES = list(PLANT_PROFILES.keys())

    def __init__(self, plants_per_user=1, readings_per_plant=100, days_of_data=30,
                 waterings_per_plant=10, watering_threshold_percent=0.85):
        self.watering_threshold_percent = watering_threshold_percent
        self.plants_per_user = plants_per_user
        self.readings_per_plant = readings_per_plant
        self.days_of_data = days_of_data
        self.waterings_per_plant = waterings_per_plant
        self.base_timestamp = datetime(2025, 1, 1, 12, 0, 0)

    def generate_users(self):
        return ["janedoe", "Mario", "Carolina", "Patrik", "Teo"]

    def generate_mac_address(self):
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    def generate_plant_optimal_values(self, plant_name):
        p = PLANT_PROFILES[plant_name]

        def mid_jitter(lo, hi, jitter_frac=0.08):
            mid = (lo + hi) / 2
            half = (hi - lo) / 2
            raw = mid + random.gauss(0, half * jitter_frac)
            return round(max(lo, min(hi, raw)), 1)

        return {
            "optimal_temperature": mid_jitter(*p["temp_range"]),
            "optimal_air_humidity": mid_jitter(*p["air_hum_range"]),
            "optimal_soil_humidity": mid_jitter(*p["soil_hum_range"]),
            "optimal_light_intensity": mid_jitter(*p["light_range"]),
            "_profile": p,
        }

    def generate_sensor_readings(self, plant_mac, optimal_values):
        profile = optimal_values["_profile"]
        readings = []
        soil = optimal_values["optimal_soil_humidity"]

        for i in range(self.readings_per_plant):
            ts = self.base_timestamp + timedelta(hours=i)
            hour = ts.hour
            day_of_year = ts.timetuple().tm_yday

            light_lo, light_hi = profile["light_range"]
            if 6 <= hour <= 20:
                angle = math.pi * (hour - 6) / 14
                diurnal = math.sin(angle)
                cloud = random.triangular(0.4, 1.0, 0.85)
                light_val = light_lo + (light_hi - light_lo) * diurnal * cloud + random.gauss(0, (light_hi - light_lo) * 0.05)
            else:
                light_val = random.gauss(20, 40)

            light_intensity = int(max(0, min(1023, light_val)))

            seasonal_offset = 2.0 * math.cos(2 * math.pi * (day_of_year - 196) / 365)
            diurnal_offset = 1.5 * math.sin(2 * math.pi * (hour - 5) / 24)
            temperature = max(0.0, optimal_values["optimal_temperature"] + seasonal_offset + diurnal_offset + random.gauss(0, 0.5))

            temp_effect = -(temperature - optimal_values["optimal_temperature"]) * 0.8
            air_humidity = max(0.0, min(100.0, optimal_values["optimal_air_humidity"] + temp_effect + random.gauss(0, 2.5)))

            et_rate = (0.005 * max(0, temperature - 18) + 0.002 * (light_intensity / 400) + 0.002 * max(0, 60 - air_humidity))
            soil = max(profile["soil_hum_range"][0] - 5, soil - et_rate + random.gauss(0, 0.3))
            soil_clamped = round(min(100.0, max(0.0, soil)), 2)

            readings.append(Sensor(
                plant_mac=plant_mac,
                temperature=round(temperature, 2),
                air_humidity=round(air_humidity, 2),
                soil_humidity=soil_clamped,
                light_intensity=light_intensity,
                timestamp=ts,
            ))

        return readings

    @staticmethod
    def _et_pump_multiplier(reading, optimal_values):
        T = reading.temperature
        RH = reading.air_humidity
        Lux = reading.light_intensity

        T_term = max(0.7, min(1.3, 1.0 + 0.02 * (T - 22)))
        RH_term = max(0.7, min(1.3, 1.0 + 0.012 * (60 - RH)))
        light_norm = (Lux - 400) / 600
        Rn_term = max(0.7, min(1.3, 1.0 + 0.3 * light_norm))

        soil_stress = 1.0 if reading.soil_humidity >= 20 else (0.7 + 0.015 * reading.soil_humidity)
        multiplier = ((T_term + RH_term + Rn_term) / 3.0) * soil_stress
        return round(max(0.5, min(2.5, multiplier)), 4)

    def generate_waterings(self, plant_mac, sensor_readings, optimal_values):
        profile = optimal_values["_profile"]
        optimal_soil = optimal_values["optimal_soil_humidity"]
        pump_sec_per_pct = profile["pump_sec_per_pct"]

        waterings = []
        last_watered_at = sensor_readings[0].timestamp

        min_hours_between = max(48.0, profile["watering_interval"][0] * 20)
        max_hours_between = profile["watering_interval"][1] * 26

        waterings.append(Watering(
            plant_mac=plant_mac,
            last_water_time=sensor_readings[0].timestamp,
            predicted_future_water_time=sensor_readings[0].timestamp + timedelta(hours=random.uniform(120, 400)),
            water_level=round(random.uniform(82, 100), 2),
            pump_time_in_seconds=0.0,
        ))

        last_watered_at = sensor_readings[0].timestamp

        for reading in sensor_readings[1:]:
            hours_since = (reading.timestamp - last_watered_at).total_seconds() / 3600.0

            soil_low_enough = reading.soil_humidity <= optimal_soil * self.watering_threshold_percent
            very_dry = reading.soil_humidity < max(20, optimal_soil * 0.35)

            if hours_since >= min_hours_between and (soil_low_enough or very_dry):
                deficit = max(0.0, optimal_soil - reading.soil_humidity)
                et_mult = self._et_pump_multiplier(reading, optimal_values)

                outlier = 1.0
                if random.random() < 0.15:
                    outlier = random.choice([0.35, 0.55, 1.65, 2.3, 3.0])

                pump_time = max(6.0, (deficit * pump_sec_per_pct * 1.1) * et_mult * outlier)
                pump_time = round(pump_time + random.gauss(0, pump_time * 0.18), 1)

                days_total = (reading.timestamp - self.base_timestamp).days
                water_level = max(6.0, 100 - days_total * random.uniform(0.1, 0.25))
                if random.random() < 0.18:
                    water_level = random.uniform(78, 100)

                waterings.append(Watering(
                    plant_mac=plant_mac,
                    last_water_time=reading.timestamp,
                    predicted_future_water_time=reading.timestamp + timedelta(hours=random.uniform(min_hours_between * 0.9, max_hours_between)),
                    water_level=round(water_level, 2),
                    pump_time_in_seconds=pump_time,
                ))
                last_watered_at = reading.timestamp

        print(f"Plant {plant_mac[-8:]} → Generated {len(waterings)} waterings")
        return waterings

    def generate_plant(self, username):
        name = random.choice(self.PLANT_NAMES)
        optimal_values = self.generate_plant_optimal_values(name)
        mac = self.generate_mac_address()
        sensor_readings = self.generate_sensor_readings(mac, optimal_values)
        waterings = self.generate_waterings(mac, sensor_readings, optimal_values)

        return Plant(
            MAC=mac,
            username=username,
            optimal_temperature=optimal_values["optimal_temperature"],
            optimal_air_humidity=optimal_values["optimal_air_humidity"],
            optimal_soil_humidity=optimal_values["optimal_soil_humidity"],
            optimal_light_intensity=optimal_values["optimal_light_intensity"],
            sensors=sensor_readings,
            waterings=waterings,
            name=name,
        )

    def generate_all_plants(self):
        plants = []
        for username in self.generate_users():
            for _ in range(self.plants_per_user):
                plants.append(self.generate_plant(username))
        return plants

    @staticmethod
    def export_plants_csv(plants, output_dir, filename="plants.csv"):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["MAC", "Name", "Username", "OptimalTemperature", "OptimalAirHumidity", "OptimalSoilHumidity", "OptimalLightIntensity"])
            for plant in plants:
                writer.writerow([plant.MAC, plant.name, plant.username, plant.optimal_temperature, plant.optimal_air_humidity, plant.optimal_soil_humidity, plant.optimal_light_intensity])

    @staticmethod
    def export_sensor_datas_csv(plants, output_dir, filename="sensor_datas.csv"):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PlantMAC", "Temperature", "AirHumidity", "SoilHumidity", "LightIntensity", "Timestamp"])
            for plant in plants:
                for r in plant.sensors:
                    writer.writerow([plant.MAC, r.temperature, r.air_humidity, r.soil_humidity, r.light_intensity, r.timestamp.isoformat()])

    @staticmethod
    def export_waterings_csv(plants, output_dir, filename="waterings.csv"):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PlantMAC", "PredictedFutureWaterTime", "LastWaterTime", "WaterLevel", "PumpTimeInSeconds"])
            for plant in plants:
                for w in plant.waterings:
                    writer.writerow([plant.MAC, w.predicted_future_water_time.isoformat(), w.last_water_time.isoformat(), w.water_level, w.pump_time_in_seconds])


def main():
    random.seed(42)
    generator = PlantDataGenerator(plants_per_user=3, readings_per_plant=10000, days_of_data=365,
                                   waterings_per_plant=1000, watering_threshold_percent=0.70)
    plants = generator.generate_all_plants()
    output_dir = "/workspace/datapreparation/mockdata"
    generator.export_plants_csv(plants, output_dir)
    generator.export_sensor_datas_csv(plants, output_dir)
    generator.export_waterings_csv(plants, output_dir)

    print(f"Generated {len(plants)} plants.")
    print(f"  Sensor readings : {sum(len(p.sensors) for p in plants):,}")
    print(f"  Watering events : {sum(len(p.waterings) for p in plants):,}")


if __name__ == "__main__":
    main()