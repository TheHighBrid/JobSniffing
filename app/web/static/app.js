const message = document.querySelector("#message");

function showMessage(text, isError = false) {
  message.textContent = text;
  message.className = isError ? "message error" : "message success";
}

async function sendJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail || payload);
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return payload;
}

document.querySelector("#scan-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const body = Object.fromEntries(form.entries());
  if (!body.company) delete body.company;
  try {
    const result = await sendJson("/api/discovery/scan", body);
    showMessage(`Saved ${result.upserted} jobs from ${result.source}. Reloading...`);
    window.setTimeout(() => window.location.reload(), 500);
  } catch (error) {
    showMessage(error.message, true);
  }
});

document.querySelector("#job-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = Object.fromEntries(new FormData(event.currentTarget).entries());
  try {
    await sendJson("/api/jobs", body);
    showMessage("Job saved. Reloading...");
    window.setTimeout(() => window.location.reload(), 400);
  } catch (error) {
    showMessage(error.message, true);
  }
});

document.querySelectorAll(".status-form").forEach((formElement) => {
  formElement.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      await sendJson(`/api/jobs/${event.currentTarget.dataset.jobId}/status`, body);
      showMessage("Status updated. Reloading...");
      window.setTimeout(() => window.location.reload(), 300);
    } catch (error) {
      showMessage(error.message, true);
    }
  });
});
