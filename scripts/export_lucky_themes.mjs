// fortune.bundle.js의 행운의 아이템 테마(LUCKY_ITEM_THEMES)를 data/lucky_themes.json 으로 내보낸다 — 핫딜 매칭 수집기(fetchers/lucky_deals.py)가 읽는다.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ctx = { console };
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root, 'fortune.bundle.js'), 'utf8'), ctx);
const themes = ctx.Fortune.LUCKY_ITEM_THEMES;
fs.writeFileSync(path.join(root, 'data', 'lucky_themes.json'), JSON.stringify(themes));
console.log('themes', themes.length);
