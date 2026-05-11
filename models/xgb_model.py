import xgboost as xgb
import pandas as pd

model = xgb.XGBRegressor()
model.load_model("xgb_model.ubj")

test_cases = [
    {"Temperature": 28, "AirHumidity": 25, "SoilHumidity": 20, "LightIntensity": 900, "seconds_since_watering": 14400, "OptimalTemperature": 22, "OptimalAirHumidity": 55, "OptimalSoilHumidity": 40, "OptimalLightIntensity": 650},
    {"Temperature": 22, "AirHumidity": 50, "SoilHumidity": 35, "LightIntensity": 600, "seconds_since_watering": 6000, "OptimalTemperature": 22, "OptimalAirHumidity": 55, "OptimalSoilHumidity": 40, "OptimalLightIntensity": 650},
    {"Temperature": 21, "AirHumidity": 60, "SoilHumidity": 85, "LightIntensity": 500, "seconds_since_watering": 2000, "OptimalTemperature": 22, "OptimalAirHumidity": 55, "OptimalSoilHumidity": 40, "OptimalLightIntensity": 650},
    {"Temperature": 35, "AirHumidity": 15, "SoilHumidity": 10, "LightIntensity": 1000, "seconds_since_watering": 20000, "OptimalTemperature": 22, "OptimalAirHumidity": 55, "OptimalSoilHumidity": 40, "OptimalLightIntensity": 650},
]

df = pd.DataFrame(test_cases)

preds = model.predict(df)
#Case 1 dry
#Case 2 medium
#case 3 wet
#case for very dry
for i, p in enumerate(preds):
    print(f"Case {i+1}: Pump runtime = {p:.2f}")