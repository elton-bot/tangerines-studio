// POST /api/contact: contact forms on paying clients' sites (public/clients/{slug}/).
// Each form posts its site slug. The recipient comes from the Vercel environment
// variable CLIENT_FORM_TO, so clients' addresses never sit in this public repo:
//   CLIENT_FORM_TO = {"harbor-street-auto-port-lewis": "owner@theirdomain.com", ...}
// A value can also be {"to": "owner@theirdomain.com", "name": "Harbor Street Auto"}.
// GET /api/contact?site={slug} answers {"enabled": true|false}.
"use strict";

const m = require("./_lib/mail");

function recipients() {
  try {
    const map = JSON.parse(process.env.CLIENT_FORM_TO || "{}");
    return map && typeof map === "object" ? map : {};
  } catch {
    return {};
  }
}

function target(site) {
  const v = recipients()[site];
  if (!v) return null;
  const to = typeof v === "string" ? v : v.to;
  if (!to || !m.isEmail(to)) return null;
  return { to, name: (typeof v === "object" && m.clean(v.name, 120)) || "" };
}

module.exports = async (req, res) => {
  const cfg = m.smtpConfig();
  if (req.method === "GET") {
    const site = m.clean(req.query && req.query.site, 80);
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Robots-Tag", "noindex");
    return res.status(200).json({ enabled: Boolean(cfg && target(site)) });
  }
  if (req.method !== "POST") {
    res.setHeader("Allow", "GET, POST");
    return res.status(405).json({ ok: false, error: "Method not allowed." });
  }
  const body = m.readBody(req);
  const page = typeof body.page === "string" && /^\/[A-Za-z0-9/_\-.]*$/.test(body.page) ? body.page : "/";
  if (!m.sameOrigin(req)) return m.reply(req, res, 403, { ok: false, error: "This form only works from its own website.", anchor: "contact" }, page);
  if (m.clean(body.company, 200)) return m.reply(req, res, 200, { ok: true, anchor: "contact" }, page);

  const site = m.clean(body.site, 80);
  const f = {
    name: m.clean(body.name, 100),
    phone: m.clean(body.phone, 40),
    email: m.clean(body.email, 200),
    service: m.clean(body.service, 120),
    vehicle: m.clean(body.vehicle, 120),
    times: m.clean(body.times, 120),
    message: m.cleanText(body.message, 3000),
  };
  const errors = {};
  if (!f.name) errors.name = "Please add your name.";
  if (!f.phone && !f.email) errors.phone = "Please add a phone number or an email address so we can reply.";
  if (f.email && !m.isEmail(f.email)) errors.email = "Please check the email address.";
  if (f.phone && !/^[0-9+().\s-]{7,40}$/.test(f.phone)) errors.phone = "Please check the phone number.";
  if (Object.keys(errors).length) return m.reply(req, res, 400, { ok: false, error: "Please check the highlighted fields.", errors, anchor: "contact" }, page);

  if (m.rateLimited(m.clientIp(req))) return m.reply(req, res, 429, { ok: false, fallback: true, error: "Too many messages from this connection. Please call or email instead.", anchor: "contact" }, page);
  const t = target(site);
  if (!cfg || !t) return m.reply(req, res, 503, { ok: false, fallback: true, error: "The form is not switched on yet. Please call or email instead.", anchor: "contact" }, page);

  const lines = [`Name: ${f.name}`, `Phone: ${f.phone || "(not given)"}`, `Email: ${f.email || "(not given)"}`];
  if (f.service) lines.push(`Service: ${f.service}`);
  if (f.vehicle) lines.push(`Vehicle: ${f.vehicle}`);
  if (f.times) lines.push(`Best times: ${f.times}`);
  lines.push(`Message: ${f.message ? f.message.replace(/\n/g, "\n  ") : "(none)"}`, "", `Sent from the contact form on ${req.headers.host}${page}, ${new Date().toISOString()}`);

  try {
    await m.sendMail(cfg, {
      fromName: t.name ? `${t.name} website` : "Website form",
      to: t.to,
      replyTo: f.email || null,
      subject: `Website message from ${f.name}`,
      text: lines.join("\n"),
    });
  } catch (e) {
    console.error("contact form: send failed for", site, e.message);
    return m.reply(req, res, 502, { ok: false, fallback: true, error: "Sorry, that did not go through. Please call or email instead.", anchor: "contact" }, page);
  }
  return m.reply(req, res, 200, { ok: true, anchor: "contact" }, page);
};
