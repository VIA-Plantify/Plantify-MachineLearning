import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
class Data_Preparation:
    path = "/workspace/datapreparation/mockdata/"
# 6565555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555ta my cat wrote this

    def __init__(self, path="/workspace/datapreparation/mockdata/"):
        self.path = path
        self.df_waterings = pd.read_csv(f'{path}waterings.csv')
        self.df_sensors   = pd.read_csv(f'{path}sensor_datas.csv')
        self.df_plants    = pd.read_csv(f'{path}plants.csv')
    def prepare_data_general(self):
        # 1 MAC Mapping
        mac_map = {mac: i for i, mac in enumerate(self.df_plants['MAC'].unique())}

        # 2 Prepare waterings

        df_waterings = self.df_waterings.rename(columns={'LastWaterTime': 'WaterTimestamp'})

        # 3 Convert timestamps
        self.df_sensors['Timestamp'] = pd.to_datetime(self.df_sensors['Timestamp'])
        df_waterings['WaterTimestamp'] = pd.to_datetime(df_waterings['WaterTimestamp'], format='mixed')

        # 4 Add mac_id to all dataframes
        self.df_sensors['mac_id'] = self.df_sensors['PlantMAC'].map(mac_map)
        df_waterings['mac_id'] = df_waterings['PlantMAC'].map(mac_map)
        self.df_plants['mac_id'] = self.df_plants['MAC'].map(mac_map)

        # 5 Clean plants table
        df_plants_cleaned = self.df_plants.drop(columns=['MAC', 'Username', 'Name'])

        sensors_sorted = self.df_sensors.sort_values(['Timestamp']).reset_index(drop=True)
        waterings_sorted = df_waterings.sort_values(['WaterTimestamp']).reset_index(drop=True)

        df_water_sensors = pd.merge_asof(
            sensors_sorted,
            waterings_sorted[['mac_id', 'WaterTimestamp', 'PumpTimeInSeconds', 'WaterLevel']],
            left_on='Timestamp',
            right_on='WaterTimestamp',
            by='mac_id',
            direction='backward',
            tolerance=pd.Timedelta(days=90)
        )

        df_water_sensors['hours_since_watering'] = (
        df_water_sensors['Timestamp'] - df_water_sensors['WaterTimestamp']).dt.total_seconds() / 3600

        df_water_sensors = df_water_sensors.drop(columns=['WaterTimestamp', 'Timestamp'])

        # Bring in plant optimal values
        df_water_sensors = df_water_sensors.merge(df_plants_cleaned, on='mac_id', how='left')

        # Deviation function

        df = self.feature_engineering(df = df_water_sensors)

        X = df.drop(columns=['mac_id','PlantMAC'])
        return X
    def prepare_data_pump_time_v1(self):
        df = self.prepare_data_general().dropna()
        columns_to_drop = [
            'OptimalTemperature', 'OptimalAirHumidity',
            'OptimalSoilHumidity', 'OptimalLightIntensity',
            'Temperature', 'AirHumidity', 'SoilHumidity', 'LightIntensity', 'PumpTimeInSeconds', 'WaterLevel'
        ]
        X = df.drop(columns=columns_to_drop)
        y = df['PumpTimeInSeconds']
        return X, y
    @property
    def prepare_data_general_v2(self):
        # 1 MAC Mapping
        mac_map = {mac: i for i, mac in enumerate(self.df_plants['MAC'].unique())}

        # 2 Prepare waterings

        df_waterings = self.df_waterings.rename(columns={'LastWaterTime': 'WaterTimestamp'})

        # 3 Convert timestamps
        self.df_sensors['Timestamp'] = pd.to_datetime(self.df_sensors['Timestamp'])
        df_waterings['WaterTimestamp'] = pd.to_datetime(df_waterings['WaterTimestamp'], format='mixed')

        # 4 Add mac_id to all dataframes
        self.df_sensors['mac_id'] = self.df_sensors['PlantMAC'].map(mac_map)
        df_waterings['mac_id'] = df_waterings['PlantMAC'].map(mac_map)
        self.df_plants['mac_id'] = self.df_plants['MAC'].map(mac_map)

        # 5 Clean plants table
        df_plants_cleaned = self.df_plants.drop(columns=['MAC', 'Username', 'Name'])

        sensors_sorted = self.df_sensors.sort_values(['Timestamp']).reset_index(drop=True)
        waterings_sorted = df_waterings.sort_values(['WaterTimestamp']).reset_index(drop=True)
        df_water_sensors = pd.merge_asof(
            sensors_sorted,
            waterings_sorted[['mac_id', 'WaterTimestamp', 'PumpTimeInSeconds', 'WaterLevel']],
            left_on='Timestamp',
            right_on='WaterTimestamp',
            by='mac_id',
            direction='backward',
            tolerance=pd.Timedelta(days=90)
        )

        df_water_sensors['hours_since_watering'] = (
                                                           df_water_sensors['Timestamp'] - df_water_sensors[
                                                       'WaterTimestamp']
                                                   ).dt.total_seconds() / 3600
        # Readings that surpass the plant being watered for 90 days are removed
        df_water_sensors = df_water_sensors[~df_water_sensors['hours_since_watering'].isnull()]

        df_water_sensors = df_water_sensors.drop(columns=['WaterTimestamp', 'Timestamp'])

        # Bring in plant optimal values
        df = df_water_sensors.merge(df_plants_cleaned, on='mac_id', how='left')

        # Remove impossible outliers
        ## Team decided the following sensor values are highly like errors above 9000 light,
        # above 50C and below 5C, soil humidity above 100 or below 0, air humidity below 5 and above 95

        df = df[(df["SoilHumidity"] > 0) & (df["SoilHumidity"] < 100) | (df["SoilHumidity"].isnull())]
        df = df[(df["Temperature"] > 5) & (df["Temperature"] < 50) | (df["Temperature"].isnull())]
        df = df[(df["AirHumidity"] > 5) & (df["AirHumidity"] < 95) | (df["AirHumidity"].isnull())]
        df = df[(df["LightIntensity"] > 0) & (df["LightIntensity"] < 9000) | (df["LightIntensity"].isnull())]

        # Deviation function
        df = self.feature_engineering(df = df)

        df = df.drop(
            columns=['PlantMAC', 'Temperature', 'LightIntensity', 'AirHumidity', 'SoilHumidity', 'OptimalAirHumidity',
                     'OptimalSoilHumidity', 'OptimalLightIntensity', 'OptimalTemperature'])
        return df
    def prepare_data_pump_time_v2(self):
        X = self.prepare_data_general_v2
        y = X['PumpTimeInSeconds']
        X = X.drop(columns=['PumpTimeInSeconds', 'WaterLevel','mac_id'])
        # transform feature that are right-skewed
        X["et_approx"] = X["et_approx"].apply(lambda x: np.log1p(x))
        return X, y
    def train_val_test_split_64_16_20(self, func):
        X, y = func()
        # First split into training and temp (validation + test)
        X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.20, random_state=42)
        return X_train, X_val,X_test, y_train, y_val, y_test

    @staticmethod
    def  feature_engineering(df):
        # Deviation function

        df['soil_deficit'] = df['OptimalSoilHumidity'] - df['SoilHumidity']
        df['soil_deficit_ratio'] = df['soil_deficit'] / df[
            'OptimalSoilHumidity']

        df['temp_deviation'] = df['Temperature'] - df['OptimalTemperature']
        df['air_hum_deficit'] = df['OptimalAirHumidity'] - df['AirHumidity']
        df['light_deviation'] = df['LightIntensity'] - df[
            'OptimalLightIntensity']

        # Interaction features
        df['deficit_x_temp'] = df['soil_deficit'] * df['temp_deviation']
        df['deficit_x_light'] = df['soil_deficit'] * df['light_deviation']
        df['deficit_x_air'] = df['soil_deficit'] * df['air_hum_deficit']

        df['et_approx'] = (df['Temperature'] * df['LightIntensity']) / (
                df['AirHumidity'] + 1)
        df = df.drop(columns =['soil_deficit'])
        return df