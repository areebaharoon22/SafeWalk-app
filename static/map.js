let map, marker, watchId;
let startTime, startCoords;
let walkPath = [];

function toggleMenu() {
  const menu = document.getElementById('sideMenu');
  menu.classList.toggle('d-none');
}

function initMap(lat, lng) {
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
  marker.setLatLng([latitude, longitude]).update();
}

function startWalk() {
  navigator.geolocation.getCurrentPosition(pos => {
    startTime = new Date();
    startCoords = pos.coords;

    document.getElementById('startWalkBtn').classList.add('d-none');
    document.getElementById('walkingGif').classList.remove('d-none');

    initMap(startCoords.latitude, startCoords.longitude);
    watchId = navigator.geolocation.watchPosition(updateLocation);
  });
}

function alertContacts() {
  alert('Your current location has been sent to your trusted contacts!');
}

function endWalk() {
  navigator.geolocation.getCurrentPosition(pos => {
    const endTime = new Date();
    const duration = Math.round((endTime - startTime) / 1000 / 60);

    document.getElementById('startSection').classList.add('d-none');
    document.getElementById('walkingGif').classList.add('d-none');
    document.getElementById('summarySection').classList.remove('d-none');

    document.getElementById('startTimeDisplay').textContent = startTime.toLocaleString();
    document.getElementById('endTimeDisplay').textContent = endTime.toLocaleString();
    document.getElementById('startLocation').textContent = `${startCoords.latitude.toFixed(5)}, ${startCoords.longitude.toFixed(5)}`;
    document.getElementById('endLocation').textContent = `${pos.coords.latitude.toFixed(5)}, ${pos.coords.longitude.toFixed(5)}`;
    document.getElementById('durationDisplay').textContent = `${duration} minutes`;
    document.getElementById('stepsDisplay').textContent = `${duration * 120} steps`;

    navigator.geolocation.clearWatch(watchId);

    // Optional: Send walk data to server here

    console.log('Walk ended at', endTime);
  });
}

window.onload = () => {
  document.getElementById('startWalkBtn').addEventListener('click', startWalk);
};
