// 영문법 검토용 표본: 영어 사전과 조립 규칙이 실제로 만드는 문장을 모아 i18n/fortune_review/*.tsv 로 쓴다.
// 실행: node scripts/sample_fortune_en.mjs   (검토는 사람이나 별도 에이전트가 하고, 고칠 때는 i18n/fortune_en_{A,B,C}.txt 를 수정한 뒤 build_fortune_en.py)
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ctx = { console };
ctx.globalThis = ctx;
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root, 'fortune.bundle.js'), 'utf8'), ctx);
vm.runInContext(fs.readFileSync(path.join(root, 'fortune-en.js'), 'utf8'), ctx);
const F = ctx.Fortune, T = ctx.FZ.T;
const out = path.join(root, 'i18n', 'fortune_review');
fs.mkdirSync(out, { recursive: true });
const w = (name, rows) => fs.writeFileSync(path.join(out, name), rows.map((r, i) => `${i}\t${r}`).join('\n') + '\n');

// 1) 사주 요약: 오행 조합 20가지(max≠min) 전부 + 대운 문장 2종
const els = ['목', '화', '토', '금', '수'];
const seen = new Set(), rows = [];
for (let y = 1900; y < 2100 && rows.length < 40; y += 3) {
  for (let m = 1; m <= 12; m += 5) {
    const r = F.calculateSaju({ year: y, month: m, day: 11, hour: 9, minute: 0, isLunar: false, isLeapMonth: false, gender: 'male' });
    const it = F.interpretSaju(r);
    const key = it.elementSummaryText.slice(0, 40) + it.elementSummaryText.slice(-60);
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push(T(it.elementSummaryText));
    if (it.luckPillarText && rows.length % 9 === 0) rows.push(T(it.luckPillarText));
  }
}
w('saju_composed.tsv', rows);

// 2) 일간 성격 10종 + 별칭
w('saju_daymaster.tsv', Object.keys(F.DAY_MASTER_NICKNAME).map((k) => T(F.interpretSaju(F.calculateSaju({ year: 1990 + els.length, month: 5, day: 15, hour: 12, minute: 0, isLunar: false, isLeapMonth: false, gender: 'male' })).dayMasterText) && `${T(F.DAY_MASTER_NICKNAME[k].name)}`));

// 3) 띠별 운세 문장: 오늘·주·월·연 각 일부(분야별 text·advice)
const zrows = [];
for (const z of F.ZODIAC_SIGNS.slice(0, 6)) {
  for (const f of [F.getDailyFortune(z.key), F.getPeriodFortune('week', z.key), F.getPeriodFortune('month', z.key), F.getPeriodFortune('year', z.key)]) {
    for (const k of ['general', 'love', 'money', 'health']) zrows.push(T(f[k].text) + '  ||  ' + T(f[k].advice));
  }
}
w('zodiac.tsv', [...new Set(zrows)].slice(0, 120));

// 4) 타로: 22장 정·역 + 분야별 한 줄
const trows = [];
for (const c of F.TAROT_CARDS) {
  trows.push(`${T(c.name)} | UP: ${T(c.upright)} | REV: ${T(c.reversed)}`);
}
for (const cat of ['general', 'love', 'career', 'money']) for (const c of F.TAROT_CARDS.slice(0, 5)) trows.push(`[${cat}] ` + T(F.getCategoryPoint(c, false, cat)));
w('tarot.tsv', trows);
console.log('wrote', fs.readdirSync(out).join(', '));
