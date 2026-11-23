// run_tests.mjs — runs every test_*.mjs in this folder with the same Node binary; exit 1 if any fails.
// Usage: node assets/examples/motion/run_tests.mjs
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { HERE } from './_harness.mjs';

let bad = 0;
for (const f of fs.readdirSync(HERE).filter((n) => /^test_.*\.mjs$/.test(n)).sort()) {
  const r = spawnSync(process.execPath, [path.join(HERE, f)], { encoding: 'utf8' });
  const last = (r.stdout || '').trim().split(/\r?\n/).pop();
  console.log(`${r.status === 0 ? 'ok  ' : 'FAIL'} ${f}  ${last}`);
  if (r.status !== 0) { bad++; process.stdout.write((r.stdout || '') + (r.stderr || '')); }
}
console.log(bad ? `${bad} test file(s) failed` : 'all lib/motion tests passed');
process.exitCode = bad ? 1 : 0;
