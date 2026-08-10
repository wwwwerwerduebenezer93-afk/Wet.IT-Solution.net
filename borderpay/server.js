const express = require("express");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const QRCode = require("qrcode");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const app = express();
const PORT = process.env.PORT || 3000;
const SECRET = process.env.JWT_SECRET || "change-this-development-secret";
const DATA = path.join(__dirname, "data", "store.json");
const emptyStore = { users: [], transfers: [], codes: {} };

app.use(helmet({ contentSecurityPolicy: false }));
app.use(express.json({ limit: "3mb" }));
app.use("/api", rateLimit({ windowMs: 60_000, limit: 100 }));
app.use(express.static(path.join(__dirname, "public")));

function load() {
  try {
    return JSON.parse(fs.readFileSync(DATA, "utf8"));
  } catch {
    return structuredClone(emptyStore);
  }
}
function save(store) {
  fs.mkdirSync(path.dirname(DATA), { recursive: true });
  fs.writeFileSync(DATA, JSON.stringify(store, null, 2));
}
function cleanEmail(v = "") {
  return String(v).trim().toLowerCase();
}
function cleanPhone(v = "") {
  return String(v).replace(/[\s()-]/g, "");
}
function auth(req, res, next) {
  try {
    req.user = jwt.verify(
      (req.headers.authorization || "").replace("Bearer ", ""),
      SECRET,
    );
    next();
  } catch {
    res.status(401).json({ error: "Please sign in again." });
  }
}
function publicUser(u) {
  return {
    id: u.id,
    name: u.name,
    email: u.email,
    phone: u.phone,
    country: u.country,
    verified: u.verified,
    phoneVerified: u.phoneVerified,
  };
}

app.post("/api/register", async (req, res) => {
  const {
    name,
    email: rawEmail,
    phone: rawPhone,
    password,
    pin,
    country,
    livePhoto,
  } = req.body;
  const email = cleanEmail(rawEmail);
  const phone = cleanPhone(rawPhone);
  if (
    !name ||
    !/^\S+@\S+\.\S+$/.test(email) ||
    !/^\+[1-9]\d{7,14}$/.test(phone) ||
    String(password).length < 8 ||
    !/^\d{4,6}$/.test(pin || "") ||
    !country ||
    !String(livePhoto || "").startsWith("data:image/")
  )
    return res
      .status(400)
      .json({
        error:
          "Complete every field. Use a phone number like +233..., an 8+ character password, a 4–6 digit PIN, and a live photo.",
      });
  const store = load();
  if (store.users.some((u) => u.email === email))
    return res
      .status(409)
      .json({ error: "An account already exists for this email." });
  if (store.users.some((u) => u.phone === phone))
    return res
      .status(409)
      .json({ error: "An account already exists for this phone number." });
  const user = {
    id: crypto.randomUUID(),
    name: String(name).trim(),
    email,
    phone,
    country,
    passwordHash: await bcrypt.hash(password, 12),
    pinHash: await bcrypt.hash(pin, 12),
    livePhoto,
    verified: false,
    phoneVerified: false,
    createdAt: new Date().toISOString(),
  };
  store.users.push(user);
  save(store);
  res
    .status(201)
    .json({
      message: "Account created. Request an email verification code.",
      user: publicUser(user),
    });
});

app.post("/api/send-code", (req, res) => {
  const email = cleanEmail(req.body.email);
  const store = load();
  if (!store.users.some((u) => u.email === email))
    return res.status(404).json({ error: "Account not found." });
  const code = String(crypto.randomInt(100000, 999999));
  store.codes[email] = {
    hash: crypto.createHash("sha256").update(code).digest("hex"),
    expires: Date.now() + 10 * 60_000,
  };
  save(store);
  // Demo delivery. Replace this with an email provider in production.
  res.json({
    message: "Verification code generated (demo mode).",
    demoCode: code,
  });
});

app.post("/api/verify-email", (req, res) => {
  const email = cleanEmail(req.body.email);
  const store = load();
  const item = store.codes[email];
  const hash = crypto
    .createHash("sha256")
    .update(String(req.body.code || ""))
    .digest("hex");
  if (!item || item.expires < Date.now() || item.hash !== hash)
    return res.status(400).json({ error: "Code is invalid or expired." });
  const user = store.users.find((u) => u.email === email);
  user.verified = true;
  delete store.codes[email];
  save(store);
  res.json({ message: "Email verified. You can now sign in." });
});

app.post("/api/send-phone-code", (req, res) => {
  const phone = cleanPhone(req.body.phone);
  const store = load();
  if (!store.users.some((u) => u.phone === phone))
    return res.status(404).json({ error: "Phone number not found." });
  const code = String(crypto.randomInt(100000, 999999));
  const key = `phone:${phone}`;
  store.codes[key] = {
    hash: crypto.createHash("sha256").update(code).digest("hex"),
    expires: Date.now() + 10 * 60_000,
  };
  save(store);
  res.json({ message: "SMS code generated (demo mode).", demoCode: code });
});

app.post("/api/verify-phone", (req, res) => {
  const phone = cleanPhone(req.body.phone);
  const store = load();
  const key = `phone:${phone}`;
  const item = store.codes[key];
  const hash = crypto
    .createHash("sha256")
    .update(String(req.body.code || ""))
    .digest("hex");
  if (!item || item.expires < Date.now() || item.hash !== hash)
    return res.status(400).json({ error: "SMS code is invalid or expired." });
  const user = store.users.find((u) => u.phone === phone);
  user.phoneVerified = true;
  delete store.codes[key];
  save(store);
  res.json({ message: "Phone verified. Verify your email too, then sign in." });
});

app.post("/api/login", async (req, res) => {
  const store = load();
  const user = store.users.find((u) => u.email === cleanEmail(req.body.email));
  if (
    !user ||
    !(await bcrypt.compare(String(req.body.password || ""), user.passwordHash))
  )
    return res.status(401).json({ error: "Incorrect email or password." });
  if (!user.verified || !user.phoneVerified)
    return res
      .status(403)
      .json({ error: "Verify both your email and phone before signing in." });
  const token = jwt.sign({ id: user.id, email: user.email }, SECRET, {
    expiresIn: "2h",
  });
  res.json({ token, user: publicUser(user) });
});

app.get("/api/me", auth, (req, res) => {
  const user = load().users.find((u) => u.id === req.user.id);
  if (!user) return res.sendStatus(404);
  res.json(publicUser(user));
});

app.get("/api/qr", auth, async (req, res) => {
  const user = load().users.find((u) => u.id === req.user.id);
  const payload = JSON.stringify({
    type: "borderpay-payee",
    recipient: user.email,
    name: user.name,
  });
  res.json({
    qr: await QRCode.toDataURL(payload, { width: 300, margin: 1 }),
    payload,
  });
});

app.get("/api/transfers", auth, (req, res) => {
  res.json(
    load()
      .transfers.filter((t) => t.senderId === req.user.id)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt)),
  );
});

const knowledge = [
  {
    keys: "country countries destination global send abroad international",
    answer:
      "Choose a destination from the country list in New international payment. This prototype displays global destinations; actual availability depends on your regulated payment partner.",
  },
  {
    keys: "fee fees cost price charge exchange fx rate",
    answer:
      "This demo does not calculate live fees or FX rates. A production review screen must show the rate, provider fee, recipient amount and total cost before PIN approval.",
  },
  {
    keys: "verify verification email phone sms picture photo identity kyc",
    answer:
      "Account access requires both email and phone verification. Registration also captures a live camera picture; production use needs consent, liveness checks, encrypted storage and KYC review.",
  },
  {
    keys: "pin password secure security fraud",
    answer:
      "Passwords and payment PINs are separately hashed. The PIN is checked again for every payment. Never share verification codes, passwords or PINs.",
  },
  {
    keys: "qr scan receive recipient",
    answer:
      "Your QR contains your verified payee name and email. It does not contain your password, PIN or live photo.",
  },
  {
    keys: "status pending transfer history track reference",
    answer:
      "Open Recent activity to see payment references and status. All transfers in this package are marked Simulated because no real payment rail is connected.",
  },
  {
    keys: "limit amount maximum minimum",
    answer:
      "The prototype accepts positive amounts up to 100,000 per simulated payment. Real limits must be set by corridor, currency, risk level and regulatory requirements.",
  },
];
app.post("/api/ai-search", auth, (req, res) => {
  const question = String(req.body.question || "")
    .trim()
    .slice(0, 300);
  if (question.length < 2)
    return res.status(400).json({ error: "Enter a question." });
  const words = new Set(question.toLowerCase().match(/[a-z0-9]+/g) || []);
  const ranked = knowledge
    .map((item) => ({
      ...item,
      score: item.keys.split(" ").filter((k) => words.has(k)).length,
    }))
    .sort((a, b) => b.score - a.score);
  const answer = ranked[0].score
    ? ranked[0].answer
    : "I could not find a confident answer in the local payment guide. Try asking about fees, countries, verification, QR payments, security, limits or transfer status.";
  res.json({
    answer,
    mode: "Local AI-assisted search",
    disclaimer: "Informational demo response—not financial advice.",
  });
});

app.post("/api/transfers", auth, async (req, res) => {
  const { recipient, amount, currency, destinationCountry, pin, note } =
    req.body;
  const numericAmount = Number(amount);
  const store = load();
  const user = store.users.find((u) => u.id === req.user.id);
  if (!user || !user.verified || !user.phoneVerified)
    return res
      .status(403)
      .json({ error: "Email- and phone-verified account required." });
  if (!(await bcrypt.compare(String(pin || ""), user.pinHash)))
    return res.status(401).json({ error: "Incorrect payment PIN." });
  if (
    !/^\S+@\S+\.\S+$/.test(cleanEmail(recipient)) ||
    !Number.isFinite(numericAmount) ||
    numericAmount <= 0 ||
    numericAmount > 100000 ||
    !/^[A-Z]{3}$/.test(currency || "") ||
    !destinationCountry
  )
    return res.status(400).json({ error: "Enter valid transfer information." });
  const transfer = {
    id: "BP-" + crypto.randomBytes(4).toString("hex").toUpperCase(),
    senderId: user.id,
    recipient: cleanEmail(recipient),
    amount: numericAmount,
    currency,
    destinationCountry,
    note: String(note || "").slice(0, 120),
    status: "Simulated",
    createdAt: new Date().toISOString(),
  };
  store.transfers.push(transfer);
  save(store);
  res.status(201).json({ message: "Demo payment authorised.", transfer });
});

app.use((req, res) =>
  res.sendFile(path.join(__dirname, "public", "index.html")),
);
app.listen(PORT, () => console.log(`BorderPay demo: http://localhost:${PORT}`));
