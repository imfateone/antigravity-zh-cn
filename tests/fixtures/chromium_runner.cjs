const { spawn } = require('node:child_process');
const chromePath = process.argv[2];
const htmlUrl = process.argv[3];
const userDataDir = process.argv[4];

async function run() {
  const proc = spawn(chromePath, [
    '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--remote-debugging-port=0',
    `--user-data-dir=${userDataDir}`,
    'about:blank'
  ], { stdio: ['ignore', 'pipe', 'pipe'] });

  let wsUrl = '';
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('timeout waiting for DevTools ws')), 15000);
    proc.stderr.on('data', (chunk) => {
      const m = chunk.toString().match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (m) {
        wsUrl = m[1];
        clearTimeout(timer);
        resolve();
      }
    });
    proc.on('exit', (code) => { clearTimeout(timer); reject(new Error('chrome exited ' + code)); });
  });

  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let nextId = 1;
  const pending = new Map();
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(msg.error.message));
      else resolve(msg.result);
    }
  };
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    const payload = { id, method, params };
    if (sessionId) payload.sessionId = sessionId;
    ws.send(JSON.stringify(payload));
  });

  try {
    const { targetId } = await send('Target.createTarget', { url: htmlUrl });
    const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
    await send('Runtime.enable', {}, sessionId);
    let out = null;
    for (let i = 0; i < 400; i++) {
      const r = await send('Runtime.evaluate', {
        expression: 'window.__TEST_ERROR__ ? JSON.stringify({__error: String(window.__TEST_ERROR__)}) : (window.__TEST_DONE__ ? JSON.stringify(window.__TEST_RESULT__) : null)',
        returnByValue: true
      }, sessionId);
      if (r.result && r.result.value) {
        out = r.result.value;
        break;
      }
      await new Promise((r) => setTimeout(r, 25));
    }
    if (!out) throw new Error('headless chromium page timed out');
    console.log(out);
  } finally {
    try { ws.close(); } catch (_) {}
    try { proc.kill(); } catch (_) {}
  }
}
run().catch((e) => { console.error(e); process.exit(1); });

