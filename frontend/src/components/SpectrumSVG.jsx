import React from 'react';

function SpectrumSVG({ values = [], width = 320, height = 100, color = '#4caf50' }) {
  const n = values.length || 0;
  const barW = n ? Math.max(1, Math.floor(width / n)) : width;
  const bars = values.map((v, i) => {
    const h = Math.max(1, Math.floor(v * height));
    const x = i * barW;
    const y = height - h;
    return (
      <rect key={i} x={x} y={y} width={barW - 1} height={h} fill={color} />
    );
  });

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} role="img" aria-label="Audio spectrum">
      <rect x="0" y="0" width={width} height={height} fill="#ffffff" />
      {bars}
    </svg>
  );
}

export default SpectrumSVG;
