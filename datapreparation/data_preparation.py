import pandas as pd
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
        for mac, group in df_water_sensors.groupby('mac_id'):
            pass
        X = df_water_sensors.drop(columns=['mac_id'])
        return X