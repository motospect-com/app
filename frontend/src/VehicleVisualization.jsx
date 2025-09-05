import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Client as MqttClient } from 'paho-mqtt';
import SpectrumSVG from './components/SpectrumSVG';
import ToFProfileSVG from './components/ToFProfileSVG';
import config from './config';

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
  const [selectedChannel, setSelectedChannel] = useState('tof');
  const selectedChannelRef = useRef('tof');

  // Per-channel last frames for Live panels
  const [tofData, setTofData] = useState(null);
  const [thermalData, setThermalData] = useState(null);
  const [paintData, setPaintData] = useState(null);
  const [audioData, setAudioData] = useState(null);

  // Canvas refs for panels
  const thermalCanvasRef = useRef(null);

  useEffect(() => {
    selectedChannelRef.current = selectedChannel;
  }, [selectedChannel]);

    // Backend base URL – prefer explicit env var, fallback to current hostname:8000
  const backendUrl = process.env.REACT_APP_BACKEND_URL || `http://${window.location.hostname}:8000`;
  const httpBase = backendUrl;
  const useMqtt = String(process.env.REACT_APP_USE_MQTT || 'false') === 'true';
    const mqttUrl = process.env.REACT_APP_MQTT_URL || `ws://${window.location.hostname}:9002`;
  const mqttBaseTopic = process.env.REACT_APP_MQTT_BASE_TOPIC || 'motospect/v1';

  // Data ingress via WebSocket (fallback when MQTT is disabled)
  useEffect(() => {
    if (useMqtt) return undefined;
    
    // Use WebSocket URL from config
    const ws = new WebSocket(config.wsUrl);
    console.log(`[WebSocket] Connecting to ${config.wsUrl}`);

    ws.onopen = () => {
      console.info('[WS] connected to', config.wsUrl);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const channel = data.channel || data.scan_type || 'unknown';
      // Store per-channel last frames for Live panels
      switch (channel) {
        case 'tof':
          setTofData(data);
          break;
        case 'thermal':
          setThermalData(data);
          break;
        case 'uv':
          // UV data is no longer used, but we'll keep the case for future use
          // setUvData(data);
          break;
        case 'paint_thickness':
          setPaintData(data);
          break;
        case 'audio':
          setAudioData(data);
          break;
        default:
          break;
      }
      if (channel === selectedChannelRef.current) {
        setScanData(data);
        setScanType(data.scan_type || 'N/A');
      }
    };

    ws.onerror = (e) => {
      console.warn('[WS] error', e);
    };

    ws.onclose = () => {
      console.info('[WS] closed');
    };

    return () => {
      try {
        ws.close();
      } catch (_) {}
    };
  }, [useMqtt]);

  // Data ingress via MQTT (preferred when enabled)
  useEffect(() => {
    let client = null;
    let isMounted = true;
    let reconnectTimeout = null;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;
    const RECONNECT_DELAY = 5000; // 5 seconds
    
    const connectMqtt = () => {
      if (!isMounted) return;
      
      // Clear any existing connection
      if (client) {
        try {
          if (client.isConnected()) {
            console.log('[MQTT] Disconnecting existing client...');
            client.disconnect();
          }
        } catch (e) {
          console.warn('[MQTT] Error disconnecting existing client:', e);
        }
      }
      
      try {
        console.log('[MQTT] Connecting to', config.mqtt.url);
        
        // Parse the WebSocket URL to extract host, port, and path
        const mqttUrl = new URL(config.mqtt.url);
        const host = mqttUrl.hostname;
        const port = mqttUrl.port || (mqttUrl.protocol === 'wss:' ? 443 : 80);
        const path = mqttUrl.pathname || '/mqtt';
        
        // Use the client ID from config or generate a new one
        const clientId = config.mqtt.clientId || `motospect-ui-${Math.random().toString(16).substr(2, 8)}`;
        
        console.log(`[MQTT] Creating client with ID: ${clientId}`);
        
        // Create MQTT client with explicit WebSocket options
        client = new MqttClient(host, Number(port), path, clientId);
        
        // Configure WebSocket options
        const wsOptions = {
          protocol: 'mqtt',
          rejectUnauthorized: false // Only for development with self-signed certificates
        };
        
        // Set WebSocket options if using WebSocket transport
        if (path && (path.includes('ws') || path.includes('wss'))) {
          client.connectOptions = {
            ...client.connectOptions,
            useSSL: mqttUrl.protocol === 'wss:',
            protocol: mqttUrl.protocol.replace(':', ''),
            wsOptions: wsOptions
          };
        }
        
        // Set callback handlers
        client.onConnectionLost = (responseObject) => {
          if (responseObject.errorCode !== 0) {
            console.error('[MQTT] Connection lost:', responseObject.errorMessage);
          }
          // Only attempt to reconnect if component is still mounted and we haven't exceeded max attempts
          if (isMounted && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            const delay = Math.min(RECONNECT_DELAY * reconnectAttempts, 30000); // Max 30s delay
            console.log(`[MQTT] Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}) in ${delay}ms...`);
            reconnectTimeout = setTimeout(connectMqtt, delay);
          } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            console.error('[MQTT] Max reconnection attempts reached. Please refresh the page to try again.');
            // Reset reconnect attempts after a longer delay
            setTimeout(() => {
              reconnectAttempts = 0;
            }, 60000); // Reset after 1 minute
          }
        };
        
        // Handle connection success
        const onConnect = () => {
          if (!isMounted) {
            if (client && client.isConnected()) client.disconnect();
            return;
          }
          console.log('[MQTT] Connected successfully to', config.mqtt.url);
          reconnectAttempts = 0; // Reset reconnect counter on successful connection
          
          // Subscribe to topics after successful connection
          try {
            const topic = `${config.mqtt.baseTopic}/#`;
            client.subscribe(topic, { qos: 0 });
            console.log(`[MQTT] Subscribed to topic: ${topic}`);
          } catch (error) {
            console.error('[MQTT] Error subscribing to topics:', error);
          }
        };
        
        // Handle connection failure
        const onFailure = (error) => {
          console.error('[MQTT] Connection failed:', error.errorMessage);
          // Only attempt to reconnect if component is still mounted
          if (isMounted) {
            reconnectTimeout = setTimeout(connectMqtt, 5000);
          }
        };
        
        // Set up connection options
        const connectOptions = {
          onSuccess: onConnect,
          onFailure: onFailure,
          userName: config.mqtt.username,
          password: config.mqtt.password,
          useSSL: mqttUrl.protocol === 'wss:',
          reconnect: false, // We handle reconnection manually
          keepAliveInterval: 30,
          cleanSession: true,
          mqttVersion: 4, // Use MQTT 3.1.1
          protocol: mqttUrl.protocol.replace(':', ''),
          wsOptions: {
            protocol: 'mqtt',
            rejectUnauthorized: false // Only for development
          }
        };
        
        // Connect to the broker
        console.log('[MQTT] Connecting with options:', {
          ...connectOptions,
          password: '***' // Don't log the actual password
        });
        
        try {
          client.connect(connectOptions);
        } catch (error) {
          console.error('[MQTT] Error during connect:', error);
          if (isMounted) {
            reconnectTimeout = setTimeout(connectMqtt, 5000);
          }
        }
        
        client.onMessageArrived = (message) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(message.payloadString);
            console.log('[MQTT] Message received on', message.destinationName, ':', data);
            // Handle the incoming MQTT message
            const channel = data.channel || data.scan_type || 'unknown';
            switch (channel) {
              case 'tof':
                setTofData(data);
                break;
              case 'thermal':
                setThermalData(data);
                break;
              case 'uv':
                // UV data is no longer used, but we'll keep the case for future use
                // setUvData(data);
                break;
              case 'paint_thickness':
                setPaintData(data);
                break;
              case 'audio':
                setAudioData(data);
                break;
              default:
                break;
            }
            if (channel === selectedChannelRef.current) {
              setScanData(data);
              setScanType(data.scan_type || 'N/A');
            }
          } catch (error) {
            console.error('[MQTT] Error parsing message:', error);
          }
        };
        
        // Connect to the MQTT broker
        client.connect({
          onSuccess: () => {
            if (!isMounted) {
              if (client && client.isConnected()) client.disconnect();
              return;
            }
            console.log('[MQTT] Connected successfully to', config.mqtt.url);
            // Subscribe to topics after successful connection
            try {
              client.subscribe(`${mqttBaseTopic}/+`, { qos: 0 });
              console.log(`[MQTT] Subscribed to ${mqttBaseTopic}/+`);
            } catch (error) {
              console.error('[MQTT] Error subscribing to topics:', error);
            }
          },
          onFailure: (error) => {
            console.error('[MQTT] Connection failed:', error.errorMessage);
            // Only attempt to reconnect if component is still mounted
            if (isMounted) {
              reconnectTimeout = setTimeout(connectMqtt, 5000);
            }
          },
          userName: config.mqtt.username,
          password: config.mqtt.password,
          useSSL: mqttUrl.protocol === 'wss:',
          reconnect: false, // We handle reconnection manually
          keepAliveInterval: 30,
          cleanSession: true,
          mqttVersion: 4, // Use MQTT 3.1.1
        });
        
      } catch (error) {
        console.error('[MQTT] Error in MQTT setup:', error);
        // Only attempt to reconnect if component is still mounted
        if (isMounted) {
          reconnectTimeout = setTimeout(connectMqtt, 5000);
        }
      }
    };

    // Start connection attempt
    connectMqtt();

    // Cleanup function
    return () => {
      isMounted = false;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (mqttClient && mqttClient.isConnected()) {
        try {
          mqttClient.disconnect();
        } catch (_) {}
      }
    };
  }, [useMqtt, mqttUrl, mqttBaseTopic]);

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

    // Store the current ref values in the effect's closure
    const currentMountRef = mountRef.current;
    const currentRendererRef = rendererRef.current;
    const currentGeometryRef = geometryRef.current;
    const currentMaterialRef = materialRef.current;
    const currentAnimationId = animationIdRef.current;
    const currentPointsRef = pointsRef.current;
    
    return () => {
      window.removeEventListener('resize', handleResize);
      if (currentAnimationId) cancelAnimationFrame(currentAnimationId);
      if (currentPointsRef) {
        if (currentGeometryRef) currentGeometryRef.dispose();
        if (currentMaterialRef) currentMaterialRef.dispose();
      }
      if (currentRendererRef?.domElement && currentMountRef) {
        try {
          currentMountRef.removeChild(currentRendererRef.domElement);
        } catch (_) {}
        currentRendererRef.dispose?.();
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

  // Draw thermal heatmap when thermalData changes
  useEffect(() => {
    if (!thermalData || !thermalCanvasRef.current) return;
    const canvas = thermalCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const temps = thermalData.temperatures || [];
    if (temps.length === 0) return;

    // Map 1000 samples to a 32x32 grid (approx.)
    const gridW = 32;
    const gridH = 32;
    const total = gridW * gridH;
    const vals = new Array(total).fill(0);
    for (let i = 0; i < total; i += 1) {
      vals[i] = temps[i % temps.length];
    }
    const minV = 20;
    const maxV = 100;

    const cellW = W / gridW;
    const cellH = H / gridH;
    for (let gy = 0; gy < gridH; gy += 1) {
      for (let gx = 0; gx < gridW; gx += 1) {
        const v = vals[gy * gridW + gx];
        const t = Math.max(0, Math.min(1, (v - minV) / (maxV - minV)));
        const color = new THREE.Color().setHSL(0.7 * (1 - t), 1, 0.5);
        ctx.fillStyle = `rgb(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)})`;
        ctx.fillRect(gx * cellW, gy * cellH, Math.ceil(cellW), Math.ceil(cellH));
      }
    }
  }, [thermalData]);

  // Memoized derived arrays for SVG components
  const tofDistances = React.useMemo(() => {
    const pts = tofData?.points || [];
    if (!pts.length) return [];
    const arr = pts.slice(0, 300).map((p) => Math.sqrt(p[0] * p[0] + p[1] * p[1] + p[2] * p[2]));
    return arr;
  }, [tofData]);
  const audioSpectrum = audioData?.spectrum || [];

  // Minimal anomaly detection banner
  const anomalies = [];
  if (thermalData?.temperatures?.some((t) => t > 80)) anomalies.push('Thermal: hotspot > 80°C');
  if (audioData?.level && audioData.level > 0.85) anomalies.push('Audio: high level');
  if (audioData?.spectrum?.some((v) => v > 0.9)) anomalies.push('Audio: strong peak');
  if (tofData?.points?.some((p) => p[2] < 10)) anomalies.push('ToF: object too close');
  if (paintData?.thickness?.some((th) => th < 90 || th > 190)) anomalies.push('Paint: out of range');

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {['tof', 'thermal', 'uv', 'paint_thickness'].map((ch) => (
            <button
              key={ch}
              onClick={() => setSelectedChannel(ch)}
              style={{
                padding: '6px 10px',
                border: '1px solid #ccc',
                background: selectedChannel === ch ? '#1976d2' : '#f5f5f5',
                color: selectedChannel === ch ? 'white' : 'black',
                borderRadius: 4,
                cursor: 'pointer',
              }}
              title={`Pokaż kanał: ${ch}`}
            >
              {ch}
            </button>
          ))}
        </div>

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
          status: {scanStatus} {scanId ? `| id: ${scanId}` : ''} | channel: {selectedChannel}
        </span>
        <span style={{ marginLeft: 'auto' }}>
          typ skanu: <b>{scanType.replace('_', ' ').toUpperCase()}</b>
        </span>
      </div>

      {anomalies.length > 0 && (
        <div
          style={{
            background: '#ffebee',
            color: '#c62828',
            border: '1px solid #ef9a9a',
            padding: '8px 12px',
            borderRadius: 6,
            marginBottom: 10,
          }}
        >
          <b>Alerty:</b> {anomalies.join(' · ')}
        </div>
      )}

      <div ref={mountRef} style={{ width: '100%', height: '60vh', marginBottom: 12 }} />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 12,
        }}
      >
        <div style={{ border: '1px solid #eee', borderRadius: 6, padding: 8 }}>
          <div style={{ marginBottom: 6 }}><b>Thermal heatmap</b></div>
          <canvas ref={thermalCanvasRef} width={320} height={160} style={{ width: '100%' }} />
        </div>

        <div style={{ border: '1px solid #eee', borderRadius: 6, padding: 8 }}>
          <div style={{ marginBottom: 6 }}><b>ToF profile</b></div>
          <ToFProfileSVG values={tofDistances} width={320} height={160} />
        </div>

        <div style={{ border: '1px solid #eee', borderRadius: 6, padding: 8 }}>
          <div style={{ marginBottom: 6, display: 'flex', alignItems: 'center', gap: 10 }}>
            <b>Audio</b>
            <div
              title={`level: ${Math.round((audioData?.level || 0) * 100)}%`}
              style={{
                flex: 1,
                height: 10,
                background: '#eee',
                borderRadius: 4,
                position: 'relative',
              }}
            >
              <div
                style={{
                  width: `${Math.min(100, Math.max(0, (audioData?.level || 0) * 100))}%`,
                  height: '100%',
                  background: '#4caf50',
                  borderRadius: 4,
                }}
              />
            </div>
          </div>
          <SpectrumSVG values={audioSpectrum} width={320} height={100} />
        </div>
      </div>
    </div>
  );
};

export default VehicleVisualization;
