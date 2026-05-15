from datetime import datetime, timedelta
import random
import csv
import math
from pathlib import Path
from typing import List, Optional


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
# Plant Profiles with Bias and Trigger Sensitivity
# ---------------------------------------------------------------------------
PLANT_PROFILES = {
    "Monstera": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (60, 75),
                 "light_range": (1000, 2500), "watering_interval": (7, 14), "pump_sec_per_pct": 1.8,
                 "soil_sensor_bias": 8.0, "trigger_sensitivity": 0.75},
    "Pothos": {"temp_range": (15, 29), "air_hum_range": (50, 70), "soil_hum_range": (50, 65),
               "light_range": (150, 1500), "watering_interval": (7, 14), "pump_sec_per_pct": 1.5,
               "soil_sensor_bias": 6.0, "trigger_sensitivity": 0.70},
    "Snake Plant": {"temp_range": (16, 27), "air_hum_range": (30, 50), "soil_hum_range": (30, 50),
                    "light_range": (100, 1000), "watering_interval": (14, 42), "pump_sec_per_pct": 1.0,
                    "soil_sensor_bias": 4.0, "trigger_sensitivity": 0.45},
    "Fiddle Leaf Fig": {"temp_range": (15, 24), "air_hum_range": (50, 60), "soil_hum_range": (55, 70),
                        "light_range": (1000, 3000), "watering_interval": (7, 14), "pump_sec_per_pct": 2.0,
                        "soil_sensor_bias": 10.0, "trigger_sensitivity": 0.80},
    "ZZ Plant": {"temp_range": (18, 26), "air_hum_range": (40, 50), "soil_hum_range": (35, 55),
                 "light_range": (100, 800), "watering_interval": (14, 28), "pump_sec_per_pct": 1.0,
                 "soil_sensor_bias": 5.0, "trigger_sensitivity": 0.50},
    "Rubber Plant": {"temp_range": (15, 24), "air_hum_range": (40, 60), "soil_hum_range": (50, 65),
                     "light_range": (800, 2000), "watering_interval": (7, 14), "pump_sec_per_pct": 1.6,
                     "soil_sensor_bias": 7.0, "trigger_sensitivity": 0.65},
    "Peace Lily": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (65, 80),
                   "light_range": (250, 1000), "watering_interval": (5, 10), "pump_sec_per_pct": 2.0,
                   "soil_sensor_bias": 11.0, "trigger_sensitivity": 0.85},
    "Philodendron": {"temp_range": (18, 27), "air_hum_range": (60, 70), "soil_hum_range": (55, 70),
                     "light_range": (500, 1500), "watering_interval": (7, 14), "pump_sec_per_pct": 1.7,
                     "soil_sensor_bias": 9.0, "trigger_sensitivity": 0.75},
    "Calathea": {"temp_range": (18, 27), "air_hum_range": (60, 80), "soil_hum_range": (60, 75),
                 "light_range": (500, 1000), "watering_interval": (7, 12), "pump_sec_per_pct": 1.8,
                 "soil_sensor_bias": 12.0, "trigger_sensitivity": 0.80},
    "Dracaena": {"temp_range": (18, 26), "air_hum_range": (40, 60), "soil_hum_range": (40, 60),
                 "light_range": (300, 1200), "watering_interval": (7, 21), "pump_sec_per_pct": 1.4,
                 "soil_sensor_bias": 6.0, "trigger_sensitivity": 0.60},
    "Spider Plant": {"temp_range": (13, 27), "air_hum_range": (40, 60), "soil_hum_range": (50, 65),
                     "light_range": (500, 2000), "watering_interval": (7, 14), "pump_sec_per_pct": 1.5,
                     "soil_sensor_bias": 7.0, "trigger_sensitivity": 0.70},
    "Boston Fern": {"temp_range": (15, 24), "air_hum_range": (60, 80), "soil_hum_range": (65, 80),
                    "light_range": (500, 1500), "watering_interval": (3, 7), "pump_sec_per_pct": 2.2,
                    "soil_sensor_bias": 13.0, "trigger_sensitivity": 0.90},
    "Succulent": {"temp_range": (15, 29), "air_hum_range": (20, 40), "soil_hum_range": (15, 35),
                  "light_range": (2000, 10000), "watering_interval": (14, 28), "pump_sec_per_pct": 0.7,
                  "soil_sensor_bias": 3.0, "trigger_sensitivity": 0.40},
    "Cactus": {"temp_range": (18, 30), "air_hum_range": (10, 30), "soil_hum_range": (10, 25),
               "light_range": (5000, 10000), "watering_interval": (21, 42), "pump_sec_per_pct": 0.5,
               "soil_sensor_bias": 2.0, "trigger_sensitivity": 0.35},
    "Orchid": {"temp_range": (18, 24), "air_hum_range": (50, 70), "soil_hum_range": (40, 60),
               "light_range": (1000, 3000), "watering_interval": (7, 14), "pump_sec_per_pct": 1.3,
               "soil_sensor_bias": 8.0, "trigger_sensitivity": 0.65},
}


class PlantDataGenerator:
    def __init__(self, plants_per_user=1, readings_per_plant=100, watering_threshold_percent=0.85,
                 base_null_prob=0.08, max_null_prob=0.25):
        self.plants_per_user = plants_per_user
        self.readings_per_plant = readings_per_plant
        self.watering_threshold_percent = watering_threshold_percent
        self.base_null_prob = base_null_prob
        self.max_null_prob = max_null_prob
        self.base_timestamp = datetime(2025, 1, 1, 12, 0, 0)
        self.PLANT_NAMES = list(PLANT_PROFILES.keys())

    def generate_users(self) -> List[str]:
        return ["janedoe", "Mario", "Carolina", "Patrik", "Teo"]

    def generate_mac_address(self) -> str:
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    def generate_plant_optimal_values(self, plant_name: str) -> dict:
        p = PLANT_PROFILES[plant_name]

        def mid_jitter(lo, hi):
            mid = (lo + hi) / 2
            return round(mid + random.gauss(0, (hi - lo) * 0.08), 1)

        return {
            "name": plant_name,
            "optimal_temperature": mid_jitter(*p["temp_range"]),
            "optimal_air_humidity": mid_jitter(*p["air_hum_range"]),
            "optimal_soil_humidity": mid_jitter(*p["soil_hum_range"]),
            "optimal_light_intensity": mid_jitter(*p["light_range"]),
            "_profile": p,
        }

    def generate_sensor_readings(self, plant_mac: str, opt: dict, w_times: list = None) -> List[Sensor]:
        profile, bias = opt["_profile"], opt["_profile"]["soil_sensor_bias"]
        readings, gt_soil = [], opt["optimal_soil_humidity"]
        w_set = {ts.replace(minute=0, second=0, microsecond=0) for ts in (w_times or [])}
        bad_period_end = None

        for i in range(self.readings_per_plant):
            ts = self.base_timestamp + timedelta(hours=i)
            if ts.replace(minute=0, second=0, microsecond=0) in w_set:
                gt_soil = opt["optimal_soil_humidity"] + random.uniform(-1, 1)

            # Physics logic
            h = ts.hour
            seasonal = 2.0 * math.cos(2 * math.pi * (ts.timetuple().tm_yday - 196) / 365)
            diurnal = 1.5 * math.sin(2 * math.pi * (h - 5) / 24)
            gt_temp = opt["optimal_temperature"] + seasonal + diurnal + random.gauss(0, 0.5)
            gt_air_hum = max(0, min(100, opt["optimal_air_humidity"] - (gt_temp - opt["optimal_temperature"]) * 0.8))
            gt_light = profile["light_range"][0] + (profile["light_range"][1] - profile["light_range"][0]) * math.sin(
                math.pi * (h - 6) / 14) if 6 <= h <= 20 else 2.0
            gt_soil = max(5.0, gt_soil - (gt_soil * 0.0004 * max(0.1, (gt_temp - 15) / 10)))


            def poll(val, p):
                if random.random() < p: return None  # This injects the NULL
                if random.random() < 0.01: return val * random.choice([0.2, 2.0])  # Spike
                return round(val + random.gauss(0, val * 0.015), 2)

            if bad_period_end is None and random.random() < 0.005: bad_period_end = i + random.randint(6, 24)
            cur_p = self.max_null_prob if (bad_period_end and i < bad_period_end) else self.base_null_prob
            if bad_period_end and i >= bad_period_end: bad_period_end = None

            readings.append(Sensor(plant_mac, poll(gt_temp, cur_p), poll(gt_air_hum, cur_p),
                                   poll(gt_soil + bias, cur_p * 0.5), poll(gt_light, cur_p), ts))
        return readings

    def generate_waterings(self, plant_mac: str, sensors: List[Sensor], opt: dict) -> List[Watering]:
        profile, opt_s, bias = opt["_profile"], opt["optimal_soil_humidity"], opt["_profile"]["soil_sensor_bias"]
        waterings, last_w, last_c = [], sensors[0].timestamp - timedelta(days=10), sensors[0].timestamp - timedelta(
            hours=25)
        sim_soil = opt_s + bias

        for r in sensors:
            if r.soil_humidity is not None: sim_soil = 0.8 * r.soil_humidity + 0.2 * sim_soil
            if (r.timestamp - last_c).total_seconds() / 3600 < 24: continue

            last_c = r.timestamp
            true_est = sim_soil - bias
            if true_est <= opt_s * profile.get("trigger_sensitivity", self.watering_threshold_percent):
                raw_p = (max(0, opt_s - true_est) * profile["pump_sec_per_pct"])
                if raw_p >= 2.0:  # 2s Floor
                    p_time = round(raw_p * random.uniform(0.9, 1.1), 1)
                    sim_soil = (opt_s + bias) + random.uniform(-1, 1)
                    last_w = r.timestamp
                    waterings.append(
                        Watering(plant_mac, last_w, r.timestamp + timedelta(days=7), round(random.uniform(20, 100), 2),
                                 p_time))
        return waterings

    def generate_all(self) -> List[Plant]:
        plants = []
        for user in self.generate_users():
            for _ in range(self.plants_per_user):
                opt = self.generate_plant_optimal_values(random.choice(self.PLANT_NAMES))
                mac = self.generate_mac_address()
                s_init = self.generate_sensor_readings(mac, opt)
                waters = self.generate_waterings(mac, s_init, opt)
                w_ts = [w.last_water_time for w in waters]
                plants.append(Plant(mac, user, opt["optimal_temperature"], opt["optimal_air_humidity"],
                                    opt["optimal_soil_humidity"], opt["optimal_light_intensity"],
                                    self.generate_sensor_readings(mac, opt, w_ts), waters, opt["name"]))
        return plants

    @staticmethod
    def export(plants: List[Plant], path: Path):
        path.mkdir(parents=True, exist_ok=True)
        # Export Plants
        with open(path / "plants.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["MAC", "Name", "Username", "OptTemp", "OptAir", "OptSoil", "OptLight"])
            for p in plants: w.writerow(
                [p.MAC, p.name, p.username, p.optimal_temperature, p.optimal_air_humidity, p.optimal_soil_humidity,
                 p.optimal_light_intensity])
        # Export Sensors
        with open(path / "sensor_datas.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["PlantMAC", "Temp", "AirHum", "SoilHum", "Light", "Timestamp"])
            for p in plants:
                for r in p.sensors: w.writerow(
                    [p.MAC, r.temperature, r.air_humidity, r.soil_humidity, r.light_intensity, r.timestamp.isoformat()])
        # Export Waterings
        with open(path / "waterings.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["PlantMAC", "PredTime", "LastTime", "Level", "PumpSec"])
            for p in plants:
                for wt in p.waterings: w.writerow(
                    [p.MAC, wt.predicted_future_water_time.isoformat(), wt.last_water_time.isoformat(), wt.water_level,
                     wt.pump_time_in_seconds])


if __name__ == "__main__":
    gen = PlantDataGenerator(plants_per_user=3, readings_per_plant=10000)
    data = gen.generate_all()
    gen.export(data, Path("./mock_data"))
    print("Done! Check for empty fields in CSVs—those are your Nulls.")