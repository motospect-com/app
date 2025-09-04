import React from 'react';

function ToFProfileSVG({ values = [], width = 320, height = 160, stroke = '#1976d2' }) {
  const n = values.length;
  const minD = 0;
  const maxD = 180;

  let path = '';
  if (n > 0) {
    values.forEach((d, i) => {
      const x = (i / (n - 1)) * (width - 1);
      const y = height - ((d - minD) / (maxD - minD)) * height;
      path += `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)} `;
    });
  }

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} role="img" aria-label="ToF profile">
      <rect x="0" y="0" width={width} height={height} fill="#ffffff" />
      <path d={path} stroke={stroke} strokeWidth="1.5" fill="none" />
    </svg>
  );
}

export default ToFProfileSVG;
