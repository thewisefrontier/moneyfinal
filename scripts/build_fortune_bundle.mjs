// 핫딜월드의 계산 코드(TS)를 브라우저용 단일 JS(fortune.bundle.js)로 묶는다.
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HDW = process.env.HDW_ROOT || 'D:/thewise/hotdealworld';
const require = createRequire(path.join(HDW, 'package.json'));
const esbuild = require('esbuild');
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');

const r = await esbuild.build({
  entryPoints: [path.join(here, 'fortune_entry.ts')],
  outfile: path.join(root, 'fortune.bundle.js'),
  bundle: true,
  format: 'iife',
  minify: true,
  target: 'es2019',
  charset: 'utf8',
  alias: { '@': path.join(HDW, 'apps/web') },
  nodePaths: [path.join(HDW, 'node_modules'), path.join(HDW, 'apps/web/node_modules')],
  legalComments: 'none',
  logLevel: 'info',
});
if (r.errors.length) process.exit(1);
