from dataclasses import dataclass, field
from datetime import datetime


@dataclass(repr=True, slots=True)
class Watering:
    plant_mac: str
    predicted_future_water_time: datetime = field(default_factory=datetime.now)
    last_water_time: datetime = field(default_factory=datetime.now)
    water_level: float = 0.0
    pump_time_in_seconds: float = 0.0

    def __str__(self) -> str:
        return (f"Watering(plant_mac={self.plant_mac}, "
                f"predicted_future_water_time={self.predicted_future_water_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"last_water_time={self.last_water_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"water_level={self.water_level:.2f}, "
                f"pump_time_in_seconds={self.pump_time_in_seconds:.2f})")
