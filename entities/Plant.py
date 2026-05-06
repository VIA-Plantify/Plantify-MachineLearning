class Plant:
    def __init__(self, name, username, optimal_temperature, optimal_air_humidity, optimal_soil_humidity,
                 optimal_light_intensity, MAC):
        self.name = name
        self.username = username
        self.optimal_temperature = optimal_temperature
        self.optimal_air_humidity = optimal_air_humidity
        self.optimal_soil_humidity = optimal_soil_humidity
        self.optimal_light_intensity = optimal_light_intensity
        self.MAC = MAC
