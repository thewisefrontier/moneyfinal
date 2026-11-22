// 영어 번역 누락 검사: 계산 번들이 낼 수 있는 화면용 문구를 넓게 돌려 보고, FZ.T()를 거친 결과에 한글이 남으면 실패한다.
// 실행: node scripts/test_fortune_en.mjs   (사전 갱신: python scripts/build_fortune_en.py)
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const RD = Date;
let OFF = 0;
class FD extends RD {
  constructor(...a) { if (a.length === 0) super(RD.now() + OFF); else super(...a); }
  static now() { return RD.now() + OFF; }
}
const ctx = { console, Date: FD };
ctx.globalThis = ctx;
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root, 'fortune.bundle.js'), 'utf8'), ctx);
vm.runInContext(fs.readFileSync(path.join(root, 'fortune-en.js'), 'utf8'), ctx);
const F = ctx.Fortune, T = ctx.FZ.T, HAN = /[가-힣]/;

const miss = new Map();
let checked = 0;
function chk(s, where) {
  if (typeof s !== 'string' || !HAN.test(s)) return;
  checked++;
  const en = T(s);
  if (HAN.test(en) && !miss.has(s)) miss.set(s, where);
}
function walk(o, where, skip = new Set()) {
  if (o == null) return;
  if (typeof o === 'string') return chk(o, where);
  if (typeof o !== 'object') return;
  for (const [k, v] of Object.entries(o)) { if (!skip.has(k)) walk(v, where + '.' + k, skip); }
}
const SKIP = new Set(['luckyItem', 'zodiac']);  // 행운의 아이템(핫딜 연동)은 한국어 전용, zodiac 객체는 용어 표로 따로 표시

for (let d = 0; d < 400; d++) {
  OFF = d * 86400000;
  for (const z of F.ZODIAC_SIGNS) {
    walk(F.getDailyFortune(z.key), 'daily', SKIP);
    for (const p of ['week', 'month', 'year']) walk(F.getPeriodFortune(p, z.key), p, SKIP);
  }
}
OFF = 0;
for (const z of F.ZODIAC_SIGNS) { if (!ctx.FZ.data.zodiac[z.label]) miss.set(z.label, 'zodiac 용어 표'); }

let seed = 7;
const rnd = (n) => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed % n; };
for (let i = 0; i < 300; i++) {
  const y = 1920 + rnd(140), m = 1 + rnd(12), d = 1 + rnd(28);
  const r = F.calculateSaju({ year: y, month: m, day: d, hour: rnd(5) === 0 ? null : rnd(24), minute: rnd(60), isLunar: false, isLeapMonth: false, gender: rnd(2) ? 'male' : 'female' });
  const it = F.interpretSaju(r);
  for (const k of ['dayMasterText', 'elementSummaryText', 'luckPillarText', 'luckyColor']) chk(it[k], 'saju.' + k);
  const tg = r.tenGods;
  for (const side of [tg.year, tg.month, tg.day, tg.hour]) {
    if (side) for (const x of [side.stem, side.branch]) if (!ctx.FZ.data.tenGods[x]) miss.set(x, '십신 용어 표');
  }
  for (const p of [r.yearPillar, r.monthPillar, r.dayPillar, r.hourPillar]) {
    if (p && (!ctx.FZ.data.stems[p.stem] || !ctx.FZ.data.branches[p.branch])) miss.set(p.stem + p.branch, '천간·지지 용어 표');
  }
}
for (const n of Object.values(F.DAY_MASTER_NICKNAME)) chk(n.name, 'nickname');

for (const c of F.TAROT_CARDS) {
  chk(c.name, 'tarot.name'); chk(c.upright, 'tarot.upright'); chk(c.reversed, 'tarot.reversed');
  for (const cat of ['general', 'love', 'career', 'money']) for (const rev of [false, true]) chk(F.getCategoryPoint(c, rev, cat), 'tarot.point.' + cat);
}

console.log(`검사한 한국어 문구 ${checked}건, 영어로 바뀌지 않은 고유 문구 ${miss.size}개`);
for (const [s, w] of [...miss].slice(0, 25)) console.log(`  [${w}] ${s.slice(0, 70)}`);
if (miss.size) process.exit(1);
console.log('OK');
