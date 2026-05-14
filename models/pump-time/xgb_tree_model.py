from pathlib import Path
import xgboost as xgb
import pandas as pd

MODEL_PATH = Path(__file__).parent / "xgb_tree_model.ubj"

def load_model():
    model = xgb.XGBRegressor()
    model.load_model(MODEL_PATH)
    return model
model = load_model()
def prepare_input(temperature, air_humidity, soil_humidity, light_intensity,
                  sensor_timestamp, last_water_timestamp,
                  optimal_temperature, optimal_air_humidity,
                  optimal_soil_humidity, optimal_light_intensity):
    sensor_timestamp = pd.to_datetime(sensor_timestamp)
    last_water_timestamp = pd.to_datetime(last_water_timestamp)
    hours_since_watering = (sensor_timestamp - last_water_timestamp).total_seconds() / 3600

    soil_deficit = optimal_soil_humidity - soil_humidity

    features = {
        "SoilHumidity": soil_humidity,
        "Temperature": temperature,
        "AirHumidity": air_humidity,
        "LightIntensity": light_intensity,
        "hours_since_watering": hours_since_watering,
        "OptimalTemperature": optimal_temperature,
        "OptimalAirHumidity": optimal_air_humidity,
        "OptimalSoilHumidity": optimal_soil_humidity,
        "OptimalLightIntensity": optimal_light_intensity,
        "soil_deficit_ratio": soil_deficit / optimal_soil_humidity,
        "temp_deviation": temperature - optimal_temperature,
        "air_hum_deficit": optimal_air_humidity - air_humidity,
        "light_deviation": light_intensity - optimal_light_intensity,
        "deficit_x_temp": soil_deficit * (temperature - optimal_temperature),
        "deficit_x_light": soil_deficit * (light_intensity - optimal_light_intensity),
        "deficit_x_air": soil_deficit * (optimal_air_humidity - air_humidity),
        "et_approx": (temperature * light_intensity) / (air_humidity + 1),
    }

    df = pd.DataFrame([features])
    return df[model.feature_names_in_]

# =================================================================
# HIGH-DEMAND & EXTREME DEFICIT TEST CASES
# =================================================================

extreme_synthetic_cases = [
    # 1. THE "DESERT TO JUNGLE" (Max Deficit + Max Heat + High Optimal)
    # Plant needs 80% soil, but has 5%. Temp is 40C.
    prepare_input(40.0, 15.0, 5.0, 1023, "2026-05-14 14:00", "2026-04-14 10:00", 25.0, 60.0, 85.0, 900),

    # 2. THE "B thirsty" (Large Boston Fern in a dry room)
    # High soil humidity requirement (80%) currently at 10%.
    prepare_input(28.0, 20.0, 10.0, 800, "2026-05-14 12:00", "2026-05-01 10:00", 22.0, 75.0, 80.0, 700),

    # 3. THE "BONE DRY MONSTERA" (Massive soil deficit)
    # Optimal is 75%, current is 8%.
    prepare_input(30.0, 30.0, 8.0, 950, "2026-05-14 15:00", "2026-04-20 10:00", 24.0, 65.0, 75.0, 850),

    # 4. HIGH EVAPOTRANSPIRATION (Hot, Windy, Bright)
    # Even if soil isn't at 0, the deviation and ET approximation are maxed out.
    prepare_input(42.0, 10.0, 20.0, 1023, "2026-06-01 13:00", "2026-05-25 10:00", 22.0, 55.0, 70.0, 600),

    # 5. LARGE POT SIMULATION (High Optimal Soil + Deep Deficit)
    # If the model learned that soil_deficit * OptimalSoil is a feature, this should trigger a high value.
    prepare_input(25.0, 45.0, 15.0, 500, "2026-05-14 10:00", "2026-04-01 10:00", 22.0, 55.0, 90.0, 600),
]

extreme_labels = [
    "Extreme Desert Drought",
    "Thirsty Fern (Deep Deficit)",
    "Bone Dry Monstera",
    "Max ET / Heat Wave",
    "Large Pot / Max Deficit"
]

print("\n" + "#" * 60)
print("EXTREME TEST CASES - Testing for High Pump Times")
print("#" * 60 + "\n")

for label, case in zip(extreme_labels, extreme_synthetic_cases):
    pred = model.predict(case)[0]
    print(f"{label:30s}: Pump runtime = {pred:7.2f} seconds")

print("=" * 60)
print("SYNTHETIC TEST CASES - Model Predictions")
print("=" * 60)

cases = [
    # Basic conditions
    prepare_input(28, 25, 20, 900, "2025-01-11 10:00", "2025-01-01 10:00", 22, 55, 40, 650),
    prepare_input(22, 50, 35, 600, "2025-01-08 10:00", "2025-01-04 10:00", 22, 55, 40, 650),
    prepare_input(21, 60, 85, 500, "2025-01-03 10:00", "2025-01-02 10:00", 22, 55, 40, 650),
    prepare_input(35, 15, 10, 1000, "2025-01-15 10:00", "2025-01-01 10:00", 22, 55, 40, 650),
    prepare_input(22, 55, 40, 650, "2025-01-04 10:00", "2025-01-01 10:00", 22, 55, 40, 650),
    prepare_input(19, 58, 38, 0, "2025-01-05 02:00", "2025-01-03 10:00", 22, 55, 40, 650),
    prepare_input(26, 30, 18, 850, "2025-01-20 10:00", "2025-01-01 10:00", 24, 30, 25, 800), # Succulent
    prepare_input(20, 70, 50, 800, "2025-01-06 10:00", "2025-01-01 10:00", 20, 70, 72, 950), # Boston Fern
    prepare_input(28, 20, 12, 1020, "2025-01-22 10:00", "2025-01-01 10:00", 25, 20, 18, 1000), # Cactus
    prepare_input(22, 55, 90, 600, "2025-01-02 10:00", "2025-01-01 10:00", 22, 55, 40, 650),

    # Stress conditions
    prepare_input(35, 15, 8, 1023, "2025-01-25 14:00", "2024-12-25 10:00", 25, 20, 18, 1000),
    prepare_input(26, 85, 75, 800, "2025-01-10 10:00", "2025-01-08 10:00", 24, 75, 70, 900),
    prepare_input(5, 45, 28, 200, "2025-01-15 08:00", "2025-01-10 10:00", 22, 55, 40, 650),
    prepare_input(40, 20, 15, 1023, "2025-07-20 16:00", "2025-07-10 10:00", 22, 55, 40, 650),

    # Watering schedules
    prepare_input(23, 52, 82, 700, "2025-01-11 10:00", "2025-01-11 09:00", 22, 55, 40, 650),
    prepare_input(24, 45, 32, 600, "2025-01-18 10:00", "2025-01-11 10:00", 22, 55, 40, 650),
    prepare_input(25, 40, 22, 700, "2025-01-25 10:00", "2025-01-11 10:00", 22, 55, 40, 650),
    prepare_input(27, 35, 15, 800, "2025-02-01 10:00", "2025-01-11 10:00", 22, 55, 40, 650),

    # Plant-specific profiles
    prepare_input(23, 65, 48, 500, "2025-01-10 10:00", "2025-01-08 10:00", 23, 65, 50, 800),
    prepare_input(22, 50, 42, 250, "2025-01-10 10:00", "2025-01-07 10:00", 21, 50, 40, 400),
    prepare_input(26, 35, 25, 900, "2025-01-20 10:00", "2025-01-05 10:00", 24, 35, 20, 950),
    prepare_input(28, 25, 15, 950, "2025-01-30 10:00", "2025-01-01 10:00", 25, 25, 15, 1000),
    prepare_input(21, 68, 55, 400, "2025-01-08 10:00", "2025-01-05 10:00", 21, 70, 60, 600),
    prepare_input(22, 72, 60, 600, "2025-01-09 10:00", "2025-01-06 10:00", 22, 75, 65, 800),

    # Seasonal variations
    prepare_input(18, 48, 35, 300, "2025-01-15 10:00", "2025-01-08 10:00", 22, 55, 40, 650),
    prepare_input(20, 52, 38, 800, "2025-03-15 10:00", "2025-03-08 10:00", 22, 55, 40, 650),
    prepare_input(30, 45, 28, 1000, "2025-07-15 14:00", "2025-07-08 10:00", 22, 55, 40, 650),
    prepare_input(22, 55, 42, 900, "2025-10-15 10:00", "2025-10-08 10:00", 22, 55, 40, 650),

    # Time-of-day variations
    prepare_input(18, 62, 48, 100, "2025-01-10 06:00", "2025-01-08 10:00", 22, 55, 40, 650),
    prepare_input(28, 35, 32, 950, "2025-01-10 12:00", "2025-01-08 10:00", 22, 55, 40, 650),
    prepare_input(32, 30, 28, 1023, "2025-01-10 16:00", "2025-01-08 10:00", 22, 55, 40, 650),
    prepare_input(24, 52, 38, 400, "2025-01-10 18:00", "2025-01-08 10:00", 22, 55, 40, 650),
    prepare_input(19, 70, 52, 0, "2025-01-10 22:00", "2025-01-08 10:00", 22, 55, 40, 650),

    # Edge cases
    prepare_input(25, 40, 5, 800, "2025-01-12 10:00", "2025-01-05 10:00", 22, 55, 40, 650),
    prepare_input(20, 80, 95, 300, "2025-01-08 10:00", "2025-01-07 10:00", 22, 55, 40, 650),
    prepare_input(21, 55, 45, 0, "2025-01-10 10:00", "2025-01-08 10:00", 22, 55, 40, 650),
    prepare_input(24, 50, 40, 1023, "2025-01-10 10:00", "2025-01-08 10:00", 22, 55, 40, 650),
    prepare_input(10, 50, 42, 600, "2025-01-05 10:00", "2025-01-03 10:00", 22, 55, 40, 650),
    prepare_input(38, 25, 20, 1023, "2025-01-12 10:00", "2025-01-05 10:00", 22, 55, 40, 650),

    # Recovery scenarios
    prepare_input(24, 58, 75, 700, "2025-01-12 10:00", "2025-01-12 09:00", 22, 55, 40, 650),
    prepare_input(23, 45, 48, 800, "2025-01-15 10:00", "2025-01-08 10:00", 22, 55, 40, 650),
    prepare_input(22, 72, 65, 400, "2025-01-10 10:00", "2025-01-09 10:00", 22, 55, 40, 650),
    prepare_input(25, 45, 35, 200, "2025-01-11 10:00", "2025-01-10 10:00", 22, 55, 40, 650),
]

labels = [
    "Dry", "Medium", "Wet", "Very Dry", "At Optimal", "Night",
    "Succulent", "Boston Fern", "Cactus", "Overwatered",
    "Extreme Drought", "Extreme Humidity", "Freezing Cold", "Heat Wave",
    "Just Watered", "1 Week Since Watering", "2 Weeks Since Watering", "3 Weeks - Dry Stress",
    "Monstera - Moderate", "Pothos - Low Light", "Snake Plant - Drought",
    "Jade Plant - Succulent", "Peace Lily - Sensitive", "Calathea - Tropical",
    "Winter - Dormant", "Spring - Growth", "Summer - Peak Growth", "Fall - Transition",
    "Early Morning - Cool", "Noon Peak - Hot", "Afternoon - Max Temp", "Evening - Cooling", "Night - Rest Phase",
    "Critical Low Soil", "Waterlogged Root", "Dark Room", "Grow Light - Intense",
    "Temperature - Too Cold", "Temperature - Too Hot",
    "Drought Recovery", "Overwater Recovery", "Post-Propagation", "New Location",
]

for label, case in zip(labels, cases):
    pred = model.predict(case)[0]
    print(f"{label:25s}: Pump runtime = {pred:6.2f} seconds")

print("\n" + "=" * 60)
print("REAL IoT DATA - Model Predictions")
print("=" * 60 + "\n")

real_cases = [
    prepare_input(23.4, 23, 85, 198, "2026-05-11 21:12", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 23, 84, 30, "2026-05-12 00:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 23, 86, 396, "2026-05-12 05:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.8, 23, 85, 814, "2026-05-12 08:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(24.1, 23, 86, 903, "2026-05-12 10:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 23, 79, 102, "2026-05-11 21:32", "2026-05-09 08:00", 23, 55, 80, 600),
    prepare_input(23.8, 23, 81, 198, "2026-05-11 21:12", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 23, 80, 102, "2026-05-11 21:32", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.1, 23, 70, 38, "2026-05-11 21:52", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23, 23, 88, 28, "2026-05-11 22:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 45, 85, 28, "2026-05-11 23:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 45, 85, 35, "2026-05-11 23:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 46, 84, 44, "2026-05-11 23:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 46, 84, 31, "2026-05-12 00:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 46, 85, 34, "2026-05-12 00:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 47, 84, 31, "2026-05-12 00:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 47, 84, 33, "2026-05-12 01:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 47, 83, 33, "2026-05-12 01:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 47, 84, 33, "2026-05-12 01:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 47, 83, 31, "2026-05-12 02:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 48, 83, 43, "2026-05-12 02:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 48, 83, 45, "2026-05-12 02:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 48, 87, 50, "2026-05-12 03:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23, 48, 87, 49, "2026-05-12 03:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23, 49, 86, 30, "2026-05-12 03:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.6, 49, 86, 49, "2026-05-12 04:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.6, 50, 86, 49, "2026-05-12 04:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.6, 52, 86, 49, "2026-05-12 04:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 52, 87, 49, "2026-05-12 05:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 53, 86, 50, "2026-05-12 05:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.6, 54, 86, 41, "2026-05-12 05:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 53, 86, 50, "2026-05-12 06:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 52, 86, 42, "2026-05-12 06:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.6, 52, 85, 42, "2026-05-12 06:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.6, 50, 86, 50, "2026-05-12 07:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 50, 85, 49, "2026-05-12 07:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.4, 51, 85, 50, "2026-05-12 07:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.8, 52, 85, 49, "2026-05-12 08:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.8, 51, 85, 50, "2026-05-12 08:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.8, 51, 85, 50, "2026-05-12 08:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.8, 49, 85, 49, "2026-05-12 09:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23.8, 52, 85, 49, "2026-05-12 09:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(24.1, 49, 85, 50, "2026-05-12 09:40", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(24.1, 47, 86, 45, "2026-05-12 10:00", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(24.1, 45, 83, 35, "2026-05-12 10:20", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(23, 45, 83, 35, "2026-05-12 20:11", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(24.1, 44, 84, 34, "2026-05-12 20:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(20.6, 40, 85, 29, "2026-05-12 20:37", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 41, 84, 34, "2026-05-12 20:57", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.6, 42, 85, 45, "2026-05-12 21:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.6, 44, 85, 83, "2026-05-12 21:37", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 44, 84, 34, "2026-05-12 21:57", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 45, 85, 34, "2026-05-12 22:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 45, 85, 34, "2026-05-12 22:37", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 47, 85, 34, "2026-05-12 22:57", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 48, 85, 34, "2026-05-12 23:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 49, 85, 34, "2026-05-12 23:37", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(22.2, 49, 84, 34, "2026-05-12 23:57", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.8, 51, 84, 34, "2026-05-13 00:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.8, 52, 85, 34, "2026-05-13 00:37", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 53, 85, 26, "2026-05-13 00:57", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 57, 85, 34, "2026-05-13 01:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 58, 85, 34, "2026-05-13 01:37", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 60, 85, 34, "2026-05-13 02:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 60, 85, 45, "2026-05-13 02:37", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 62, 85, 34, "2026-05-13 02:57", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 63, 85, 34, "2026-05-13 03:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 63, 85, 34, "2026-05-13 03:37", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 64, 85, 34, "2026-05-13 03:57", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.4, 64, 85, 34, "2026-05-13 04:17", "2026-05-10 08:00", 23, 55, 80, 600),
    prepare_input(21.8, 64, 85, 560, "2026-05-13 07:09", "2026-05-10 08:00", 23, 55, 80, 600),
]

real_labels = [
    "Morning - Low Light",
    "Night - Zero Light",
    "Dawn - Light Ramping",
    "Mid Morning - Bright",
    "Peak Light - Midday",
    "Soil Low",
    "Evening - Low Light",
    "Evening - Fading Light",
    "Night - Very Low Light",
    "Night - Humidity Rising",
    "Late Night - Cool",
    "Late Night - Stable",
    "Midnight - Transition",
    "Midnight - Dark",
    "Late Night - Low Light",
    "Deep Night",
    "Deep Night - Stable",
    "Deep Night - Low Soil",
    "Deep Night - Holding",
    "Deep Night - Low Thirst",
    "Deep Night - Rising Humidity",
    "Deep Night - High Humidity",
    "Early Morning - Humidity Peak",
    "Early Morning - Cooling",
    "Pre-Dawn - Light Minimal",
    "Pre-Dawn - Light Rising",
    "Pre-Dawn - Light Increasing",
    "Pre-Dawn - Brightness Ramping",
    "Dawn - Low Light Phase",
    "Dawn - Light Rising Steady",
    "Dawn - Medium Light",
    "Early Morning - Increasing Light",
    "Early Morning - Light Accelerating",
    "Early Morning - Warmth Increasing",
    "Early Morning - Temperature Rising",
    "Morning - Light Approaching Peak",
    "Morning - Medium Brightness",
    "Morning - Bright",
    "Morning - High Light Intensity",
    "Bright Morning - Peak Hour",
    "Mid-Morning - High Light",
    "Mid-Morning - Warm & Bright",
    "Mid-Morning - Optimal Conditions",
    "Midday - Peak Brightness",
    "Midday - Hot & Bright",
    "Late Morning - Light Stable",
    "Afternoon - Light High",
    "Late Afternoon - Cooling Start",
    "Late Afternoon - Temperature Drop",
    "Evening Transition - Darkening",
    "Evening - Light Fading",
    "Evening - Dusk Phase",
    "Evening - Low Light Returning",
    "Evening - Night Approaching",
    "Dusk - Cooling Fast",
    "Night - Cycle Restart",
    "Night - Deep Dark",
    "Deep Night - Temperature Minimum",
    "Deep Night - Humidity Climbing",
    "Deep Night - Humidity High",
    "Deep Night - Humidity Peak",
    "Pre-Dawn - Cool & Humid",
    "Pre-Dawn - Humidity Stable",
    "Pre-Dawn - Temperature Recovery",
    "Pre-Dawn - Warmth Starting",
    "Pre-Dawn - Light Emerging",
    "Pre-Dawn - Transition Phase",
    "Early Morning - Light Returning",
    "Early Morning - Humidity Dropping",
    "Early Morning - Brightness Increasing",
    "Early Morning - Full Light Cycle",
]


for label, case in zip(real_labels, real_cases):

    pred = model.predict(case)[0]
    print(f"{label:35s}: Pump runtime = {pred:6.2f} seconds")

print("\n" + "=" * 60)
print(f"Total test cases: {len(labels) + len(real_labels)}")
print("=" * 60)
