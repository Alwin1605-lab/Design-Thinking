import React, { useEffect, useRef } from 'react';

function loadGoogleMaps(apiKey) {
  return new Promise((resolve, reject) => {
    if (window.google && window.google.maps) return resolve();
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

export default function MapView({ issues = [] }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    if (!apiKey) return; // silently skip if no key configured
    let mounted = true;
    loadGoogleMaps(apiKey)
      .then(() => {
        if (!mounted || !mapRef.current) return;
        // Center to average location or default
        const defaultCenter = { lat: 20.5937, lng: 78.9629 }; // India
        mapInstance.current = new window.google.maps.Map(mapRef.current, {
          center: defaultCenter,
          zoom: 5,
        });
        // Add markers
        issues.forEach((issue) => {
          const loc = issue.location || {};
          if (typeof loc.latitude === 'number' && typeof loc.longitude === 'number') {
            const pos = { lat: loc.latitude, lng: loc.longitude };
            const marker = new window.google.maps.Marker({ position: pos, map: mapInstance.current });
            const info = new window.google.maps.InfoWindow({
              content: `<div><strong>${issue.category}</strong><br/>${issue.description || ''}<br/>Status: ${issue.status}</div>`,
            });
            marker.addListener('click', () => info.open({ anchor: marker, map: mapInstance.current }));
          }
        });
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [issues]);

  return (
    <div style={{ width: '100%', height: '320px', borderRadius: 8, overflow: 'hidden', background: '#eee' }} ref={mapRef} />
  );
}
