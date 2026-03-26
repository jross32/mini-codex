const form = document.getElementById("gen-form");
const promptEl = document.getElementById("prompt");
const resultEl = document.getElementById("result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultEl.textContent = "Generating...";

  const response = await fetch("http://localhost:8000/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: promptEl.value }),
  });

  const payload = await response.json();
  resultEl.textContent = JSON.stringify(payload, null, 2);
});
