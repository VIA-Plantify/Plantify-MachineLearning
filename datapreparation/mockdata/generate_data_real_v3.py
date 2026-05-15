from datetime import datetime, timedelta
import random
import csv
import math
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# Entity classes
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Plant Profiles
# ---------------------------------------------------------------------------
PLANT_PROFILES = {
    "Monstera": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (60, 75),
                 "light_range": (400, 950), "watering_interval": (7, 14), "pump_sec_per_pct": 1.8},
    "Pothos": {"temp_range": (15, 29), "air_hum_range": (50, 70), "soil_hum_range": (50, 65),
               "light_range": (150, 700), "watering_interval": (7, 14), "pump_sec_per_pct": 1.5},
    "Snake Plant": {"temp_range": (16, 27), "air_hum_range": (30, 50), "soil_hum_range": (30, 50),
                    "light_range": (100, 800), "watering_interval": (14, 42), "pump_sec_per_pct": 1.0},
    "Fiddle Leaf Fig": {"temp_range": (15, 24), "air_hum_range": (50, 60), "soil_hum_range": (55, 70),
                        "light_range": (500, 950), "watering_interval": (7, 14), "pump_sec_per_pct": 2.0},
    "ZZ Plant": {"temp_range": (18, 26), "air_hum_range": (40, 50), "soil_hum_range": (35, 55),
                 "light_range": (100, 600), "watering_interval": (14, 28), "pump_sec_per_pct": 1.0},
    "Rubber Plant": {"temp_range": (15, 24), "air_hum_range": (40, 60), "soil_hum_range": (50, 65),
                     "light_range": (400, 850), "watering_interval": (7, 14), "pump_sec_per_pct": 1.6},
    "Peace Lily": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (65, 80),
                   "light_range": (250, 700), "watering_interval": (5, 10), "pump_sec_per_pct": 2.0},
    "Philodendron": {"temp_range": (18, 27), "air_hum_range": (60, 70), "soil_hum_range": (55, 70),
                     "light_range": (300, 750), "watering_interval": (7, 14), "pump_sec_per_pct": 1.7},
    "Calathea": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (60, 75),
                 "light_range": (300, 650), "watering_interval": (7, 12), "pump_sec_per_pct": 1.8},
    "Dracaena": {"temp_range": (18, 26), "air_hum_range": (40, 60), "soil_hum_range": (40, 60),
                 "light_range": (200, 700), "watering_interval": (7, 21), "pump_sec_per_pct": 1.4},
    "Spider Plant": {"temp_range": (13, 27), "air_hum_range": (40, 60), "soil_hum_range": (50, 65),
                     "light_range": (250, 800), "watering_interval": (7, 14), "pump_sec_per_pct": 1.5},
    "Boston Fern": {"temp_range": (15, 24), "air_hum_range": (60, 80), "soil_hum_range": (65, 80),
                    "light_range": (200, 600), "watering_interval": (3, 7), "pump_sec_per_pct": 2.2},
    "Succulent": {"temp_range": (15, 29), "air_hum_range": (20, 40), "soil_hum_range": (15, 35),
                  "light_range": (600, 1023), "watering_interval": (14, 28), "pump_sec_per_pct": 0.7},
    "Cactus": {"temp_range": (18, 35), "air_hum_range": (10, 30), "soil_hum_range": (10, 25),
               "light_range": (700, 1023), "watering_interval": (21, 42), "pump_sec_per_pct": 0.5},
    "Orchid": {"temp_range": (18, 24), "air_hum_range": (50, 70), "soil_hum_range": (40, 60),
               "light_range": (300, 750), "watering_interval": (7, 14), "pump_sec_per_pct": 1.3},
}


class PlantDataGenerator:
    PLANT_NAMES = list(PLANT_PROFILES.keys())

    def __init__(
            self,
            plants_per_user: int = 3,
            readings_per_plant: int = 10000,
            watering_threshold_percent: float = 0.78,
            null_chance: float = 0.07,      # ← Easy to tune
            noise_percent: float = 0.012,
            seed: int = 42
    ):
        random.seed(seed)
        self.null_chance = null_chance
        self.noise_percent = noise_percent
        self.watering_threshold_percent = watering_threshold_percent
        self.plants_per_user = plants_per_user
        self.readings_per_plant = readings_per_plant
        self.base_timestamp = datetime(2025, 1, 1, 12, 0, 0)

    def generate_users(self) -> List[str]:
        return ["janedoe", "Mario", "Carolina", "Patrik", "Teo"]

    def generate_mac_address(self) -> str:
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    def generate_plant_optimal_values(self, plant_name: str) -> dict:
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

    def _maybe_null(self, value):
        return None if random.random() < self.null_chance else value

    # ------------------------------------------------------------------
    def generate_sensor_readings(self, plant_mac: str, optimal_values: dict) -> List[Sensor]:
        profile = optimal_values["_profile"]
        readings = []
        soil = optimal_values["optimal_soil_humidity"]

        for i in range(self.readings_per_plant):
            ts = self.base_timestamp + timedelta(hours=i)
            hour = ts.hour
            day_of_year = ts.timetuple().tm_yday

            # Light (ADT sensor friendly: 0-1023)
            if 6 <= hour <= 20:
                angle = math.pi * (hour - 6) / 14
                diurnal = math.sin(angle)
                cloud = random.triangular(0.5, 1.0, 0.8)
                light = profile["light_range"][0] + (profile["light_range"][1] - profile["light_range"][0]) * diurnal * cloud
                light += random.gauss(0, 30)
            else:
                light = random.gauss(8, 15)

            light = max(0, min(1023, light))

            # Temperature
            seasonal = 1.8 * math.cos(2 * math.pi * (day_of_year - 196) / 365)
            diurnal = 1.4 * math.sin(2 * math.pi * (hour - 5) / 24)
            temperature = optimal_values["optimal_temperature"] + seasonal + diurnal + random.gauss(0, 0.6)

            # Air Humidity
            air_humidity = optimal_values["optimal_air_humidity"] - (temperature - 22) * 0.7 + random.gauss(0, 2.5)
            air_humidity = max(10, min(95, air_humidity))

            # Soil Humidity
            et_rate = (0.006 * max(0, temperature - 18) +
                       0.0022 * (light / 1000) +
                       0.002 * max(0, 60 - air_humidity))
            soil = max(profile["soil_hum_range"][0] - 6, soil - et_rate + random.gauss(0, 0.35))
            soil = max(0, min(100, soil))

            readings.append(Sensor(
                plant_mac=plant_mac,
                temperature=self._maybe_null(round(temperature, 2)),
                air_humidity=self._maybe_null(round(air_humidity, 2)),
                soil_humidity=self._maybe_null(round(soil, 2)),
                light_intensity=self._maybe_null(round(light, 1)),
                timestamp=ts,
            ))

        return readings

    # ------------------------------------------------------------------
    @staticmethod
    def _et_pump_multiplier(reading: Sensor, optimal_values: dict) -> float:
        T = reading.temperature or 22.0
        RH = reading.air_humidity or 60.0
        Lux = reading.light_intensity or 500.0

        T_term = max(0.75, min(1.3, 1.0 + 0.022 * (T - 22)))
        RH_term = max(0.75, min(1.3, 1.0 + 0.013 * (60 - RH)))
        light_norm = (Lux - 500) / 800.0
        light_term = max(0.75, min(1.3, 1.0 + 0.35 * light_norm))

        soil_stress = 1.0 if (reading.soil_humidity or 50) >= 22 else 0.8

        multiplier = ((T_term + RH_term + light_term) / 3.0) * soil_stress
        return round(max(0.5, min(2.5, multiplier)), 4)

    # ------------------------------------------------------------------
    def generate_waterings(self, plant_mac: str, sensor_readings: List[Sensor], optimal_values: dict) -> List[Watering]:
        profile = optimal_values["_profile"]
        optimal_soil = optimal_values["optimal_soil_humidity"]
        pump_sec_per_pct = profile["pump_sec_per_pct"]

        waterings = []
        last_watered_at = sensor_readings[0].timestamp

        min_hours_between = max(48.0, profile["watering_interval"][0] * 18)
        max_hours_between = profile["watering_interval"][1] * 26

        # First watering
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

            # Robust to nulls
            soil = reading.soil_humidity if reading.soil_humidity is not None else optimal_soil * 0.82

            if hours_since >= min_hours_between and soil <= optimal_soil * self.watering_threshold_percent:
                deficit = max(0.0, optimal_soil - soil)
                et_mult = self._et_pump_multiplier(reading, optimal_values)

                # Physical pot model
                POT_ML = 775.0
                MAX_ML = 200.0
                demand = (deficit / 100.0) ** 1.35
                ml_needed = POT_ML * demand * et_mult * random.triangular(0.85, 1.35, 1.05)

                ml_needed = min(MAX_ML, ml_needed)
                pump_time = round(ml_needed / 10.0, 2)   # ~10ml per second
                pump_time = max(0.8, min(24.0, pump_time))

                # Water level
                days_total = (reading.timestamp - self.base_timestamp).days
                water_level = max(6.0, 100 - days_total * random.uniform(0.09, 0.23))
                if random.random() < 0.14:
                    water_level = random.uniform(76, 100)

                waterings.append(Watering(
                    plant_mac=plant_mac,
                    last_water_time=reading.timestamp,
                    predicted_future_water_time=reading.timestamp + timedelta(
                        hours=random.uniform(min_hours_between * 0.9, max_hours_between)
                    ),
                    water_level=round(water_level, 2),
                    pump_time_in_seconds=pump_time,
                ))

                last_watered_at = reading.timestamp

        print(f"Plant {plant_mac[-8:]} → Generated {len(waterings)} waterings")
        return waterings

    # ------------------------------------------------------------------
    def generate_plant(self, username: str) -> Plant:
        name = random.choice(self.PLANT_NAMES)
        optimal_values = self.generate_plant_optimal_values(name)
        mac = self.generate_mac_address()

        sensors = self.generate_sensor_readings(mac, optimal_values)
        waterings = self.generate_waterings(mac, sensors, optimal_values)

        return Plant(
            MAC=mac,
            username=username,
            optimal_temperature=optimal_values["optimal_temperature"],
            optimal_air_humidity=optimal_values["optimal_air_humidity"],
            optimal_soil_humidity=optimal_values["optimal_soil_humidity"],
            optimal_light_intensity=optimal_values["optimal_light_intensity"],
            sensors=sensors,
            waterings=waterings,
            name=name,
        )

    def generate_all_plants(self) -> List[Plant]:
        plants = []
        for username in self.generate_users():
            for _ in range(self.plants_per_user):
                plants.append(self.generate_plant(username))
        return plants

    # ------------------------------------------------------------------
    # Export methods (unchanged)
    # ------------------------------------------------------------------
    @staticmethod
    def export_plants_csv(plants: List[Plant], output_dir: str | Path, filename: str = "plants.csv"):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["MAC", "Name", "Username", "OptimalTemperature",
                             "OptimalAirHumidity", "OptimalSoilHumidity", "OptimalLightIntensity"])
            for p in plants:
                writer.writerow([p.MAC, p.name, p.username, p.optimal_temperature,
                                 p.optimal_air_humidity, p.optimal_soil_humidity, p.optimal_light_intensity])

    @staticmethod
    def export_sensor_datas_csv(plants: List[Plant], output_dir: str | Path, filename: str = "sensor_datas.csv"):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PlantMAC", "Temperature", "AirHumidity", "SoilHumidity", "LightIntensity", "Timestamp"])
            for p in plants:
                for r in p.sensors:
                    writer.writerow([p.MAC, r.temperature, r.air_humidity, r.soil_humidity,
                                     r.light_intensity, r.timestamp.isoformat()])

    @staticmethod
    def export_waterings_csv(plants: List[Plant], output_dir: str | Path, filename: str = "waterings.csv"):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PlantMAC", "PredictedFutureWaterTime", "LastWaterTime", "WaterLevel", "PumpTimeInSeconds"])
            for p in plants:
                for w in p.waterings:
                    writer.writerow([p.MAC, w.predicted_future_water_time.isoformat(),
                                     w.last_water_time.isoformat(), w.water_level, w.pump_time_in_seconds])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    generator = PlantDataGenerator(
        plants_per_user=3,
        readings_per_plant=10000,
        watering_threshold_percent=0.78,
        null_chance=0.07,      # Change this to control null rate
        noise_percent=0.012,
        seed=42
    )

    plants = generator.generate_all_plants()

    output_dir = "/workspace/datapreparation/mockdata"
    generator.export_plants_csv(plants, output_dir)
    generator.export_sensor_datas_csv(plants, output_dir)
    generator.export_waterings_csv(plants, output_dir)

    print(f"Generated {len(plants)} plants successfully.")


if __name__ == "__main__":
    main()