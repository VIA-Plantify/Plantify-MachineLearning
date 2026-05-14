from pathlib import Path
import xgboost as xgb
import numpy as np
import pandas as pd


class PumpTimeModel:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.model_path = self.base_path / "pump_time_tree_model.ubj"

        self.model = xgb.XGBRegressor()

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}"
            )

        self.model.load_model(self.model_path)

    def prepare_input(self, temperature, air_humidity, soil_humidity, light_intensity,
                      sensor_timestamp, last_water_timestamp,
                      optimal_temperature, optimal_air_humidity,
                      optimal_soil_humidity, optimal_light_intensity):
        sensor_ts = pd.to_datetime(sensor_timestamp)
        last_ts = pd.to_datetime(last_water_timestamp)
        hours_since_watering = (sensor_ts - last_ts).total_seconds() / 3600

        hours_since_watering = np.log1p(max(0, hours_since_watering))
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
            "soil_deficit_ratio": soil_deficit / (optimal_soil_humidity + 1e-5),
            "temp_deviation": temperature - optimal_temperature,
            "air_hum_deficit": optimal_air_humidity - air_humidity,
            "light_deviation": light_intensity - optimal_light_intensity,
            "deficit_x_temp": soil_deficit * (temperature - optimal_temperature),
            "deficit_x_light": soil_deficit * (light_intensity - optimal_light_intensity),
            "deficit_x_air": soil_deficit * (optimal_air_humidity - air_humidity),
            "et_approx": (temperature * light_intensity) / (air_humidity + 1),
        }

        df = pd.DataFrame([features])
        # Use feature_names if feature_names_in_ isn't available
        cols = getattr(self.model, 'feature_names_in_', self.model.get_booster().feature_names)
        return df[cols]

    # Added **kwargs so it can accept the dictionary from the test case
    def predict(self, **kwargs):
        X = self.prepare_input(**kwargs)

        prediction = self.model.predict(X)[0]

        print(f"Pump Time: {prediction} seconds")
        runtime = round(max(0, float(prediction)))

        if runtime < 2:
            runtime = 0

        return runtime

    def run_test_case(self):
        """Quick internal test to see if the logic holds up"""
        test_data = {
            "temperature": 28,
            "air_humidity": 25,
            "soil_humidity": 50,
            "light_intensity": 900,
            "sensor_timestamp": "2025-01-11 10:00",
            "last_water_timestamp": "2025-01-10 10:00",
            "optimal_temperature": 22,
            "optimal_air_humidity": 55,
            "optimal_soil_humidity": 80,
            "optimal_light_intensity": 650
        }

        # Passing the dictionary into the modified predict
        result = self.predict(**test_data)

        print("--- Test Case Results ---")
        print(f"Input: Soil at {test_data['soil_humidity']}% (Target {test_data['optimal_soil_humidity']}%)")
        print(f"Calculated Runtime: {result} seconds")
        return result


# Execution
if __name__ == "__main__":
    predictor = PumpTimeModel()
    predictor.run_test_case()