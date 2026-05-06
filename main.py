from entities.Plant import Plant
from entities.Sensor import Sensor
from entities.Watering import Watering

plant = Plant(username="John", MAC="124123", name="Patrik", optimal_temperature=20, optimal_air_humidity=20,
              optimal_soil_humidity=20, optimal_light_intensity=1000)
sensors = list[Sensor]()
waterings = list[Watering]()
for i in range (0, 10):
    sensors.append(Sensor(temperature= i, plant_mac= plant.MAC, soil_humidity= i, air_humidity= i, light_intensity= i))
    waterings.append(Watering(plant_mac=plant.MAC,))
plant.sensors = sensors
plant.waterings = waterings
print(plant)