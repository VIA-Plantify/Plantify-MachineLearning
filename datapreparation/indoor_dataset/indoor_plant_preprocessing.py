import pandas as pd


def data_preparation():
    # Load files
    data_sensors = pd.read_csv("Indoor_Plant_Health_and_Growth_Factors.csv")
    data_optimal = pd.read_csv("optimal_plant_conditions.csv")
    light_values = pd.read_csv("light_intensity.csv")

    # Merge files
    data = pd.merge(
        data_sensors,
        data_optimal,
        left_on='Plant_ID',
        right_on='Plant_ID',
        how='left'
    )

    data["Light_Intensity"] = light_values["Lux_Value"]

    # Convert from milliliters to seconds for watering with the flow rate of 10ml/sec
    data["Pump_time"] = data["Watering_Amount_ml"] / 10

    # Drop irrelevant columns
    data = data.drop(columns=["Fertilizer_Type", "Fertilizer_Amount_ml", "Pest_Presence", "Pest_Severity", "Soil_Type",
                              "Health_Score", "Height_cm", "Leaf_Count", "New_Growth_Count", "Health_Notes",
                              "Sunlight_Exposure", "Watering_Frequency_days", "Watering_Amount_ml"])

    # Feature Engineering
    # Soil humidity deficit (optimal - current -> to get a positive value when it needs water)
    data['soil_deficit'] = (data['Optimal_Soil_Moisture_%'] - data['Soil_Moisture_%'])

    # Temperature deviation (current - optimal -> get a positive value when it's hotter than ideal)
    data['temp_deviation'] = (data['Room_Temperature_C'] - data['Optimal_Room_Temperature_C'])

    # Air humidity deficit (optimal - current -> positive means the air is too dry)
    data['air_hum_deficit'] = (data['Optimal_Humidity_%'] - data['Humidity_%'])

    # Light deviation (current - optimal -> get a positive value when it's more light than ideal)
    data['light_deviation'] = (data['Light_Intensity'] - data['Optimal_Light_Intensity_Lux'])

    # Approximate evapotranspiration (water loss due to heat, light, and dry air)
    data['et_approx'] = ((data['Room_Temperature_C'] * data['Light_Intensity']) / (data['Humidity_%'] + 1))

    return data, data_optimal
