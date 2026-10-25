// POST /api/request: the free homepage request form on tangerinesstudio.com.
// Emails each request to elton@tangerinesstudio.com through DreamHost SMTP.
// GET /api/request answers {"enabled": true|false} so the page only shows the
// form once SMTP_USER and SMTP_PASS are set in Vercel. Until then, and whenever
// sending fails, the page keeps the email link.
"use strict";

const m = require("./_lib/mail");

const TO = "elton@tangerinesstudio.com";

function normalizeWebsite(raw) {
  let s = m.clean(raw, 200);
  if (!s) return "";
  if (!/^https?:\/\//i.test(s)) s = "https://" + s;
  try {
    const u = new URL(s);
    if (!/\./.test(u.hostname) || /\s/.test(u.hostname)) return "";
    return u.toString().replace(/\/$/, "");
  } catch {
    return "";
  }
}

module.exports = async (req, res) => {
  const cfg = m.smtpConfig();
  if (req.method === "GET") {
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Robots-Tag", "noindex");
    return res.status(200).json({ enabled: Boolean(cfg) });
  }
  if (req.method !== "POST") {
    res.setHeader("Allow", "GET, POST");
    return res.status(405).json({ ok: false, error: "Method not allowed." });
  }
  const back = "/";
  if (!m.sameOrigin(req)) return m.reply(req, res, 403, { ok: false, error: "This form only works from tangerinesstudio.com." }, back);

  const body = m.readBody(req);
  // Honeypot: people never see this field, so anything in it is a bot. Pretend it worked.
  if (m.clean(body.company, 200)) return m.reply(req, res, 200, { ok: true }, back);

  const f = {
    name: m.clean(body.name, 100),
    business: m.clean(body.business, 140),
    website: normalizeWebsite(body.website),
    email: m.clean(body.email, 200),
    phone: m.clean(body.phone, 40),
    message: m.cleanText(body.message, 2000),
  };
  const errors = {};
  if (!f.name) errors.name = "Please add your name.";
  if (!f.business) errors.business = "Please add your business name.";
  if (!f.website) errors.website = "Please add your website address, for example yourbusiness.com.";
  if (!m.isEmail(f.email)) errors.email = "Please add an email address we can reply to.";
  if (f.phone && !/^[0-9+().\s-]{7,40}$/.test(f.phone)) errors.phone = "Please check the phone number, or leave it empty.";
  if (Object.keys(errors).length) return m.reply(req, res, 400, { ok: false, error: "Please check the highlighted fields.", errors }, back);

  if (m.rateLimited(m.clientIp(req))) {
    return m.reply(req, res, 429, { ok: false, fallback: true, error: "Too many requests from this connection. Please email elton@tangerinesstudio.com instead." }, back);
  }
  if (!cfg) {
    return m.reply(req, res, 503, { ok: false, fallback: true, error: "The form is not switched on yet. Please email elton@tangerinesstudio.com instead." }, back);
  }

  const text = [
    `Name: ${f.name}`,
    `Business name: ${f.business}`,
    `Website: ${f.website}`,
    `Email: ${f.email}`,
    `Phone: ${f.phone || "(not given)"}`,
    `Message: ${f.message ? f.message.replace(/\n/g, "\n  ") : "(none)"}`,
    "",
    `Sent from the request form on tangerinesstudio.com, ${new Date().toISOString()}`,
  ].join("\n");

  try {
    await m.sendMail(cfg, {
      fromName: "Tangerines Studio website",
      to: process.env.REQUEST_TO && m.isEmail(process.env.REQUEST_TO) ? process.env.REQUEST_TO : TO,
      replyTo: f.email,
      subject: `Website request: ${f.business}`,
      text,
    });
  } catch (e) {
    console.error("request form: send failed:", e.message);
    return m.reply(req, res, 502, { ok: false, fallback: true, error: "Sorry, that did not go through. Please email elton@tangerinesstudio.com instead." }, back);
  }
  return m.reply(req, res, 200, { ok: true }, back);
};
