// Smoke test: live ADS-B integration in the built earth page.
// Run on pluto-omarchy: node adsb-smoke.mjs
// Production order: poller writes the JSONP file BEFORE the page boots;
// the page auto-starts live mode from it. Spawn the poller with no
// browser open (spawnSync with a live playwright browser is flaky here).
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import { chromium } from 'playwright';

const PAGE = process.env.EARTH_PAGE || 'file://' + process.env.HOME + '/.cache/omarchy-earth/earth.html';
const POLLER = process.env.HOME + '/github/omarchy-earth/bin/adsb-poller.py';
const results = [];
const check = (name, ok, extra = '') => {
  results.push({ name, ok, extra });
  console.log((ok ? 'PASS' : 'FAIL') + '  ' + name + (extra ? '  [' + extra + ']' : ''));
};

// 1. Run the poller for real BEFORE any browser exists (widget order)
let pollRc = 0, pollErr = '', pollOut = '';
try {
  execFileSync('bash', ['-c',
    `python3 -X faulthandler ${POLLER} --lat 52.0767 --lon 4.2986 --once > /tmp/adsb-poll-out.json 2> /tmp/adsb-poll-err.txt; echo $? > /tmp/adsb-poll-rc`],
    // NB: node spawnSync timeout is MILLISECONDS
    { timeout: 60000, stdio: ['ignore', 'ignore', 'ignore'] });
} catch (e) {
  pollRc = -1;
  pollErr = String(e.message ?? '').slice(0, 200);
}
pollOut = fs.existsSync('/tmp/adsb-poll-out.json') ? fs.readFileSync('/tmp/adsb-poll-out.json', 'utf8') : '';
pollErr = (fs.existsSync('/tmp/adsb-poll-err.txt') ? fs.readFileSync('/tmp/adsb-poll-err.txt', 'utf8').slice(0, 800) : '') + ' | ' + pollErr;
if (fs.existsSync('/tmp/adsb-poll-rc')) pollRc = parseInt(fs.readFileSync('/tmp/adsb-poll-rc', 'utf8').trim(), 10) || pollRc;
let pollCounts = { civil: -1, mil: -1 }, pollTs = 0;
try {
  const p = JSON.parse(pollOut);
  pollCounts = { civil: p.aircraft?.count ?? -1, mil: p.military_aircraft?.count ?? -1 };
  pollTs = p.ts ?? 0;
} catch {}
check('poller: ran clean', pollRc === 0, 'rc=' + pollRc + ' err=' + pollErr.slice(0, 150));
check('poller: live aircraft in payload', pollCounts.civil > 0 && pollCounts.mil >= 0, `civil=${pollCounts.civil} mil=${pollCounts.mil} ts=${pollTs}`);
const jsonpOk = fs.readFileSync(process.env.HOME + '/.cache/omarchy-earth/live-adsb.js', 'utf8').startsWith('window.__LIVE_ADSB__=');
check('poller: JSONP file written', jsonpOk);

// 2. Boot the page: it must AUTO-START live mode from the fresh file
const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', args: ['--no-sandbox'] });
const page = await browser.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
await page.goto(PAGE, { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(3000); // leaflet boot + first live tick

const boot = await page.evaluate(() => ({
  lastData: !!window.lastData,
  civilSnap: (window.lastData?.aircraft?.count) ?? -1,
  milSnap: (window.lastData?.military_aircraft?.count) ?? -1,
  planesDrawn: window.__lm?.layers?.planeGroup?.getLayers().length ?? -1,
  milDrawn: window.__lm?.layers?.milPlaneGroup?.getLayers().length ?? -1,
  btn: !!document.getElementById('adsbLiveBtn'),
  autoActive: liveAdsbState.active,
  autoTs: liveAdsbState.lastTs,
  lastOkTs: liveAdsbState.lastOkTs,
  liveFileTs: (window.__LIVE_ADSB__ || {}).ts ?? 0,
  btnLabel: (document.getElementById('adsbLiveBtn') || {}).textContent ?? '',
}));
check('boot: lastData embedded', boot.lastData);
check('boot: civil snapshot count>0', boot.civilSnap > 0, 'civil=' + boot.civilSnap);
check('boot: plane markers drawn', boot.planesDrawn > 0, 'markers=' + boot.planesDrawn);
check('boot: adsbLiveBtn present', boot.btn);
check('live: auto-started from fresh file', boot.autoActive === true, 'active=' + boot.autoActive);
check('live: applied the poller frame', boot.autoTs === boot.liveFileTs && boot.autoTs > 0, `pageTs=${boot.autoTs} fileTs=${boot.liveFileTs}`);
check('live: lastOkTs set', boot.lastOkTs > 0, 'lastOkTs=' + boot.lastOkTs);
check('live: button shows live label', /Live|Live/i.test(boot.btnLabel), 'label=' + boot.btnLabel);

// 3. Popup deferral: open a plane popup, newer frame must NOT apply;
//    after close (wait out Leaflet's fade), the same frame must apply.
const deferral = await page.evaluate(() => {
  const m = __lm.layers.planeGroup.getLayers()[0];
  if (!m) return { skipped: true };
  m.openPopup();
  const hasPopup = !!document.querySelector('.leaflet-popup .ac-card');
  const d = JSON.parse(JSON.stringify(window.__LIVE_ADSB__)); // private copy
  d.ts = Math.floor(Date.now() / 1000) + 5; // future ts so it passes freshness
  const before = liveAdsbState.lastTs;
  const r = applyLiveAdsb(d);
  return { hasPopup, duringPopup: { r, before, after: liveAdsbState.lastTs }, d };
});
if (!deferral.skipped) {
  check('live: popup open blocks redraw', deferral.duringPopup.r === false && deferral.duringPopup.after === deferral.duringPopup.before);
  await page.evaluate(() => { __lm.layers.planeGroup.getLayers()[0].closePopup(); });
  await page.waitForTimeout(400); // Leaflet popup fade-out
  const r2 = await page.evaluate(d => {
    const popupGone = !document.querySelector('.leaflet-popup .ac-card');
    return { popupGone, r2: applyLiveAdsb(d) };
  }, deferral.d);
  check('live: popup fully closed', r2.popupGone);
  check('live: frame applies after popup closes', r2.r2 === true);
} else {
  check('live: popup deferral (SKIPPED - no markers)', false);
}

// 4. Stale-frame guard: an older ts must be rejected
const stale = await page.evaluate(() => {
  const d = JSON.parse(JSON.stringify(window.__LIVE_ADSB__));
  if (!d) return null;
  d.ts = 1000; // ancient
  return applyLiveAdsb(d);
});
check('live: stale frame rejected', stale === false);

// 5. Toggle wiring: off -> snapshot label + stopped timer, on -> live again
const t1 = await page.evaluate(() => { document.getElementById('adsbLiveBtn').click(); return { active: liveAdsbState.active, timer: !!liveAdsbState.timer, cls: document.getElementById('adsbLiveBtn').classList.contains('active') }; });
check('toggle: OFF stops timer', !t1.active && !t1.timer && !t1.cls);
const t2 = await page.evaluate(() => { document.getElementById('adsbLiveBtn').click(); return { active: liveAdsbState.active, timer: !!liveAdsbState.timer, cls: document.getElementById('adsbLiveBtn').classList.contains('active') }; });
check('toggle: ON sets active+timer', t2.active && t2.timer && t2.cls);

// 6. i18n: NL switch keeps button label sane
const nl = await page.evaluate(() => {
  const b = document.getElementById('adsbLiveBtn');
  const old = currentLang;
  applyLanguage('nl');
  const txt = b.textContent;
  applyLanguage(old);
  return txt;
});
check('i18n: NL label present', /ADS-B/.test(nl), 'label=' + nl);

// 7. No page errors during the whole run (ignore third-party network failures:
//    planespotters photos 403/CORS-block from file:// — pre-existing, unrelated)
const fatal = errors.filter(e => !/net::|Failed to load resource|ERR_|favicon|403|429|planespotters/.test(e));
check('no JS errors', fatal.length === 0, fatal.slice(0, 2).join(' ;; ') || 'clean');

await browser.close();
const failed = results.filter(r => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);
