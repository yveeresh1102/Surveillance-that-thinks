document.addEventListener("DOMContentLoaded", () => {

  const loginBtn = document.getElementById("loginBtn");
  const registerBtn = document.getElementById("registerBtn");

  loginBtn.addEventListener("click", () => {
    window.location.href = "/dashboard";
  });

  registerBtn.addEventListener("click", () => {
    window.location.href = "/register";
  });

});
