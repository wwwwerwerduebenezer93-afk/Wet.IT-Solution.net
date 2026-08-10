const $ = (s) => document.querySelector(s),
  $$ = (s) => document.querySelectorAll(s);
let token = localStorage.getItem("bp_token"),
  stream;
const backgrounds = ["assets/world.svg", "assets/coast.svg", "assets/city.svg"];
let bgIndex = 0,
  bgSlot = 0;
const bgEls = $$(".bg");
function rotateBg() {
  const next = backgrounds[bgIndex++ % backgrounds.length];
  bgSlot = 1 - bgSlot;
  bgEls[bgSlot].style.backgroundImage = `url(${next})`;
  bgEls.forEach((e, i) => e.classList.toggle("active", i === bgSlot));
}
rotateBg();
setInterval(rotateBg, 60000);
function toast(message, error = false) {
  const t = $("#toast");
  t.textContent = message;
  t.className = error ? "show error" : "show";
  setTimeout(() => (t.className = ""), 4000);
}
async function api(url, options = {}) {
  const r = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw Error(data.error || "Something went wrong.");
  return data;
}
const countryNames = new Intl.DisplayNames(["en"], { type: "region" });
const countries = [];
for (let a = 65; a <= 90; a++)
  for (let b = 65; b <= 90; b++) {
    const c = String.fromCharCode(a, b),
      n = countryNames.of(c);
    if (n && n !== c && !n.includes("Unknown")) countries.push([c, n]);
  }
countries.sort((a, b) => a[1].localeCompare(b[1]));
$$(".countries").forEach((s) => {
  s.innerHTML =
    '<option value="">Choose country</option>' +
    countries.map(([c, n]) => `<option value="${c}">${n}</option>`).join("");
});
$$(".tab").forEach(
  (b) =>
    (b.onclick = () => {
      $$(".tab").forEach((x) => x.classList.remove("active"));
      $$(".form").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      $("#" + b.dataset.tab).classList.add("active");
    }),
);
$("#cameraBtn").onclick = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    $("#video").srcObject = stream;
    toast("Camera ready. Capture your photo.");
  } catch {
    toast("Camera access was not allowed.", true);
  }
};
$("#captureBtn").onclick = () => {
  if (!stream) return toast("Start the camera first.", true);
  const v = $("#video"),
    c = $("#canvas");
  c.width = 480;
  c.height = 360;
  c.getContext("2d").drawImage(v, 0, 0, c.width, c.height);
  $("#register [name=livePhoto]").value = c.toDataURL("image/jpeg", 0.72);
  v.style.outline = "3px solid #49e0b1";
  toast("Live picture captured.");
  stream.getTracks().forEach((t) => t.stop());
};
$("#register").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const d = Object.fromEntries(new FormData(e.target));
    const r = await api("/api/register", {
      method: "POST",
      body: JSON.stringify(d),
    });
    toast(r.message);
    $("#verify [name=email]").value = d.email;
    $("#verify [name=phone]").value = d.phone;
    $$(".tab")[2].click();
  } catch (x) {
    toast(x.message, true);
  }
};
$("#sendCode").onclick = async () => {
  try {
    const email = $("#verify [name=email]").value;
    const r = await api("/api/send-code", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    $("#demoCode").textContent = `Demo verification code: ${r.demoCode}`;
    toast(r.message);
  } catch (x) {
    toast(x.message, true);
  }
};
$("#verify").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const r = await api("/api/verify-email", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(new FormData(e.target))),
    });
    toast(r.message);
    $$(".tab")[0].click();
  } catch (x) {
    toast(x.message, true);
  }
};
$("#sendPhoneCode").onclick = async () => {
  try {
    const phone = $("#verify [name=phone]").value;
    const r = await api("/api/send-phone-code", {
      method: "POST",
      body: JSON.stringify({ phone }),
    });
    $("#demoPhoneCode").textContent = `Demo SMS code: ${r.demoCode}`;
    toast(r.message);
  } catch (x) {
    toast(x.message, true);
  }
};
$("#verifyPhone").onclick = async () => {
  try {
    const phone = $("#verify [name=phone]").value,
      code = $("#verify [name=phoneCode]").value;
    const r = await api("/api/verify-phone", {
      method: "POST",
      body: JSON.stringify({ phone, code }),
    });
    toast(r.message);
  } catch (x) {
    toast(x.message, true);
  }
};
$("#login").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const r = await api("/api/login", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(new FormData(e.target))),
    });
    token = r.token;
    localStorage.setItem("bp_token", token);
    showDashboard(r.user);
  } catch (x) {
    toast(x.message, true);
  }
};
async function showDashboard(user) {
  $("#authPanel").classList.add("hidden");
  $(".hero").classList.add("hidden");
  $("#dashboard").classList.remove("hidden");
  $("#userName").textContent = user.name;
  try {
    const [q, tx] = await Promise.all([api("/api/qr"), api("/api/transfers")]);
    $("#qrImage").src = q.qr;
    renderHistory(tx);
  } catch (x) {
    toast(x.message, true);
  }
}
function renderHistory(items) {
  $("#history").innerHTML = items.length
    ? items
        .map(
          (t) =>
            `<div class="payment"><div><b>${t.recipient}</b><small>${new Date(t.createdAt).toLocaleString()} · ${t.destinationCountry}</small></div><strong>${t.currency} ${Number(t.amount).toFixed(2)}</strong></div>`,
        )
        .join("")
    : "<p>No payments yet.</p>";
}
$("#transfer").onsubmit = async (e) => {
  e.preventDefault();
  if (!confirm("Authorise this simulated international payment?")) return;
  try {
    const d = Object.fromEntries(new FormData(e.target));
    const r = await api("/api/transfers", {
      method: "POST",
      body: JSON.stringify(d),
    });
    toast(`${r.message} Reference: ${r.transfer.id}`);
    e.target.reset();
    renderHistory(await api("/api/transfers"));
  } catch (x) {
    toast(x.message, true);
  }
};
$("#aiSearch").onsubmit = async (e) => {
  e.preventDefault();
  const box = $("#aiAnswer");
  box.textContent = "Searching the payment guide…";
  try {
    const r = await api("/api/ai-search", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(new FormData(e.target))),
    });
    box.innerHTML = `<b>${r.mode}</b><br>${r.answer}<small>${r.disclaimer}</small>`;
  } catch (x) {
    box.textContent = x.message;
  }
};
$("#logout").onclick = () => {
  localStorage.removeItem("bp_token");
  location.reload();
};
if (token)
  api("/api/me")
    .then(showDashboard)
    .catch(() => {
      localStorage.removeItem("bp_token");
      token = null;
    });
