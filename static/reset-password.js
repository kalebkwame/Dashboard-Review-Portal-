const token = window.location.pathname.split("/").pop();
const form = document.querySelector("#resetForm");
const message = document.querySelector("#resetMessage");

form.addEventListener("submit", async event => {
  event.preventDefault();
  message.textContent = "";

  try {
    const response = await fetch(`/auth/password-reset/${encodeURIComponent(token)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: document.querySelector("#newPassword").value })
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(typeof body.detail === "string" ? body.detail : "Unable to reset password");
    }

    message.innerHTML = `Password has been reset successfully.<br><a href="/">Sign in</a>`;
    message.className = "success";
    form.classList.add("hidden");
  } catch (error) {
    message.textContent = error.message;
    message.className = "error";
  }
});
