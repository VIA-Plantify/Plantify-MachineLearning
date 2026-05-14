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
        ## Team decided the following sensor values are highly like errors above 1024 light,
        # above 50C and below 5C, soil humidity above 100 or below 0, air humidity below 5 and above 95

        df['Temperature'] = df['Temperature'].clip(5, 50)
        df['AirHumidity'] = df['AirHumidity'].clip(10, 100)
        df['SoilHumidity'] = df['SoilHumidity'].clip(0, 100)
        df['LightIntensity'] = df['LightIntensity'].clip(0, 1024)

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
        if "et_approx" in X.columns:
            X["et_approx"] = np.log1p(X["et_approx"])


        return X, y
    def train_val_test_split_64_16_20(self, func):
        X, y = func()
        # First split into training and temp (validation + test)
        X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.20, random_state=42)
        return X_train, X_val,X_test, y_train, y_val, y_test

    def prepare_data_general_v3(self):
        # 1. Basic Mapping and Cleaning
        mac_map = {mac: i for i, mac in enumerate(self.df_plants['MAC'].unique())}
        df_waterings = self.df_waterings.rename(columns={'LastWaterTime': 'WaterTimestamp'})

        self.df_sensors['Timestamp'] = pd.to_datetime(self.df_sensors['Timestamp'])
        df_waterings['WaterTimestamp'] = pd.to_datetime(df_waterings['WaterTimestamp'], format='mixed')

        self.df_sensors['mac_id'] = self.df_sensors['PlantMAC'].map(mac_map)
        df_waterings['mac_id'] = df_waterings['PlantMAC'].map(mac_map)

        sensors_sorted = self.df_sensors.sort_values(['Timestamp']).reset_index(drop=True)
        waterings_sorted = df_waterings.sort_values(['WaterTimestamp']).reset_index(drop=True)

        # 2. Merge Asof
        df = pd.merge_asof(
            sensors_sorted,
            waterings_sorted[['mac_id', 'WaterTimestamp', 'PumpTimeInSeconds', 'WaterLevel']],
            left_on='Timestamp',
            right_on='WaterTimestamp',
            by='mac_id',
            direction='backward',
            tolerance=pd.Timedelta(days=90)
        )

        # 3. Time Feature and Sorting
        df['hours_since_watering'] = (df['Timestamp'] - df['WaterTimestamp']).dt.total_seconds() / 3600
        df = df[df['hours_since_watering'].notnull()]

        # Sort by plant and time for logical interpolation
        df = df.sort_values(['mac_id', 'hours_since_watering'])

        # 4. Sequential Imputation (Interpolation)
        # We fill raw sensors BEFORE engineering interaction features
        sensor_cols = ['Temperature', 'AirHumidity', 'SoilHumidity', 'LightIntensity']
        df[sensor_cols] = df.groupby('mac_id')[sensor_cols].transform(
            lambda x: x.interpolate(method='linear').ffill().bfill()
        )

        # 5. Outlier Removal (post-interpolation)
        df['Temperature'] = df['Temperature'].clip(5, 50)
        df['AirHumidity'] = df['AirHumidity'].clip(10, 100)
        df['SoilHumidity'] = df['SoilHumidity'].clip(0, 100)
        df['LightIntensity'] = df['LightIntensity'].clip(0, 1024)

        # 6. Merge Plant Optimals
        df_plants_cleaned = self.df_plants.drop(columns=['MAC', 'Username', 'Name'])
        df = df.merge(df_plants_cleaned, on='mac_id', how='left')

        # 7. Execute Feature Engineering
        df = self.feature_engineering(df)

        return df

    def prepare_data_pump_time_v3(self):
        df = self.prepare_data_general_v3()

        y = df['PumpTimeInSeconds']

        # DROP ORIGINALS: We drop raw sensors and optimal values
        # to focus on the deviations/interactions created in engineering
        columns_to_drop = [
            'PlantMAC', 'WaterTimestamp', 'Timestamp',
            'PumpTimeInSeconds', 'WaterLevel', 'mac_id',
            'Temperature', 'AirHumidity', 'SoilHumidity', 'LightIntensity',
            'OptimalTemperature', 'OptimalAirHumidity', 'OptimalSoilHumidity', 'OptimalLightIntensity'
        ]

        X = df.drop(columns=columns_to_drop)

        # Final Log transform for the specific interaction feature
        if "et_approx" in X.columns:
            X["et_approx"] = np.log1p(X["et_approx"])

        return X, y

    @staticmethod
    def feature_engineering(df):
        # Deficit Calculations
        df['soil_deficit'] = df['OptimalSoilHumidity'] - df['SoilHumidity']
        df['soil_deficit_ratio'] = ((df['OptimalSoilHumidity'] - df['SoilHumidity']) /
                                    df['OptimalSoilHumidity']).clip(-1.0, 1.0)

        # 2. THE CONTEXT (Hidden from the model)
        temp_dev = df['Temperature'] - df['OptimalTemperature']
        light_dev = df['LightIntensity'] - df['OptimalLightIntensity']
        air_dev = df['OptimalAirHumidity'] - df['AirHumidity']

        #  Stabilized Interaction Features
        # Multiplying by 'ratio' instead of 'raw deficit' prevents the 30,000+ outliers
        df['deficit_x_light'] = df['soil_deficit_ratio'] * (light_dev / 200)
        df['deficit_x_temp'] = df['soil_deficit_ratio'] * temp_dev
        df['deficit_x_air'] = df['soil_deficit_ratio'] * air_dev

        # Evapotranspiration Approximation
        # Adding a small constant to prevent division by zero and capping the result
        df['et_approx'] = (df['Temperature'] * df['LightIntensity']) / (df['AirHumidity'] + 10)

        df = df.drop(columns=['soil_deficit'])
        return df