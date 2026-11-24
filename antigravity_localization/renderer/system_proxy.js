// Antigravity Chinese Localization Engine - System Proxy Bridge
(() => {
  const PROBE_HTTPS_URLS = [
    'https://daily-cloudcode-pa.googleapis.com',
    'https://generativelanguage.googleapis.com',
  ];
  const PROBE_HTTP_URL = 'http://generativelanguage.googleapis.com';
  const LOOPBACK_NO_PROXY = ['localhost', '127.0.0.1', '::1'];
  const RESOLVE_TIMEOUT_MS = 1500;

  function parsePacProxyResult(pacStr) {
    if (!pacStr || typeof pacStr !== 'string') return null;
    const entries = pacStr.split(';');
    for (const rawEntry of entries) {
      const entry = rawEntry.trim();
      if (!entry) continue;
      if (/^DIRECT$/i.test(entry)) return null;
      const m = entry.match(/^(PROXY|HTTP|HTTPS|SOCKS5|SOCKS)\s+(\S+)$/i);
      if (!m) continue;
      const scheme = m[1].toUpperCase();
      const hostPort = m[2];
      if (scheme === 'PROXY' || scheme === 'HTTP') {
        return { url: 'http://' + hostPort, isSocks: false };
      }
      if (scheme === 'HTTPS') {
        return { url: 'https://' + hostPort, isSocks: false };
      }
      if (scheme === 'SOCKS5' || scheme === 'SOCKS') {
        return { url: 'socks5://' + hostPort, isSocks: true };
      }
    }
    return null;
  }

  function hasExplicitProxyEnv(envObj) {
    if (!envObj || typeof envObj !== 'object') return false;
    for (const key of Object.keys(envObj)) {
      const upper = key.toUpperCase();
      if (upper === 'HTTP_PROXY' || upper === 'HTTPS_PROXY' || upper === 'ALL_PROXY') {
        if (String(envObj[key] || '').trim() !== '') return true;
      }
    }
    return false;
  }

  function mergeNoProxy(existing) {
    const seen = new Set();
    const out = [];
    for (const rawPart of String(existing || '').split(',')) {
      const part = rawPart.trim();
      if (!part) continue;
      const lower = part.toLowerCase();
      if (!seen.has(lower)) {
        seen.add(lower);
        out.push(part);
      }
    }
    for (const loopback of LOOPBACK_NO_PROXY) {
      const lower = loopback.toLowerCase();
      if (!seen.has(lower)) {
        seen.add(lower);
        out.push(loopback);
      }
    }
    return out.join(',');
  }

  async function resolveProxyWithTimeout(sessionObj, url, timeoutMs = RESOLVE_TIMEOUT_MS) {
    if (!sessionObj || typeof sessionObj.resolveProxy !== 'function') return '';
    let timer = null;
    try {
      const timeoutPromise = new Promise((resolve) => {
        timer = setTimeout(() => resolve(''), timeoutMs);
        if (timer && typeof timer.unref === 'function') timer.unref();
      });
      const result = await Promise.race([
        Promise.resolve(sessionObj.resolveProxy(url)).catch(() => ''),
        timeoutPromise,
      ]);
      return typeof result === 'string' ? result : '';
    } catch (_) {
      return '';
    } finally {
      if (timer !== null) clearTimeout(timer);
    }
  }

  async function resolveSystemProxyUrls(sessionObj, timeoutMs = RESOLVE_TIMEOUT_MS) {
    if (!sessionObj || typeof sessionObj.resolveProxy !== 'function') return null;
    let httpsParsed = null;
    for (const probeUrl of PROBE_HTTPS_URLS) {
      const raw = await resolveProxyWithTimeout(sessionObj, probeUrl, timeoutMs);
      const parsed = parsePacProxyResult(raw);
      if (parsed) {
        httpsParsed = parsed;
        break;
      }
    }
    const rawHttp = await resolveProxyWithTimeout(sessionObj, PROBE_HTTP_URL, timeoutMs);
    const httpParsed = parsePacProxyResult(rawHttp);
    if (!httpsParsed && !httpParsed) return null;

    const httpProxy = (httpParsed || httpsParsed).url;
    const httpsProxy = (httpsParsed || httpParsed).url;
    const allProxy = (httpsParsed && httpsParsed.isSocks)
      ? httpsParsed.url
      : ((httpParsed && httpParsed.isSocks) ? httpParsed.url : null);
    return { httpProxy, httpsProxy, allProxy };
  }

  function applyTempProxyEnv(envObj, resolved) {
    if (!envObj || !resolved) return () => {};
    const updates = [
      ['HTTP_PROXY', resolved.httpProxy],
      ['HTTPS_PROXY', resolved.httpsProxy],
    ];
    if (resolved.allProxy) {
      updates.push(['ALL_PROXY', resolved.allProxy]);
    }

    const existingNoProxyKey = Object.keys(envObj).find((k) => k.toUpperCase() === 'NO_PROXY');
    const existingNoProxyVal = existingNoProxyKey ? envObj[existingNoProxyKey] : '';
    updates.push(['NO_PROXY', mergeNoProxy(existingNoProxyVal)]);

    const saved = [];
    const addedKeys = [];
    for (const [upperKey, nextVal] of updates) {
      if (!nextVal) continue;
      const matchingKeys = Object.keys(envObj).filter((k) => k.toUpperCase() === upperKey);
      for (const k of matchingKeys) {
        saved.push([k, envObj[k]]);
      }
      if (!Object.prototype.hasOwnProperty.call(envObj, upperKey)) {
        addedKeys.push(upperKey);
      }
      for (const k of matchingKeys) {
        envObj[k] = nextVal;
      }
      envObj[upperKey] = nextVal;
    }

    let restored = false;
    return function restoreTempProxyEnv() {
      if (restored) return;
      restored = true;
      for (const k of addedKeys) {
        delete envObj[k];
      }
      for (const [k, oldVal] of saved) {
        envObj[k] = oldVal;
      }
    };
  }

  const bridgeApi = {
    PROBE_HTTPS_URLS,
    PROBE_HTTP_URL,
    LOOPBACK_NO_PROXY,
    RESOLVE_TIMEOUT_MS,
    parsePacProxyResult,
    hasExplicitProxyEnv,
    mergeNoProxy,
    resolveProxyWithTimeout,
    resolveSystemProxyUrls,
    applyTempProxyEnv,
  };

  try {
    if (typeof exports === 'object' && exports !== null) {
      exports.__agSystemProxyBridge = bridgeApi;
    }
    if (typeof startLanguageServer === 'function' && !startLanguageServer.__agSystemProxyWrapped) {
      const { session } = require('electron');
      const origStartLanguageServer = startLanguageServer;
      let activeDepth = 0;
      let pendingRestore = null;

      startLanguageServer = async function wrappedStartLanguageServer(port, csrf, options) {
        if (
          activeDepth === 0 &&
          !pendingRestore &&
          String(process.env.ANTIGRAVITY_DISABLE_SYSTEM_PROXY_BRIDGE || '').trim() !== '1' &&
          !(options && options.wsl) &&
          !hasExplicitProxyEnv(process.env)
        ) {
          try {
            const resolved = await resolveSystemProxyUrls(session && session.defaultSession);
            if (resolved && activeDepth === 0 && !pendingRestore && !hasExplicitProxyEnv(process.env)) {
              pendingRestore = applyTempProxyEnv(process.env, resolved);
              console.log(
                '[SystemProxyBridge] Inherited OS system proxy for language_server:',
                resolved.httpsProxy || resolved.httpProxy
              );
            }
          } catch (err) {
            console.warn(
              '[SystemProxyBridge] Failed to resolve OS system proxy:',
              err && err.message ? err.message : err
            );
          }
        }
        activeDepth++;
        try {
          return await origStartLanguageServer.apply(this, arguments);
        } finally {
          activeDepth--;
          if (activeDepth === 0 && pendingRestore) {
            const restore = pendingRestore;
            pendingRestore = null;
            restore();
          }
        }
      };

      startLanguageServer.__agSystemProxyWrapped = true;
      if (typeof exports === 'object' && exports !== null) {
        exports.startLanguageServer = startLanguageServer;
      }
    }
  } catch (e) {
    console.warn('[SystemProxyBridge] init skipped:', e && e.message ? e.message : e);
  }
})();
