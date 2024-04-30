// job.js
document.addEventListener("DOMContentLoaded", function () {
  document.querySelector("form").onsubmit = function () {
    fetch("/job", {
      method: "POST",
      body: new FormData(this),
    })
      .then((response) => response.json())
      .then((result) => {
        alert("Application submitted successfully!");
        window.location.href = "/";
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("An error occurred while submitting the application.");
      });
    return false;
  };
});
