import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const mode = process.argv[2] ?? "check";
const root = process.cwd();
const messagesDir = path.join(root, "messages");
const locales = ["ru", "kz", "en"];
const requiredKeys = [
  "seo.siteTitle",
  "seo.siteDescription",
  "seo.home.title",
  "seo.search.title",
  "seo.search.titleWithQuery",
  "seo.service.title",
  "seo.clinic.title",
  "share.copy",
  "share.copied",
];

const source = readLocale("ru");
let hadErrors = false;

for (const locale of locales) {
  const current = readLocale(locale);
  const missing = difference(flattenKeys(source), flattenKeys(current));
  const extra = difference(flattenKeys(current), flattenKeys(source));
  const missingRequired = requiredKeys.filter((key) => get(current, key) === undefined);

  if (locale !== "ru" && (mode === "sync" || mode === "translate")) {
    const next = mergeMissing(source, current);
    if (mode === "translate" && process.env.OPENROUTER_API_KEY) {
      await translateMissing(next, missing, locale);
    } else if (mode === "translate") {
      console.log(`[i18n] ${locale}: OPENROUTER_API_KEY not set; copied missing source strings.`);
    }
    writeLocale(locale, next);
  }

  if (missing.length || extra.length || missingRequired.length) {
    hadErrors = true;
    console.log(`[i18n] ${locale}: missing=${missing.length}, extra=${extra.length}, missingRequired=${missingRequired.length}`);
    if (missing.length) console.log(`  missing: ${missing.slice(0, 20).join(", ")}${missing.length > 20 ? " ..." : ""}`);
    if (extra.length) console.log(`  extra: ${extra.slice(0, 20).join(", ")}${extra.length > 20 ? " ..." : ""}`);
    if (missingRequired.length) console.log(`  missing required: ${missingRequired.join(", ")}`);
  } else {
    console.log(`[i18n] ${locale}: ok`);
  }
}

if (mode === "check" && hadErrors) {
  process.exitCode = 1;
}

function readLocale(locale) {
  return JSON.parse(fs.readFileSync(path.join(messagesDir, `${locale}.json`), "utf8"));
}

function writeLocale(locale, value) {
  fs.writeFileSync(path.join(messagesDir, `${locale}.json`), `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function flattenKeys(value, prefix = "") {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  return Object.entries(value).flatMap(([key, child]) => {
    const next = prefix ? `${prefix}.${key}` : key;
    return child && typeof child === "object" && !Array.isArray(child) ? flattenKeys(child, next) : [next];
  });
}

function difference(left, right) {
  const rightSet = new Set(right);
  return left.filter((key) => !rightSet.has(key));
}

function mergeMissing(sourceValue, targetValue) {
  if (!sourceValue || typeof sourceValue !== "object" || Array.isArray(sourceValue)) return targetValue ?? sourceValue;
  const next = { ...(targetValue && typeof targetValue === "object" && !Array.isArray(targetValue) ? targetValue : {}) };
  for (const [key, value] of Object.entries(sourceValue)) {
    if (!(key in next)) {
      next[key] = value;
    } else if (value && typeof value === "object" && !Array.isArray(value)) {
      next[key] = mergeMissing(value, next[key]);
    }
  }
  return next;
}

function get(value, dottedKey) {
  return dottedKey.split(".").reduce((current, key) => {
    if (current && typeof current === "object" && key in current) return current[key];
    return undefined;
  }, value);
}

function set(value, dottedKey, nextValue) {
  const parts = dottedKey.split(".");
  let current = value;
  for (const part of parts.slice(0, -1)) {
    current[part] ??= {};
    current = current[part];
  }
  current[parts.at(-1)] = nextValue;
}

async function translateMissing(target, missingKeys, locale) {
  if (!missingKeys.length) return;
  const payload = Object.fromEntries(missingKeys.map((key) => [key, get(source, key)]));
  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
    },
    body: JSON.stringify({
      model: process.env.OPENROUTER_MODEL || "openai/gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "Translate UI/SEO strings from Russian. Return only compact JSON with the same keys. Preserve placeholders like {query}, {city}, {service}, {clinic}.",
        },
        { role: "user", content: JSON.stringify({ locale, strings: payload }) },
      ],
      response_format: { type: "json_object" },
    }),
  });
  if (!response.ok) {
    console.log(`[i18n] ${locale}: OpenRouter request failed with ${response.status}; copied source strings.`);
    return;
  }
  const data = await response.json();
  const content = data?.choices?.[0]?.message?.content;
  if (!content) return;
  const translated = JSON.parse(content);
  for (const key of missingKeys) {
    if (typeof translated[key] === "string") set(target, key, translated[key]);
  }
}
