const navLinks = document.querySelectorAll(".nav-link");
navLinks.forEach((el) => {
  el.addEventListener("click", () => {
    navLinks.forEach((link) => {
      link.classList.remove("active");
    });
    el.classList.add("active");
    if (el.innerText === "Dynamic") {
      document.getElementById("dynamic").hidden = false;
      document.getElementById("static").hidden = true;
    } else if (el.innerText === "Static") {
      document.getElementById("dynamic").hidden = true;
      document.getElementById("static").hidden = false;
    }
  });
});

const showToast = (message) => {
  // Show toast
  const toastItem = document.querySelector("#show-toast");
  toastItem.classList.add("toast");
  toastItem.parentElement.classList.add("toast-container");
  const toastBody = document.querySelector(".toast-body");
  toastBody.innerText = message;
  toastBody.style.fontSize = "1.75rem";
  const toast = new bootstrap.Toast(toastItem);
  toast.show();
  toastItem.classList.remove("fade");
};
