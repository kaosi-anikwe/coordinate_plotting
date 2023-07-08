const getUserID = async () => {
  let userDiv = document.getElementById("userDiv");
  userDiv.classList.toggle("running");
  let plant = document.getElementById("plantName").value;
  let data = { plantName: plant };
  let response = await fetch("/get-users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (response.ok) {
    let data = await response.json();
    const dropdown = document.getElementById("userIDDropdown");
    // remove previous options
    while (dropdown.options.length > 0) {
      dropdown.remove(0);
    }
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
    userDiv.classList.toggle("running");
  } else {
    showToast("Error getting Users");
    console.log(response.status);
    userDiv.classList.toggle("running");
  }
};

document.getElementById("plantName").addEventListener("change", getUserID);

window.addEventListener("load", async () => {
  await getUserID();
});

// Stiatic Plot
const staticPlot = async () => {
  const spinner = document.getElementById("spinner");
  spinner.classList.add("running");
  const plantName = document.getElementById("plantName").value;
  const userID = document.getElementById("userIDDropdown").value;
  const dateFrom = document.getElementById("from_date").value;
  const dateTo = document.getElementById("to_date").value;
  const speed = document.getElementById("speed").value;

  if (!userID) {
    showToast("Please select a User ID");
    spinner.classList.remove("running");
    return;
  }

  const data = {
    plantName: plantName,
    userID: userID,
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
