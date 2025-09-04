import React from 'react';
import VehicleVisualization from './VehicleVisualization';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8030';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Motospect 3D Vehicle Scanner</h1>
      </header>
      <VehicleVisualization />
    </div>
  );
}

export default App;
