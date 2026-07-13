/*
 * Offline certificate verifier — pure client-side Ed25519 verification.
 *
 * Verifies a certificate's "verification block" against the authority's public
 * key with no server round-trip, so a field inspector with no connectivity can
 * confirm authenticity. The canonicalisation here must match the Python signer
 * byte-for-byte (json.dumps sort_keys, separators (",",":"), ensure_ascii=False).
 *
 * Runs unchanged in the browser and in Node (for tests) — both expose
 * globalThis.crypto.subtle and base64 helpers.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) module.exports = factory();
  else root.OfflineVerify = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function b64ToBytes(b64) {
    const bin = (typeof atob !== "undefined")
      ? atob(b64)
      : Buffer.from(b64, "base64").toString("binary");
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  function urlsafeB64ToBytes(b64) {
    let s = b64.trim().replace(/-/g, "+").replace(/_/g, "/");
    while (s.length % 4) s += "=";
    return b64ToBytes(s);
  }

  // Canonical JSON identical to the Python signer's canonical_bytes().
  function canonicalize(v) {
    if (v === null) return "null";
    const t = typeof v;
    if (t === "number") return JSON.stringify(v);
    if (t === "boolean") return v ? "true" : "false";
    if (t === "string") return JSON.stringify(v);
    if (Array.isArray(v)) return "[" + v.map(canonicalize).join(",") + "]";
    const keys = Object.keys(v).sort();
    return "{" + keys.map(function (k) {
      return JSON.stringify(k) + ":" + canonicalize(v[k]);
    }).join(",") + "}";
  }

  function decodeBlock(block) {
    const bytes = urlsafeB64ToBytes(block);
    const compact = JSON.parse(new TextDecoder().decode(bytes));
    return {
      payload: compact.p,
      signature: compact.s,
      key_id: compact.k,
      alg: compact.a || "Ed25519",
    };
  }

  function pemToDer(pem) {
    const b64 = pem
      .replace(/-----BEGIN PUBLIC KEY-----/, "")
      .replace(/-----END PUBLIC KEY-----/, "")
      .replace(/\s+/g, "");
    return b64ToBytes(b64);
  }

  async function importKey(pem) {
    return crypto.subtle.importKey(
      "spki", pemToDer(pem), { name: "Ed25519" }, false, ["verify"]);
  }

  /*
   * keys: object mapping key_id -> PEM (or a single PEM string).
   * Returns { valid: bool, payload: object|null, error: string|null }.
   */
  async function verifyBlock(block, keys) {
    let signed;
    try {
      signed = decodeBlock(block);
    } catch (e) {
      return { valid: false, payload: null, error: "Could not read the verification code." };
    }
    if (!signed.payload || !signed.signature || (signed.alg || "Ed25519") !== "Ed25519") {
      return { valid: false, payload: null, error: "Unsupported or incomplete verification code." };
    }

    const keyMap = (typeof keys === "string") ? { _single: keys } : (keys || {});
    const candidates = [];
    if (signed.key_id && keyMap[signed.key_id]) candidates.push(keyMap[signed.key_id]);
    for (const k in keyMap) if (keyMap[k] && candidates.indexOf(keyMap[k]) === -1) candidates.push(keyMap[k]);

    const msg = new TextEncoder().encode(canonicalize(signed.payload));
    const sig = b64ToBytes(signed.signature);

    for (const pem of candidates) {
      try {
        const key = await importKey(pem);
        const ok = await crypto.subtle.verify("Ed25519", key, sig, msg);
        if (ok) return { valid: true, payload: signed.payload, error: null };
      } catch (e) {
        // WebCrypto may lack Ed25519 on very old browsers — report clearly.
        if (String(e && e.name) === "NotSupportedError") {
          return { valid: false, payload: null,
                   error: "This browser cannot verify offline. Use the online verifier or a current browser." };
        }
      }
    }
    return { valid: false, payload: signed.payload, error: null };
  }

  return { canonicalize: canonicalize, decodeBlock: decodeBlock, verifyBlock: verifyBlock };
});
