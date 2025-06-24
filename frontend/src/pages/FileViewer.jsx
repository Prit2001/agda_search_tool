import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

export default function FileViewer() {
  const [searchParams] = useSearchParams();
  const [fileText, setFileText] = useState('');
  const file = searchParams.get('file');
  const fn = searchParams.get('fn');

  useEffect(() => {
    if (!file) return;
    fetch(`/api/file-content?file=${encodeURIComponent(file)}`)
      .then(res => res.text())
      .then(setFileText)
      .catch(console.error);
  }, [file]);

  const isSignatureLine = (line) => {
    if (!fn) return false;
    const regex = new RegExp(`^\\s*${fn}\\s*:`);
    return regex.test(line);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>{file}</h2>
      <pre style={{
        whiteSpace: 'pre-wrap',
        backgroundColor: '#f9f9f9',
        border: '1px solid #ccc',
        padding: '10px',
        fontFamily: 'monospace',
        lineHeight: '1.4',
        overflowX: 'auto'
      }}>
        {fileText.split('\n').map((line, idx) =>
          isSignatureLine(line) ? (
            <span key={idx} style={{ backgroundColor: 'yellow' }}>{line + '\n'}</span>
          ) : (
            <span key={idx}>{line + '\n'}</span>
          )
        )}
      </pre>
    </div>
  );
}
