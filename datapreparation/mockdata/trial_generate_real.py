from datetime import datetime, timedelta
import random
import csv
import math
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# Lightweight stand-ins for your entity classes so this file runs standalone.
# Replace these imports with your real ones:
#   from entities.Plant import Plant
#   from entities.Sensor import Sensor
#   from entities.Watering import Watering
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
# Per-species care profiles derived from horticultural sources.
#
# Sources consulted:
#   • AcuRite soil moisture guide (flowers 21-40 %, vegetables 41-80 %)
#   • Houseplant Journal light-level chart (lux / foot-candle correlations)
#   • Individual species care pages (Bloomscape, Soltech, León & George,
#     Garden Design, Sargent's Gardens, Lively Root, Gardenia.net, etc.)
#
# Fields
# ------
# temp_range        (min_°C, max_°C)   — comfortable indoor band
# air_hum_range     (min_%, max_%)     — preferred relative humidity
# soil_hum_range    (min_%, max_%)     — target volumetric soil moisture
# light_range       (min_lux, max_lux) — indirect indoor light band
# watering_interval (min_days, max_days) — typical days between waterings
# pump_seconds_per_pct_deficit          — pump run-time scaling factor
#   (seconds of pumping needed to raise soil humidity by 1 percentage point)
# ---------------------------------------------------------------------------
PLANT_PROFILES = {
    # --- Tropical / high-humidity lovers ---
    "Monstera": {
        # Bright indirect light; 1 000-2 500 lux near a window
        # Temp: 18-27 °C; Air humidity: 60-80 %; Soil: keep moist 60-75 %
        # Water every 1-2 weeks when top 2 cm are dry
        "temp_range": (18, 27),
        "air_hum_range": (60, 80),
        "soil_hum_range": (60, 75),
        "light_range": (1000, 2500),
        "watering_interval": (7, 14),
        "pump_sec_per_pct": 1.8,
    },
    "Pothos": {
        # Tolerates low light; 150-1 500 lux; moderate watering
        # Temp: 15-29 °C; Air humidity: 50-70 %; Soil: 50-65 %
        # Water every 1-2 weeks; very forgiving
        "temp_range": (15, 29),
        "air_hum_range": (50, 70),
        "soil_hum_range": (50, 65),
        "light_range": (150, 1500),
        "watering_interval": (7, 14),
        "pump_sec_per_pct": 1.5,
    },
    "Snake Plant": {
        # Very drought-tolerant; low-light champion; 100-1 000 lux
        # Temp: 16-27 °C; Air humidity: 30-50 % (drier side)
        # Soil: 30-50 % — let fully dry between waterings
        # Water every 2-6 weeks
        "temp_range": (16, 27),
        "air_hum_range": (30, 50),
        "soil_hum_range": (30, 50),
        "light_range": (100, 1000),
        "watering_interval": (14, 42),
        "pump_sec_per_pct": 1.0,
    },
    "Fiddle Leaf Fig": {
        # Needs bright indirect light; 1 000-3 000 lux near south/east window
        # Temp: 15-24 °C; Air humidity: 50-60 %; Soil: 55-70 %
        # Water when top 2.5 cm dry — roughly every 1-2 weeks
        # Very sensitive to drafts and inconsistency
        "temp_range": (15, 24),
        "air_hum_range": (50, 60),
        "soil_hum_range": (55, 70),
        "light_range": (1000, 3000),
        "watering_interval": (7, 14),
        "pump_sec_per_pct": 2.0,
    },
    "ZZ Plant": {
        # Drought-tolerant; low-medium light; 100-800 lux
        # Temp: 18-26 °C; Air humidity: 40-50 %; Soil: 35-55 %
        # Water every 2-4 weeks
        "temp_range": (18, 26),
        "air_hum_range": (40, 50),
        "soil_hum_range": (35, 55),
        "light_range": (100, 800),
        "watering_interval": (14, 28),
        "pump_sec_per_pct": 1.0,
    },
    "Rubber Plant": {
        # Medium-bright indirect light; 800-2 000 lux
        # Temp: 15-24 °C; Air humidity: 40-60 %; Soil: 50-65 %
        # Water every 1-2 weeks; allow top layer to dry
        "temp_range": (15, 24),
        "air_hum_range": (40, 60),
        "soil_hum_range": (50, 65),
        "light_range": (800, 2000),
        "watering_interval": (7, 14),
        "pump_sec_per_pct": 1.6,
    },
    "Peace Lily": {
        # Low-medium light; 250-1 000 lux; loves moisture
        # Temp: 18-27 °C; Air humidity: 60-80 %; Soil: 65-80 %
        # Water every 1-2 weeks; droops visibly when thirsty
        "temp_range": (18, 27),
        "air_hum_range": (60, 80),
        "soil_hum_range": (65, 80),
        "light_range": (250, 1000),
        "watering_interval": (5, 10),
        "pump_sec_per_pct": 2.0,
    },
    "Philodendron": {
        # Medium-bright indirect light; 500-1 500 lux
        # Temp: 18-27 °C; Air humidity: 60-70 %; Soil: 55-70 %
        # Water every 1-2 weeks
        "temp_range": (18, 27),
        "air_hum_range": (60, 70),
        "soil_hum_range": (55, 70),
        "light_range": (500, 1500),
        "watering_interval": (7, 14),
        "pump_sec_per_pct": 1.7,
    },
    "Calathea": {
        # Medium indirect light; 500-1 000 lux — no direct sun
        # Temp: 18-27 °C; Air humidity: 60-80 %; Soil: 60-75 %
        # Water when top 2-4 cm dry — every 1-2 weeks
        "temp_range": (18, 27),
        "air_hum_range": (60, 80),
        "soil_hum_range": (60, 75),
        "light_range": (500, 1000),
        "watering_interval": (7, 12),
        "pump_sec_per_pct": 1.8,
    },
    "Dracaena": {
        # Low-medium light; 300-1 200 lux
        # Temp: 18-26 °C; Air humidity: 40-60 %; Soil: 40-60 %
        # Water every 1-3 weeks
        "temp_range": (18, 26),
        "air_hum_range": (40, 60),
        "soil_hum_range": (40, 60),
        "light_range": (300, 1200),
        "watering_interval": (7, 21),
        "pump_sec_per_pct": 1.4,
    },
    "Spider Plant": {
        # Bright indirect light; 500-2 000 lux
        # Temp: 13-27 °C; Air humidity: 40-60 %; Soil: 50-65 %
        # Water every 1-2 weeks; very adaptable
        "temp_range": (13, 27),
        "air_hum_range": (40, 60),
        "soil_hum_range": (50, 65),
        "light_range": (500, 2000),
        "watering_interval": (7, 14),
        "pump_sec_per_pct": 1.5,
    },
    "Boston Fern": {
        # Medium-bright indirect light; 500-1 500 lux
        # Temp: 15-24 °C; Air humidity: 60-80 %; Soil: 65-80 %
        # Water 2-3× per week to keep consistently moist
        "temp_range": (15, 24),
        "air_hum_range": (60, 80),
        "soil_hum_range": (65, 80),
        "light_range": (500, 1500),
        "watering_interval": (3, 7),
        "pump_sec_per_pct": 2.2,
    },
    "Succulent": {
        # Bright direct/indirect light; 2 000-10 000 lux
        # Temp: 15-29 °C; Air humidity: 20-40 %; Soil: 15-35 %
        # Water every 2-4 weeks; let fully dry between waterings
        "temp_range": (15, 29),
        "air_hum_range": (20, 40),
        "soil_hum_range": (15, 35),
        "light_range": (2000, 10000),
        "watering_interval": (14, 28),
        "pump_sec_per_pct": 0.7,
    },
    "Cactus": {
        # Full sun / very bright; 5 000-10 000 lux
        # Temp: 18-30 °C (tolerates 10 °C min); Air humidity: 10-30 %
        # Soil: 10-25 %; Water every 3-6 weeks
        "temp_range": (18, 30),
        "air_hum_range": (10, 30),
        "soil_hum_range": (10, 25),
        "light_range": (5000, 10000),
        "watering_interval": (21, 42),
        "pump_sec_per_pct": 0.5,
    },
    "Orchid": {
        # Bright indirect light; 1 000-3 000 lux — no direct sun
        # Temp: 18-24 °C; Air humidity: 50-70 %; Soil/bark: 40-60 %
        # Water every 1-2 weeks; allow roots to nearly dry
        "temp_range": (18, 24),
        "air_hum_range": (50, 70),
        "soil_hum_range": (40, 60),
        "light_range": (1000, 3000),
        "watering_interval": (7, 14),
        "pump_sec_per_pct": 1.3,
    },
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
    ):
        self.watering_threshold_percent = watering_threshold_percent
        self.plants_per_user = plants_per_user
        self.readings_per_plant = readings_per_plant
        self.days_of_data = days_of_data
        self.waterings_per_plant = waterings_per_plant
        self.base_timestamp = datetime(2025, 1, 1, 12, 0, 0)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def generate_users(self) -> List[str]:
        return ["janedoe", "Mario", "Carolina", "Patrik", "Teo"]

    # ------------------------------------------------------------------
    # Hardware
    # ------------------------------------------------------------------
    def generate_mac_address(self) -> str:
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    # ------------------------------------------------------------------
    # Per-species optimal values
    # ------------------------------------------------------------------
    def generate_plant_optimal_values(self, plant_name: str) -> dict:
        """
        Draw optimal values from the species profile with a small random
        offset so different pots of the same species feel individual.
        """
        p = PLANT_PROFILES[plant_name]

        def mid_jitter(lo, hi, jitter_frac=0.08):
            mid = (lo + hi) / 2
            half = (hi - lo) / 2
            raw = mid + random.gauss(0, half * jitter_frac)
            return round(max(lo, min(hi, raw)), 1)

        return {
            "optimal_temperature":    mid_jitter(*p["temp_range"]),
            "optimal_air_humidity":   mid_jitter(*p["air_hum_range"]),
            "optimal_soil_humidity":  mid_jitter(*p["soil_hum_range"]),
            "optimal_light_intensity": mid_jitter(*p["light_range"]),
            # keep extra profile data for realistic simulation
            "_profile": p,
        }

    # ------------------------------------------------------------------
    # Sensor readings — realistic diurnal + seasonal variation
    # ------------------------------------------------------------------
    def generate_sensor_readings(
            self,
            plant_mac: str,
            optimal_values: dict,
    ) -> List[Sensor]:

        profile = optimal_values["_profile"]
        readings = []

        soil = optimal_values["optimal_soil_humidity"]

        for i in range(self.readings_per_plant):
            ts = self.base_timestamp + timedelta(hours=i)
            hour = ts.hour
            day_of_year = ts.timetuple().tm_yday

            # --- Diurnal light curve (bell around solar noon) ---
            # 0 lux at night, peak at 13:00, using a sine approximation
            light_lo, light_hi = profile["light_range"]
            if 6 <= hour <= 20:
                angle = math.pi * (hour - 6) / 14          # 0 → π over daylight hours
                diurnal = math.sin(angle)                   # 0…1…0
                # overcast factor — random cloudiness
                cloud = random.triangular(0.4, 1.0, 0.85)
                light_intensity = max(
                    0.0,
                    light_lo + (light_hi - light_lo) * diurnal * cloud
                    + random.gauss(0, (light_hi - light_lo) * 0.05)
                )
            else:
                light_intensity = max(0.0, random.gauss(0, 30))  # near-zero at night

            # --- Temperature: daily swing + seasonal offset ---
            # Seasonal: ±2 °C swing over the year (cosine, peak in July)
            seasonal_offset = 2.0 * math.cos(2 * math.pi * (day_of_year - 196) / 365)
            # Diurnal: ±1.5 °C swing (coolest at 05:00, warmest at 14:00)
            diurnal_offset = 1.5 * math.sin(2 * math.pi * (hour - 5) / 24)
            temperature = max(
                0.0,
                optimal_values["optimal_temperature"]
                + seasonal_offset + diurnal_offset
                + random.gauss(0, 0.5)
            )

            # --- Air humidity: inversely correlated with temperature ---
            air_hum_base = optimal_values["optimal_air_humidity"]
            temp_effect = -(temperature - optimal_values["optimal_temperature"]) * 0.8
            air_humidity = max(
                0.0, min(100.0,
                         air_hum_base + temp_effect + random.gauss(0, 2.5))
            )

            # --- Soil humidity: evapotranspiration model ---
            # Soil dries based on temperature, light, and low air humidity;
            # it resets whenever a watering event is applied (handled in
            # generate_waterings, but we approximate here with slow decay).
            et_rate = (
                0.005 * max(0, temperature - 18)         # warmer → faster drying
                + 0.002 * (light_intensity / 1000)        # brighter → faster
                + 0.002 * max(0, 60 - air_humidity)       # drier air → faster
            )
            soil = max(
                profile["soil_hum_range"][0] - 5,
                soil - et_rate + random.gauss(0, 0.3)
            )
            soil_clamped = round(min(100.0, max(0.0, soil)), 2)

            readings.append(Sensor(
                plant_mac=plant_mac,
                temperature=round(temperature, 2),
                air_humidity=round(air_humidity, 2),
                soil_humidity=soil_clamped,
                light_intensity=round(light_intensity, 2),
                timestamp=ts,
            ))

        return readings

    # ------------------------------------------------------------------
    # Evapotranspiration-based pump time
    # ------------------------------------------------------------------
    @staticmethod
    def _et_pump_multiplier(reading: "Sensor", optimal_values: dict) -> float:
        """
        Science-backed ET multiplier derived from the FAO-56 Penman-Monteith
        evapotranspiration model (Allen et al. 1998 / USGS ET water cycle).
        Sources:
          - USGS: "Temperature: Transpiration rates go up as temperature goes up"
          - USGS: "Humidity: as relative humidity rises, transpiration rate falls"
          - MSU Extension: "Solar radiation and air temp are most important [for PET];
                            humidity is negatively correlated"
          - Penman-Monteith (FAO-56): PET driven by Rn (radiation), T, VPD (vapour
                                       pressure deficit = f(T, RH))

        Returns a multiplier in [0.5 … 2.5] that scales the base pump time.
        Higher multiplier → soil dried out faster → need more water now.
        """
        T   = reading.temperature       # °C
        RH  = reading.air_humidity      # %
        Lux = reading.light_intensity   # lux  (proxy for solar radiation Rn)

        # Each term normalised to ~1.0 at typical indoor conditions.
        # Terms are AVERAGED (not multiplied) so no single variable dominates.

        # 1. Temperature term — range [0.7 … 1.3], neutral at 22 °C
        T_term = 1.0 + 0.02 * (T - 22.0)
        T_term = max(0.7, min(1.3, T_term))

        # 2. Air humidity term — range [0.7 … 1.3], neutral at RH=60 %
        #    Linear (replaces nonlinear VPD which was over-dominant)
        RH_term = 1.0 + 0.012 * (60.0 - RH)
        RH_term = max(0.7, min(1.3, RH_term))

        # 3. Light term — range [0.7 … 1.3], neutral at 800 lux
        light_norm = (Lux - 800.0) / 2000.0
        Rn_term = 1.0 + 0.3 * light_norm
        Rn_term = max(0.7, min(1.3, Rn_term))

        # 4. Soil stress — reduces pump on critically dry soil (stomata close)
        soil_stress = 1.0 if reading.soil_humidity >= 20 else (
            0.7 + 0.015 * reading.soil_humidity
        )

        # Equal-weight average so all three sensors contribute equally
        multiplier = ((T_term + RH_term + Rn_term) / 3.0) * soil_stress

        # Clamp to a physically sensible range
        return round(max(0.5, min(2.5, multiplier)), 4)

    # ------------------------------------------------------------------
    # Watering events
    # ------------------------------------------------------------------
    def generate_waterings(
            self,
            plant_mac: str,
            sensor_readings: List[Sensor],
            optimal_values: dict,
    ) -> List[Watering]:

        profile = optimal_values["_profile"]
        optimal_soil = optimal_values["optimal_soil_humidity"]
        pump_sec_per_pct = profile["pump_sec_per_pct"]

        waterings = []
        last_watered_at = sensor_readings[0].timestamp

        # More realistic minimum time between waterings
        min_hours_between = max(48.0, profile["watering_interval"][0] * 20)  # at least 2 days
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

            soil_low_enough = reading.soil_humidity <= optimal_soil * self.watering_threshold_percent
            very_dry = reading.soil_humidity < max(20, optimal_soil * 0.35)  # species-aware emergency

            if hours_since >= min_hours_between and (soil_low_enough or very_dry):

                deficit = max(0.0, optimal_soil - reading.soil_humidity)
                et_mult = self._et_pump_multiplier(reading, optimal_values)

                # Outliers
                outlier = 1.0
                if random.random() < 0.15:
                    outlier = random.choice([0.35, 0.55, 1.65, 2.3, 3.0])

                pump_time = max(6.0, (deficit * pump_sec_per_pct * 1.1) * et_mult * outlier)
                pump_time = round(pump_time + random.gauss(0, pump_time * 0.18), 1)

                # Water level
                days_total = (reading.timestamp - self.base_timestamp).days
                water_level = max(6.0, 100 - days_total * random.uniform(0.1, 0.25))
                if random.random() < 0.18:
                    water_level = random.uniform(78, 100)

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

        print(f"Plant {plant_mac[-8:]} → Generated {len(waterings)} waterings ({profile['watering_interval']})")
        return waterings

    # ------------------------------------------------------------------
    # Plant assembly
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------
    @staticmethod
    def export_plants_csv(
            plants: List[Plant],
            output_dir: str | Path,
            filename: str = "plants.csv"
    ):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow([
                "MAC", "Name", "Username",
                "OptimalTemperature", "OptimalAirHumidity",
                "OptimalSoilHumidity", "OptimalLightIntensity",
            ])

            for plant in plants:
                writer.writerow([
                    plant.MAC,
                    plant.name,
                    plant.username,
                    plant.optimal_temperature,
                    plant.optimal_air_humidity,
                    plant.optimal_soil_humidity,
                    plant.optimal_light_intensity,
                ])

        print(f"Saved: {filepath}")

    @staticmethod
    def export_sensor_datas_csv(
            plants: List[Plant],
            output_dir: str | Path,
            filename: str = "sensor_datas.csv"
    ):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow([
                "PlantMAC", "Temperature", "AirHumidity",
                "SoilHumidity", "LightIntensity", "Timestamp",
            ])

            for plant in plants:
                for r in plant.sensors:
                    writer.writerow([
                        plant.MAC,
                        r.temperature,
                        r.air_humidity,
                        r.soil_humidity,
                        r.light_intensity,
                        r.timestamp.isoformat(),
                    ])

        print(f"Saved: {filepath}")

    @staticmethod
    def export_waterings_csv(
            plants: List[Plant],
            output_dir: str | Path,
            filename: str = "waterings.csv"
    ):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow([
                "PlantMAC",
                "PredictedFutureWaterTime",
                "LastWaterTime",
                "WaterLevel",
                "PumpTimeInSeconds",
            ])

            for plant in plants:
                for w in plant.waterings:
                    writer.writerow([
                        plant.MAC,
                        w.predicted_future_water_time.isoformat(),
                        w.last_water_time.isoformat(),
                        w.water_level,
                        w.pump_time_in_seconds,
                    ])

        print(f"Saved: {filepath}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(plants_per_user=3,
        readings_per_plant=10_000,
        days_of_data=365,
        waterings_per_plant=1_000,
        watering_threshold_percent=0.70,

         output_dir="/workspace/datapreparation/mockdata",):

    random.seed(42)

    generator = PlantDataGenerator(
        plants_per_user,
        readings_per_plant,
        days_of_data,
        waterings_per_plant,
        watering_threshold_percent,
    )

    plants = generator.generate_all_plants()

    generator.export_plants_csv(plants, output_dir)
    generator.export_sensor_datas_csv(plants, output_dir)
    generator.export_waterings_csv(plants, output_dir)

    print(f"Generated {len(plants)} plants.")
    total_readings  = sum(len(p.sensors)   for p in plants)
    total_waterings = sum(len(p.waterings) for p in plants)
    print(f"  Sensor readings : {total_readings:,}")
    print(f"  Watering events : {total_waterings:,}")


if __name__ == "__main__":
    main()