// fortune.bundle.js가 window.Fortune 계약대로 동작하는지 확인한다. 실행: node scripts/test_fortune_bundle.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ctx = { globalThis: null, console };
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root, 'fortune.bundle.js'), 'utf8'), ctx);
const F = ctx.Fortune;

assert.equal(F.ZODIAC_SIGNS.length, 12, '12지');
const a = F.getDailyFortune('tiger');
assert.deepEqual(a, F.getDailyFortune('tiger'), '같은 날 같은 띠는 결과가 같아야 한다');
assert.ok(a && typeof a === 'object');
const p = F.getPeriodFortune('week', 'tiger');
assert.ok(p && typeof p === 'object');
assert.ok(F.TAROT_CARDS.length >= 22, '타로 카드');
const d = F.drawTarotCard();
assert.ok(d.card && typeof d.reversed === 'boolean');

const s = F.calculateSaju({ year: 1990, month: 5, day: 15, hour: 12, minute: 0, isLunar: false, isLeapMonth: false, gender: 'male' });
assert.ok(s, '사주 계산 결과');
console.log('daily keys:', Object.keys(a).join(','));
console.log('saju keys:', Object.keys(s).join(','));
console.log('OK');
