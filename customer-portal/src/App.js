import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import QRCode from 'qrcode';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8084';
const REPORT_URL = process.env.REACT_APP_REPORT_URL || 'http://localhost:3050';

function App() {
  const [stage, setStage] = useState('welcome'); // welcome, vin, scanning, complete
  const [vin, setVin] = useState('');
  const [vehicleData, setVehicleData] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanPosition, setScanPosition] = useState(0);
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [reportId, setReportId] = useState('');
  const [error, setError] = useState('');

  // Simulate scanning progress
  useEffect(() => {
    if (stage === 'scanning') {
      const interval = setInterval(() => {
        setScanProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            handleScanComplete();
            return 100;
          }
          return prev + 2;
        });
        setScanPosition(prev => prev + 2);
      }, 100);
      return () => clearInterval(interval);
    }
  }, [stage]);

  const handleVinSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      // Validate and decode VIN
      const response = await axios.post(`${BACKEND_URL}/api/vehicle/decode`, { vin });
      setVehicleData(response.data);
      
      // Start scanning simulation
      setStage('scanning');
      setScanProgress(0);
      setScanPosition(0);
      
      // Initiate actual scan
      await axios.post(`${BACKEND_URL}/api/scan/start`, { 
        vin, 
        scan_type: 'comprehensive' 
      });
    } catch (err) {
      setError('Invalid VIN or vehicle not supported. Please try again.');
    }
  };

  const handleScanComplete = async () => {
    try {
      // Get scan results and generate report
      const response = await axios.post(`${BACKEND_URL}/api/report/generate`, {
        vin: vin,
        vehicle: vehicleData
      });
      
      const reportId = response.data.report_id;
      setReportId(reportId);
      
      // Generate QR code for report access
      const reportAccessUrl = `${REPORT_URL}/report/${reportId}`;
      const qrDataUrl = await QRCode.toDataURL(reportAccessUrl);
      setQrCodeUrl(qrDataUrl);
      
      setStage('complete');
    } catch (err) {
      setError('Error generating report. Please contact staff.');
    }
  };

  const resetProcess = () => {
    setStage('welcome');
    setVin('');
    setVehicleData(null);
    setScanProgress(0);
    setScanPosition(0);
    setQrCodeUrl('');
    setReportId('');
    setError('');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>MotoSpect Diagnostic Gate</h1>
      </header>

      <main className="App-main">
        <AnimatePresence mode="wait">
          {stage === 'welcome' && (
            <motion.div
              key="welcome"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="stage-container"
            >
              <h2>Welcome to MotoSpect</h2>
              <p className="instructions">
                Professional automotive diagnostics for vehicles up to 3L engine capacity.
              </p>
              <div className="feature-grid">
                <div className="feature-card">
                  <span className="feature-icon">🔍</span>
                  <h3>Comprehensive Scan</h3>
                  <p>Full OBD2/OBD3 diagnostic</p>
                </div>
                <div className="feature-card">
                  <span className="feature-icon">📊</span>
                  <h3>Detailed Report</h3>
                  <p>Complete analysis with costs</p>
                </div>
                <div className="feature-card">
                  <span className="feature-icon">⚡</span>
                  <h3>Quick Results</h3>
                  <p>Under 5 minutes</p>
                </div>
              </div>
              <button 
                className="btn-primary"
                onClick={() => setStage('vin')}
              >
                Start Diagnostic
              </button>
            </motion.div>
          )}

          {stage === 'vin' && (
            <motion.div
              key="vin"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="stage-container"
            >
              <h2>Vehicle Identification</h2>
              <p className="instructions">
                Enter your vehicle's VIN number or connect via OBD port for auto-detection.
              </p>
              
              <form onSubmit={handleVinSubmit} className="vin-form">
                <input
                  type="text"
                  value={vin}
                  onChange={(e) => setVin(e.target.value.toUpperCase())}
                  placeholder="Enter 17-character VIN"
                  maxLength="17"
                  pattern="[A-HJ-NPR-Z0-9]{17}"
                  required
                  className="vin-input"
                />
                <button type="submit" className="btn-primary">
                  Continue
                </button>
              </form>

              <div className="alternative-options">
                <button className="btn-secondary">
                  Auto-Detect via OBD
                </button>
                <button className="btn-secondary">
                  Manual Entry
                </button>
              </div>

              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              <button 
                className="btn-back"
                onClick={() => setStage('welcome')}
              >
                ← Back
              </button>
            </motion.div>
          )}

          {stage === 'scanning' && (
            <motion.div
              key="scanning"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="stage-container scanning-stage"
            >
              <h2>Scanning in Progress</h2>
              <p className="instructions">
                Please drive slowly (10 km/h) through the scanning gate
              </p>

              {vehicleData && (
                <div className="vehicle-info">
                  <h3>{vehicleData.year} {vehicleData.make} {vehicleData.model}</h3>
                  <p>Engine: {vehicleData.engine_size}L</p>
                </div>
              )}

              <div className="scan-visualization">
                <div className="scan-gate">
                  <div className="gate-frame">
                    <div className="scanner-beam" style={{ left: `${scanPosition % 100}%` }} />
                  </div>
                  
                  <motion.div
                    className="vehicle-icon"
                    animate={{ x: scanPosition * 3 }}
                    transition={{ type: "spring", stiffness: 50 }}
                  >
                    🚗
                  </motion.div>

                  <div className="scan-zones">
                    <div className={`zone ${scanProgress > 0 ? 'active' : ''}`}>
                      <span>Undercarriage</span>
                    </div>
                    <div className={`zone ${scanProgress > 33 ? 'active' : ''}`}>
                      <span>Engine Bay</span>
                    </div>
                    <div className={`zone ${scanProgress > 66 ? 'active' : ''}`}>
                      <span>Body & Interior</span>
                    </div>
                  </div>
                </div>

                <div className="progress-container">
                  <div className="progress-bar">
                    <motion.div 
                      className="progress-fill"
                      animate={{ width: `${scanProgress}%` }}
                    />
                  </div>
                  <span className="progress-text">{scanProgress}%</span>
                </div>

                <div className="scan-metrics">
                  <div className="metric">
                    <span className="metric-label">Systems Checked</span>
                    <span className="metric-value">{Math.floor(scanProgress / 10)}/10</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Parameters Read</span>
                    <span className="metric-value">{Math.floor(scanProgress * 2.5)}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Time Remaining</span>
                    <span className="metric-value">{Math.max(0, 50 - Math.floor(scanProgress / 2))}s</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {stage === 'complete' && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="stage-container complete-stage"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2 }}
                className="success-icon"
              >
                ✓
              </motion.div>

              <h2>Scan Complete!</h2>
              <p className="instructions">
                Your diagnostic report is ready. Scan the QR code to access your detailed report.
              </p>

              {qrCodeUrl && (
                <div className="qr-container">
                  <img src={qrCodeUrl} alt="Report QR Code" className="qr-code" />
                  <p className="qr-instructions">
                    Scan with your phone to download the report
                  </p>
                </div>
              )}

              <div className="report-summary">
                <h3>Quick Summary</h3>
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="summary-label">Report ID</span>
                    <span className="summary-value">{reportId}</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Direct Link</span>
                    <span className="summary-value">
                      <a href={`${REPORT_URL}/report/${reportId}`} target="_blank" rel="noopener noreferrer">
                        View Report
                      </a>
                    </span>
                  </div>
                </div>
              </div>

              <button 
                className="btn-primary"
                onClick={resetProcess}
              >
                New Scan
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {error && stage !== 'vin' && (
          <div className="error-overlay">
            <div className="error-content">
              <h3>Error</h3>
              <p>{error}</p>
              <button onClick={() => setError('')}>Dismiss</button>
            </div>
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>© 2024 MotoSpect - Professional Automotive Diagnostics</p>
        <p>Support: 1-800-MOTOSPECT</p>
      </footer>
    </div>
  );
}

export default App;
