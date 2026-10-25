// Shared helpers for the form functions (api/request.js, api/contact.js).
// Files under api/_lib are not served as functions.
//
// Mail goes out through DreamHost SMTP over SSL (smtp.dreamhost.com:465) with a
// small built-in client, so the functions need no npm packages and no build step.
//
// Environment variables (set by Elton in Vercel, never committed):
//   SMTP_USER   the DreamHost mailbox that sends, e.g. forms@tangerinesstudio.com
//   SMTP_PASS   its password
//   SMTP_HOST   optional, default smtp.dreamhost.com
//   SMTP_PORT   optional, default 465
"use strict";

const tls = require("node:tls");
const crypto = require("node:crypto");

const EMAIL_RE = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;

function smtpConfig() {
  const user = process.env.SMTP_USER || "";
  const pass = process.env.SMTP_PASS || "";
  if (!user || !pass || !EMAIL_RE.test(user)) return null;
  return {
    host: process.env.SMTP_HOST || "smtp.dreamhost.com",
    port: Number(process.env.SMTP_PORT || 465),
    user,
    pass,
  };
}

// One line, no control characters: safe for a header or a plain-text line.
function clean(value, max) {
  return String(value == null ? "" : value)
    .replace(/[\u0000-\u001f\u007f]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, max);
}

// Multi-line text: keep line breaks, drop other control characters.
function cleanText(value, max) {
  return String(value == null ? "" : value)
    .replace(/\r\n?/g, "\n")
    .replace(/[\u0000-\u0009\u000b-\u001f\u007f]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
    .slice(0, max);
}

function isEmail(s) {
  return s.length <= 200 && EMAIL_RE.test(s);
}

function encodeHeader(s) {
  return /^[\x20-\x7e]*$/.test(s) ? s : "=?UTF-8?B?" + Buffer.from(s, "utf8").toString("base64") + "?=";
}

function displayName(name, email) {
  const n = clean(name, 80).replace(/["\\]/g, "");
  return n ? `${encodeHeader(`"${n}"`)} <${email}>` : `<${email}>`;
}

function buildMessage({ fromName, from, to, replyTo, subject, text }) {
  const domain = from.split("@")[1];
  const body = Buffer.from(text.replace(/\n/g, "\r\n"), "utf8").toString("base64").replace(/.{76}/g, "$&\r\n");
  const headers = [
    `From: ${displayName(fromName, from)}`,
    `To: <${to}>`,
    replyTo ? `Reply-To: <${replyTo}>` : null,
    `Subject: ${encodeHeader(clean(subject, 200))}`,
    `Date: ${new Date().toUTCString().replace("GMT", "+0000")}`,
    `Message-ID: <${crypto.randomUUID()}@${domain}>`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: base64",
  ].filter(Boolean);
  return headers.join("\r\n") + "\r\n\r\n" + body + "\r\n";
}

// Minimal SMTP over implicit TLS: EHLO, AUTH PLAIN, MAIL, RCPT, DATA, QUIT.
function smtpSend(cfg, { from, to, raw }) {
  return new Promise((resolve, reject) => {
    const sock = tls.connect({ host: cfg.host, port: cfg.port, servername: cfg.host });
    let buf = "";
    let step = 0;
    let done = false;
    const auth = Buffer.from(`\u0000${cfg.user}\u0000${cfg.pass}`, "utf8").toString("base64");
    const steps = [
      { expect: [220], send: "EHLO tangerinesstudio.com" },
      { expect: [250], send: `AUTH PLAIN ${auth}` },
      { expect: [235], send: `MAIL FROM:<${from}>` },
      { expect: [250], send: `RCPT TO:<${to}>` },
      { expect: [250, 251], send: "DATA" },
      { expect: [354], send: raw + "." },
      { expect: [250], send: "QUIT" },
    ];
    const finish = (err) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      sock.destroy();
      err ? reject(err) : resolve();
    };
    const timer = setTimeout(() => finish(new Error("SMTP timeout")), 20000);
    sock.setEncoding("utf8");
    sock.on("error", (e) => finish(e));
    sock.on("data", (chunk) => {
      buf += chunk;
      // a reply is complete when its last line is "NNN text" (no dash)
      const lines = buf.split("\r\n");
      const last = lines[lines.length - 2];
      if (!last || !/^\d{3} /.test(last)) return;
      buf = "";
      const code = Number(last.slice(0, 3));
      const s = steps[step];
      if (!s) return finish();
      if (!s.expect.includes(code)) {
        return finish(new Error(`SMTP step ${step} got ${code}`)); // never log the reply: it can echo credentials
      }
      sock.write(s.send + "\r\n");
      step += 1;
      if (step === steps.length) setTimeout(() => finish(), 300);
    });
  });
}

async function sendMail(cfg, { fromName, to, replyTo, subject, text }) {
  const raw = buildMessage({ fromName, from: cfg.user, to, replyTo, subject, text });
  await smtpSend(cfg, { from: cfg.user, to, raw });
}

// Basic per-instance rate limit: max requests per window per IP.
const hits = new Map();
function rateLimited(ip, max = 5, windowMs = 15 * 60 * 1000) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter((t) => now - t < windowMs);
  list.push(now);
  hits.set(ip, list);
  if (hits.size > 5000) hits.clear();
  return list.length > max;
}

function clientIp(req) {
  return clean((req.headers["x-forwarded-for"] || "").split(",")[0] || req.socket?.remoteAddress || "unknown", 64);
}

// Only accept posts from a page on the same host as the function.
function sameOrigin(req) {
  const origin = req.headers.origin;
  if (!origin) return true; // plain form posts from some browsers send no Origin
  try {
    return new URL(origin).host === req.headers.host;
  } catch {
    return false;
  }
}

function wantsJson(req) {
  return /json/.test(req.headers.accept || "") || /json/.test(req.headers["content-type"] || "");
}

function readBody(req) {
  const b = req.body;
  if (b && typeof b === "object") return b;
  if (typeof b === "string") {
    try {
      return JSON.parse(b);
    } catch {
      return Object.fromEntries(new URLSearchParams(b));
    }
  }
  return {};
}

// JSON for the page's script; a redirect back to the form for plain form posts.
function reply(req, res, status, data, backTo) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Robots-Tag", "noindex");
  if (wantsJson(req) || !backTo) {
    res.status(status).json(data);
    return;
  }
  const state = data.ok ? "sent" : "error";
  res.setHeader("Location", `${backTo}?form=${state}#${data.anchor || "request"}`);
  res.status(303).end();
}

module.exports = { smtpConfig, clean, cleanText, isEmail, sendMail, rateLimited, clientIp, sameOrigin, readBody, reply };
