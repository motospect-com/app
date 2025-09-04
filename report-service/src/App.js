import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useParams } from 'react-router-dom';
import axios from 'axios';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8084';

function ReportViewer() {
  const { reportId } = useParams();
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReport();
  }, [reportId]);

  const fetchReport = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/report/${reportId}`);
      setReportData(response.data);
      setLoading(false);
    } catch (err) {
      setError('Report not found or expired');
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    const pdf = new jsPDF('p', 'mm', 'a4');
    const reportElement = document.getElementById('report-content');
    
    const canvas = await html2canvas(reportElement, {
      scale: 2,
      logging: false,
      useCORS: true
    });
    
    const imgData = canvas.toDataURL('image/png');
    const imgWidth = 210;
    const pageHeight = 295;
    const imgHeight = canvas.height * imgWidth / canvas.width;
    let heightLeft = imgHeight;
    let position = 0;

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;

    while (heightLeft >= 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }

    pdf.save(`motospect-report-${reportId}.pdf`);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading report...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  const severityColors = {
    'Critical': '#e74c3c',
    'High': '#e67e22',
    'Medium': '#f39c12',
    'Low': '#3498db',
    'Info': '#95a5a6'
  };

  const systemHealthData = reportData?.systems?.map(sys => ({
    name: sys.name,
    health: sys.health_percentage,
    issues: sys.issue_count
  })) || [];

  const faultDistribution = Object.entries(
    reportData?.fault_codes?.reduce((acc, fault) => {
      acc[fault.severity] = (acc[fault.severity] || 0) + 1;
      return acc;
    }, {}) || {}
  ).map(([severity, count]) => ({ severity, count }));

  return (
    <div className="report-viewer">
      <div className="report-header">
        <h1>MotoSpect Diagnostic Report</h1>
        <button className="download-btn" onClick={downloadPDF}>
          📥 Download PDF
        </button>
      </div>

      <div id="report-content" className="report-content">
        {/* Vehicle Information Section */}
        <section className="report-section">
          <h2>Vehicle Information</h2>
          <div className="vehicle-details">
            <div className="detail-row">
              <span className="label">VIN:</span>
              <span className="value">{reportData?.vehicle?.vin}</span>
            </div>
            <div className="detail-row">
              <span className="label">Make/Model:</span>
              <span className="value">
                {reportData?.vehicle?.year} {reportData?.vehicle?.make} {reportData?.vehicle?.model}
              </span>
            </div>
            <div className="detail-row">
              <span className="label">Engine:</span>
              <span className="value">
                {reportData?.vehicle?.engine_size}L {reportData?.vehicle?.fuel_type}
              </span>
            </div>
            <div className="detail-row">
              <span className="label">Mileage:</span>
              <span className="value">{reportData?.vehicle?.mileage?.toLocaleString()} km</span>
            </div>
            <div className="detail-row">
              <span className="label">Scan Date:</span>
              <span className="value">{new Date(reportData?.scan_date).toLocaleString()}</span>
            </div>
          </div>
        </section>

        {/* Overall Health Score */}
        <section className="report-section">
          <h2>Overall Vehicle Health</h2>
          <div className="health-score">
            <div className={`score-circle ${reportData?.overall_health > 80 ? 'good' : reportData?.overall_health > 60 ? 'fair' : 'poor'}`}>
              <span className="score-number">{reportData?.overall_health}%</span>
            </div>
            <p className="health-description">
              {reportData?.overall_health > 80 ? 'Your vehicle is in good condition' :
               reportData?.overall_health > 60 ? 'Your vehicle needs attention' :
               'Immediate service recommended'}
            </p>
          </div>
        </section>

        {/* System Health Chart */}
        <section className="report-section">
          <h2>System Health Overview</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={systemHealthData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="health" fill="#3498db" name="Health %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Fault Codes */}
        <section className="report-section">
          <h2>Diagnostic Trouble Codes (DTCs)</h2>
          {reportData?.fault_codes?.length > 0 ? (
            <div className="fault-codes">
              {reportData.fault_codes.map((fault, index) => (
                <div key={index} className={`fault-card severity-${fault.severity.toLowerCase()}`}>
                  <div className="fault-header">
                    <span className="fault-code">{fault.code}</span>
                    <span className={`severity-badge ${fault.severity.toLowerCase()}`}>
                      {fault.severity}
                    </span>
                  </div>
                  <p className="fault-description">{fault.description}</p>
                  <div className="fault-details">
                    <span>System: {fault.system}</span>
                    <span>Action: {fault.action}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-faults">✓ No fault codes detected</p>
          )}
        </section>

        {/* Fault Distribution Chart */}
        {faultDistribution.length > 0 && (
          <section className="report-section">
            <h2>Issue Severity Distribution</h2>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={faultDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.severity}: ${entry.count}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {faultDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={severityColors[entry.severity]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}

        {/* Maintenance Recommendations */}
        <section className="report-section">
          <h2>Maintenance Recommendations</h2>
          <div className="recommendations">
            {reportData?.recommendations?.map((rec, index) => (
              <div key={index} className={`recommendation priority-${rec.priority}`}>
                <div className="rec-header">
                  <span className="rec-title">{rec.service}</span>
                  <span className={`priority-badge ${rec.priority}`}>
                    {rec.priority} Priority
                  </span>
                </div>
                <p className="rec-description">{rec.description}</p>
                <div className="rec-footer">
                  <span className="rec-cost">
                    Estimated Cost: ${rec.estimated_cost_min} - ${rec.estimated_cost_max}
                  </span>
                  <span className="rec-time">
                    Time: {rec.time_estimate}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Cost Summary */}
        <section className="report-section">
          <h2>Service Cost Estimate</h2>
          <div className="cost-summary">
            <div className="cost-row">
              <span className="cost-label">Immediate Repairs:</span>
              <span className="cost-value">${reportData?.cost_summary?.immediate_min} - ${reportData?.cost_summary?.immediate_max}</span>
            </div>
            <div className="cost-row">
              <span className="cost-label">Preventive Maintenance:</span>
              <span className="cost-value">${reportData?.cost_summary?.preventive_min} - ${reportData?.cost_summary?.preventive_max}</span>
            </div>
            <div className="cost-row total">
              <span className="cost-label">Total Estimate:</span>
              <span className="cost-value">${reportData?.cost_summary?.total_min} - ${reportData?.cost_summary?.total_max}</span>
            </div>
          </div>
          <p className="cost-disclaimer">
            * Estimates based on average market prices. Actual costs may vary.
          </p>
        </section>

        {/* Vehicle Diagram */}
        <section className="report-section">
          <h2>Issue Locations</h2>
          <div className="vehicle-diagram">
            <svg viewBox="0 0 800 400" className="car-svg">
              {/* Simple car outline */}
              <rect x="150" y="200" width="500" height="100" fill="#e0e0e0" stroke="#333" strokeWidth="2" rx="10"/>
              <rect x="200" y="150" width="180" height="80" fill="#f0f0f0" stroke="#333" strokeWidth="2"/>
              <rect x="420" y="150" width="180" height="80" fill="#f0f0f0" stroke="#333" strokeWidth="2"/>
              <circle cx="250" cy="320" r="30" fill="#333"/>
              <circle cx="550" cy="320" r="30" fill="#333"/>
              
              {/* Issue markers */}
              {reportData?.issue_locations?.map((loc, i) => (
                <g key={i}>
                  <circle cx={loc.x} cy={loc.y} r="15" fill={severityColors[loc.severity]} opacity="0.7"/>
                  <text x={loc.x} y={loc.y + 5} textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
                    {i + 1}
                  </text>
                </g>
              ))}
            </svg>
            <div className="diagram-legend">
              {reportData?.issue_locations?.map((loc, i) => (
                <div key={i} className="legend-item">
                  <span className="legend-number">{i + 1}</span>
                  <span className="legend-text">{loc.description}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* AI Analysis */}
        {reportData?.ai_analysis && (
          <section className="report-section">
            <h2>AI Diagnostic Analysis</h2>
            <div className="ai-analysis">
              <p>{reportData.ai_analysis.summary}</p>
              <h3>Key Findings:</h3>
              <ul>
                {reportData.ai_analysis.findings?.map((finding, i) => (
                  <li key={i}>{finding}</li>
                ))}
              </ul>
              <h3>Recommendations:</h3>
              <ul>
                {reportData.ai_analysis.recommendations?.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Footer */}
        <section className="report-footer">
          <div className="footer-content">
            <p className="report-id">Report ID: {reportId}</p>
            <p className="generated-date">Generated: {new Date().toLocaleString()}</p>
            <p className="company-info">
              MotoSpect Professional Diagnostics<br/>
              1-800-MOTOSPECT | service@motospect.com
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/report/:reportId" element={<ReportViewer />} />
          <Route path="/" element={
            <div className="home-container">
              <h1>MotoSpect Report Service</h1>
              <p>Access your diagnostic reports using the provided link or QR code.</p>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
