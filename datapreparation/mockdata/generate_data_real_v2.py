from datetime import datetime, timedelta
import random
import csv
import math
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
# Plant Profiles (same as before)
# ---------------------------------------------------------------------------
PLANT_PROFILES = {
    "Monstera": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (60, 75), "light_range": (1000, 2500), "watering_interval": (7, 14), "pump_sec_per_pct": 1.8},
    "Pothos": {"temp_range": (15, 29), "air_hum_range": (50, 70), "soil_hum_range": (50, 65), "light_range": (150, 1500), "watering_interval": (7, 14), "pump_sec_per_pct": 1.5},
    "Snake Plant": {"temp_range": (16, 27), "air_hum_range": (30, 50), "soil_hum_range": (30, 50), "light_range": (100, 1000), "watering_interval": (14, 42), "pump_sec_per_pct": 1.0},
    "Fiddle Leaf Fig": {"temp_range": (15, 24), "air_hum_range": (50, 60), "soil_hum_range": (55, 70), "light_range": (1000, 3000), "watering_interval": (7, 14), "pump_sec_per_pct": 2.0},
    "ZZ Plant": {"temp_range": (18, 26), "air_hum_range": (40, 50), "soil_hum_range": (35, 55), "light_range": (100, 800), "watering_interval": (14, 28), "pump_sec_per_pct": 1.0},
    "Rubber Plant": {"temp_range": (15, 24), "air_hum_range": (40, 60), "soil_hum_range": (50, 65), "light_range": (800, 2000), "watering_interval": (7, 14), "pump_sec_per_pct": 1.6},
    "Peace Lily": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (65, 80), "light_range": (250, 1000), "watering_interval": (5, 10), "pump_sec_per_pct": 2.0},
    "Philodendron": {"temp_range": (18, 27), "air_hum_range": (60, 70), "soil_hum_range": (55, 70), "light_range": (500, 1500), "watering_interval": (7, 14), "pump_sec_per_pct": 1.7},
    "Calathea": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (60, 75), "light_range": (500, 1000), "watering_interval": (7, 12), "pump_sec_per_pct": 1.8},
    "Dracaena": {"temp_range": (18, 26), "air_hum_range": (40, 60), "soil_hum_range": (40, 60), "light_range": (300, 1200), "watering_interval": (7, 21), "pump_sec_per_pct": 1.4},
    "Spider Plant": {"temp_range": (13, 27), "air_hum_range": (40, 60), "soil_hum_range": (50, 65), "light_range": (500, 2000), "watering_interval": (7, 14), "pump_sec_per_pct": 1.5},
    "Boston Fern": {"temp_range": (15, 24), "air_hum_range": (60, 80), "soil_hum_range": (65, 80), "light_range": (500, 1500), "watering_interval": (3, 7), "pump_sec_per_pct": 2.2},
    "Succulent": {"temp_range": (15, 29), "air_hum_range": (20, 40), "soil_hum_range": (15, 35), "light_range": (2000, 10000), "watering_interval": (14, 28), "pump_sec_per_pct": 0.7},
    "Cactus": {"temp_range": (18, 30), "air_hum_range": (10, 30), "soil_hum_range": (10, 25), "light_range": (5000, 10000), "watering_interval": (21, 42), "pump_sec_per_pct": 0.5},
    "Orchid": {"temp_range": (18, 24), "air_hum_range": (50, 70), "soil_hum_range": (40, 60), "light_range": (1000, 3000), "watering_interval": (7, 14), "pump_sec_per_pct": 1.3},
}


class PlantDataGenerator:
    PLANT_NAMES = list(PLANT_PROFILES.keys())

    def __init__(
            self,
            plants_per_user: int = 1,
            readings_per_plant: int = 100,
            days_of_data: int = 30,
            waterings_per_plant: int = 10,
            watering_threshold_percent: float = 0.85,
            # Updated NULL settings
            base_null_probability: float = 0.12,      # 12% base rate
            max_null_probability: float = 0.20,       # can spike up to 20%
    ):
        self.watering_threshold_percent = watering_threshold_percent
        self.plants_per_user = plants_per_user
        self.readings_per_plant = readings_per_plant
        self.days_of_data = days_of_data
        self.waterings_per_plant = waterings_per_plant
        self.base_timestamp = datetime(2025, 1, 1, 12, 0, 0)

        self.base_null_probability = base_null_probability
        self.max_null_probability = max_null_probability

        self._stuck_until = None
        self._stuck_values = None

    # ------------------------------------------------------------------
    # Helpers (unchanged)
    # ------------------------------------------------------------------
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

    @staticmethod
    def _et_pump_multiplier(reading: Sensor, optimal_values: dict) -> float:
        if reading.soil_humidity is None:
            return 1.0
        T = reading.temperature or 22.0
        RH = reading.air_humidity or 60.0
        Lux = reading.light_intensity or 800.0

        T_term = max(0.7, min(1.3, 1.0 + 0.02 * (T - 22)))
        RH_term = max(0.7, min(1.3, 1.0 + 0.012 * (60 - RH)))
        light_norm = (Lux - 800) / 2000.0
        Rn_term = max(0.7, min(1.3, 1.0 + 0.3 * light_norm))

        soil_stress = 1.0 if (reading.soil_humidity or 50) >= 20 else 0.7
        multiplier = ((T_term + RH_term + Rn_term) / 3.0) * soil_stress
        return round(max(0.5, min(2.5, multiplier)), 4)

    # ------------------------------------------------------------------
    # Sensor Readings with Higher & Variable NULLs
    # ------------------------------------------------------------------
    def generate_sensor_readings(self, plant_mac: str, optimal_values: dict) -> List[Sensor]:
        profile = optimal_values["_profile"]
        readings = []

        soil = optimal_values["optimal_soil_humidity"]
        last_valid_temp = optimal_values["optimal_temperature"]
        last_valid_air = optimal_values["optimal_air_humidity"]
        last_valid_soil = soil
        last_valid_light = sum(profile["light_range"]) / 2

        self._stuck_until = None
        self._stuck_values = None

        # Occasional "bad period" where nulls spike
        bad_period_end = None

        for i in range(self.readings_per_plant):
            ts = self.base_timestamp + timedelta(hours=i * 2)
            hour = ts.hour
            day_of_year = ts.timetuple().tm_yday

            # === Base values (same logic) ===
            if 6 <= hour <= 20:
                angle = math.pi * (hour - 6) / 14
                light = max(0.0, profile["light_range"][0] +
                           (profile["light_range"][1] - profile["light_range"][0]) *
                           math.sin(angle) * random.triangular(0.35, 1.0, 0.82))
            else:
                light = max(0.0, random.gauss(5, 25))

            seasonal = 2.0 * math.cos(2 * math.pi * (day_of_year - 196) / 365)
            diurnal_temp = 1.6 * math.sin(2 * math.pi * (hour - 5) / 24)
            temp = optimal_values["optimal_temperature"] + seasonal + diurnal_temp + random.gauss(0, 0.6)

            air_hum = optimal_values["optimal_air_humidity"] - (temp - optimal_values["optimal_temperature"]) * 0.85 + random.gauss(0, 2.8)

            et_rate = (0.006 * max(0, temp - 18) + 0.0022 * (light / 1000) + 0.002 * max(0, 60 - air_hum))
            soil = max(profile["soil_hum_range"][0] - 6, soil - et_rate + random.gauss(0, 0.35))

            temp = max(-5, min(45, temp))
            air_hum = max(5, min(100, air_hum))
            soil = max(0, min(100, soil))
            light = max(0, light)

            # === NULL Rate Logic ===
            if bad_period_end is None and random.random() < 0.008:   # start bad period
                bad_period_end = i + random.randint(30, 120)         # 60h to 10 days of higher failures

            if bad_period_end and i < bad_period_end:
                current_null_prob = self.max_null_probability
            else:
                current_null_prob = self.base_null_probability
                if bad_period_end and i >= bad_period_end:
                    bad_period_end = None

            # Full failure
            if random.random() < 0.0015:
                readings.append(Sensor(plant_mac, None, None, None, None, ts))
                continue

            # Stuck sensor logic (unchanged)
            if self._stuck_until is None and random.random() < 0.003:
                self._stuck_until = ts + timedelta(hours=random.randint(8, 40))
                self._stuck_values = {
                    'temp': round(last_valid_temp + random.gauss(0, 1.5), 2),
                    'air': round(last_valid_air + random.gauss(0, 3), 2),
                    'soil': round(last_valid_soil, 2),
                    'light': round(last_valid_light, 2)
                }

            if self._stuck_until and ts < self._stuck_until:
                temp = self._stuck_values['temp']
                air_hum = self._stuck_values['air']
                soil = self._stuck_values['soil']
                light = self._stuck_values['light']
            else:
                self._stuck_until = None

            # Misreadings
            if random.random() < 0.012:
                st = random.choice(['temp', 'air', 'soil', 'light'])
                if st == 'temp': temp += random.choice([-12, -8, 9, 15]) + random.gauss(0, 3)
                elif st == 'air': air_hum += random.choice([-25, 22, -18])
                elif st == 'soil': soil += random.choice([-35, 28, -22])
                else: light = light * random.uniform(0.1, 3.5) + random.gauss(0, 400)

            # Apply NULLs with current probability
            temperature = round(temp, 2) if random.random() >= current_null_prob else None
            air_humidity = round(air_hum, 2) if random.random() >= current_null_prob else None
            soil_humidity = round(soil, 2) if random.random() >= current_null_prob * 0.6 else None  # soil more reliable
            light_intensity = round(light, 2) if random.random() >= current_null_prob else None

            # Update last valid readings
            if temperature is not None: last_valid_temp = temperature
            if air_humidity is not None: last_valid_air = air_humidity
            if soil_humidity is not None: last_valid_soil = soil_humidity
            if light_intensity is not None: last_valid_light = light_intensity

            readings.append(Sensor(plant_mac, temperature, air_humidity, soil_humidity, light_intensity, ts))

        return readings

    # ------------------------------------------------------------------
    # Rest of the class (generate_waterings, generate_plant, exports, main)
    # ------------------------------------------------------------------
    def generate_waterings(self, plant_mac: str, sensor_readings: List[Sensor], optimal_values: dict) -> List[Watering]:
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
            soil_val = reading.soil_humidity if reading.soil_humidity is not None else optimal_soil

            if hours_since >= min_hours_between and (soil_val <= optimal_soil * self.watering_threshold_percent or
                                                     soil_val < max(20, optimal_soil * 0.35)):
                deficit = max(0.0, optimal_soil - soil_val)
                et_mult = self._et_pump_multiplier(reading, optimal_values)

                outlier = random.choice([0.35, 0.55, 1.65, 2.3, 3.0]) if random.random() < 0.15 else 1.0
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

    def generate_plant(self, username: str) -> Plant:
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

    def generate_all_plants(self) -> List[Plant]:
        plants = []
        for username in self.generate_users():
            for _ in range(self.plants_per_user):
                plants.append(self.generate_plant(username))
        return plants

    # CSV Export methods (same as previous version)
    @staticmethod
    def export_plants_csv(plants: List[Plant], filename: str = "plants.csv"):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["MAC", "Name", "Username", "OptimalTemperature", "OptimalAirHumidity", "OptimalSoilHumidity", "OptimalLightIntensity"])
            for plant in plants:
                writer.writerow([plant.MAC, plant.name, plant.username, plant.optimal_temperature, plant.optimal_air_humidity, plant.optimal_soil_humidity, plant.optimal_light_intensity])

    @staticmethod
    def export_sensor_datas_csv(plants: List[Plant], filename: str = "sensor_datas.csv"):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PlantMAC", "Temperature", "AirHumidity", "SoilHumidity", "LightIntensity", "Timestamp"])
            for plant in plants:
                for r in plant.sensors:
                    writer.writerow([plant.MAC, r.temperature, r.air_humidity, r.soil_humidity, r.light_intensity, r.timestamp.isoformat()])

    @staticmethod
    def export_waterings_csv(plants: List[Plant], filename: str = "waterings.csv"):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PlantMAC", "PredictedFutureWaterTime", "LastWaterTime", "WaterLevel", "PumpTimeInSeconds"])
            for plant in plants:
                for w in plant.waterings:
                    writer.writerow([plant.MAC, w.predicted_future_water_time.isoformat(), w.last_water_time.isoformat(), w.water_level, w.pump_time_in_seconds])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(plants_per_user=3,
        readings_per_plant=10_000,
        days_of_data=365,
        waterings_per_plant=1_000,
        watering_threshold_percent=0.70,):
    random.seed(42)

    generator = PlantDataGenerator(
        plants_per_user,
        readings_per_plant,
        days_of_data,
        waterings_per_plant,
        watering_threshold_percent,
    )

    plants = generator.generate_all_plants()

    generator.export_plants_csv(plants, "plants.csv")
    generator.export_sensor_datas_csv(plants, "sensor_datas.csv")
    generator.export_waterings_csv(plants, "waterings.csv")

    print(f"Generated {len(plants)} plants.")
    total_readings = sum(len(p.sensors) for p in plants)
    total_waterings = sum(len(p.waterings) for p in plants)
    print(f"  Sensor readings : {total_readings:,}")
    print(f"  Watering events : {total_waterings:,}")


if __name__ == "__main__":
    main()