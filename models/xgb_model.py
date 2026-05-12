import xgboost as xgb
import pandas as pd

model = xgb.XGBRegressor()
model.load_model("xgb_model.ubj")


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
        "soil_deficit": soil_deficit,
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


# Test cases
cases = [
    # Dry — hot, bright, low soil, 10 days since watering
    prepare_input(28, 25, 20, 900, "2025-01-11 10:00", "2025-01-01 10:00", 22, 55, 40, 650),

    # Medium — normal conditions, 4 days since watering
    prepare_input(22, 50, 35, 600, "2025-01-08 10:00", "2025-01-04 10:00", 22, 55, 40, 650),

    # Wet — cool, humid, high soil, watered yesterday
    prepare_input(21, 60, 85, 500, "2025-01-03 10:00", "2025-01-02 10:00", 22, 55, 40, 650),

    # Very dry — extreme heat, very low soil, 2 weeks since watering
    prepare_input(35, 15, 10, 1000, "2025-01-15 10:00", "2025-01-01 10:00", 22, 55, 40, 650),

    # At optimal — everything perfect, watered 3 days ago
    prepare_input(22, 55, 40, 650, "2025-01-04 10:00", "2025-01-01 10:00", 22, 55, 40, 650),

    # Night reading — no light, cool, moderate soil
    prepare_input(19, 58, 38, 0, "2025-01-05 02:00", "2025-01-03 10:00", 22, 55, 40, 650),

    # Succulent — prefers dry, low optimal soil, long gap
    prepare_input(26, 30, 18, 4000, "2025-01-20 10:00", "2025-01-01 10:00", 24, 30, 25, 5000),

    # Boston Fern — needs lots of water, watered 5 days ago
    prepare_input(20, 70, 50, 800, "2025-01-06 10:00", "2025-01-01 10:00", 20, 70, 72, 1000),

    # Cactus — very dry tolerant, bright light, 3 weeks no water
    prepare_input(28, 20, 12, 7000, "2025-01-22 10:00", "2025-01-01 10:00", 25, 20, 18, 7500),

    # Overwatered — soil way above optimal
    prepare_input(22, 55, 90, 600, "2025-01-02 10:00", "2025-01-01 10:00", 22, 55, 40, 650),
]

labels = ["Dry", "Medium", "Wet", "Very Dry", "At Optimal",
          "Night", "Succulent", "Boston Fern", "Cactus", "Overwatered"]

for label, case in zip(labels, cases):
    pred = model.predict(case)[0]
    print(f"{label:15s}: Pump runtime = {pred:.2f} seconds")

print("\n Real IOT data next \n")

real_cases = [
    # Morning — low light, normal soil
    prepare_input(23.4, 23, 85, 198, "2026-05-11 21:12", "2026-05-10 08:00", 23, 55, 80, 600),

    # Night — zero light, cool
    prepare_input(23.4, 23, 84, 30, "2026-05-12 00:00", "2026-05-10 08:00", 23, 55, 80, 600),

    # Dawn — light ramping up
    prepare_input(22.2, 23, 86, 396, "2026-05-12 05:20", "2026-05-10 08:00", 23, 55, 80, 600),

    # Mid morning — bright
    prepare_input(23.8, 23, 85, 814, "2026-05-12 08:40", "2026-05-10 08:00", 23, 55, 80, 600),

    # Bright morning — peak light
    prepare_input(24.1, 23, 86, 903, "2026-05-12 10:00", "2026-05-10 08:00", 23, 55, 80, 600),

    # Soil slightly low
    prepare_input(23.4, 23, 79, 102, "2026-05-11 21:32", "2026-05-09 08:00", 23, 55, 80, 600),
]

real_labels = ["Morning", "Night", "Dawn", "Mid Morning", "Peak Light", "Soil Low"]

for real_labels, real_cases in zip(real_labels, real_cases):
    pred = model.predict(real_cases)[0]
    print(f"{real_labels:15s}: Pump runtime = {pred:.2f} seconds")