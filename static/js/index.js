// Stiatic Plot
const staticPlot = async () => {
  const spinner = document.getElementById("spinner");
  spinner.classList.add("running");
  const deviceID = document.getElementById("deviceIDDropdown").value;
  const dateFrom = document.getElementById("from_date").value;
  const dateTo = document.getElementById("to_date").value;

  const data = {
    deviceID: deviceID,
    fromTime: dateFrom,
    toTime: dateTo,
  };

  let response = await fetch("/static-plot", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (response.ok) {
    let data = await response.json();
    if (data.success) {
      try {
        document.getElementById("map").src = data.uri;
        spinner.classList.remove("running");
      } catch (error) {
        alert("Error loading map.");
        spinner.classList.remove("running");
        console.log(error);
      }
    } else {
      alert("No coordinates found.");
      spinner.classList.remove("running");
    }
  } else {
    alert("Error retrieving map.");
    spinner.classList.remove("running");
  }
};
document
  .getElementById("static-plot-btn")
  .addEventListener("click", async () => {
    await staticPlot();
  });

// Dynamic Plot
let processing = false;

const distributeProperty = (n) => {
  const minValue = 0.1;
  const maxValue = 1;
  const step = (maxValue - minValue) / (n - 1);

  const array = [];
  let value = minValue;

  for (let i = 0; i < n; i++) {
    array.push(value);
    value += step;
  }

  return array;
};

const startProcessing = async () => {
  processing = !processing; // toggle processing

  const stopProcessing = () => {
    startBtn.classList.remove("running");
    startBtn.textContent = "Start";
    processing = false;
  };

  const startBtn = document.getElementById("dynamic-plot-btn");
  if (processing) {
    // Add loading animation
    startBtn.classList.add("running");
    startBtn.textContent = "Stop";
    let loader = document.createElement("div");
    loader.classList.add("ld", "ld-ring", "ld-spin");
    startBtn.appendChild(loader);
    // Get coordinates
    const deviceID = document.getElementById("dynamicDeviceIDDropdown").value;
    const dateFrom = document.getElementById("dynamic_from_date").value;
    const data = {
      deviceID: deviceID,
      fromTime: dateFrom,
    };
    let response = await fetch("/dynamic-plot", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (response.ok) {
      let data = await response.json();
      if (data.success) {
        try {
          const coordinates = data.coordinates;
          debug = data.coordinates;
          // Destroy and create new map div
          const mapContainer = document.getElementById("map-container");
          const mapDiv = document.getElementById("dynamic-map-div");
          const newMapDiv = document.createElement("div");
          newMapDiv.id = "dynamic-map-div";
          mapDiv.remove();
          mapContainer.appendChild(newMapDiv);
          // Create new map
          const map = L.map("dynamic-map-div", {
            center: coordinates[0],
            crs: L.CRS.EPSG3857,
            zoom: 30,
            zoomControl: true,
            preferCanvas: false,
          });

          const titleLayer = L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
              attribution:
                'Data by \u0026copy; \u003ca target="_blank" href="http://openstreetmap.org"\u003eOpenStreetMap\u003c/a\u003e, under \u003ca target="_blank" href="http://www.openstreetmap.org/copyright"\u003eODbL\u003c/a\u003e.',
              detectRetina: false,
              maxNativeZoom: 18,
              maxZoom: 18,
              minZoom: 0,
              noWrap: false,
              opacity: 1,
              subdomains: "abc",
              tms: false,
            }
          ).addTo(map);
          // Create markers
          let count = 1;
          let markers = []; // old markers to be removed
          let bounds = new L.LatLngBounds();
          let i = 0;
          const addCoordinate = () => {
            setTimeout(() => {
              // remove old markers
              for (const marker of markers) {
                marker.remove();
              }
              let newMarkers = []; // new markers to be added
              // calculate opacity and add new markers
              const opacities = count === 1 ? [1] : distributeProperty(count);
              for (let j = 0; j < opacities.length; j++) {
                let circleMarker = L.circleMarker(coordinates[j], {
                  bubblingMouseEvents: true,
                  color: "red",
                  dashArray: null,
                  dashOffset: null,
                  fill: true,
                  fillColor: "red",
                  fillOpacity: opacities[j],
                  fillRule: "evenodd",
                  lineCap: "round",
                  lineJoin: "round",
                  opacity: opacities[j],
                  radius: 2.5,
                  stroke: true,
                  weight: 0.5,
                });
                newMarkers.push(circleMarker);
              }
              for (const marker of newMarkers) {
                map.addLayer(marker);
              }
              markers = newMarkers;
              count++;

              // map.addLayer(markers[i]);
              // auto adjust bounds
              bounds.extend(newMarkers[newMarkers.length - 1].getLatLng());
              map.fitBounds(bounds);
              i++;
              if (processing && i < coordinates.length) {
                addCoordinate();
              } else {
                stopProcessing();
              }
            }, 1000);
          };
          addCoordinate();

          // remove loading animation
        } catch (error) {
          alert(`Error: ${error.stack}`);
          stopProcessing();
        }
      } else {
        alert("No coordinates found.");
        stopProcessing();
      }
    } else {
      alert("Error retrieving coordinates.");
      stopProcessing();
    }
  } else {
    stopProcessing();
  }
};

document
  .getElementById("dynamic-plot-btn")
  .addEventListener("click", startProcessing);

var debug;
