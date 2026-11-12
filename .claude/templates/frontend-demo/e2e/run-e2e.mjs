#!/usr/bin/env node
// E2E con base DESECHABLE — `npm run e2e` desde frontend/ (plantilla de templates/frontend-demo, AN-22).
//
// El test crea su propio mundo y no deja residuos (rules/verification.md §Estabilidad E2E):
//   1. comprueba la RAM (hook del repo) y que los puertos están libres;
//   2. crea la base desechable, la migra y la siembra (por manage.py del proyecto);
//   3. levanta el backend (y el frontend si se pide) en 127.0.0.1, nunca 0.0.0.0, y espera a que responda;
//   4. lanza los tests (por defecto Playwright) con E2E_API_URL, E2E_WEB_URL y E2E_DB en el entorno;
//   5. para los servidores y BORRA la base al terminar, pase lo que pase (también con Ctrl+C).
//
// Variables (las del proyecto se fijan en el script `e2e` de package.json):
//   E2E_DB_PREFIX=miapp_e2e    prefijo obligatorio de la base; TIENE que acabar en «_e2e»
//   E2E_DB=miapp_e2e           la base (por defecto, el prefijo); se valida contra el prefijo
//   E2E_DB_ENV=POSTGRES_DB     la variable de entorno con la que los settings eligen la base
//   E2E_ADMIN_DB=postgres      la base a la que se conecta para crear y borrar la desechable
//   E2E_MANAGE="python backend/manage.py"     cómo se llama a manage.py, desde la raíz del repo
//   E2E_SEED="seed_demo"       órdenes de manage.py tras migrar, separadas por «;» (vacío: ninguna)
//   E2E_API_PORT=8045 · E2E_WEB_PORT=5195 · E2E_HEALTH_PATH=/      dónde se espera al backend
//   E2E_WEB_CMD="node_modules/.bin/vite --host 127.0.0.1 --port 5195 --strictPort"  (vacío: sin frontend)
//   E2E_TEST_CMD="node_modules/.bin/playwright test -c e2e/playwright.config.ts"   (cwd: frontend/)
//   E2E_KEEP_DB=1              no borrar la base al terminar (para mirar qué pasó)
//   E2E_REUSE_DB=1             si la base existe (la dejó E2E_KEEP_DB=1), usarla sin migrar ni sembrar
//   E2E_ROOT                   raíz del repo (por defecto, dos niveles por encima de este fichero)
// Lo que vaya detrás de `--` se le pasa a los tests: `npm run e2e -- --headed`.
// Salida: 0 verde · 1 tests en rojo o un paso falló · 2 no se lanzó (RAM, puerto, nombre de base).
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, openSync, readFileSync } from 'node:fs';
import { connect } from 'node:net';
import { basename, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const E2E_DIR = dirname(fileURLToPath(import.meta.url));
const FRONTEND = resolve(E2E_DIR, '..');
const ROOT = resolve(process.env.E2E_ROOT ?? resolve(E2E_DIR, '../..'));
const RESULTS = resolve(E2E_DIR, 'test-results');

const env = process.env;
const PREFIX = env.E2E_DB_PREFIX ?? `${basename(ROOT).toLowerCase().replace(/[^a-z0-9]/g, '_')}_e2e`;
const DB = env.E2E_DB ?? PREFIX;
const DB_ENV = env.E2E_DB_ENV ?? 'POSTGRES_DB';
const ADMIN_DB = env.E2E_ADMIN_DB ?? 'postgres';
const MANAGE = (env.E2E_MANAGE ?? 'python backend/manage.py').split(' ').filter(Boolean);
const SEED = (env.E2E_SEED ?? 'seed_demo').split(';').map((s) => s.trim()).filter(Boolean);
const API_PORT = env.E2E_API_PORT ?? '8045';
const WEB_PORT = env.E2E_WEB_PORT ?? '5195';
const HEALTH = env.E2E_HEALTH_PATH ?? '/';
const WEB_CMD = env.E2E_WEB_CMD ?? '';
const TEST_CMD = env.E2E_TEST_CMD ?? 'node_modules/.bin/playwright test -c e2e/playwright.config.ts';
const KEEP = env.E2E_KEEP_DB === '1';
const REUSE = env.E2E_REUSE_DB === '1';

const started = Date.now();
const step = (text) => console.log(`[e2e ${Math.round((Date.now() - started) / 1000)} s] ${text}`);

// La base se BORRA al terminar: el nombre se valida antes de tocar nada. El prefijo tiene que acabar
// en «_e2e» para que un prefijo mal puesto («miapp») no convierta la base de desarrollo en desechable.
if (!/^[a-z0-9_]+_e2e$/.test(PREFIX)) {
  console.error(`E2E_DB_PREFIX="${PREFIX}" no vale: solo minúsculas, cifras y _, y tiene que acabar en "_e2e".`);
  process.exit(2);
}
if (!DB.startsWith(PREFIX) || !/^[a-z0-9_]+$/.test(DB)) {
  console.error(`E2E_DB="${DB}" no vale: tiene que empezar por "${PREFIX}" (solo minúsculas, cifras y _).`);
  process.exit(2);
}

/** manage.py con la base que toque. Devuelve la salida; lanza si falla. */
function manage(args, { db = DB } = {}) {
  const r = spawnSync(MANAGE[0], [...MANAGE.slice(1), ...args], {
    cwd: ROOT, env: { ...env, [DB_ENV]: db }, encoding: 'utf-8',
  });
  if (r.status !== 0) {
    console.error(r.stdout ?? '', r.stderr ?? r.error ?? '');
    throw new Error(`manage.py ${args.join(' ')} salió con ${r.status}`);
  }
  return r.stdout;
}

/** SQL de administración: conectado a la base de mantenimiento, no a la del proyecto. */
function adminSql(statements) {
  const code = ['from django.db import connection', 'with connection.cursor() as c:',
    ...statements.map((s) => `    c.execute(${JSON.stringify(s)})`)].join('\n');
  manage(['shell', '-c', code], { db: ADMIN_DB });
}

function dbExists() {
  const out = manage(['shell', '-c', [
    'from django.db import connection', 'with connection.cursor() as c:',
    `    c.execute("SELECT 1 FROM pg_database WHERE datname = %s", [${JSON.stringify(DB)}])`,
    '    print("exists=" + ("1" if c.fetchone() else "0"))'].join('\n')], { db: ADMIN_DB });
  return out.includes('exists=1');
}

const dropDb = () => adminSql([`DROP DATABASE IF EXISTS ${DB} WITH (FORCE)`]);

function portBusy(port) {
  return new Promise((ok) => {
    const s = connect({ host: '127.0.0.1', port: Number(port) });
    s.once('connect', () => (s.destroy(), ok(true)));
    s.once('error', () => ok(false));
  });
}

/** Un servidor en su propio grupo de procesos (para pararlo entero) y con su log en test-results/. */
function serve(command, args, cwd, log, extraEnv) {
  mkdirSync(RESULTS, { recursive: true });
  const fd = openSync(resolve(RESULTS, log), 'w');
  return spawn(command, args, { cwd, env: { ...env, ...extraEnv }, stdio: ['ignore', fd, fd], detached: true });
}

async function waitFor(url, child, seconds = 90) {
  for (let i = 0; i < seconds * 2; i++) {
    checkpoint();
    if (child.exitCode !== null) throw new Error(`el servidor de ${url} se cerró al arrancar (código ${child.exitCode})`);
    try {
      const r = await fetch(url, { redirect: 'manual' });
      if (r.status < 500) return;
    } catch { /* aún no escucha */ }
    await new Promise((ok) => setTimeout(ok, 500));
  }
  throw new Error(`${url} no respondió en ${seconds} s`);
}

function showLog(name) {
  const path = resolve(RESULTS, name);
  if (!existsSync(path)) return;
  const lines = readFileSync(path, 'utf-8').trimEnd().split('\n');
  console.error(`\n── últimas líneas de e2e/test-results/${name} ──\n${lines.slice(-25).join('\n')}`);
}

// ── 1. Antes de tocar nada ───────────────────────────────────────────────────────────────────
const ramHook = resolve(ROOT, '.claude/hooks/check-ram.sh');
if (existsSync(ramHook) && spawnSync('bash', [ramHook], { cwd: ROOT, stdio: 'inherit' }).status !== 0) {
  console.error('RAM insuficiente (check-ram.sh): el E2E abre un navegador y cuenta doble. No se lanza.');
  process.exit(2);
}
for (const port of WEB_CMD ? [API_PORT, WEB_PORT] : [API_PORT]) {
  if (await portBusy(port)) {
    console.error(`El puerto 127.0.0.1:${port} ya está en uso. Cambia E2E_API_PORT / E2E_WEB_PORT.`);
    process.exit(2);
  }
}

let code = 1;
const servers = [];
let tests = null;
// Un listener quita la salida por defecto de Node: se marca la interrupción y cada paso la mira, así el
// finally limpia también si llega antes de los tests (con Ctrl+C, manage.py muere con el grupo).
let interrupted = false;
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => { interrupted = true; tests?.kill(sig); });
const checkpoint = () => { if (interrupted) throw new Error('interrumpido'); };

try {
  // ── 2. La base desechable ────────────────────────────────────────────────────────────────
  if (REUSE && dbExists()) {
    step(`base ${DB}: REUSADA tal cual (E2E_REUSE_DB=1), sin migrar ni sembrar`);
  } else {
    step(`base ${DB}: creando desde cero`);
    adminSql([`DROP DATABASE IF EXISTS ${DB} WITH (FORCE)`, `CREATE DATABASE ${DB}`]);
    // Los settings tienen que elegir la base por E2E_DB_ENV; si no, migrate y seed irían a la de desarrollo.
    const used = manage(['shell', '-c', 'from django.db import connection; print("db=" + connection.settings_dict["NAME"])']);
    if (!used.includes(`db=${DB}\n`)) {
      code = 2;
      throw new Error(`los settings no usan ${DB} con ${DB_ENV}=${DB} (dicen: ${used.trim()}). No se migra ni se siembra`);
    }
    checkpoint();
    step('migrate');
    manage(['migrate', '--no-input']);
    for (const cmd of SEED) {
      step(cmd);
      manage(cmd.split(' ').filter(Boolean));
    }
  }

  // ── 3. Servidores, solo en 127.0.0.1 ────────────────────────────────────────────────────
  const apiUrl = `http://127.0.0.1:${API_PORT}`;
  step(`backend ${apiUrl}`);
  const api = serve(MANAGE[0], [...MANAGE.slice(1), 'runserver', `127.0.0.1:${API_PORT}`, '--noreload'],
    ROOT, 'server-api.log', { [DB_ENV]: DB });
  servers.push(api);
  await waitFor(apiUrl + HEALTH, api);
  let webUrl = apiUrl;
  if (WEB_CMD) {
    webUrl = `http://127.0.0.1:${WEB_PORT}`;
    step(`frontend ${webUrl}`);
    const parts = WEB_CMD.split(' ').filter(Boolean);
    const web = serve(parts[0], parts.slice(1), FRONTEND, 'server-web.log',
      { E2E_API_URL: apiUrl, E2E_API_PORT: API_PORT, E2E_WEB_PORT: WEB_PORT });
    servers.push(web);
    await waitFor(webUrl + '/', web);
  }

  // ── 4. Los tests ─────────────────────────────────────────────────────────────────────────
  step(`tests: ${TEST_CMD}`);
  const parts = TEST_CMD.split(' ').filter(Boolean);
  code = await new Promise((ok) => {
    tests = spawn(parts[0], [...parts.slice(1), ...process.argv.slice(2)], {
      cwd: FRONTEND, stdio: 'inherit',
      env: { ...env, E2E_DB: DB, E2E_API_URL: apiUrl, E2E_WEB_URL: webUrl },
    });
    tests.on('error', (e) => (console.error(e.message), ok(1)));
    tests.on('exit', (c, sig) => ok(c ?? (sig ? 130 : 1)));
  });
  if (code !== 0) {
    showLog('server-api.log');
    if (WEB_CMD) showLog('server-web.log');
  }
} catch (error) {
  console.error(`\nE2E abortado: ${error.message}`);
  showLog('server-api.log');
  code = code === 2 ? 2 : 1;
} finally {
  // ── 5. Sin residuos ──────────────────────────────────────────────────────────────────────
  for (const s of servers) {
    try { process.kill(-s.pid, 'SIGTERM'); } catch { /* ya no estaba */ }
  }
  if (KEEP) {
    step(`base ${DB} CONSERVADA (E2E_KEEP_DB=1) — bórrala tú cuando acabes`);
  } else {
    try {
      dropDb();
      step(`base ${DB} borrada`);
    } catch (error) {
      console.error(`No se pudo borrar la base ${DB}: ${error.message}`);
      code ||= 1;
    }
  }
  step(code === 0 ? 'E2E en verde' : `E2E en ROJO (código ${code})`);
}
process.exit(code);
