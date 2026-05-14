import numpy as np
import pandas as pd

np.random.seed(42)

data = pd.read_csv("Indoor_Plant_Health_and_Growth_Factors.csv")

def sunlight_to_lux(sunlight_exposure):
    sunlight_str = str(sunlight_exposure).lower()

    if "6h full sun" in sunlight_str or "full sun" in sunlight_str:
        return np.random.randint(950, 1024)
    elif "3h direct" in sunlight_str or "direct morning sun" in sunlight_str or "direct afternoon sun" in sunlight_str:
        return np.random.randint(700, 1000)
    elif "filtered sunlight" in sunlight_str or "filtered" in sunlight_str:
        return np.random.randint(500, 1050)
    elif "indirect light" in sunlight_str:
        return np.random.randint(200, 501)
    elif "low light" in sunlight_str or "low light corner" in sunlight_str:
        return np.random.randint(50, 201)
    else:
        return np.random.randint(200, 501)  # Default to indirect light for unknown values

data["Lux_Value"] = data["Sunlight_Exposure"].apply(sunlight_to_lux)

light_intensity_data = data[["Plant_ID", "Sunlight_Exposure", "Lux_Value"]]
light_intensity_data.to_csv("light_intensity.csv", index=False)

