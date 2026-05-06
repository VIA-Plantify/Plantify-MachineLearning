from dataclasses import field, dataclass

from entities.Sensor import Sensor
from entities.Watering import Watering


@dataclass(slots=True)
class Plant:
    MAC: str
    username: str
    optimal_temperature: float
    optimal_air_humidity: float
    optimal_soil_humidity: float
    optimal_light_intensity: float
    sensors: list[Sensor] = field(default_factory=list[Sensor])
    waterings: list[Watering] = field(default_factory=list[Watering])
    name: str = ""

    def __str__(self) -> str:
        sensor_str = f"\n    ".join(str(s) for s in self.sensors) if self.sensors else "None"
        watering_str = f"\n    ".join(str(w) for w in self.waterings) if self.waterings else "None"

        return (
            f"Plant: {self.name or 'Unnamed'}\n"
            f"  MAC Address: {self.MAC}\n"
            f"  Owner: {self.username}\n"
            f"  Optimal Conditions:\n"
            f"    Temperature: {self.optimal_temperature}°C\n"
            f"    Air Humidity: {self.optimal_air_humidity}%\n"
            f"    Soil Humidity: {self.optimal_soil_humidity}%\n"
            f"    Light Intensity: {self.optimal_light_intensity}\n"
            f"  Sensors ({len(self.sensors)}):\n"
            f"    {sensor_str}\n"
            f"  Waterings ({len(self.waterings)}):\n"
            f"    {watering_str}"
        )
