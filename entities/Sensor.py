from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True, repr=True)
class Sensor:
    plant_mac: str
    soil_humidity: float = 0.0
    light_intensity: float = 0.0
    air_humidity: float = 0.0
    temperature: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return (
            f"Sensor Reading for Plant {self.plant_mac}"
            f"  Temperature:      {self.temperature:.2f}°C"
            f"  Air Humidity:     {self.air_humidity:.2f}%"
            f"  Soil Humidity:    {self.soil_humidity:.2f}%"
            f"  Light Intensity:  {self.light_intensity:.2f}"
            f"  Timestamp:        {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
