/** Standalone browser test. The loopback server supplies synthetic history records. */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { createServer } from 'vite';

const fixture = spawn(process.env.MEMBER6_PYTHON || path.resolve('../backend/.venv/Scripts/python.exe'),
  ['-B', '-m', 'tests.repair_history_browser_fixture'], { cwd: '../backend', windowsHide: true,
    env: { ...process.env, DATABASE_URL: 'sqlite:///:memory:' }, stdio: ['ignore', 'pipe', 'inherit'] });
const fixturePort = await new Promise((resolve, reject) => {
  fixture.once('error', reject);
  fixture.once('exit', code => reject(Error('Fixture exited: ' + code)));
  fixture.stdout.once('data', data => resolve(Number(data.toString().trim())));
});
assert(Number.isInteger(fixturePort) && fixturePort > 0);
let reads = 0;
const plugin = {
  name: 'fixture-history', configureServer(server) {
    server.middlewares.use(async (req, res, next) => {
      const url = new URL(req.url, 'http://localhost');
      if (url.pathname === '/fixture') {
        res.setHeader('Set-Cookie', 'fixture_session=reader; HttpOnly; SameSite=Strict; Path=/');
        res.setHeader('Content-Type', 'text/html');
        return res.end(await server.transformIndexHtml('/fixture', '<div id="root"></div><script type="module" src="/@id/virtual:history-test"></script>'));
      }
      if (url.pathname !== '/api/v1/repair/history') return next();
      reads++;
      const reply = await fetch('http://127.0.0.1:' + fixturePort + url.pathname + url.search,
        { headers: { cookie: req.headers.cookie ?? '' } });
      res.statusCode = reply.status;
      res.setHeader('Content-Type', 'application/json');
      res.end(await reply.text());
    });
  },
  resolveId(id) { if (id === 'virtual:history-test') return id; },
  load(id) {
    if (id === 'virtual:history-test') return `
      import React from 'react';
      import {createRoot} from 'react-dom/client';
      import {RepairHistory} from '/src/components/activity/RepairHistory.tsx';
      const root=createRoot(document.querySelector('#root'));
      window.selectRun=id=>root.render(React.createElement(RepairHistory,{scope:{workflow_id:id,workflow_revision_id:'demo-original',execution_run_id:'demo-run'}}));
      window.selectRun('first');`;
  },
};

const server = await createServer({ plugins: [plugin], server: { host: '127.0.0.1', port: 0 } });
let chrome, ws;
async function until(read, label) {
  for (let i=0; i<150; i++) {
    try { const value=await read(); if(value) return value; } catch { /* starting */ }
    await delay(100);
  }
  throw Error('Timed out waiting for ' + label);
}
try {
  await server.listen();
  const profile = await mkdtemp(path.join(tmpdir(), 'repair-history-'));
  chrome = spawn(process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    ['--headless=new','--disable-gpu','--disable-background-networking','--no-first-run','--remote-debugging-port=0',
      '--user-data-dir='+profile,'about:blank'], { stdio:'ignore', windowsHide:true });
  const port = await until(async () => (await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0], 'Chrome');
  const [tab] = await (await fetch('http://127.0.0.1:'+port+'/json/list')).json();
  ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise(resolve => ws.addEventListener('open', resolve, {once:true}));
  let sequence=0;
  const replies = new Map();
  ws.addEventListener('message', event => {
    const msg=JSON.parse(event.data);
    if (replies.has(msg.id)) { replies.get(msg.id)(msg.result); replies.delete(msg.id); }
  });
  const send=(method,params={})=>new Promise(resolve=>{
    const id=++sequence; replies.set(id,resolve); ws.send(JSON.stringify({id,method,params}));
  });
  const evaluate=async expression=>(await send('Runtime.evaluate',{expression,returnByValue:true})).result.value;
  const visible=async label=>(await evaluate('document.body.innerText')).includes(label);
  await send('Page.navigate',{url:'http://127.0.0.1:'+server.httpServer.address().port+'/fixture'});
  await until(()=>visible('Promotion confirmed'),'verified history');
  const before=reads;
  await send('Page.reload',{ignoreCache:true});
  await until(async()=>reads>before && await visible('recovery-first'),'server reload');
  await evaluate("window.selectRun('slow')");
  await until(()=>visible('Workflow slow'),'slow scope');
  await evaluate("window.selectRun('rollback')");
  await until(()=>visible('Rollback confirmed'),'rollback history');
  await delay(650);
  assert(await visible('Regression regression-shape · failed'));
  assert.equal(await visible('recovery-slow'),false);
  assert.equal(await visible('Promotion confirmed'),false);
  console.log('Chrome fixture passed: verified promotion, backend reload, scope switch, stale response, regression failure and rollback.');
} finally {
  ws?.close(); chrome?.kill(); fixture.kill(); await server.close();
}
