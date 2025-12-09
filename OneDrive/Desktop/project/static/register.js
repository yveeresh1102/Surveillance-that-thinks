document.addEventListener("DOMContentLoaded", () => {

  // When user clicks REGISTER → create account
  document.getElementById("registerBtn").addEventListener("click", () => {
    alert("Account Created Successfully!");

    // Redirect to login page
    window.location.href = "/";
  });

  // Existing user → go to login page
  document.getElementById("loginRedirect").addEventListener("click", () => {
    window.location.href = "/";
  });

});
document.getElementById("registerBtn").addEventListener("click", async function () {

    const uname = document.querySelector("input[name='username']").value.trim();
    const pwd = document.querySelector("input[name='password']").value.trim();

    if (uname === "" || pwd === "") {
        alert("Please fill all fields.");
        return;
    }

    const response = await fetch("/register_user", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: uname, password: pwd})
    });

    const result = await response.json();

    if (result.status === "success") {
        alert("Account created successfully!");
        window.location.href = "/";
    }
    else {
        alert("Username already exists.");
    }
});
