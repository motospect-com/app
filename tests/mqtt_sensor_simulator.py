#!/usr/bin/env python3
"""
MQTT Sensor Simulator for MotoSpect
Simulates all sensor channels: OBD, Audio, Thermal, TOF
"""

import json
import time
import random
import argparse
from datetime import datetime
import paho.mqtt.client as mqtt
from typing import Dict, Any

class SensorSimulator:
    """Simulates vehicle sensor data over MQTT"""
    
    def __init__(self, broker_host='localhost', broker_port=1883, base_topic='motospect/v1'):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.base_topic = base_topic
        self.client = mqtt.Client(client_id=f"sensor-simulator-{random.randint(1000, 9999)}")
        self.connected = False
        self.test_vin = '1HGBH41JXMN109186'
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.connected = True
        else:
            print(f"✗ Connection failed with code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        print(f"Disconnected from broker (code: {rc})")
        self.connected = False
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            time.sleep(1)  # Wait for connection
            return self.connected
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def generate_obd_data(self, scan_id: str) -> Dict[str, Any]:
        """Generate realistic OBD sensor data"""
        # Simulate engine running conditions
        rpm = 800 + random.randint(0, 3200)
        speed = min(120, rpm * 0.03)  # Rough speed calculation
        
        data = {
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat(),
            'channel': 'obd',
            'vin': self.test_vin,
            'parameters': {
                'rpm': rpm,
                'engine_temp': 75 + random.randint(0, 40),  # 75-115°C
                'oil_pressure': 30 + random.randint(0, 30),  # 30-60 PSI
                'fuel_pressure': 350 + random.randint(0, 80),  # 350-430 kPa
                'battery_voltage': 13.5 + random.random() * 1.5,  # 13.5-15V
                'throttle_position': random.randint(0, 100),  # 0-100%
                'maf_rate': 5 + random.random() * 20,  # 5-25 g/s
                'o2_voltage': 0.1 + random.random() * 0.8,  # 0.1-0.9V
                'vehicle_speed': speed,
                'intake_temp': 20 + random.randint(0, 40),  # 20-60°C
                'fuel_level': random.randint(10, 100),  # 10-100%
            },
            'fault_codes': [],
            'freeze_frame': {}
        }
        
        # Randomly add fault codes
        if random.random() > 0.7:
            codes = ['P0301', 'P0171', 'P0420', 'P0442', 'B1234', 'C0035']
            num_codes = random.randint(1, 3)
            data['fault_codes'] = random.sample(codes, num_codes)
            
            # Add freeze frame data for first code
            if data['fault_codes']:
                data['freeze_frame'][data['fault_codes'][0]] = {
                    'rpm': rpm + random.randint(-200, 200),
                    'engine_temp': data['parameters']['engine_temp'],
                    'vehicle_speed': speed
                }
        
        return data
    
    def generate_audio_data(self, scan_id: str) -> Dict[str, Any]:
        """Generate audio spectrum data"""
        frequencies = [100, 250, 500, 1000, 2000, 4000, 8000]
        base_amplitude = 40
        
        # Generate frequency amplitudes with some variation
        amplitudes = [
            base_amplitude + random.randint(-10, 20) for _ in frequencies
        ]
        
        # Find peak
        peak_idx = amplitudes.index(max(amplitudes))
        
        data = {
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat(),
            'channel': 'audio',
            'frequencies': frequencies,
            'amplitudes': amplitudes,
            'peak_frequency': frequencies[peak_idx],
            'peak_amplitude': amplitudes[peak_idx],
            'noise_level': base_amplitude + random.randint(0, 15),
            'anomalies': []
        }
        
        # Randomly add anomalies
        if random.random() > 0.6:
            anomalies = ['bearing_noise', 'exhaust_leak', 'belt_squeal', 'knocking']
            data['anomalies'] = random.sample(anomalies, random.randint(1, 2))
        
        return data
    
    def generate_thermal_data(self, scan_id: str) -> Dict[str, Any]:
        """Generate thermal camera data"""
        # Base temperatures for different zones
        engine_temp = 85 + random.randint(0, 30)
        exhaust_temp = 250 + random.randint(0, 100)
        brake_temp_front = 80 + random.randint(0, 80)
        brake_temp_rear = 60 + random.randint(0, 60)
        trans_temp = 60 + random.randint(0, 30)
        
        zones = {
            'engine': {
                'temp': engine_temp,
                'status': 'high' if engine_temp > 105 else 'normal'
            },
            'exhaust': {
                'temp': exhaust_temp,
                'status': 'high' if exhaust_temp > 320 else 'normal'
            },
            'brakes_front': {
                'temp': brake_temp_front,
                'status': 'high' if brake_temp_front > 140 else 'normal'
            },
            'brakes_rear': {
                'temp': brake_temp_rear,
                'status': 'high' if brake_temp_rear > 120 else 'normal'
            },
            'transmission': {
                'temp': trans_temp,
                'status': 'high' if trans_temp > 85 else 'normal'
            }
        }
        
        temps = [z['temp'] for z in zones.values()]
        
        data = {
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat(),
            'channel': 'thermal',
            'zones': zones,
            'max_temp': max(temps),
            'min_temp': min(temps),
            'avg_temp': sum(temps) / len(temps),
            'hotspots': []
        }
        
        # Add hotspots if any zone is high
        for zone, info in zones.items():
            if info['status'] == 'high':
                data['hotspots'].append({'zone': zone, 'temp': info['temp']})
        
        return data
    
    def generate_tof_data(self, scan_id: str) -> Dict[str, Any]:
        """Generate Time-of-Flight sensor data"""
        data = {
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat(),
            'channel': 'tof',
            'measurements': {
                'ground_clearance': 150 + random.randint(0, 50),  # 150-200mm
                'tire_tread_depth': {
                    'front_left': 6 + random.random() * 4,  # 6-10mm
                    'front_right': 6 + random.random() * 4,
                    'rear_left': 5 + random.random() * 4,  # 5-9mm
                    'rear_right': 5 + random.random() * 4
                },
                'brake_pad_thickness': {
                    'front_left': 7 + random.random() * 5,  # 7-12mm
                    'front_right': 7 + random.random() * 5,
                    'rear_left': 6 + random.random() * 4,  # 6-10mm
                    'rear_right': 6 + random.random() * 4
                },
                'suspension_height': {
                    'front_left': 300 + random.randint(-20, 20),
                    'front_right': 300 + random.randint(-20, 20),
                    'rear_left': 320 + random.randint(-20, 20),
                    'rear_right': 320 + random.randint(-20, 20)
                }
            }
        }
        
        return data
    
    def publish_sensor_data(self, scan_id: str, channels: list = None):
        """Publish sensor data for specified channels"""
        if not self.connected:
            print("✗ Not connected to broker")
            return False
        
        if channels is None:
            channels = ['obd', 'audio', 'thermal', 'tof']
        
        results = {}
        
        for channel in channels:
            try:
                # Generate data based on channel
                if channel == 'obd':
                    data = self.generate_obd_data(scan_id)
                elif channel == 'audio':
                    data = self.generate_audio_data(scan_id)
                elif channel == 'thermal':
                    data = self.generate_thermal_data(scan_id)
                elif channel == 'tof':
                    data = self.generate_tof_data(scan_id)
                else:
                    print(f"✗ Unknown channel: {channel}")
                    continue
                
                # Publish to MQTT
                topic = f"{self.base_topic}/{channel}"
                payload = json.dumps(data)
                result = self.client.publish(topic, payload, qos=1)
                
                if result.rc == 0:
                    print(f"✓ Published {channel} data to {topic}")
                    results[channel] = True
                else:
                    print(f"✗ Failed to publish {channel} data")
                    results[channel] = False
                    
                time.sleep(0.1)  # Small delay between publishes
                
            except Exception as e:
                print(f"✗ Error publishing {channel} data: {e}")
                results[channel] = False
        
        return results
    
    def simulate_continuous(self, scan_id: str, duration: int = 60, interval: int = 5):
        """Continuously simulate sensor data"""
        print(f"\nStarting continuous simulation for {duration} seconds...")
        print(f"Publishing every {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while time.time() - start_time < duration:
                iteration += 1
                print(f"\n--- Iteration {iteration} ---")
                
                # Publish all sensor data
                self.publish_sensor_data(scan_id)
                
                # Wait for next iteration
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nSimulation stopped by user")
        
        elapsed = time.time() - start_time
        print(f"\nSimulation complete. Duration: {elapsed:.1f} seconds")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            print("Disconnected from MQTT broker")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='MQTT Sensor Simulator for MotoSpect')
    parser.add_argument('--host', default='localhost', help='MQTT broker host')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--topic', default='motospect/v1', help='Base MQTT topic')
    parser.add_argument('--scan-id', default=f'sim-{int(time.time())}', help='Scan ID')
    parser.add_argument('--duration', type=int, default=60, help='Simulation duration (seconds)')
    parser.add_argument('--interval', type=int, default=5, help='Publishing interval (seconds)')
    parser.add_argument('--single', action='store_true', help='Single publish and exit')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("   MQTT SENSOR SIMULATOR")
    print("="*60)
    print(f"Broker: {args.host}:{args.port}")
    print(f"Topic: {args.topic}")
    print(f"Scan ID: {args.scan_id}")
    print("="*60)
    
    # Create simulator
    simulator = SensorSimulator(args.host, args.port, args.topic)
    
    # Connect to broker
    if not simulator.connect():
        print("✗ Failed to connect to MQTT broker")
        return 1
    
    # Run simulation
    if args.single:
        print("\nPublishing single data set...")
        simulator.publish_sensor_data(args.scan_id)
    else:
        simulator.simulate_continuous(args.scan_id, args.duration, args.interval)
    
    # Cleanup
    simulator.disconnect()
    return 0

if __name__ == "__main__":
    exit(main())
