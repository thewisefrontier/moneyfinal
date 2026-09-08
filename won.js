/* 원화 표시는 3자리 콤마가 아니라 억/만 단위로 끊어서 보여준다
   (예: 1,508,069원 -> 150만8069원). 계산기류 페이지 전반에서 쓰는 공용 함수. */
function won(v) {
  const n = Math.round(v);
  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);
  const eok = Math.floor(abs / 1e8);
  const man = Math.floor((abs % 1e8) / 1e4);
  const rest = abs % 1e4;
  if (!eok && !man) return sign + rest.toLocaleString('ko-KR') + '원';
  let s = sign;
  if (eok) s += eok + '억';
  if (man) s += man + '만';
  if (rest) s += rest;
  return s + '원';
}
