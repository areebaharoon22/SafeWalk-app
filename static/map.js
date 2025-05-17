
let map, marker, watchId, fallbackInterval;
let startTime, startCoords;
let walkPath = [];

function toggleMenu() {
  const menu = document.getElementById('sideMenu');
  menu.classList.toggle('d-none');
}

function initMap(lat, lng) {
  if (map) {
    map.remove();
  }
  map = L.map('map').setView([lat, lng], 15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);
  marker = L.marker([lat, lng]).addTo(map).bindPopup('You are here.').openPopup();
}

function updateLocation(position) {
  const { latitude, longitude } = position.coords;
  const timestamp = new Date().toISOString();
  walkPath.push({ latitude, longitude, timestamp });
  console.log("Adding location to path:", latitude, longitude);
  console.log("Current path:", walkPath);
  marker.setLatLng([latitude, longitude]).update();
}

function startWalk() {
  navigator.geolocation.getCurrentPosition(pos => {
    startTime = new Date();
    startCoords = pos.coords;

    document.getElementById('startWalkBtn').classList.add('d-none');
    document.getElementById('walkingGif').classList.remove('d-none');

    initMap(startCoords.latitude, startCoords.longitude);

    watchId = navigator.geolocation.watchPosition(position => {
      console.log("Received position (watch):", position);
      updateLocation(position);
    }, geoError, {
      enableHighAccuracy: true,
      maximumAge: 0,
      timeout: 10000
    });

    fallbackInterval = setInterval(() => {
      navigator.geolocation.getCurrentPosition(pos => {
        console.log("Received position (fallback):", pos);
        updateLocation(pos);
      }, geoError);
    }, 10000);

  }, geoError);
}

function alertContacts() {
  if (!marker) {
    alert("Location not available yet.");
    return;
  }

  const latlng = marker.getLatLng();
  const location = `${latlng.lat},${latlng.lng}`;

  fetch('/send-alert', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ location })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message || "Alert sent!");
  })
  .catch(() => {
    alert("Failed to send alert. Please try again.");
  });
}


function endWalk() {
  if (!startTime || !startCoords) {
    alert('Please start a walk before ending it.');
    return;
  }

  navigator.geolocation.clearWatch(watchId);
  clearInterval(fallbackInterval);

  const endTime = new Date();
  const duration = Math.max(1, Math.ceil((endTime - startTime) / 1000 / 60));

  navigator.geolocation.getCurrentPosition(pos => {
    const finalCoords = pos.coords;
    const timestamp = new Date().toISOString();
    const lastPoint = {
      latitude: finalCoords.latitude,
      longitude: finalCoords.longitude,
      timestamp: timestamp
    };
    walkPath.push(lastPoint);

    document.getElementById('startSection').classList.add('d-none');
    document.getElementById('walkingGif').classList.add('d-none');
    document.getElementById('summarySection').classList.remove('d-none');

    document.getElementById('startTimeDisplay').textContent = startTime.toLocaleString();
    document.getElementById('endTimeDisplay').textContent = endTime.toLocaleString();
    document.getElementById('startLocation').textContent = `${startCoords.latitude.toFixed(5)}, ${startCoords.longitude.toFixed(5)}`;
    document.getElementById('endLocation').textContent = `${finalCoords.latitude.toFixed(5)}, ${finalCoords.longitude.toFixed(5)}`;
    document.getElementById('durationDisplay').textContent = `${duration} minutes`;
    document.getElementById('stepsDisplay').textContent = `${duration * 120} steps`;

    fetch('/save-walk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        path: walkPath
      })
    }).then(res => res.json()).then(data => {
      console.log('Walk saved:', data);
    });
  }, geoError);
}

function geoError(err) {
  console.error('Geolocation error:', err);
  alert('Location access is required for SafeWalk to work. Please allow location permissions.');
}

window.onload = () => {
  navigator.geolocation.getCurrentPosition(pos => {
    initMap(pos.coords.latitude, pos.coords.longitude);
  }, geoError);

  document.getElementById('startWalkBtn').addEventListener('click', startWalk);
};
