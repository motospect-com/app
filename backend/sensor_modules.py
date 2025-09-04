"""
Sensor Modules for MOTOSPECT
Interfaces and implementations for various vehicle diagnostic sensors
"""
import asyncio
import logging
import random
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Standard sensor reading format"""
    sensor_id: str
    sensor_type: str
    timestamp: datetime
    value: Any
    unit: str
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]


class BaseSensor(ABC):
    """Abstract base class for all sensors"""
    
    def __init__(self, sensor_id: str, debug_mode: bool = False):
        self.sensor_id = sensor_id
        self.debug_mode = debug_mode
        self.is_active = False
        self.last_reading = None
        self.calibration_data = {}
        self.error_count = 0
        
        if debug_mode:
            logger.debug(f"Initializing sensor: {sensor_id} in DEBUG mode")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the sensor hardware/connection"""
        pass
    
    @abstractmethod
    async def read(self) -> SensorReading:
        """Get current reading from sensor"""
        pass
    
    @abstractmethod
    async def calibrate(self) -> bool:
        """Calibrate the sensor"""
        pass
    
    async def start(self):
        """Start sensor operation"""
        self.is_active = True
        logger.info(f"Sensor {self.sensor_id} started")
    
    async def stop(self):
        """Stop sensor operation"""
        self.is_active = False
        logger.info(f"Sensor {self.sensor_id} stopped")
    
    async def cleanup(self):
        """Cleanup sensor resources"""
        await self.stop()
        logger.debug(f"Sensor {self.sensor_id} cleaned up")


class ThermalSensor(BaseSensor):
    """Thermal imaging sensor for heat detection"""
    
    def __init__(self, sensor_id: str = "thermal_01", resolution: Tuple[int, int] = (32, 24), debug_mode: bool = False):
        super().__init__(sensor_id, debug_mode)
        self.resolution = resolution
        self.temperature_range = (-20, 380)  # Celsius
        self.emissivity = 0.95  # Default emissivity
        
    async def initialize(self) -> bool:
        """Initialize thermal sensor (MLX90640 or FLIR Lepton)"""
        try:
            logger.info(f"Initializing thermal sensor {self.sensor_id} with resolution {self.resolution}")
            # In production: Initialize I2C/SPI connection
            await asyncio.sleep(0.1)  # Simulate initialization
            self.calibration_data = {
                "offset": 0.5,
                "gain": 1.02,
                "bad_pixels": []
            }
            return True
        except Exception as e:
            logger.error(f"Failed to initialize thermal sensor: {e}")
            return False
    
    async def read(self) -> SensorReading:
        """Read thermal image data"""
        if not self.is_active:
            await self.start()
        
        # Simulate thermal image capture
        thermal_image = np.random.normal(25, 5, self.resolution)
        
        # Add some hot spots for realism
        if random.random() > 0.7:
            hot_x = random.randint(5, self.resolution[0] - 5)
            hot_y = random.randint(5, self.resolution[1] - 5)
            thermal_image[hot_x-2:hot_x+2, hot_y-2:hot_y+2] += random.uniform(10, 30)
        
        reading = SensorReading(
            sensor_id=self.sensor_id,
            sensor_type="thermal",
            timestamp=datetime.now(),
            value={
                "image": thermal_image.tolist(),
                "max_temp": float(np.max(thermal_image)),
                "min_temp": float(np.min(thermal_image)),
                "avg_temp": float(np.mean(thermal_image)),
                "hot_spots": self._detect_hot_spots(thermal_image)
            },
            unit="celsius",
            confidence=0.95,
            metadata={
                "resolution": self.resolution,
                "emissivity": self.emissivity,
                "frame_rate": 8  # Hz
            }
        )
        
        self.last_reading = reading
        if self.debug_mode:
            logger.debug(f"Thermal reading: Max={reading.value['max_temp']:.1f}°C, Min={reading.value['min_temp']:.1f}°C")
        
        return reading
    
    def _detect_hot_spots(self, thermal_image: np.ndarray) -> List[Dict]:
        """Detect anomalous hot spots in thermal image"""
        hot_spots = []
        threshold = np.mean(thermal_image) + 2 * np.std(thermal_image)
        
        hot_pixels = np.where(thermal_image > threshold)
        if len(hot_pixels[0]) > 0:
            for i in range(min(5, len(hot_pixels[0]))):  # Max 5 hot spots
                hot_spots.append({
                    "x": int(hot_pixels[0][i]),
                    "y": int(hot_pixels[1][i]),
                    "temperature": float(thermal_image[hot_pixels[0][i], hot_pixels[1][i]])
                })
        
        return hot_spots
    
    async def calibrate(self) -> bool:
        """Calibrate thermal sensor using known reference"""
        logger.info(f"Calibrating thermal sensor {self.sensor_id}")
        await asyncio.sleep(1)  # Simulate calibration
        self.calibration_data["last_calibration"] = datetime.now().isoformat()
        return True


class AudioSensor(BaseSensor):
    """Audio sensor for sound analysis and anomaly detection"""
    
    def __init__(self, sensor_id: str = "audio_01", sample_rate: int = 44100, debug_mode: bool = False):
        super().__init__(sensor_id, debug_mode)
        self.sample_rate = sample_rate
        self.channels = 2  # Stereo
        self.buffer_size = 4096
        
    async def initialize(self) -> bool:
        """Initialize audio sensor (microphone array)"""
        try:
            logger.info(f"Initializing audio sensor {self.sensor_id} at {self.sample_rate}Hz")
            # In production: Initialize audio device
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize audio sensor: {e}")
            return False
    
    async def read(self) -> SensorReading:
        """Read audio data and perform frequency analysis"""
        if not self.is_active:
            await self.start()
        
        # Simulate audio capture
        duration = 0.1  # 100ms sample
        samples = int(self.sample_rate * duration)
        
        # Generate synthetic audio with some frequency components
        time = np.linspace(0, duration, samples)
        audio_data = (
            0.1 * np.sin(2 * np.pi * 100 * time) +  # Engine idle
            0.05 * np.sin(2 * np.pi * 500 * time) +  # Belt noise
            0.02 * np.random.randn(samples)  # Background noise
        )
        
        # Perform FFT for frequency analysis
        fft_data = np.abs(np.fft.rfft(audio_data))
        frequencies = np.fft.rfftfreq(samples, 1/self.sample_rate)
        
        # Find dominant frequencies
        peak_indices = np.argsort(fft_data)[-5:]  # Top 5 frequencies
        dominant_frequencies = frequencies[peak_indices].tolist()
        
        reading = SensorReading(
            sensor_id=self.sensor_id,
            sensor_type="audio",
            timestamp=datetime.now(),
            value={
                "rms_level": float(np.sqrt(np.mean(audio_data**2))),
                "peak_level": float(np.max(np.abs(audio_data))),
                "dominant_frequencies": dominant_frequencies,
                "spectral_centroid": float(np.sum(frequencies * fft_data) / np.sum(fft_data)),
                "anomalies": self._detect_audio_anomalies(fft_data, frequencies)
            },
            unit="amplitude",
            confidence=0.92,
            metadata={
                "sample_rate": self.sample_rate,
                "duration": duration,
                "channels": self.channels
            }
        )
        
        self.last_reading = reading
        if self.debug_mode:
            logger.debug(f"Audio reading: RMS={reading.value['rms_level']:.3f}, Peak={reading.value['peak_level']:.3f}")
        
        return reading
    
    def _detect_audio_anomalies(self, fft_data: np.ndarray, frequencies: np.ndarray) -> List[Dict]:
        """Detect audio anomalies (knocking, grinding, etc.)"""
        anomalies = []
        
        # Check for knocking (low frequency spikes)
        knock_range = (20, 200)  # Hz
        knock_indices = np.where((frequencies >= knock_range[0]) & (frequencies <= knock_range[1]))[0]
        if len(knock_indices) > 0:
            knock_energy = np.mean(fft_data[knock_indices])
            if knock_energy > 0.1:  # Threshold
                anomalies.append({
                    "type": "knocking",
                    "severity": "medium" if knock_energy < 0.2 else "high",
                    "frequency_range": knock_range,
                    "energy": float(knock_energy)
                })
        
        # Check for belt squeal (high frequency)
        squeal_range = (2000, 5000)  # Hz
        squeal_indices = np.where((frequencies >= squeal_range[0]) & (frequencies <= squeal_range[1]))[0]
        if len(squeal_indices) > 0:
            squeal_energy = np.mean(fft_data[squeal_indices])
            if squeal_energy > 0.05:
                anomalies.append({
                    "type": "belt_squeal",
                    "severity": "low" if squeal_energy < 0.1 else "medium",
                    "frequency_range": squeal_range,
                    "energy": float(squeal_energy)
                })
        
        return anomalies
    
    async def calibrate(self) -> bool:
        """Calibrate audio sensor using ambient noise"""
        logger.info(f"Calibrating audio sensor {self.sensor_id}")
        # Record ambient noise for baseline
        await asyncio.sleep(2)
        self.calibration_data["noise_floor"] = 0.02
        self.calibration_data["last_calibration"] = datetime.now().isoformat()
        return True


class VibrationSensor(BaseSensor):
    """Vibration/Accelerometer sensor for detecting mechanical issues"""
    
    def __init__(self, sensor_id: str = "vibration_01", axes: int = 3, debug_mode: bool = False):
        super().__init__(sensor_id, debug_mode)
        self.axes = axes  # 3-axis accelerometer
        self.sensitivity = 100  # mV/g
        self.range = 16  # +/- 16g
        
    async def initialize(self) -> bool:
        """Initialize vibration sensor (IMU/Accelerometer)"""
        try:
            logger.info(f"Initializing {self.axes}-axis vibration sensor {self.sensor_id}")
            # In production: Initialize I2C/SPI connection to IMU
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize vibration sensor: {e}")
            return False
    
    async def read(self) -> SensorReading:
        """Read vibration/acceleration data"""
        if not self.is_active:
            await self.start()
        
        # Simulate vibration data (x, y, z axes)
        base_vibration = 0.1  # g
        vibration_data = {
            "x": base_vibration + random.gauss(0, 0.02),
            "y": base_vibration + random.gauss(0, 0.02),
            "z": base_vibration + random.gauss(0, 0.03)  # More vertical vibration
        }
        
        # Add occasional spike for imbalance
        if random.random() > 0.9:
            axis = random.choice(["x", "y", "z"])
            vibration_data[axis] += random.uniform(0.5, 1.0)
        
        # Calculate magnitude
        magnitude = np.sqrt(sum(v**2 for v in vibration_data.values()))
        
        reading = SensorReading(
            sensor_id=self.sensor_id,
            sensor_type="vibration",
            timestamp=datetime.now(),
            value={
                "axes": vibration_data,
                "magnitude": float(magnitude),
                "frequency_analysis": self._analyze_vibration_frequency(),
                "imbalance_detected": magnitude > 0.3,
                "vibration_pattern": self._classify_vibration_pattern(magnitude)
            },
            unit="g",
            confidence=0.94,
            metadata={
                "axes_count": self.axes,
                "sampling_rate": 1000,  # Hz
                "range": self.range
            }
        )
        
        self.last_reading = reading
        if self.debug_mode:
            logger.debug(f"Vibration reading: Magnitude={magnitude:.3f}g")
        
        return reading
    
    def _analyze_vibration_frequency(self) -> Dict:
        """Analyze vibration frequency spectrum"""
        return {
            "dominant_frequency": random.uniform(10, 100),  # Hz
            "harmonics": [random.uniform(20, 200) for _ in range(3)],
            "resonance_detected": random.random() > 0.8
        }
    
    def _classify_vibration_pattern(self, magnitude: float) -> str:
        """Classify vibration pattern"""
        if magnitude < 0.2:
            return "normal"
        elif magnitude < 0.5:
            return "slight_imbalance"
        elif magnitude < 1.0:
            return "moderate_imbalance"
        else:
            return "severe_vibration"
    
    async def calibrate(self) -> bool:
        """Calibrate vibration sensor"""
        logger.info(f"Calibrating vibration sensor {self.sensor_id}")
        await asyncio.sleep(1)
        self.calibration_data["offset"] = {"x": 0.01, "y": 0.01, "z": 0.02}
        self.calibration_data["last_calibration"] = datetime.now().isoformat()
        return True


class LiDARSensor(BaseSensor):
    """LiDAR sensor for 3D scanning and distance measurement"""
    
    def __init__(self, sensor_id: str = "lidar_01", range_meters: float = 10.0, debug_mode: bool = False):
        super().__init__(sensor_id, debug_mode)
        self.range = range_meters
        self.angular_resolution = 0.5  # degrees
        self.scan_rate = 10  # Hz
        
    async def initialize(self) -> bool:
        """Initialize LiDAR sensor"""
        try:
            logger.info(f"Initializing LiDAR sensor {self.sensor_id} with range {self.range}m")
            # In production: Initialize serial/USB connection to LiDAR
            await asyncio.sleep(0.2)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LiDAR sensor: {e}")
            return False
    
    async def read(self) -> SensorReading:
        """Read LiDAR point cloud data"""
        if not self.is_active:
            await self.start()
        
        # Simulate 360-degree scan
        num_points = 720  # 0.5 degree resolution
        angles = np.linspace(0, 360, num_points)
        
        # Generate distance measurements
        base_distance = 2.0  # meters to vehicle
        distances = base_distance + 0.5 * np.sin(np.radians(angles * 2)) + np.random.normal(0, 0.05, num_points)
        
        # Detect surface irregularities
        irregularities = []
        for i in range(1, len(distances) - 1):
            if abs(distances[i] - distances[i-1]) > 0.1:  # 10cm jump
                irregularities.append({
                    "angle": float(angles[i]),
                    "distance_change": float(abs(distances[i] - distances[i-1])),
                    "type": "dent" if distances[i] > distances[i-1] else "bump"
                })
        
        reading = SensorReading(
            sensor_id=self.sensor_id,
            sensor_type="lidar",
            timestamp=datetime.now(),
            value={
                "point_count": num_points,
                "min_distance": float(np.min(distances)),
                "max_distance": float(np.max(distances)),
                "avg_distance": float(np.mean(distances)),
                "surface_irregularities": irregularities[:10],  # Top 10
                "scan_quality": 0.95 if len(irregularities) < 5 else 0.85
            },
            unit="meters",
            confidence=0.96,
            metadata={
                "angular_resolution": self.angular_resolution,
                "scan_rate": self.scan_rate,
                "range": self.range
            }
        )
        
        self.last_reading = reading
        if self.debug_mode:
            logger.debug(f"LiDAR reading: {num_points} points, {len(irregularities)} irregularities detected")
        
        return reading
    
    async def calibrate(self) -> bool:
        """Calibrate LiDAR sensor"""
        logger.info(f"Calibrating LiDAR sensor {self.sensor_id}")
        await asyncio.sleep(2)
        self.calibration_data["angle_offset"] = 0.0
        self.calibration_data["distance_correction"] = 1.0
        self.calibration_data["last_calibration"] = datetime.now().isoformat()
        return True


class EmissionsSensor(BaseSensor):
    """Emissions sensor for exhaust gas analysis"""
    
    def __init__(self, sensor_id: str = "emissions_01", debug_mode: bool = False):
        super().__init__(sensor_id, debug_mode)
        self.gas_types = ["CO", "CO2", "NOx", "HC", "O2", "PM2.5"]
        
    async def initialize(self) -> bool:
        """Initialize emissions sensor"""
        try:
            logger.info(f"Initializing emissions sensor {self.sensor_id}")
            # In production: Initialize gas sensor array
            await asyncio.sleep(0.15)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize emissions sensor: {e}")
            return False
    
    async def read(self) -> SensorReading:
        """Read emissions data"""
        if not self.is_active:
            await self.start()
        
        # Simulate emissions readings (ppm or percentage)
        emissions_data = {
            "CO": random.uniform(0.1, 2.0),      # % 
            "CO2": random.uniform(12, 15),       # %
            "NOx": random.uniform(20, 200),      # ppm
            "HC": random.uniform(50, 300),       # ppm
            "O2": random.uniform(0.5, 2.0),      # %
            "PM2.5": random.uniform(5, 50)       # µg/m³
        }
        
        # Check compliance
        compliance = {
            "euro6": all([
                emissions_data["CO"] < 1.0,
                emissions_data["NOx"] < 80,
                emissions_data["HC"] < 100,
                emissions_data["PM2.5"] < 25
            ]),
            "euro5": all([
                emissions_data["CO"] < 1.5,
                emissions_data["NOx"] < 180,
                emissions_data["HC"] < 150
            ])
        }
        
        reading = SensorReading(
            sensor_id=self.sensor_id,
            sensor_type="emissions",
            timestamp=datetime.now(),
            value={
                "gases": emissions_data,
                "compliance": compliance,
                "air_fuel_ratio": 14.7 * (1 + random.uniform(-0.1, 0.1)),
                "catalyst_efficiency": random.uniform(85, 98),  # %
                "emissions_score": self._calculate_emissions_score(emissions_data)
            },
            unit="mixed",
            confidence=0.91,
            metadata={
                "sensor_types": self.gas_types,
                "temperature": random.uniform(180, 220)  # Celsius
            }
        )
        
        self.last_reading = reading
        if self.debug_mode:
            logger.debug(f"Emissions reading: CO={emissions_data['CO']:.2f}%, NOx={emissions_data['NOx']:.1f}ppm")
        
        return reading
    
    def _calculate_emissions_score(self, emissions: Dict) -> float:
        """Calculate overall emissions score (0-100)"""
        # Simple scoring based on emissions levels
        score = 100.0
        
        if emissions["CO"] > 1.0:
            score -= (emissions["CO"] - 1.0) * 10
        if emissions["NOx"] > 100:
            score -= (emissions["NOx"] - 100) / 10
        if emissions["HC"] > 100:
            score -= (emissions["HC"] - 100) / 20
        if emissions["PM2.5"] > 25:
            score -= (emissions["PM2.5"] - 25) / 5
            
        return max(0, min(100, score))
    
    async def calibrate(self) -> bool:
        """Calibrate emissions sensor"""
        logger.info(f"Calibrating emissions sensor {self.sensor_id}")
        # Calibrate with clean air
        await asyncio.sleep(3)
        self.calibration_data["zero_point"] = {gas: 0.0 for gas in self.gas_types}
        self.calibration_data["last_calibration"] = datetime.now().isoformat()
        return True


class SensorManager:
    """Manages all sensor modules"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.sensors: Dict[str, BaseSensor] = {}
        self.sensor_threads: Dict[str, asyncio.Task] = {}
        logger.info("SensorManager initialized")
        
    async def register_sensor(self, sensor: BaseSensor) -> bool:
        """Register a new sensor"""
        try:
            if await sensor.initialize():
                self.sensors[sensor.sensor_id] = sensor
                logger.info(f"Registered sensor: {sensor.sensor_id}")
                return True
            else:
                logger.error(f"Failed to register sensor: {sensor.sensor_id}")
                return False
        except Exception as e:
            logger.error(f"Error registering sensor {sensor.sensor_id}: {e}")
            return False
    
    async def start_all_sensors(self):
        """Start all registered sensors"""
        for sensor_id, sensor in self.sensors.items():
            await sensor.start()
            if self.debug_mode:
                # Start continuous reading in debug mode
                self.sensor_threads[sensor_id] = asyncio.create_task(
                    self._continuous_read(sensor)
                )
    
    async def _continuous_read(self, sensor: BaseSensor):
        """Continuously read from sensor (for debug/monitoring)"""
        while sensor.is_active:
            try:
                reading = await sensor.read()
                logger.debug(f"Continuous reading from {sensor.sensor_id}: confidence={reading.confidence}")
                await asyncio.sleep(1)  # Read interval
            except Exception as e:
                logger.error(f"Error in continuous read for {sensor.sensor_id}: {e}")
                await asyncio.sleep(5)
    
    async def stop_all_sensors(self):
        """Stop all sensors"""
        # Cancel continuous reading tasks
        for task in self.sensor_threads.values():
            task.cancel()
        
        # Stop sensors
        for sensor in self.sensors.values():
            await sensor.stop()
    
    async def read_sensor(self, sensor_id: str) -> Optional[SensorReading]:
        """Read from specific sensor"""
        if sensor_id in self.sensors:
            return await self.sensors[sensor_id].read()
        else:
            logger.warning(f"Sensor {sensor_id} not found")
            return None
    
    async def calibrate_all_sensors(self) -> Dict[str, bool]:
        """Calibrate all sensors"""
        results = {}
        for sensor_id, sensor in self.sensors.items():
            logger.info(f"Calibrating sensor: {sensor_id}")
            results[sensor_id] = await sensor.calibrate()
        return results
    
    def get_sensor_status(self) -> Dict[str, Dict]:
        """Get status of all sensors"""
        status = {}
        for sensor_id, sensor in self.sensors.items():
            status[sensor_id] = {
                "active": sensor.is_active,
                "error_count": sensor.error_count,
                "last_reading": sensor.last_reading.timestamp.isoformat() if sensor.last_reading else None,
                "calibrated": bool(sensor.calibration_data)
            }
        return status
    
    async def cleanup(self):
        """Cleanup all sensors"""
        await self.stop_all_sensors()
        for sensor in self.sensors.values():
            await sensor.cleanup()
        logger.info("SensorManager cleanup completed")


# Factory function to create sensor instances
def create_sensor(sensor_type: str, sensor_id: Optional[str] = None, debug_mode: bool = False) -> Optional[BaseSensor]:
    """Factory function to create sensor instances"""
    sensor_classes = {
        "thermal": ThermalSensor,
        "audio": AudioSensor,
        "vibration": VibrationSensor,
        "lidar": LiDARSensor,
        "emissions": EmissionsSensor
    }
    
    if sensor_type not in sensor_classes:
        logger.error(f"Unknown sensor type: {sensor_type}")
        return None
    
    sensor_id = sensor_id or f"{sensor_type}_01"
    return sensor_classes[sensor_type](sensor_id=sensor_id, debug_mode=debug_mode)
