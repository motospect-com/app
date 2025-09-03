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
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const geometryRef = useRef(null);
  const materialRef = useRef(null);
  const pointsRef = useRef(null);
  const animationIdRef = useRef(null);

  const [scanData, setScanData] = useState(null);
  const [scanType, setScanType] = useState('N/A');
  const [scanId, setScanId] = useState(null);
  const [scanStatus, setScanStatus] = useState('idle');

  const httpBase =
    process.env.REACT_APP_BACKEND_HTTP_URL || `http://${window.location.hostname}:8084`;

  // WebSocket setup – prefers REACT_APP_... else fallback to window.hostname:8084
  useEffect(() => {
    const wsUrl =
      process.env.REACT_APP_BACKEND_WS_URL || `ws://${window.location.hostname}:8084/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      // eslint-disable-next-line no-console
      console.info('[WS] connected', wsUrl);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setScanData(data);
      setScanType(data.scan_type || 'N/A');
    };

    ws.onerror = (e) => {
      // eslint-disable-next-line no-console
      console.warn('[WS] error', e);
    };

    ws.onclose = () => {
      // eslint-disable-next-line no-console
      console.info('[WS] closed');
    };

    return () => {
      try {
        ws.close();
      } catch (_) {}
    };
  }, []);

  // Initialize Three.js once
  useEffect(() => {
    if (!mountRef.current || sceneRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 150;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mountRef.current.appendChild(renderer.domElement);

    const geometry = new THREE.BufferGeometry();
    const material = new THREE.PointsMaterial({ size: 0.5, vertexColors: true });
    const points = new THREE.Points(geometry, material);
    scene.add(points);

    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    geometryRef.current = geometry;
    materialRef.current = material;
    pointsRef.current = points;

    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      if (pointsRef.current) {
        pointsRef.current.rotation.x += 0.001;
        pointsRef.current.rotation.y += 0.001;
      }
      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!mountRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      rendererRef.current.setSize(w, h);
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationIdRef.current) cancelAnimationFrame(animationIdRef.current);
      if (pointsRef.current) {
        if (geometryRef.current) geometryRef.current.dispose();
        if (materialRef.current) materialRef.current.dispose();
      }
      if (rendererRef.current && rendererRef.current.domElement && mountRef.current) {
        try {
          mountRef.current.removeChild(rendererRef.current.domElement);
        } catch (_) {}
        rendererRef.current.dispose?.();
      }
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
      geometryRef.current = null;
      materialRef.current = null;
      pointsRef.current = null;
    };
  }, []);

  // Update buffers when new scanData arrives
  useEffect(() => {
    if (!scanData || !geometryRef.current) return;

    const pointsFlat = new Float32Array(scanData.points.flat());
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

    const geometry = geometryRef.current;
    // If attributes do not exist or sizes changed, create new attributes
    const posAttr = geometry.getAttribute('position');
    if (!posAttr || posAttr.array.length !== pointsFlat.length) {
      geometry.setAttribute('position', new THREE.BufferAttribute(pointsFlat, 3));
    } else {
      posAttr.array.set(pointsFlat);
      posAttr.needsUpdate = true;
    }

    const colorAttr = geometry.getAttribute('color');
    if (!colorAttr || colorAttr.array.length !== colors.length) {
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    } else {
      colorAttr.array.set(colors);
      colorAttr.needsUpdate = true;
    }

    geometry.computeBoundingSphere();
  }, [scanData]);

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
        <button
          onClick={async () => {
            try {
              setScanStatus('starting');
              const res = await fetch(`${httpBase}/api/scan/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vehicle_id: 'DEMO' }),
              });
              const json = await res.json();
              setScanId(json.scan_id);
              setScanStatus(json.status || 'scanning');
            } catch (e) {
              // eslint-disable-next-line no-console
              console.error('Start scan failed', e);
              setScanStatus('error');
            }
          }}
        >
          Start scan
        </button>

        <button
          onClick={async () => {
            if (!scanId) return;
            try {
              const res = await fetch(`${httpBase}/api/scan/stop/${scanId}`, { method: 'POST' });
              const json = await res.json();
              setScanStatus(json.status || 'stopped');
            } catch (e) {
              // eslint-disable-next-line no-console
              console.error('Stop scan failed', e);
              setScanStatus('error');
            }
          }}
          disabled={!scanId}
        >
          Stop scan
        </button>

        <span style={{ fontFamily: 'monospace' }}>
          status: {scanStatus} {scanId ? `| id: ${scanId}` : ''}
        </span>
        <span style={{ marginLeft: 'auto' }}>
          typ skanu: <b>{scanType.replace('_', ' ').toUpperCase()}</b>
        </span>
      </div>

      <div ref={mountRef} style={{ width: '100%', height: '80vh' }} />
    </div>
  );
};

export default VehicleVisualization;
