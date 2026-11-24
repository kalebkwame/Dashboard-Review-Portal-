const token = window.location.pathname.split("/").pop();
const form = document.querySelector("#inviteForm");

async function readApi(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Invitation unavailable");
  return body;
}

async function loadInvitation() {
  const message = document.querySelector("#inviteMessage");
  try {
    const invitation = await readApi(await fetch(`/auth/admin-invitations/${encodeURIComponent(token)}`));
    document.querySelector("#invitationEmail").textContent = `Invitation for ${invitation.email}`;
  } catch (error) {
    message.textContent = error.message;
    message.className = "error";
    form.classList.add("hidden");
  }
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  const message = document.querySelector("#inviteMessage");
  message.textContent = "";
  try {
    const account = await readApi(await fetch(`/auth/admin-invitations/${encodeURIComponent(token)}/redeem`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: document.querySelector("#inviteName").value,
        password: document.querySelector("#invitePassword").value
      })
    }));
    message.textContent = `Admin account created for ${account.email}. You can now sign in.`;
    message.className = "success";
    form.classList.add("hidden");
  } catch (error) {
    message.textContent = error.message;
    message.className = "error";
  }
});

loadInvitation();
