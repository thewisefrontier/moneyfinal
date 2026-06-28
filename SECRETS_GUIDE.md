# GitHub Secrets 설정 가이드

moneyfinal 레포 → Settings → Secrets and variables → Actions → New repository secret

## 필수 Secrets

| Name | Value | 출처 |
|------|-------|------|
| `SUPABASE_URL` | https://xxxx.supabase.co | Supabase → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | service_role 키 | Supabase → Project Settings → API |
| `GEMINI_API_KEY` | AIza... | Google AI Studio |
| `GH_PAT` | github_pat_... | GitHub → Settings → Developer settings |
| `FSS_API_KEY` | 금감원 API 키 | 공공데이터포털 (data.go.kr) |
| `ECOS_API_KEY` | 한국은행 API 키 | ECOS (ecos.bok.or.kr) |
| `DART_API_KEY` | DART API 키 | DART (dart.fss.or.kr) |
| `FRED_API_KEY` | FRED API 키 | FRED (fred.stlouisfed.org) |
| `TELEGRAM_BOT_TOKEN` | 봇 토큰 | @BotFather |
| `TELEGRAM_CHANNEL_ID` | @채널명 또는 -100... | 텔레그램 채널 |

## API 키 발급 우선순위

1. SUPABASE_URL / SUPABASE_SERVICE_KEY → 이미 있음
2. GEMINI_API_KEY → Google AI Studio (무료)
3. GH_PAT → 이미 발급
4. FSS_API_KEY → 공공데이터포털 (무료, 즉시 발급)
5. ECOS_API_KEY → ecos.bok.or.kr (무료, 즉시 발급)
6. DART_API_KEY → dart.fss.or.kr (무료, 즉시 발급)
7. FRED_API_KEY → fred.stlouisfed.org (무료, 즉시 발급)
8. TELEGRAM_BOT_TOKEN → 나중에 (채널 개설 후)
