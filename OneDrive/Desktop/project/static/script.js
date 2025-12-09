document.addEventListener("DOMContentLoaded", () => {

  // CREATE ACCOUNT BUTTON → FLASK REGISTER PAGE
  document.getElementById("registerBtn").addEventListener("click", () => {
    window.location.href = "/register";
  });

  // LOGIN BUTTON → FLASK DASHBOARD PAGE
  document.getElementById("loginBtn").addEventListener("click", () => {
    window.location.href = "/dashboard";
  });

});
document.getElementById("loginBtn").addEventListener("click", async function () {

    const user = document.getElementById("uname").value.trim();
    const pass = document.getElementById("pwd").value.trim();

    if (user === "" || pass === "") {
        alert("Please enter username and password.");
        return;
    }

    const response = await fetch("/login_user", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: user, password: pass})
    });

    const result = await response.json();

    if (result.status === "success") {
        localStorage.setItem("logged_in", "true");
        window.location.href = "/dashboard";
    } 
    else {
        alert("Invalid username or password.");
    }
});
