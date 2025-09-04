const config = {
  // Backend API URL
  apiUrl: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8030',
  
  // WebSocket URL for real-time updates
  wsUrl: process.env.REACT_APP_BACKEND_WS_URL || 'ws://localhost:8030/ws',
  
  // MQTT Configuration
  mqtt: {
    // Use the correct WebSocket port (9001) as defined in mosquitto.conf
    url: process.env.REACT_APP_MQTT_URL || 'ws://motospect-mosquitto:9001',
    baseTopic: process.env.REACT_APP_MQTT_BASE_TOPIC || 'motospect/v1',
    username: process.env.REACT_APP_MQTT_USERNAME || 'motospect',
    password: process.env.REACT_APP_MQTT_PASSWORD || 'motospect123'
  }
};

export default config;
