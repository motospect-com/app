import unittest
from backend.data_generator import (
    generate_tof_scan_data,
    generate_thermal_scan_data,
    generate_uv_scan_data,
    generate_paint_thickness_data,
    generate_audio_data,
    generate_scan_data
)


class TestDataGenerator(unittest.TestCase):

    def test_generate_tof_scan_data(self):
        data = generate_tof_scan_data()
        self.assertEqual(data['scan_type'], 'tof')
        self.assertIn('points', data)
        self.assertIn('colors', data)
        self.assertEqual(len(data['points']), 1000)

    def test_generate_thermal_scan_data(self):
        data = generate_thermal_scan_data()
        self.assertEqual(data['scan_type'], 'thermal')
        self.assertIn('points', data)
        self.assertIn('temperatures', data)
        self.assertEqual(len(data['points']), 1000)

    def test_generate_uv_scan_data(self):
        data = generate_uv_scan_data()
        self.assertEqual(data['scan_type'], 'uv')
        self.assertIn('points', data)
        self.assertIn('intensity', data)
        self.assertEqual(len(data['points']), 1000)

    def test_generate_paint_thickness_data(self):
        data = generate_paint_thickness_data()
        self.assertEqual(data['scan_type'], 'paint_thickness')
        self.assertIn('points', data)
        self.assertIn('thickness', data)
        self.assertEqual(len(data['points']), 1000)

    def test_generate_audio_data(self):
        data = generate_audio_data()
        self.assertEqual(data['scan_type'], 'audio')
        self.assertIn('level', data)
        self.assertIn('spectrum', data)
        self.assertEqual(len(data['spectrum']), 64)

    def test_generate_scan_data(self):
        data = generate_scan_data()
        self.assertIn('scan_type', data)
        valid_types = ['tof', 'thermal', 'uv', 'paint_thickness', 'audio']
        self.assertIn(data['scan_type'], valid_types)


if __name__ == '__main__':
    unittest.main()
