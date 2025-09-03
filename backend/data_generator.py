import numpy as np
import random


def generate_tof_scan_data():
    """Generuje przykładowe dane skanowania z czujnika ToF."""
    num_points = 1000
    points = np.random.rand(num_points, 3) * 100
    colors = np.random.randint(0, 255, size=(num_points, 3))
    return {
        'scan_type': 'tof',
        'points': points.tolist(),
        'colors': colors.tolist()
    }

def generate_thermal_scan_data():
    """Generuje przykładowe dane skanowania z kamery termowizyjnej."""
    num_points = 1000
    points = np.random.rand(num_points, 3) * 100
    temperatures = np.random.uniform(20.0, 100.0, size=num_points)
    return {
        'scan_type': 'thermal',
        'points': points.tolist(),
        'temperatures': temperatures.tolist()
    }

def generate_uv_scan_data():
    """Generuje przykładowe dane skanowania w świetle UV."""
    num_points = 1000
    points = np.random.rand(num_points, 3) * 100
    uv_intensity = np.random.uniform(0.0, 1.0, size=num_points)
    return {
        'scan_type': 'uv',
        'points': points.tolist(),
        'intensity': uv_intensity.tolist()
    }

def generate_paint_thickness_data():
    """Generuje przykładowe dane o grubości lakieru."""
    num_points = 1000
    points = np.random.rand(num_points, 3) * 100
    thickness = np.random.uniform(80.0, 200.0, size=num_points)
    return {
        'scan_type': 'paint_thickness',
        'points': points.tolist(),
        'thickness': thickness.tolist()
    }

def generate_scan_data():
    """Generuje losowy typ danych skanowania."""
    scan_functions = [
        generate_tof_scan_data,
        generate_thermal_scan_data,
        generate_uv_scan_data,
        generate_paint_thickness_data
    ]
    return random.choice(scan_functions)()

