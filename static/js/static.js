const getDeviceID = async () => {
  let userID = document.getElementById("userIDDropdown").value;
  let response = await fetch(`/get-devices?user_id=${userID}`);
  if (response.ok) {
    let data = await response.json();
    const dropdown = document.getElementById("deviceIDDropdown");
    // remove previous options
    while (dropdown.options.length > 0) {
      dropdown.remove(0);
    }
    // add new device ids
    for (const device of data.devices) {
      const option = document.createElement("option");
      option.value = device;
      option.innerText = device;
      dropdown.appendChild(option);
    }
  } else {
    showToast("Error getting device IDs");
    console.log(response.status);
  }
};

document
  .getElementById("userIDDropdown")
  .addEventListener("change", getDeviceID);

window.addEventListener("load", async () => {
  await getDeviceID();
});

// Stiatic Plot
const staticPlot = async () => {
  const spinner = document.getElementById("spinner");
  spinner.classList.add("running");
  const plantName = document.getElementById("plantName").value;
  const userID = document.getElementById("userIDDropdown").value;
  const deviceID = document.getElementById("deviceIDDropdown").value;
  const dateFrom = document.getElementById("from_date").value;
  const dateTo = document.getElementById("to_date").value;
  const speed = document.getElementById("speed").value;

  const data = {
    plantName: plantName,
    userID: userID,
    deviceID: deviceID,
    fromTime: dateFrom,
    toTime: dateTo,
    speed: speed,
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
        showToast("Error loading map.");
        spinner.classList.remove("running");
        console.log(error);
      }
    } else {
      showToast("No coordinates found.");
      spinner.classList.remove("running");
    }
  } else {
    showToast("Error retrieving map.");
    spinner.classList.remove("running");
  }
};
document
  .getElementById("static-plot-btn")
  .addEventListener("click", async () => {
    await staticPlot();
  });
