import pandas as pd
import numpy as np
class Data_Preparation:
    path = "../mockdata/"
# 6565555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555ta my cat wrote this

    def __init__(self, path="../mockdata/"):
        self.df_waterings = pd.read_csv(f'{path}waterings.csv')
        self.df_sensors   = pd.read_csv(f'{path}sensor_datas.csv')
        self.df_plants    = pd.read_csv(f'{path}plants.csv')
    def prepare_data_general(self):
        mac_map = {mac: i for i, mac in enumerate(self.df_plants['MAC'].unique())}

        self.df_waterings = self.df_waterings.drop(columns=['PredictedFutureWaterTime'])
        self.df_waterings = self.df_waterings.rename(columns={'LastWaterTime': 'Timestamp'})

        self.df_sensors['Timestamp'] = pd.to_datetime(self.df_sensors['Timestamp'])
        self.df_waterings['Timestamp'] = pd.to_datetime(self.df_waterings['Timestamp'], format='mixed')

        self.df_sensors['mac_id'] = self.df_sensors['PlantMAC'].map(mac_map)
        self.df_waterings['mac_id'] = self.df_waterings['PlantMAC'].map(mac_map)
        self.df_plants['mac_id'] = self.df_plants['MAC'].map(mac_map)

        df_plants_cleaned = self.df_plants.drop(columns=['MAC', 'Username', 'Name'])

        sensors_sorted = self.df_sensors.sort_values('Timestamp').reset_index(drop=True).drop(columns=['PlantMAC'])
        waterings_sorted = self.df_waterings.sort_values('Timestamp').reset_index(drop=True).drop(columns=['PlantMAC'])

        df_water_sensors = pd.merge_asof(
            sensors_sorted,
            waterings_sorted[['mac_id', 'Timestamp', 'PumpTimeInSeconds','WaterLevel']].rename(
                columns={'Timestamp': 'LastWaterTimestamp'}),
            left_on='Timestamp',
            right_on='LastWaterTimestamp',
            by='mac_id',
            direction='backward'
        )

        df_water_sensors['seconds_since_watering'] = (
                df_water_sensors['Timestamp'] - df_water_sensors['LastWaterTimestamp']
        ).dt.total_seconds()

        df_water_sensors = df_water_sensors.drop(columns=['LastWaterTimestamp', 'Timestamp'])

        # Bring in plant optimal values
        df_water_sensors = df_water_sensors.merge(df_plants_cleaned, on='mac_id', how='left')

        X = df_water_sensors.drop(columns=['mac_id'])
        return X

    def prepare_data_general_trial(self):
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

        df_water_sensors = df_water_sensors.drop(columns=['WaterTimestamp', 'Timestamp'])

        df_water_sensors = df_water_sensors.dropna()  # drop water readings beyond 90 days of last watering

        # Bring in plant optimal values
        df_water_sensors = df_water_sensors.merge(df_plants_cleaned, on='mac_id', how='left')

        # Deviation function

        df_water_sensors['soil_deficit'] = df_water_sensors['OptimalSoilHumidity'] - df_water_sensors['SoilHumidity']
        df_water_sensors['soil_deficit_ratio'] = df_water_sensors['soil_deficit'] / df_water_sensors[
            'OptimalSoilHumidity']

        df_water_sensors['temp_deviation'] = df_water_sensors['Temperature'] - df_water_sensors['OptimalTemperature']
        df_water_sensors['air_hum_deficit'] = df_water_sensors['OptimalAirHumidity'] - df_water_sensors['AirHumidity']
        df_water_sensors['light_deviation'] = df_water_sensors['LightIntensity'] - df_water_sensors[
            'OptimalLightIntensity']

        # Interaction features
        df_water_sensors['deficit_x_temp'] = df_water_sensors['soil_deficit'] * df_water_sensors['temp_deviation']
        df_water_sensors['deficit_x_light'] = df_water_sensors['soil_deficit'] * df_water_sensors['light_deviation']
        df_water_sensors['deficit_x_air'] = df_water_sensors['soil_deficit'] * df_water_sensors['air_hum_deficit']

        df_water_sensors['et_approx'] = (df_water_sensors['Temperature'] * df_water_sensors['LightIntensity']) / (
                    df_water_sensors['AirHumidity'] + 1)

        X = df_water_sensors.drop(columns=['mac_id','PlantMAC'])
        return X