import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

// Funkcja pomocnicza do mapowania wartości na kolor w gradiencie
const mapValueToColor = (value, min, max) => {
  const t = (value - min) / (max - min);
  const color = new THREE.Color();
  color.setHSL(0.7 * (1 - t), 1, 0.5);
  return color;
};

const VehicleVisualization = () => {
  const mountRef = useRef(null);
  const [scanData, setScanData] = useState(null);
  const [scanType, setScanType] = useState('N/A');

  useEffect(() => {
    const wsUrl = process.env.REACT_APP_BACKEND_WS_URL || 'ws://localhost:8080/ws';
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setScanData(data);
      setScanType(data.scan_type || 'N/A');
    };

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (!scanData || !mountRef.current) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, mountRef.current.clientWidth / mountRef.current.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });

    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    mountRef.current.innerHTML = ''; // Wyczyść poprzednią scenę
    mountRef.current.appendChild(renderer.domElement);

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(scanData.points.flat());
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const colors = new Float32Array(scanData.points.length * 3);
    let minVal, maxVal;

    switch (scanData.scan_type) {
      case 'thermal':
        minVal = 20;
        maxVal = 100;
        scanData.temperatures.forEach((temp, i) => {
          const color = mapValueToColor(temp, minVal, maxVal);
          colors[i * 3] = color.r;
          colors[i * 3 + 1] = color.g;
          colors[i * 3 + 2] = color.b;
        });
        break;
      case 'uv':
        minVal = 0;
        maxVal = 1;
        scanData.intensity.forEach((val, i) => {
          const color = new THREE.Color().setHSL(0.75, val, 0.5);
          colors[i * 3] = color.r;
          colors[i * 3 + 1] = color.g;
          colors[i * 3 + 2] = color.b;
        });
        break;
      case 'paint_thickness':
        minVal = 80;
        maxVal = 200;
        scanData.thickness.forEach((thick, i) => {
          const color = mapValueToColor(thick, minVal, maxVal);
          colors[i * 3] = color.r;
          colors[i * 3 + 1] = color.g;
          colors[i * 3 + 2] = color.b;
        });
        break;
      case 'tof':
      default:
        scanData.colors.forEach((c, i) => {
          colors[i * 3] = c[0] / 255;
          colors[i * 3 + 1] = c[1] / 255;
          colors[i * 3 + 2] = c[2] / 255;
        });
        break;
    }

    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({ size: 0.5, vertexColors: true });
    const points = new THREE.Points(geometry, material);
    scene.add(points);

    camera.position.z = 150;

    const animate = () => {
      requestAnimationFrame(animate);
      points.rotation.x += 0.001;
      points.rotation.y += 0.001;
      renderer.render(scene, camera);
    };

    animate();

    const currentMount = mountRef.current;
    return () => {
      if (currentMount && renderer.domElement) {
        currentMount.removeChild(renderer.domElement);
      }
    };
  }, [scanData]);

  return (
    <div>
      <h3>Aktualny typ skanu: {scanType.replace('_', ' ').toUpperCase()}</h3>
      <div ref={mountRef} style={{ width: '100%', height: '80vh' }} />
    </div>
  );
};

export default VehicleVisualization;
