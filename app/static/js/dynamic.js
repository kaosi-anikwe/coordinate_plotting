const getDynamicUserID = async () => {
  let userDiv = document.getElementById("dynamicUserDiv");
  userDiv.classList.toggle("running");
  let plant = document.getElementById("dynamicPlantName").value;
  let data = { plantName: plant };
  let response = await fetch("/get-users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (response.ok) {
    let data = await response.json();
    const dropdown = document.getElementById("dynamicUserIDDropdown");
    // remove previous options
    while (dropdown.options.length > 0) {
      dropdown.remove(0);
    }
    console.log(`Got ${data.users.length} users`);
    // add new device ids
    if (data.users.length > 1) {
      const option = document.createElement("option");
      option.value = "All";
      option.innerText = "All";
      dropdown.appendChild(option);
    }
    for (const user of data.users) {
      const option = document.createElement("option");
      option.value = user;
      option.innerText = user;
      dropdown.appendChild(option);
    }
    console.log("Done creating options");
    userDiv.classList.toggle("running");
  } else {
    showToast("Error getting Users");
    console.log(response.status);
    userDiv.classList.toggle("running");
  }
};

document
  .getElementById("dynamicPlantName")
  .addEventListener("change", getDynamicUserID);

window.addEventListener("load", async () => {
  await getDynamicUserID();
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
    const plantName = document.getElementById("dynamicPlantName").value;
    const userID = document.getElementById("dynamicUserIDDropdown").value;
    const dateFrom = document.getElementById("dynamic_from_date").value;
    const dateTo = document.getElementById("dynamic_to_date").value;
    const speed = document.getElementById("dynamic_speed").value;

    if (userID === "All") {
      showToast("Please select a different User ID option.");
      stopProcessing();
      return;
    }
    if (!userID) {
      showToast("Please select a User ID");
      stopProcessing();
      return;
    }

    const data = {
      plantName: plantName,
      userID: userID,
      fromTime: dateFrom,
      toTime: dateTo,
      speed: speed,
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
          const geoJSON = data.geojson ? data.geojson : null;
          // Destroy and create new map div
          const mapContainer = document.getElementById("map-container");
          const mapDiv = document.getElementById("dynamic-map-div");
          const newMapDiv = document.createElement("div");
          mapDiv.remove();
          newMapDiv.id = "dynamic-map-div";
          mapContainer.appendChild(newMapDiv);
          // Create new map
          const map = L.map("dynamic-map-div", {
            center: coordinates[0],
            crs: L.CRS.EPSG3857,
            zoom: 30,
            zoomControl: true,
            preferCanvas: false,
          });
          geoJSON && geoJSON.forEach((json) => L.geoJSON(json).addTo(map));

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
          let bounds = new L.LatLngBounds(); // bounds for map
          let i = 0; // intiate counter
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
                  color: data.shade,
                  dashArray: null,
                  dashOffset: null,
                  fill: true,
                  fillColor: data.shade,
                  fillOpacity: opacities[j],
                  fillRule: "evenodd",
                  lineCap: "round",
                  lineJoin: "round",
                  opacity: opacities[j],
                  radius: 0.5,
                  stroke: true,
                  weight: 7.5,
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
          showToast(`Error: ${error.stack}`);
          stopProcessing();
        }
      } else {
        showToast("No coordinates found.");
        stopProcessing();
      }
    } else {
      showToast("Error retrieving coordinates.");
      stopProcessing();
    }
  } else {
    stopProcessing();
  }
};

document
  .getElementById("dynamic-plot-btn")
  .addEventListener("click", startProcessing);
