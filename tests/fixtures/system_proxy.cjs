const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const rendererDir = process.argv[2];
const systemProxyJs = fs.readFileSync(path.join(rendererDir, 'system_proxy.js'), 'utf8');

function createHarness({ resolveProxyImpl, initialEnv = {} } = {}) {
  const spawned = [];
  const logs = [];
  const warns = [];
  const sandboxExports = {};
  const sandboxModule = { exports: sandboxExports };
  const sandboxEnv = { ...initialEnv };

  const lsPrelude = `
"use strict";
exports.startLanguageServer = startLanguageServer;
exports.startAndMonitorLanguageServer = startAndMonitorLanguageServer;
exports.simulateCrashRestart = simulateCrashRestart;
async function startLanguageServer(port, csrf, options = {}) {
  __recordSpawn({ port, csrf, options, env: { ...process.env } });
  return { port: 43210 };
}
async function startAndMonitorLanguageServer(port, csrf, options = {}) {
  return await startLanguageServer(port, csrf, options);
}
async function simulateCrashRestart(port, csrf, options = {}) {
  return await startLanguageServer(port, csrf, options);
}
`;

  const sandbox = {
    exports: sandboxExports,
    module: sandboxModule,
    process: { env: sandboxEnv, platform: process.platform },
    console: {
      log: (...args) => logs.push(args.join(' ')),
      warn: (...args) => warns.push(args.join(' ')),
      error: (...args) => warns.push(args.join(' ')),
    },
    setTimeout,
    clearTimeout,
    require: (id) => {
      if (id === 'electron') {
        return {
          session: {
            defaultSession: {
              resolveProxy: resolveProxyImpl,
            },
          },
        };
      }
      throw new Error('Unexpected require: ' + id);
    },
    __recordSpawn: (entry) => spawned.push(entry),
  };

  vm.runInNewContext(lsPrelude + '\n' + systemProxyJs, sandbox, { filename: 'languageServer.js' });
  return {
    exports: sandboxModule.exports,
    bridge: sandboxModule.exports.__agSystemProxyBridge,
    env: sandboxEnv,
    spawned,
    logs,
    warns,
  };
}

(async () => {
  const { bridge } = createHarness();

  // 1. Unit tests for parsePacProxyResult
  assert.equal(bridge.parsePacProxyResult(''), null);
  assert.equal(bridge.parsePacProxyResult('DIRECT'), null);
  assert.equal(bridge.parsePacProxyResult('DIRECT; PROXY 127.0.0.1:7897'), null);
  assert.deepStrictEqual({ ...bridge.parsePacProxyResult('PROXY 127.0.0.1:7897') }, {
    url: 'http://127.0.0.1:7897',
    isSocks: false,
  });
  assert.deepStrictEqual({ ...bridge.parsePacProxyResult('PROXY 127.0.0.1:7897; DIRECT') }, {
    url: 'http://127.0.0.1:7897',
    isSocks: false,
  });
  assert.deepStrictEqual({ ...bridge.parsePacProxyResult('HTTPS proxy.corp:443') }, {
    url: 'https://proxy.corp:443',
    isSocks: false,
  });
  assert.deepStrictEqual({ ...bridge.parsePacProxyResult('SOCKS5 127.0.0.1:7898') }, {
    url: 'socks5://127.0.0.1:7898',
    isSocks: true,
  });
  assert.deepStrictEqual({ ...bridge.parsePacProxyResult('SOCKS [::1]:1080') }, {
    url: 'socks5://[::1]:1080',
    isSocks: true,
  });
  assert.deepStrictEqual({ ...bridge.parsePacProxyResult('SOCKS4 127.0.0.1:1080; PROXY 127.0.0.1:7897') }, {
    url: 'http://127.0.0.1:7897',
    isSocks: false,
  });

  // 2. Unit tests for mergeNoProxy and hasExplicitProxyEnv
  assert.equal(bridge.mergeNoProxy(''), 'localhost,127.0.0.1,::1');
  assert.equal(
    bridge.mergeNoProxy('corp.local, LOCALHOST, 10.0.0.1'),
    'corp.local,LOCALHOST,10.0.0.1,127.0.0.1,::1'
  );
  assert.equal(bridge.hasExplicitProxyEnv({}), false);
  assert.equal(bridge.hasExplicitProxyEnv({ HTTP_PROXY: '   ', NO_PROXY: 'localhost' }), false);
  assert.equal(bridge.hasExplicitProxyEnv({ http_proxy: 'http://127.0.0.1:8888' }), true);
  assert.equal(bridge.hasExplicitProxyEnv({ HTTPS_PROXY: 'http://127.0.0.1:8888' }), true);
  assert.equal(bridge.hasExplicitProxyEnv({ ALL_PROXY: 'socks5://127.0.0.1:7898' }), true);

  // 3. Unit test for resolveProxyWithTimeout
  const timedOut = await bridge.resolveProxyWithTimeout(
    { resolveProxy: () => new Promise(() => {}) },
    'https://daily-cloudcode-pa.googleapis.com',
    25
  );
  assert.equal(timedOut, '');

  // 4. Integration Scenario 1: System proxy enabled -> inherited on initial start & crash restart, restored cleanly after
  {
    const h = createHarness({
      resolveProxyImpl: async () => 'PROXY 127.0.0.1:7897',
      initialEnv: { no_proxy: 'corp.local' },
    });
    await h.exports.startAndMonitorLanguageServer(0, 'csrf-1', {});
    await h.exports.simulateCrashRestart(0, 'csrf-1', {});
    assert.equal(h.spawned.length, 2);
    for (const s of h.spawned) {
      assert.equal(s.env.HTTP_PROXY, 'http://127.0.0.1:7897');
      assert.equal(s.env.HTTPS_PROXY, 'http://127.0.0.1:7897');
      assert.equal(s.env.NO_PROXY, 'corp.local,localhost,127.0.0.1,::1');
    }
    assert.equal(h.env.HTTP_PROXY, undefined);
    assert.equal(h.env.HTTPS_PROXY, undefined);
    assert.equal(h.env.NO_PROXY, undefined);
    assert.equal(h.env.no_proxy, 'corp.local');
  }

  // 5. Integration Scenario 1b: SOCKS5 system proxy also sets ALL_PROXY and cleans up
  {
    const h = createHarness({
      resolveProxyImpl: async () => 'SOCKS5 127.0.0.1:7898',
    });
    await h.exports.startAndMonitorLanguageServer(0, 'csrf-socks', {});
    assert.equal(h.spawned[0].env.HTTP_PROXY, 'socks5://127.0.0.1:7898');
    assert.equal(h.spawned[0].env.HTTPS_PROXY, 'socks5://127.0.0.1:7898');
    assert.equal(h.spawned[0].env.ALL_PROXY, 'socks5://127.0.0.1:7898');
    assert.equal(h.spawned[0].env.NO_PROXY, 'localhost,127.0.0.1,::1');
    assert.equal(h.env.ALL_PROXY, undefined);
  }

  // 6. Integration Scenario 2: System proxy disabled (DIRECT / TUN mode) -> no proxy env injected
  {
    const h = createHarness({
      resolveProxyImpl: async () => 'DIRECT',
    });
    await h.exports.startAndMonitorLanguageServer(0, 'csrf-2', {});
    assert.equal(h.spawned[0].env.HTTP_PROXY, undefined);
    assert.equal(h.spawned[0].env.HTTPS_PROXY, undefined);
    assert.equal(h.spawned[0].env.ALL_PROXY, undefined);
  }

  // 7. Integration Scenario 3: Explicit user HTTPS_PROXY respected without override
  {
    const h = createHarness({
      resolveProxyImpl: async () => 'PROXY 127.0.0.1:7897',
      initialEnv: { HTTPS_PROXY: 'http://127.0.0.1:9999' },
    });
    await h.exports.startAndMonitorLanguageServer(0, 'csrf-3', {});
    assert.equal(h.spawned[0].env.HTTPS_PROXY, 'http://127.0.0.1:9999');
    assert.equal(h.spawned[0].env.HTTP_PROXY, undefined);
  }

  // 8. Integration Scenario 4: WSL launch skips OS proxy bridging
  {
    let called = false;
    const h = createHarness({
      resolveProxyImpl: async () => {
        called = true;
        return 'PROXY 127.0.0.1:7897';
      },
    });
    await h.exports.startAndMonitorLanguageServer(0, 'csrf-4', { wsl: { distro: 'Ubuntu' } });
    assert.equal(called, false);
    assert.equal(h.spawned[0].env.HTTP_PROXY, undefined);
  }

  // 9. Integration Scenario 5: ANTIGRAVITY_DISABLE_SYSTEM_PROXY_BRIDGE=1 disables bridge
  {
    let called = false;
    const h = createHarness({
      resolveProxyImpl: async () => {
        called = true;
        return 'PROXY 127.0.0.1:7897';
      },
      initialEnv: { ANTIGRAVITY_DISABLE_SYSTEM_PROXY_BRIDGE: '1' },
    });
    await h.exports.startAndMonitorLanguageServer(0, 'csrf-5', {});
    assert.equal(called, false);
    assert.equal(h.spawned[0].env.HTTP_PROXY, undefined);
  }

  // 10. Integration Scenario 6: resolveProxy throwing error or timing out -> fail-open startup succeeds
  {
    const hErr = createHarness({
      resolveProxyImpl: async () => {
        throw new Error('session unavailable');
      },
    });
    const resErr = await hErr.exports.startAndMonitorLanguageServer(0, 'csrf-6a', {});
    assert.deepStrictEqual({ ...resErr }, { port: 43210 });
    assert.equal(hErr.spawned.length, 1);

    const hHang = createHarness({
      resolveProxyImpl: () => new Promise(() => {}),
    });
    const resHang = await hHang.exports.startAndMonitorLanguageServer(0, 'csrf-6b', {});
    assert.deepStrictEqual({ ...resHang }, { port: 43210 });
    assert.equal(hHang.spawned.length, 1);
  }
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
