# 공공데이터 오픈API 필드 레퍼런스 (머니파이널)

원본 활용가이드 docx 22종에서 **엔드포인트 · 요청 파라미터 · 응답 필드명**만 추출한 압축본.
원본 docx는 이 파일 생성 후 프로젝트에서 제거함.

## 읽는 법
- `필드명*` = 필수 항목, 괄호 안 = 국문명
- 공통 요청 파라미터 `serviceKey` / `pageNo` / `numOfRows` / `resultType` 는 생략
- 공통 응답 헤더 `resultCode` / `resultMsg` / `numOfRows` / `pageNo` / `totalCount` 는 생략
- 요청 파라미터의 `beginX`·`endX`(범위검색), `likeX`(부분일치)는 개수만 표기. 기본 필드명 앞에 접두어를 붙여 사용
- 인증키: `DATA_GO_KR_API_KEY_DEC` (디코딩 키, `data_go_kr_get()` 사용). ENC 키 URL 직접 삽입 금지

## 라이선스 경고 (사용 금지)
- **주식권리일정정보(`GetStocRighScheService_V2`)** — 한국예탁결제원 계열, 공공누리 제한으로 사용 금지
- **DR 국제거래종목정보(`GetDrTradItemInfoService_V2`)** — 사용 금지 (본 문서 미수록)
- 신규 API 사용 전 공공누리 유형 확인 필수 (Type 2 이상만 허용)

## 연동 현황
| 상태 | API |
|---|---|
| 연동 완료 | 지수시세정보, 금융투자협회종합통계, KRX상장종목정보, KOTRA 외국인직접투자, ISA다모아, 금융회사지배구조, 기업재무정보, 주식시세정보, 일반상품시세정보, 공시정보_V2 |
| 예정 (미검증 fetcher) | 펀드상품기본정보, 실손보험정보, 채권기본정보, 파생상품시세정보, 금융회사기본정보, 금융통계국내은행정보 |
| 계획 없음 | 개인사업자기본/재무정보, 채권시세정보, 금융회사재무신용정보, 기업기본정보 |
| 사용 금지 | 주식권리일정정보 |

---

## 금융통계_활용자가이드_금융통계국내은행정보
- **서비스명(영문)**: `GetDomeBankInfoService`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetDomeBankInfoService`
- **갱신주기**: 월1회
- **오퍼레이션**:
  - `getDomeBankGeneInfo` — 국내은행일반현황조회
  - `getDomeBankFinaInfo` — 국내은행재무현황조회
  - `getDomeBankKeyManaIndi` — 국내은행주요경영지표조회
  - `getDomeBankMajoBusiActi` — 국내은행주요영업활동조회

### getDomeBankGeneInfo
- 요청: title(타이틀), basYm(기준년월)
- 응답: title(타이틀), basYm*(기준년월), crno(법인등록번호), fncoCd*(금융회사코드), fncoNm(금융회사명), xcsmCnt(임직원수), xcsmDcd*(임직원구분코드), xcsmDcdNm(임직원구분코드명)

### getDomeBankFinaInfo
- 요청: title(타이틀), basYm(기준년월)
- 응답: title(타이틀), basYm*(기준년월), bnkAstItemAcitAmt(은행자산항목계정과목금액), bnkAstItemAcitCd*(은행자산항목계정과목코드), bnkAstItemAcitCdNm(은행자산항목계정과목코드명), bnkAstItemAcitCmpsRto(은행자산항목계정과목구성비율), crno(법인등록번호), fncoCd*(금융회사코드), fncoNm(금융회사명)

### getDomeBankKeyManaIndi
- 요청: title(타이틀), basYm(기준년월)
- 응답: title(타이틀), basYm*(기준년월), cpaqItemClsfVal(자본적정성항목구분값), cpaqItemDcd*(자본적정성항목구분코드), cpaqItemDcdNm(자본적정성항목구분코드명), crno(법인등록번호), fncoCd*(금융회사코드), fncoNm(금융회사명)

### getDomeBankMajoBusiActi
- 요청: title(타이틀), basYm(기준년월)
- 응답: title(타이틀), basYm*(기준년월), bzopSclItemAmt(영업규모항목금액), bzopSclItemDcd*(영업규모항목구분코드), bzopSclItemDcdNm(영업규모항목구분코드명), crno(법인등록번호), fncoCd*(금융회사코드), fncoNm(금융회사명)

---

## 오픈API_활용자가이드_금융위원회_ISA다모아정보
- **서비스명(영문)**: `GetISAInfoService_V2`
- **BASE URL**: `http://apis.data.go.kr/1160100/GetISAInfoService_V2`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getJoinStatus_V2` — ISA업권별가입현황
  - `getManagementStatus_V2` — ISA운용현황
  - `getMPBenefitRateInfo_V2` — ISAMP대표수익률

### getJoinStatus_V2
- 요청: basDt(기준일자), isaForm(ISA형태), ctg(업권)  <sub>(+범위/부분일치 변형 5개: begin*/end*/like* 접두)</sub>
- 응답: invAmt(투자금액), basDt(기준일자), isaForm(ISA 형태), ctg(구분), cmpyCnt(회사수), jnpnCnt(가입자수)

### getManagementStatus_V2
- 요청: basDt(기준일자), bzds(업권), ctg(구분), isaForm(ISA 형태), incAstCtg(편입자산구분)  <sub>(+범위/부분일치 변형 5개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), bzds(업권), ctg(구분), isaForm(ISA형태), incAstCtg(편입자산구분), amt(금액)

### getMPBenefitRateInfo_V2
- 요청: basDt(기준일자), bzds(업권), cmpyNm(회사명), mpTp(MP유형), mpNm(MP명칭)  <sub>(+범위/부분일치 변형 5개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), bzds(업권), cmpyNm(회사명), mpTp(MP유형), mpNm(MP명칭), rlsDt(출시일), trm(기간), bnfRt(수익률)

---

## 오픈API_활용자가이드_금융위원회_KRX상장종목정보
- **서비스명(영문)**: `GetKrxListedInfoService`
- **BASE URL**: `https://apis.data.go.kr/1160100/service/GetKrxListedInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getItemInfo` — 종목정보

### getItemInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명), crno(법인등록번호), corpNm(법인명)  <sub>(+범위/부분일치 변형 7개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), srtnCd(단축코드), isinCd(ISIN코드), mrktCtg(시장 구분), itmsNm(종목명), crno(법인등록번호), corpNm(법인명)

---

## 오픈API_활용자가이드_금융위원회_개인사업자기본정보
- **서비스명(영문)**: `GetSBProfileInfoService`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetSBProfileInfoService`
- **갱신주기**: 연1회
- **오퍼레이션**:
  - `getOtlInfo` — 개인사업자개요정보조회
  - `getCsdoStatus` — 개인사업자휴폐업정보조회

### getOtlInfo
- 요청: basYm(기준년월), bizAreaNm(사업 지역명), bizBzcCdNm(사업 업종명), bizBzcCd(사업 업종코드), estbYr(설립년도), rprSexNm(대표자 성별명)
- 응답: basYm(기준년월), rprSexNm(대표자 성별명), rprAggrNm(대표자 연령대명), estbYr(설립년도), bizAreaNm(사업 지역명), bizBzcCd(사업 업종코드), bizBzcCdNm(사업 업종명), empeCntNm(종업원수구분명)

### getCsdoStatus
- 요청: basYm(기준년월)
- 응답: basYm(기준년월), rprSexNm(대표자 성별명), rprAggrNm(대표자 연령대명), estbYr(설립년도), bizAreaNm(사업 지역명), bizBzcCd(사업 업종코드), bizBzcCdNm(사업 업종명), empeCntNm(종업원수구분명), csdoClsfNm(휴폐업구분명)

---

## 오픈API_활용자가이드_금융위원회_개인사업자재무정보
- **서비스명(영문)**: `GetSBFinanceInfoService`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetSBFinanceInfoService`
- **갱신주기**: 연1회
- **오퍼레이션**:
  - `getFnafInfo` — 개인사업자재무정보조회
  - `getSlsInfo` — 개인사업자매출액정보조회
  - `getDbtInfo` — 개인사업자부채정보조회

### getFnafInfo
- 요청: basYm(기준년월), bizAreaNm(사업 지역명), bizBzcCdNm(사업 업종명), bizBzcCd(사업 업종코드), cptlAmtMin(자본금액min), cptlAmtMax(자본금액max), saleAmtMin(매출금액min), saleAmtMax(매출금액max), bzopPftAmtMin(영업이익min), bzopPftAmtMax(영업이익max), crtmNpfAmtMin(당기순이익min), crtmNpfAmtMax(당기순이익max), astTsumAmtMin(자산총합계금액min), astTsumAmtMax(자산총합계금액max), debtTsumAmtMin(부채총합계금액min), debtTsumAmtMax(부채총합계금액max)
- 응답: basYm(기준년월), rprSexNm(대표자 성별명), rprAggrNm(대표자 연령대명), estbYr(설립년도), bizAreaNm(사업 지역명), bizBzcCd(사업 업종코드), bizBzcCdNm(사업 업종명), empeCntNm(종업원수구분명), fnafBasYr(재무기준년도), cptlAmt(자본금액), saleAmt(매출금액), bzopPftAmt(영업이익), crtmNpfAmt(당기순이익), astTsumAmt(자산총합계금액), debtTsumAmt(부채총합계금액)

### getSlsInfo
- 요청: basYm(기준년월), bizAreaNm(사업 지역명), bizBzcCdNm(사업 업종명), bizBzcCd(사업 업종코드), saleAmtMin(매출금액min), saleAmtMax(매출금액max)
- 응답: basYm(기준년월), rprSexNm(대표자 성별명), rprAggrNm(대표자 연령대명), estbYr(설립년도), bizAreaNm(사업 지역명), bizBzcCd(사업 업종코드), bizBzcCdNm(사업 업종명), empeCntNm(종업원수구분명), fnafBasYr(재무기준년도), saleAmt(매출금액)

### getDbtInfo
- 요청: basYm(기준년월), bizAreaNm(사업 지역명), bizBzcCdNm(사업 업종명), bizBzcCd(사업 업종코드), debtTsumAmtMin(부채총합계금액min), debtTsumAmtMax(부채총합계금액max)
- 응답: basYm(기준년월), rprSexNm(대표자 성별명), rprAggrNm(대표자 연령대명), estbYr(설립년도), bizAreaNm(사업 지역명), bizBzcCd(사업 업종코드), bizBzcCdNm(사업 업종명), empeCntNm(종업원수구분명), fnafBasYr(재무기준년도), debtTsumAmt(부채총합계금액)

---

## 오픈API_활용자가이드_금융위원회_공시정보_V2
- **서비스명(영문)**: `GetDiscInfoService_V2`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetDiscInfoService_V2`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `GetDiviDiscInfo_V2` — 배당공시정보조회
  - `getCapiIncrWithConsDiscInfo_V2` — 유상증자결정공시정보조회
  - `getBonuIssuDiscInfo_V2` — 무상증자결정공시정보조회
  - `getCapiIncrWithConsBonuIssuDiscInfo_V2` — 유무상증자결정공시정보조회
  - `getGeneMeetStocPublNotiDiscInfo_V2` — 주주총회소집공고공시정보조회
  - `getAsseTranPutBackOptiDiscInfo_V2` — 자산양수도(기타)_풋백옵션공시정보조회
  - `getDishDiscInfo_V2` — 부도발생공시정보조회
  - `getBusiSuspDiscInfo_V2` — 영업정지공시정보조회
  - `getReviProcDiscInfo_V2` — 회생절차개시신청공시정보조회
  - `getDissReasDiscInfo_V2` — 해산사유발생공시정보조회
  - `getReduCapiDiscInfo_V2` — 감자결정공시정보조회
  - `getProcByCredBankDiscInfo_V2` — 채권은행등의관리절차개시공시정보조회
  - `getLitiEtcDiscInfo_V2` — 소송등의제기공시정보조회
  - `getOffsSecuMarkListDiscInfo_V2` — 해외증권시장주권등상장공시정보조회
  - `getOffsSecuMarkDeliDiscInfo_V2` — 해외증권시장주권등상장폐지공시정보조회
  - `getCbRighIssuDiscInfo_V2` — 전환사채권발행결정공시정보조회
  - `getBwRighIssuDiscInfo_V2` — 신주인수권부사채권발행결정공시정보조회
  - `getEbRighIssuDiscInfo_V2` — 교환사채권발행결정공시정보조회
  - `getAmorCoCoBondDisclInfo_V2` — 상각형조건부자본증권발행결정공시정보조회
  - `getTreaStocRepuDiscInfo_V2` — 자기주식취득결정공시정보조회
  - `getTreaStocSellDiscInfo_V2` — 자기주식처분결정공시정보조회
  - `getBusiInhetDiscInfo_V2` — 영업양수결정공시정보조회
  - `getBusiConvDiscInfo_V2` — 영업양도결정공시정보조회
  - `getStocSubsCertInheDiscInfo_V2` — 타법인주식및출자증권양수결정공시정보조회
  - `getStocSubsCertConvDiscInfo_V2` — 타법인주식및출자증권양도결정공시정보조회
  - `getDebeRighInheDiscInfo_V2` — 주권관련사채권양수결정공시정보조회
  - `getDebeRighConvDiscInfo_V2` — 주권관련사채권양도결정공시정보조회
  - `getMnaDiscInfo_V2` — 회사합병결정공시정보조회
  - `getSpilUpDiscInfo_V2` — 회사분할결정공시정보조회
  - `getDiviCombDiscInfo_V2` — 회사분할합병결정공시정보조회
  - `getStocExchTranDiscInfo_V2` — 주식교환·이전결정공시정보조회
  - `getStocOptiRepo_V2` — 주식매수선택권부여에관한신고조회
  - `getOutsDireHumaResoAffaRepo_V2` — 사외이사의선임·해임또는중도퇴임에관한신고조회

### GetDiviDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), bpvtrParPrc(전전기액면가), pvtrCrtmNpf(전기당기순이익), bpvtrPstcNpf(전전기주당순이익), bpvtrCashTdvdAmt(전전기현금총배당금액), bpvtrStckTdvdAmt(전전기주식총배당금액), bpvtrCashDvdnTndnCtt(전전기현금배당성향내용), bpvtrOnskCashDvdnBnfRt(전전기보통주현금배당수익률), bpvtrPfstCashDvdnBnfRt(전전기우선주현금배당수익률), bpvtrOnskStckDvdnBnfRt(전전기보통주주식배당수익률), bpvtrPfstStckDvdnBnfRt(전전기우선주주식배당수익률), bpvtrOnskCashDvdnAmt(전전기보통주현금배당금액), bpvtrPfstCashDvdnAmt(전전기우선주현금배당금액), bpvtrOnskStckDvdnAmt(전전기보통주주식배당금액), bpvtrPfstStckDvdnAmt(전전기우선주주식배당금액), pvtrParPrc(전기액면가), bpvtrIdvCrtmNpf(전전기개별당기순이익), pvtrPstcNpf(전기주당순이익), pvtrCashTdvdAmt(전기현금총배당금액), pvtrStckTdvdAmt(전기주식총배당금액), pvtrCashDvdnTndnCtt(전기현금배당성향내용), pvtrOnskCashDvdnBnfRt(전기보통주현금배당수익률), pvtrPfstCashDvdnBnfRt(전기우선주현금배당수익률), pvtrOnskStckDvdnBnfRt(전기보통주주식배당수익률), pvtrPfstStckDvdnBnfRt(전기우선주주식배당수익률), pvtrOnskCashDvdnAmt(전기보통주현금배당금액), pvtrPfstCashDvdnAmt(전기우선주현금배당금액), pvtrOnskStckDvdnAmt(전기보통주주식배당금액), pvtrPfstStckDvdnAmt(전기우선주주식배당금액), crtmParPrc(당기액면가), pvtrIdvCrtmNpf(전기개별당기순이익), crtmPstcNpf(당기주당순이익), crtmCashTdvdAmt(당기현금총배당금액), crtmStckTdvdAmt(당기주식총배당금액), crtmCashDvdnTndnCtt(당기현금배당성향내용), crtmOnskCashDvdnBnfRt(당기보통주현금배당수익률), crtmPfstCashDvdnBnfRt(당기우선주현금배당수익률), crtmOnskStckDvdnBnfRt(당기보통주주식배당수익률), crtmPfstStckDvdnBnfRt(당기우선주주식배당수익률), crtmOnskCashDvdnAmt(당기보통주현금배당금액), crtmPfstCashDvdnAmt(당기우선주현금배당금액), crtmOnskStckDvdnAmt(당기보통주주식배당금액), crtmPfstStckDvdnAmt(당기우선주주식배당금액), crtmIdvCrtmNpf(당기개별당기순이익), enpCrtmNpf(기업당기순이익), fnclCrtmNpf(재무제표당기순이익)

### getCapiIncrWithConsDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), onskNstCnt(보통주신주수), pfstNstCnt(우선주신주수), stckParPrc(주식액면가), bfciOnskIssuStckCnt(증자전보통주발행주식수), bfciPfstIssuStckCnt(증자전우선주발행주식수), fctfndAt(시설자금액), mgmCptAt(운영자금액), otcoScrtAcqAmt(타법인증권취득금액), etcCptlAmt(기타자본금액), capiMthoNm(증자방식명), arasBsisCtt(정관근거내용), stckCtt(주식내용), etcCtt(기타내용), stckRdptCondNm(주식상환조건명), stckRdptMthNm(주식상환방법명), stckRdptTermMnthCnt(주식상환기간개월수), stckRdptAmt(주식상환금액), wt1YRdptSchYn(1년이내상환예정여부), stckCnvrCondCtt(주식전환조건내용), stckCnvrClmTermMnthCnt(주식전환청구기간개월수), cnvrStckKindNm(전환주식종류명), cnvrIssuStckCnt(전환발행주식수), stckVtrgCtt(주식의결권내용), pftDvdnCtt(이익배당내용), etcAgrmCtt(기타약정내용), onskIssuFrmPric(보통주발행확정가격), otshIssuFrmPric(기타주발행확정가격), onskIssuSchPric(보통주발행예정가격), otshIssuSchPric(기타주발행예정가격), onskFrmIssuPricSchDt(보통주확정발행가격예정일자), otshFrmIssuPricSchDt(기타주확정발행가격예정일자), issuPricCmpuMthCtt(발행가격산정방법내용), nstAlctBasDt(신주배정기준일자), nstAlctStckCnt(신주배정주식수), emstowUnnFoalAlctRto(우리사주조합우선배정비율), emstowUnnSbscSchSttgDt(우리사주조합청약예정시작일자), emstowUnnSbscSchEdDt(우리사주조합청약예정종료일자), bfSthdSbscSchSttgDt(이전주주청약예정시작일자), bfSthdSbscSchEdDt(이전주주청약예정종료일자), pbsbSbscSchSttgDt(공모청약예정시작일자), pbsbSbscSchEdDt(공모청약예정종료일자), shcpPymtDt(주금납입일자), frstPcPlanCtt(실권주처리계획내용), nstDvdnRckDt(신주배당기산일자), nrfsHndvSchDt(신주권교부예정일자), nstLstgSchDt(신주상장예정일자), rprsSptdCmpyNm(대표주관회사명), prmrCnvYn(신주인수권양도여부), prmrCrtfLstgYn(신주인수권증서상장여부), trdMdatFinInvsNm(매매중개금융투자자명), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audpnAtndYn(감사인참석여부), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), ivsRefCtt(투자참고내용), basStprDcXchrRt(기준주가할인할증률), rd3PtAlctArasBsisCtt(제3자배정정관근거내용), dturLstgYn(우회상장여부), acthInvtYn(현물출자여부), rgscUnltStckYn(주권비상장주식여부), pymtSchActhInvtAmt(납입예정현물출자금액), pymtSchActhInvtRto(납입예정현물출자비율), pymtSchStckCnt(납입예정주식수), dturLstgPsblYn(우회상장가능여부), corRsnCtt(정정사유내용), hcfhPlanCtt(향후계획내용), rptFileCtt(보고서파일내용)

### getBonuIssuDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), onskNstCnt(보통주신주수), otshNstCnt(기타주신주수), stckParPrc(주식액면가), bfciOnskTisuStckCnt(증자전보통주총발행주식수), bfciOtshTisuStckCnt(증자전기타주총발행주식수), nstAlctBasDt(신주배정기준일자), onskNstAlctStckCnt(보통주신주배정주식수), otshNstAlctStckCnt(기타주신주배정주식수), nstDvdnRckDt(신주배당기산일자), nrfsHndvSchDt(신주권교부예정일자), nstLstgSchDt(신주상장예정일자), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), ivsRefCtt(투자참고내용), rptFileCtt(보고서파일내용)

### getCapiIncrWithConsBonuIssuDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), enpCorpNm(기업법인명)
- 응답: basDt*(기준일자), crno*(법인등록번호), enpCorpNm*(기업법인명), onskNstCnt(보통주신주수), otshNstCnt(기타주신주수), stckParPrc(주식액면가), bfciOnskTisuStckCnt(증자전보통주총발행주식수), bfciOtshTisuStckCnt(증자전기타주총발행주식수), fctfndAt(시설자금액), mgmCptAt(운영자금액), otcoScrtAcqAmt(타법인증권취득금액), etcCptlAmt(기타자본금액), capiMthoNm(증자방식명), arasBsisCtt(정관근거내용), stckCtt(주식내용), etcCtt(기타내용), stckRdptCondNm(주식상환조건명), stckRdptMthNm(주식상환방법명), stckRdptTermMnthCnt(주식상환기간개월수), stckRdptAmt(주식상환금액), wt1YRdptSchYn(1년이내상환예정여부), stckCnvrCondCtt(주식전환조건내용), stckCnvrClmTermMnthCnt(주식전환청구기간개월수), cnvrStckKindNm(전환주식종류명), cnvrIssuStckCnt(전환발행주식수), stckVtrgCtt(주식의결권내용), pftDvdnCtt(이익배당내용), etcAgrmCtt(기타약정내용), onskIssuFrmPric(보통주발행확정가격), otshIssuFrmPric(기타주발행확정가격), onskIssuSchPric(보통주발행예정가격), otshIssuSchPric(기타주발행예정가격), onskFrmIssuPricSchDt(보통주확정발행가격예정일자), otshFrmIssuPricSchDt(기타주확정발행가격예정일자), issuPricCmpuMthCtt(발행가격산정방법내용), nstAlctBasDt(신주배정기준일자), onskNstAlctStckCnt(보통주신주배정주식수), otshNstAlctStckCnt(기타주신주배정주식수), emstowUnnFoalAlctRto(우리사주조합우선배정비율), emstowUnnSbscSchSttgDt(우리사주조합청약예정시작일자), emstowUnnSbscSchEdDt(우리사주조합청약예정종료일자), bfSthdSbscSchSttgDt(이전주주청약예정시작일자), bfSthdSbscSchEdDt(이전주주청약예정종료일자), pbsbSbscSchSttgDt(공모청약예정시작일자), pbsbSbscSchEdDt(공모청약예정종료일자), shcpPymtDt(주금납입일자), frstPcPlanCtt(실권주처리계획내용), nstDvdnRckDt(신주배당기산일자), nrfsHndvSchDt(신주권교부예정일자), nstLstgSchDt(신주상장예정일자), rprsSptdCmpyNm(대표주관회사명), prmrCnvYn(신주인수권양도여부), prmrCrtfLstgYn(신주인수권증서상장여부), trdMdatFinInvsNm(매매중개금융투자자명), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audpnAtndYn(감사인참석여부), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), ivsRefCtt(투자참고내용), basStprDcXchrRt(기준주가할인할증률), rd3PtAlctArasBsisCtt(제3자배정정관근거내용), dturLstgYn(우회상장여부), acthInvtYn(현물출자여부), rgscUnltStckYn(주권비상장주식여부), pymtSchActhInvtAmt(납입예정현물출자금액), pymtSchActhInvtRto(납입예정현물출자비율), pymtSchStckCnt(납입예정주식수), dturLstgPsblYn(우회상장가능여부), corRsnCtt(정정사유내용), hcfhPlanCtt(향후계획내용), rptFileCtt(보고서파일내용)

### getGeneMeetStocPublNotiDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), corpNm(법인명)
- 응답: basDt*(기준일자), crno*(법인등록번호), corpNm*(법인명), rptFileCtt(보고서파일내용)

### getAsseTranPutBackOptiDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), enpCorpNm(기업법인명), rptFileCtt(보고서파일내용)

### getDishDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), dshCtt(부도내용), dshAmt(부도금액), dshOccrBnkNm(부도발생은행명), lastDshDt(최종부도일자), dshRsnCtt(부도사유내용), ivsRefCtt(투자참고내용), rptFileCtt(보고서파일내용)

### getBusiSuspDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), bzopStopFildNm(영업정지분야명), bzopStopAmt(영업정지금액), ltstTsleAmt(최근총매출금액), bzopStopAmtRto(영업정지금액비율), lgscCorpYn(대규모법인여부), xchgLblPbanYn(거래소의무공시여부), bzopStopCtt(영업정지내용), bzopStopRsnCtt(영업정지사유내용), bzopStopCtpnCtt(영업정지대책내용), bzopStopInfcCtt(영업정지영향내용), bzopStopDt(영업정지일자), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audpnAtndYn(감사인참석여부), ivsRefCtt(투자참고내용), rptFileCtt(보고서파일내용)

### getReviProcDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), corvAplpnFnm(기업회생신청인성명), corvJurdCurtNm(기업회생관할법원명), corvPropRsnCtt(기업회생신청사유내용), corvPropDt(기업회생신청일자), corvCtpnCtt(기업회생대책내용), ivsRefCtt(투자참고내용), rptFileCtt(보고서파일내용)

### getDissReasDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), corpDsonRsnCtt(법인해산사유내용), corpDsonCtt(법인해산내용), corpDsonRsnOccrDt(법인해산사유발생일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), ivsRefCtt(투자참고내용), rptFileCtt(보고서파일내용)

### getReduCapiDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), rdcpOnskCnt(감자보통주수), rdcpOtshCnt(감자기타주수), stckParPrc(주식액면가), bfrcCptlAmt(감자전자본금액), afrcCptlAmt(감자후자본금액), bfrcIssuOnskCnt(감자전발행보통주수), bfrcIssuOtshCnt(감자전발행기타주수), afrcIssuOnskCnt(감자후발행보통주수), afrcIssuOtshCnt(감자후발행기타주수), onskRdcpRto(보통주감자비율), otshRdcpRto(기타주감자비율), rdcpBasDt(감자기준일자), rdcpMthNm(감자방법명), rdcpRsnCtt(감자사유내용), gmshSchDt(주주총회예정일자), trsnmStopTermMnthCnt(명의개서정지기간개월수), orfsSbmsTermMnthCnt(구주권제출기간개월수), trStopSchTermMnthCnt(거래정지예정기간개월수), nrfsHndvSchDt(신주권교부예정일자), nstLstgSchDt(신주상장예정일자), dsceSbmsSttgDt(이의제출시작일자), dsceSbmsEdDt(이의제출종료일자), nrfsHndvPlcNm(신주권교부장소명), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), ivsRefCtt(투자참고내용), arasBsisCtt(정관근거내용), stckCtt(주식내용), etcCtt(기타내용), rptFileCtt(보고서파일내용)

### getProcByCredBankDiscInfo_V2
- 요청: crno(법인등록번호), mngOpngDecsDt(관리개시결정일자)
- 응답: basDt(기준일자), crno*(법인등록번호), mngOpngDecsDt*(관리개시결정일자), bondMngInstNm(채권관리기관명), mngTermMnthCnt(관리기간개월수), crbkMngRsnCtt(채권은행관리사유내용), crbkMngCtt(채권은행관리내용), lwstAfrmDt(소송확인일자), ivsRefCtt(투자참고내용), rptFileCtt(보고서파일내용)

### getLitiEtcDiscInfo_V2
- 요청: crno(법인등록번호), lwstSggsDt(소송제기일자)
- 응답: basDt(기준일자), crno*(법인등록번호), lwstIcdtNm(소송사건명), lwstAplpnNm(소송신청인명), lwstClmCtt(소송청구내용), lwstJurdCurtNm(소송관할법원명), lwstRsltHcfhCtpnCtt(소송결과향후대책내용), lwstSggsDt*(소송제기일자), lwstAfrmDt(소송확인일자), ivsRefCtt(투자참고내용), rptFileCtt(보고서파일내용)

### getOffsSecuMarkListDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), enpCorpNm(기업법인명)
- 응답: basDt*(기준일자), crno*(법인등록번호), enpCorpNm*(기업법인명), lstgOnskCnt(상장보통주수), lstgOtshCnt(상장기타주수), lstgXchgDwplNtnlNm(상장거래소소재국가명), drIsinCdNm(DRISIN코드명), enpOvseXchgLstgDt(기업해외거래소상장일자), lwstAfrmDt(소송확인일자), ivsRefCtt(투자참고내용), arasBsisCtt(정관근거내용), stckCtt(주식내용), etcCtt(기타내용), rptFileCtt(보고서파일내용)

### getOffsSecuMarkDeliDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), lstgXchgDwplNtnlNm(상장거래소소재국가명), lstgAbolOnskCnt(상장폐지보통주수), lstgAbolOtshCnt(상장폐지기타주수), trEdDt(거래종료일자), lstgAbolRsnCtt(상장폐지사유내용), lstgAbolHcfhScedCtt(상장폐지향후일정내용), lwstAfrmDt(소송확인일자), ivsRefCtt(투자참고내용), arasBsisCtt(정관근거내용), stckCtt(주식내용), etcCtt(기타내용), rptFileCtt(보고서파일내용)

### getCbRighIssuDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), bondIssuDcnt(채권발행차수), bondKindNm(채권종류명), tcpbFcvlAmt(총사채권면금액), ovseCpbdTfcvlAmt(해외사채총권면금액), basExrt(기준환율), bondIssuAreaNm(채권발행지역명), ovseLstgMrktNm(해외상장시장명), fctfndAt(시설자금액), mgmCptAt(운영자금액), otcoScrtAcqAmt(타법인증권취득금액), etcCptlAmt(기타자본금액), srfcInrt(표면이율), exprInrt(만기이율), cpbdExprDt(사채만기일자), intPayMthNm(이자지급방법명), pamtRdptMthNm(원금상환방법명), cbIssuMthCtt(전환사채발행방법내용), cpbdCnvrRto(사채전환비율), cbCnvrPrc(전환사채전환가), cbPricDecsMthCtt(전환사채가격결정방법내용), dbetCnvrStckKindNm(사채권전환주식종류명), cpbdCnvrStckCnt(사채전환주식수), cpbdCnvrStckRto(사채전환주식비율), cbClmSttgDt(전환사채청구시작일자), cbClmEdDt(전환사채청구종료일자), cvprcAdjCtt(전환가조정내용), optnCtt(옵션내용), mracCtt(합병내용), cbrSbscDt(전환사채권청약일자), shcpPymtDt(주금납입일자), rprsSptdCmpyNm(대표주관회사명), grnInstNm(보증기관명), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audpnAtndYn(감사인참석여부), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), ovseIssuLnbTrCtt(해외발행대차거래내용), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), ivsRefCtt(투자참고내용), spcfIssuTrprNm(특정발행대상자명), maxSthdRltNm(최대주주관계명), tisuFcvlAmt(총발행권면금액), rgtExertCorpNm(권리행사법인명), fnpnCnt(출자자수), ceoFnm(대표이사성명), ceoShrRat(대표이사지분율), bzwrExorFnm(업무집행자성명), bzwrExorShrRat(업무집행자지분율), maxSthdFnm(최대주주성명), maxSthdShrRat(최대주주지분율), actnYear(회계연도), corpTastAmt(법인총자산금액), corpTdbtAmt(법인총부채금액), fncoTcptAmt(금융회사총자본금액), fncoCptlAmt(금융회사자본금액), stacTermMnthCnt(결산기간개월수), enpSaleAmt(기업매출금액), crtmNpal(당기순손익), actnAudpnNm(회계감사인명), audtOpnnCtt(감사의견내용), corRsnCtt(정정사유내용), hcfhPlanCtt(향후계획내용), rptFileCtt(보고서파일내용)

### getBwRighIssuDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), bondIssuDcnt(채권발행차수), bwrKindNm(신주인수권부사채권종류명), tcpbFcvlAmt(총사채권면금액), ovseCpbdTfcvlAmt(해외사채총권면금액), basExrt(기준환율), bondIssuAreaNm(채권발행지역명), ovseLstgMrktNm(해외상장시장명), fctfndAt(시설자금액), mgmCptAt(운영자금액), otcoScrtAcqAmt(타법인증권취득금액), etcCptlAmt(기타자본금액), srfcInrt(표면이율), exprInrt(만기이율), cpbdExprDt(사채만기일자), intPayMthNm(이자지급방법명), pamtRdptMthNm(원금상환방법명), bwIssuMthCtt(신주인수권부사채발행방법내용), bwrExertRto(신주인수권부사채권행사비율), bwrExertPrc(신주인수권부사채권행사가), exertPricDecsMthNm(행사가격결정방법명), prmrSprtYn(신주인수권분리여부), shcpPymtMthNm(주금납입방법명), issuStckKindNm(발행주식종류명), prmrIssuStckCnt(신주인수권발행주식수), issuStckRto(발행주식비율), rgtExertSttgDt(권리행사시작일자), rgtExertEdDt(권리행사종료일자), exertPricAdjCtt(행사가격조정내용), optnCtt(옵션내용), mracCtt(합병내용), bwrSbscDt(신주인수권부사채권청약일자), shcpPymtDt(주금납입일자), rprsSptdCmpyNm(대표주관회사명), grnInstNm(보증기관명), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audpnAtndYn(감사인참석여부), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), ovseIssuLnbTrCtt(해외발행대차거래내용), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), ivsRefCtt(투자참고내용), spcfIssuTrprNm(특정발행대상자명), maxSthdRltNm(최대주주관계명), tisuFcvlAmt(총발행권면금액), bwrThryPric(신주인수권부사채권이론가격), bwrThryPricMdelNm(신주인수권부사채권이론가격모델명), prmrValuCtt(신주인수권가치내용), bwrIssuDecsRmkCtt(신주인수권부사채권발행결정비고내용), dsslSchDt(매각예정일자), bwrFcvlAmt(신주인수권부사채권권면금액), prmrScrtTdslAmt(신주인수권증권총매각금액), nstUndtScrtDsslAmt(신주인수증권매각금액), prmrDsslCnptNm(신주인수권매각상대방명), dsslCnptMaxSthdRltNm(매각상대방최대주주관계명), corRsnCtt(정정사유내용), hcfhPlanCtt(향후계획내용), rptFileCtt(보고서파일내용)

### getEbRighIssuDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), bondIssuDcnt(채권발행차수), ebrKindNm(교환사채권종류명), tcpbFcvlAmt(총사채권면금액), ebFcvlAmt(교환사채권면금액), basExrt(기준환율), bondIssuAreaNm(채권발행지역명), ovseLstgMrktNm(해외상장시장명), fctfndAt(시설자금액), mgmCptAt(운영자금액), otcoScrtAcqAmt(타법인증권취득금액), etcCptlAmt(기타자본금액), srfcInrt(표면이율), exprInrt(만기이율), cpbdExprDt(사채만기일자), intPayMthNm(이자지급방법명), pamtRdptMthNm(원금상환방법명), ebrIssuMthCtt(교환사채권발행방법내용), ebrExchRto(교환사채권교환비율), ebExchPric(교환사채교환가격), ebExchPricDecsMthCtt(교환사채교환가격결정방법내용), exchTrgtStckKindNm(교환대상주식종류명), exchTrgtStckCnt(교환대상주식수), exchTrgtStckRto(교환대상주식비율), exchClmSttgDt(교환청구시작일자), exchClmEdDt(교환청구종료일자), ebExchPricAdjCtt(교환사채교환가격조정내용), optnCtt(옵션내용), ebrSbscDt(교환사채권청약일자), shcpPymtDt(주금납입일자), rprsSptdCmpyNm(대표주관회사명), grnInstNm(보증기관명), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audpnAtndYn(감사인참석여부), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), ovseIssuLnbTrCtt(해외발행대차거래내용), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), ivsRefCtt(투자참고내용), spcfIssuTrprNm(특정발행대상자명), maxSthdRltNm(최대주주관계명), tisuFcvlAmt(총발행권면금액), rptFileCtt(보고서파일내용)

### getAmorCoCoBondDisclInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), bondIssuDcnt(채권발행차수), ccbKindNm(조건부자본증권종류명), tcpbFcvlAmt1(총사채권면금액1), tcpbFcvlAmt2(총사채권면금액2), basExrt(기준환율), bondIssuAreaNm(채권발행지역명), ovseLstgMrktNm(해외상장시장명), fctfndAt(시설자금액), mgmCptAt(운영자금액), otcoScrtAcqAmt(타법인증권취득금액), etcCptlAmt(기타자본금액), srfcInrt(표면이율), exprInrt(만기이율), cpbdExprDt(사채만기일자), intPayMthNm(이자지급방법명), pamtRdptMthNm(원금상환방법명), amtpCpscIssuMthCtt(상각형자본증권발행방법내용), lblarbRsnCtt(채무조정사유내용), lblarbRngNm(채무조정범위명), lblarbRngDecsMthCtt(채무조정범위결정방법내용), optnCtt(옵션내용), ccbSbscDt(조건부자본증권청약일자), shcpPymtDt(주금납입일자), rprsSptdCmpyNm(대표주관회사명), grnInstNm(보증기관명), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audpnAtndYn(감사인참석여부), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), ovseIssuLnbTrCtt(해외발행대차거래내용), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), ivsRefCtt(투자참고내용), spcfIssuTrprNm(특정발행대상자명), maxSthdRltNm(최대주주관계명), tisuFcvlAmt(총발행권면금액), rptFileCtt(보고서파일내용)

### getTreaStocRepuDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), acqSchOnskCnt(취득예정보통주수), acqSchOtshCnt(취득예정기타주수), onskAcqSchAmt(보통주취득예정금액), otshAcqSchAmt(기타주취득예정금액), acqXpctSttgDt(취득예상시작일자), acqXpctEdDt(취득예상종료일자), holdXpctSttgDt(보유예상시작일자), holdXpctEdDt(보유예상종료일자), acqPrpsCtt(취득목적내용), acqMthCtt(취득방법내용), brkBrkrNm(위탁중개업자명), dvdnPsblWtpftOnskCnt(배당가능이익금내보통주수), dvdnPsblWtpftOtshCnt(배당가능이익금내기타주수), dvdnPsblWtpftOnskRto(배당가능이익금내보통주비율), dvdnPsblWtpftOtshRto(배당가능이익금내기타주비율), etcAcqOnskCnt(기타취득보통주수), etcAcqOtshCnt(기타취득기타주수), etcAcqOnskRto(기타취득보통주비율), etcAcqOtshRto(기타취득기타주비율), acqDecsDt(취득결정일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), onskBuynOrdgLmtCnt(보통주매수주문한도수), otshBuynOrdgCntLmtCnt(기타주매수주문수한도수), ivsRefCtt(투자참고내용), eolyNtprAmt(전년도말순자산금액), rbfEbzyrCptlAmt(직전사업연도말자본금액), dvdnPsblAmt(배당가능금액), nrlztPftAmt(미실현이익금액), mainSbjcRptStotAmt(주요사항보고서소계금액), trsstcAcqAmt(자기주식취득금액), dvdnPftPrprAm(배당이익준비금), midDvdnPftPrprAm(중간배당이익준비금), trstCntrAmt(신탁계약금액), mvavDspStckAcqOpr(이동평균처분주식취득원가), trsstcAcqLmtAmt(자기주식취득한도금액), onbdBssOnskAcqCnt(장내기초보통주취득수), onbdOnskAcqCnt(장내보통주취득수), onbdOnskDspCnt(장내보통주처분수), onbdOnskIcnrCnt(장내보통주소각수), onbdEoteOnskAcqCnt(장내기말보통주취득수), otcBssOnskAcqCnt(장외기초보통주취득수), otcOnskAcqCnt(장외보통주취득수), otcOnskDspCnt(장외보통주처분수), otcOnskIcnrCnt(장외보통주소각수), otcEoteOnskAcqCnt(장외기말보통주취득수), bssOppbBuynOnskCnt(기초공개매수보통주수), oppbBuynOnskAcqCnt(공개매수보통주취득수), oppbBuynOnskDspCnt(공개매수보통주처분수), oppbBuynOnskIcnrCnt(공개매수보통주소각수), eoteOnskPusaCnt(기말보통주공매수), bssOnskStotCnt(기초보통주소계수), acqOnskStotCnt(취득보통주소계수), dspOnskStotCnt(처분보통주소계수), icnrOnskStotCnt(소각보통주소계수), eoteOnskStotCnt(기말보통주소계수), onbdBssOtshAcqCnt(장내기초기타주취득수), onbdOtshAcqCnt(장내기타주취득수), onbdOtshDspCnt(장내기타주처분수), onbdOtshIcnrCnt(장내기타주소각수), onbdEoteOtshAcqCnt(장내기말기타주취득수), otcBssOtshAcqCnt(장외기초기타주취득수), otcOtshAcqCnt(장외기타주취득수), otcOtshDspCnt(장외기타주처분수), otcOtshIcnrCnt(장외기타주소각수), otcEoteOtshAcqCnt(장외기말기타주취득수), bssOppbBuynOtshCnt(기초공개매수기타주수), oppbBuynOtshAcqCnt(공개매수기타주취득수), oppbBuynOtshDspCnt(공개매수기타주처분수), oppbBuynOtshIcnrCnt(공개매수기타주소각수), eoteOppbBuynOtshCnt(기말공개매수기타주수), bssOtshStotCnt(기초기타주소계수), acqOtshStotCnt(취득기타주소계수), dspOtshStotCnt(처분기타주소계수), icnrOtshStotCnt(소각기타주소계수), eoteOtshStotCnt(기말기타주소계수), bssHoldOnskCnt(기초보유보통주수), trteOnskAcqStckCnt(수탁자보통주취득주식수), trteOnskDspStckCnt(수탁자보통주처분주식수), trteOnskIcnrStckCnt(수탁자보통주소각주식수), eoteOnskHoldStckCnt(기말보통주보유주식수), bssActhHoldOnskCnt(기초현물보유보통주수), acqOnskCnt(취득보통주수), dspOnskCnt(처분보통주수), icnrOnskCnt(소각보통주수), eoteOnskCnt(기말보통주수), bssAcqOtshCnt(기초취득기타주수), otshAcqStckCnt(기타주취득주식수), otshDspStckCnt(기타주처분주식수), otshIcnrStckCnt(기타주소각주식수), eoteOtshAcqStckCnt(기말기타주취득주식수), bssOtshAcqStckCnt(기초기타주취득주식수), onskAcqStckCnt(보통주취득주식수), onskDspStckCnt(보통주처분주식수), onskIcnrStckCnt(보통주소각주식수), eoteOnskAcqStckCnt(기말보통주취득주식수), bssOnskTsumCnt(기초보통주총합계수), onskAcqTsumCnt(보통주취득총합계수), onskDspTsumCnt(보통주처분총합계수), onskIcnrTsumCnt(보통주소각총합계수), eoteOnskTsumCnt(기말보통주총합계수), bssOtshCntTsumCnt(기초기타주수총합계수), acqOtshTsumCnt(취득기타주총합계수), dspOtshTsumCnt(처분기타주총합계수), icnrOtshTsumCnt(소각기타주총합계수), eoteOtshTsumCnt(기말기타주총합계수), rptFileCtt(보고서파일내용)

### getTreaStocSellDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), fncoCorpNm(금융회사법인명)
- 응답: basDt*(기준일자), crno*(법인등록번호), fncoCorpNm*(금융회사법인명), onskDspSchCnt(보통주처분예정수), otshDspSchCnt(기타주처분예정수), dspTrgtOnskPric(처분대상보통주가격), dspTrgtOtshPric(처분대상기타주가격), onskDspSchAmt(보통주처분예정금액), otshDspSchAmt(기타주처분예정금액), dspSchSttgDt(처분예정시작일자), dspSchEdDt(처분예정종료일자), dspPrpsCtt(처분목적내용), trsstcDspCtt1(자기주식처분내용1), trsstcDspCtt2(자기주식처분내용2), trsstcDspCtt3(자기주식처분내용3), trsstcDspCtt4(자기주식처분내용4), brkBrkrKrnFnm(위탁중개업자한글성명), bfdsTrsstcHoldCtt1(처분전자기주식보유내용1), bfdsTrsstcHoldCtt2(처분전자기주식보유내용2), bfdsTrsstcHoldCtt3(처분전자기주식보유내용3), bfdsTrsstcHoldCtt4(처분전자기주식보유내용4), bfdsTrsstcHoldCtt5(처분전자기주식보유내용5), bfdsTrsstcHoldCtt6(처분전자기주식보유내용6), bfdsTrsstcHoldCtt7(처분전자기주식보유내용7), bfdsTrsstcHoldCtt8(처분전자기주식보유내용8), dspDecsDt(처분결정일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), onskOrdgLmtCnt(보통주주문한도수), otshOrdgLmtCnt(기타주주문한도수), ivsRefCtt(투자참고내용), onbdBssDrctAcqOnskCnt(장내기초직접취득보통주수), onbdDrctAcqOnskAcqChngCnt(장내직접취득보통주취득변동수), onbdDrctAcqOnskDspChngCnt(장내직접취득보통주처분변동수), onbdDrctAcqOnskIcnrChngCnt(장내직접취득보통주소각변동수), onbdBssDrctAcqOtshCnt(장내기초직접취득기타주수), onbdDrctAcqOtshAcqChngCnt(장내직접취득기타주취득변동수), onbdDrctAcqOtshDspChngCnt(장내직접취득기타주처분변동수), onbdDrctAcqOtshIcnrChngCnt(장내직접취득기타주소각변동수), otcBssDrctAcqOnskCnt(장외기초직접취득보통주수), otcDrctAcqOnskAcqChngCnt(장외직접취득보통주취득변동수), otcDrctAcqOnskDspChngCnt(장외직접취득보통주처분변동수), otcDrctAcqOnskIcnrChngCnt(장외직접취득보통주소각변동수), otcBssDrctAcqOtshCnt(장외기초직접취득기타주수), otcDrctAcqOtshAcqChngCnt(장외직접취득기타주취득변동수), otcDrctAcqOtshDspChngCnt(장외직접취득기타주처분변동수), otcDrctAcqOtshIcnrChngCnt(장외직접취득기타주소각변동수), bssOppbBuynOnskCnt(기초공개매수보통주수), oppbBuynOnskAcqChngCnt(공개매수보통주취득변동수), oppbBuynOnskDspChngCnt(공개매수보통주처분변동수), oppbBuynOnskIcnrChngCnt(공개매수보통주소각변동수), bssOppbBuynOtshCnt(기초공개매수기타주수), oppbBuynOtshAcqChngCnt(공개매수기타주취득변동수), oppbBuynOtshDspChngCnt(공개매수기타주처분변동수), oppbBuynOtshIcnrChngCnt(공개매수기타주소각변동수), bssOnskStotCnt(기초보통주소계수), stotOnskAcqChngCnt(소계보통주취득변동수), stotOnskDspChngCnt(소계보통주처분변동수), stotOnskIcnrChngCnt(소계보통주소각변동수), bssOtshStotCnt(기초기타주소계수), stotOtshAcqChngCnt(소계기타주취득변동수), stotOtshDspChngCnt(소계기타주처분변동수), stotOtshIcnrChngCnt(소계기타주소각변동수), bssEtcAcqOnskCnt(기초기타취득보통주수), etcAcqOnskAcqChngCnt(기타취득보통주취득변동수), etcAcqOnskDspChngCnt(기타취득보통주처분변동수), etcAcqOnskIcnrChngCnt(기타취득보통주소각변동수), bssEtcAcqOtshCnt(기초기타취득기타주수), etcAcqOtshAcqChngCnt(기타취득기타주취득변동수), etcAcqOtshDspChngCnt(기타취득기타주처분변동수), etcAcqOtshIcnrChngCnt(기타취득기타주소각변동수), bssOnskTsumCnt(기초보통주총합계수), onskTacqChngCnt(보통주총취득변동수), onskTdspChngCnt(보통주총처분변동수), onskTincChngCnt(보통주총소각변동수), bssOtshTsumCnt(기초기타주총합계수), otshTacqChngCnt(기타주총취득변동수), otshTdspChngCnt(기타주총처분변동수), otshTincChngCnt(기타주총소각변동수), dspTrprCtt(처분대상자내용), maxSthdRltNm(최대주주관계명), selWhccCtt(선정경위내용), dspStckCnt(처분주식수), trsstcDspDecsRmkCtt(자기주식처분결정비고내용), rptFileCtt(보고서파일내용)

### getBusiInhetDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), inhtBzopCtt(양수영업내용), inhtBzopMainCtt(양수영업주요내용), inhtPric(양수가격), inhtYn(양수여부), inhtTrgtBzopSctnAstAmt(양수대상영업부문자산금액), inhtTrgtBzopSctnSaleAmt(양수대상영업부문매출금액), inhtTrgtBzopSctnDebtAmt(양수대상영업부문부채금액), tastAmt(총자산금액), tsleAmt(총매출금액), tdbtAmt(총부채금액), astAmtRto(자산금액비율), saleAmtRto(매출금액비율), debtAmtRto(부채금액비율), inhtPrpsCtt(양수목적내용), inhtInfcCtt(양수영향내용), cntrCclDt(계약체결일자), inhtBasDt(양수기준일자), trCnptNm(거래상대방명), trCnptCptlAmt(거래상대방자본금액), trCnptMainBizNm(거래상대방주요사업명), trCnptHdofAdr(거래상대방본점주소), cmpyRltNm(회사관계명), inhtMnpbPayCtt(양수대금지급내용), extnEvlYn(외부평가여부), inhtRsnCtt(양수사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), gmshSpclRsolYn(주주총회특별결의여부), gmshSchDt(주주총회예정일자), stckBuynRgclExertRqrmCtt(주식매수청구권행사요건내용), buynSchPric(매수예정가격), rgtExertCtt(권리행사내용), paySchCtt(지급예정내용), stckBuynRgclRstcCtt(주식매수청구권제한내용), cntrEfctCtt(계약효력내용), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), dturLstgYn(우회상장여부), hcfhScedCtt(향후일정내용), otcoDturLstgPsblYn(타법인우회상장가능여부), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), rptFileCtt(보고서파일내용)

### getBusiConvDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), cnvBzopTrgtYn(양도영업대상여부), cnvBzopCtt(양도영업내용), bzopCnvPric(영업양도가격), cnvTrgtBzopAstAmt(양도대상영업자산금액), cnvTrgtBzopSaleAmt(양도대상영업매출금액), tastAmt(총자산금액), tsleAmt(총매출금액), astAmtRto(자산금액비율), saleAmtRto(매출금액비율), cnvPrpsCtt(양도목적내용), cnvInfcCtt(양도영향내용), cntrCclDt(계약체결일자), cnvBasDt(양도기준일자), trCnptNm(거래상대방명), trCnptCptlAmt(거래상대방자본금액), trCnptMainBizNm(거래상대방주요사업명), trCnptHdofAdr(거래상대방본점주소), cmpyRltNm(회사관계명), cnvMnpbPayCtt(양도대금지급내용), extnEvlYn(외부평가여부), bzopCnvDecsBsisRsnCtt(영업양도결정근거사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), gmshSpclRsolYn(주주총회특별결의여부), gmshSchDt(주주총회예정일자), stckBuynRgclExertRqrmCtt(주식매수청구권행사요건내용), buynSchPric(매수예정가격), rgtExertCtt(권리행사내용), paySchCtt(지급예정내용), stckBuynRgclRstcCtt(주식매수청구권제한내용), cntrEfctCtt(계약효력내용), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), rptFileCtt(보고서파일내용)

### getStocSubsCertInheDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), issuCmpyNm(발행회사명)
- 응답: basDt*(기준일자), crno*(법인등록번호), issuCmpyNm*(발행회사명), issuCmpyNtnlNm(발행회사국가명), issuCmpyCptlAmt(발행회사자본금액), tisuStckCnt(총발행주식수), issuCmpyRprNm(발행회사대표자명), cmpyRltNm(회사관계명), issuCmpyMainBizNm(발행회사주요사업명), wt6MNstAcqYn(6개월이내신주취득여부), inhtStckCnt(양수주식수), inhtAmt(양수금액), tastAmt(총자산금액), tastRto(총자산비율), oselfCptlAm(자기자본금), oselfCptlRto(자기자본비율), afinOwnStckCnt(양수후소유주식수), afinShrRat(양수후지분율), inhtPrpsCtt(양수목적내용), inhtSchDt(양수예정일자), trCnptCorpNm1(거래상대방법인명1), trCnptCptlAmt(거래상대방자본금액), trCnptMainBizNm(거래상대방주요사업명), trCnptHdofAdr(거래상대방본점주소), corpRltNm(법인관계명), trMnpbPayCtt(거래대금지급내용), extnEvlYn(외부평가여부), inhtDecsRsnCtt(양수결정사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), dturLstgYn(우회상장여부), hcfhScedCtt(향후일정내용), otcoDturLstgPsblYn(타법인우회상장가능여부), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), fnafCrcmClsfNm(재무상황구분명), fncoTastAmt1(금융회사총자산금액1), fncoTdbtAmt1(금융회사총부채금액1), fncoTcptAmt1(금융회사총자본금액1), fncoCptlAmt1(금융회사자본금액1), enpSaleAmt1(기업매출금액1), fncoCrtmNpf(금융회사당기순이익), audtOpnnCtt1(감사의견내용1), actnAudpnNm1(회계감사인명1), trCnptNm(거래상대방명), trCnptNtntNm(거래상대방국적명), trCnptBsadr(거래상대방기본주소), trCnptOcptNm(거래상대방직업명), trCnptClsfNm(거래상대방구분명), trCnptCorpNm2(거래상대방법인명2), trCnptStckCnt(거래상대방주식수), trCnptShrRat(거래상대방지분율), ltstBizYear(최근사업연도), fncoTastAmt2(금융회사총자산금액2), fncoTdbtAmt2(금융회사총부채금액2), fncoTcptAmt2(금융회사총자본금액2), actnAudpnNm2(회계감사인명2), audtOpnnCtt2(감사의견내용2), stacTermMnthCnt(결산기간개월수), fncoCptlAmt2(금융회사자본금액2), enpSaleAmt2(기업매출금액2), crtmNpal(당기순손익), csobYn(휴업여부), csbzYn(폐업여부), trCnptRltNm(거래상대방관계명), enpTrCnptRltNm(기업거래상대방관계명), exutNm(임원명), cnptRltNm(상대방관계명), tyrTrCtt(당해거래내용), lsyrTrCtt(전년도거래내용), yra2TrCtt(전전년도거래내용), rptFileCtt(보고서파일내용)

### getStocSubsCertConvDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), issuCmpyNm(발행회사명)
- 응답: basDt*(기준일자), crno*(법인등록번호), issuCmpyNm*(발행회사명), issuCmpyNtnlNm(발행회사국가명), issuCmpyCptlAmt(발행회사자본금액), tisuStckCnt(총발행주식수), issuCmpyRprNm(발행회사대표자명), cmpyRltNm1(회사관계명1), issuCmpyMainBizNm(발행회사주요사업명), cnvStckCnt(양도주식수), cnvAmt(양도금액), tastAmt(총자산금액), tastRto(총자산비율), oselfCptlAm(자기자본금), oselfCptlRto(자기자본비율), afcnStckCnt(양도후주식수), afcnShrRat(양도후지분율), cnvPrpsCtt(양도목적내용), cnvSchDt(양도예정일자), trCnptCorpNm(거래상대방법인명), trCnptCptlAmt(거래상대방자본금액), trCnptMainBizNm(거래상대방주요사업명), trCnptHdofAdr(거래상대방본점주소), cmpyRltNm2(회사관계명2), trMnpbPayCtt(거래대금지급내용), extnEvlYn(외부평가여부), invtScrtCnvDecsBsisRsnCtt(출자증권양도결정근거사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), fnafCrcmClsfNm(재무상황구분명), corpTastAmt(법인총자산금액), issuCmpyTdbtAmt(발행회사총부채금액), enpTcptAmt(기업총자본금액), enpCptlAmt(기업자본금액), enpSaleAmt(기업매출금액), enpCrtmNpf(기업당기순이익), trCnptAudtOpnnCtt(거래상대방감사의견내용), actnAudpnNm(회계감사인명), rptFileCtt(보고서파일내용)

### getDebeRighInheDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), issuCmpyNm(발행회사명)
- 응답: basDt*(기준일자), crno*(법인등록번호), rgscDbetClsfNm(주권사채권구분명), bondIssuDcnt(채권발행차수), rgscKindNm(주권종류명), issuCmpyNm*(발행회사명), issuCmpyNtnlNm(발행회사국가명), issuCmpyCptlAmt(발행회사자본금액), tisuStckCnt(총발행주식수), issuCmpyRprNm(발행회사대표자명), cmpyRltNm1(회사관계명1), issuCmpyMainBizNm(발행회사주요사업명), wt6MNstAcqYn(6개월이내신주취득여부), inhtDecsFcvlAmt(양수결정권면금액), inhtAmt(양수금액), tastAmt(총자산금액), tastRto(총자산비율), oselfCptlAm(자기자본금), oselfCptlRto(자기자본비율), inhtPrpsCtt(양수목적내용), inhtSchDt(양수예정일자), trCnptCmpyNm(거래상대방회사명), trCnptCptlAmt(거래상대방자본금액), trCnptMainBizNm(거래상대방주요사업명), trCnptHdofAdr1(거래상대방본점주소1), cmpyRltNm2(회사관계명2), trMnpbPayCtt(거래대금지급내용), extnEvlYn(외부평가여부), dbetInhtDecsBsisRsnCtt(사채권양수결정근거사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), fnafCrcmClsfNm(재무상황구분명), issuCmpyTastAmt1(발행회사총자산금액1), issuCmpyTdbtAmt1(발행회사총부채금액1), enpTcptAmt1(기업총자본금액1), enpCptlAmt1(기업자본금액1), enpSaleAmt1(기업매출금액1), issuCmpyCrtmNpf(발행회사당기순이익), audtOpnnCtt1(감사의견내용1), actnAudpnNm1(회계감사인명1), trCnptNm(거래상대방명), trCnptNtntNm(거래상대방국적명), trCnptHdofAdr2(거래상대방본점주소2), trCnptOcptNm(거래상대방직업명), trCnptClsfNm(거래상대방구분명), trCnptCorpNm(거래상대방법인명), trCnptStckCnt(거래상대방주식수), trCnptShrRat(거래상대방지분율), ltstBizYear(최근사업연도), issuCmpyTastAmt2(발행회사총자산금액2), issuCmpyTdbtAmt2(발행회사총부채금액2), enpTcptAmt2(기업총자본금액2), actnAudpnNm2(회계감사인명2), audtOpnnCtt2(감사의견내용2), stacTermMnthCnt(결산기간개월수), enpCptlAmt2(기업자본금액2), enpSaleAmt2(기업매출금액2), crtmNpal(당기순손익), csobYn(휴업여부), csbzYn(폐업여부), trCnptRltNm(거래상대방관계명), enpTrCnptRltNm(기업거래상대방관계명), exutFnm(임원성명), cnptRltNm(상대방관계명), tyrTrCtt(당해거래내용), lsyrTrCtt(전년도거래내용), yra2TrCtt(전전년도거래내용), srfcInrt(표면이율), exprInrt(만기이율), cpbdExprDt(사채만기일자), prmrExertRto(신주인수권행사비율), exertPric(행사가격), exertPricDecsMthNm(행사가격결정방법명), prmrSprtYn(신주인수권분리여부), shcpPymtMthNm(주금납입방법명), prmrExertIssuStckKindNm(신주인수권행사발행주식종류명), rgtExertSttgDt(권리행사시작일자), rgtExertEdDt(권리행사종료일자), exertPricAdjCtt(행사가격조정내용), cbSrfcInrt(전환사채표면이율), cbExprInrt(전환사채만기이율), cbExprDt(전환사채만기일자), cpbdCnvrRto(사채전환비율), cbCnvrPrc1(전환사채전환가1), cbPricDecsMthCtt1(전환사채가격결정방법내용1), cnvrIssuStckKindNm(전환발행주식종류명), cbClmSttgDt(전환사채청구시작일자), cbClmEdDt(전환사채청구종료일자), cvprcAdjCtt1(전환가조정내용1), ebSrfcInrt(교환사채표면이율), ebExprInrt(교환사채만기이율), ebExprDt(교환사채만기일자), ebExchRto(교환사채교환비율), ebExchPric(교환사채교환가격), ebExchPricDecsMthCtt(교환사채교환가격결정방법내용), ebExchTrgtYn(교환사채교환대상여부), exchClmSttgDt(교환청구시작일자), exchClmEdDt(교환청구종료일자), ebExchPricAdjCtt(교환사채교환가격조정내용), cpscSrfcInrt(자본증권표면이율), cpscExprInrt(자본증권만기이율), cptlScrtCpbdExprDt(자본증권사채만기일자), stckCnvrRsnCtt(주식전환사유내용), stckCnvrRngCtt(주식전환범위내용), cbCnvrPrc2(전환사채전환가2), cbPricDecsMthCtt2(전환사채가격결정방법내용2), cnvrStckIssuKindNm(전환주식발행종류명), cnvrStckIssuStckCnt(전환주식발행주식수), cvprcAdjCtt2(전환가조정내용2), rptFileCtt(보고서파일내용)

### getDebeRighConvDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), issuCmpyNm(발행회사명)
- 응답: basDt*(기준일자), crno*(법인등록번호), rgscDbetClsfNm(주권사채권구분명), bondIssuDcnt(채권발행차수), dbetKindNm(사채권종류명), dbetAcqDt(사채권취득일자), issuCmpyNm*(발행회사명), issuCmpyNtnlNm(발행회사국가명), issuCmpyCptlAmt(발행회사자본금액), tisuStckCnt(총발행주식수), issuCmpyRprNm(발행회사대표자명), cmpyRltNm1(회사관계명1), issuCmpyMainBizNm(발행회사주요사업명), cnvDecsFcvlAmt(양도결정권면금액), cnvAmt(양도금액), tastAmt(총자산금액), tastRto(총자산비율), oselfCptlAm(자기자본금), oselfCptlRto(자기자본비율), cnvPrpsCtt(양도목적내용), cnvSchDt(양도예정일자), trCnptCmpyNm(거래상대방회사명), trCnptCptlAmt(거래상대방자본금액), trCnptMainBizNm(거래상대방주요사업명), trCnptHdofAdr(거래상대방본점주소), cmpyRltNm2(회사관계명2), trMnpbPayCtt(거래대금지급내용), extnEvlYn(외부평가여부), dbetCnvDecsBsisRsnCtt(사채권양도결정근거사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), imarTrCmteDclTrgtYn(공정거래위원회신고대상여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), fnafCrcmClsfNm(재무상황구분명), issuCmpyTastAmt(발행회사총자산금액), issuCmpyTdbtAmt(발행회사총부채금액), enpTcptAmt(기업총자본금액), enpCptlAmt(기업자본금액), enpSaleAmt(기업매출금액), issuCmpyCrtmNpf(발행회사당기순이익), issuCmpyAudtOpnnCtt(발행회사감사의견내용), actnAudpnNm(회계감사인명), rptFileCtt(보고서파일내용)

### getMnaDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), mracMthNm(합병방법명), mracFrmtNm(합병형태명), mracPrpsCtt(합병목적내용), mracInfcEfftCtt(합병영향효과내용), mracRtoCalcBsisCtt(합병비율산출근거내용), extnEvlYn(외부평가여부), mracDecsBsisRsnCtt(합병결정근거사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), mracNstOnskCnt(합병신주보통주수), mracNstClshCnt(합병신주종류주수), mracOpntCmpyNm(합병상대회사명), mracOpntCmpyMainBizNm(합병상대회사주요사업명), cmpyRltNm(회사관계명), mracOpntCmpyTastAmt(합병상대회사총자산금액), mracOpntCmpyTdbtAmt(합병상대회사총부채금액), mracOpntCmpyTcptAmt(합병상대회사총자본금액), mracOpntCmpyCptlAmt(합병상대회사자본금액), mracOpntCmpySaleAmt(합병상대회사매출금액), mracOpntCmpyCrtmNpf(합병상대회사당기순이익), actnAudpnNm(회계감사인명), mracOpntCmpyAudtOpnnCtt(합병상대회사감사의견내용), nwesMracCmpyNm(신설합병회사명), nwesMracCmpyTastAmt(신설합병회사총자산금액), nwesMracCmpyTcptAmt(신설합병회사총자본금액), nwesMracCmpyTdbtAmt(신설합병회사총부채금액), nwesMracCmpyCptlAmt(신설합병회사자본금액), nwesMracCmpyEstbBasDt(신설합병회사설립기준일자), newBizSaleAmt(신규사업매출금액), nwesMracCmpyMainBizNm(신설합병회사주요사업명), nwesMracCmpyRlstPropYn(신설합병회사재상장신청여부), mracCntrDt(합병계약일자), sthdFrmBasDt(주주확정기준일자), sthdNmlsLckSttgDt(주주명부폐쇄시작일자), sthdNmlsLckEdDt(주주명부폐쇄종료일자), oppsItntNtcRcptSttgDt(반대의사통지접수시작일자), oppsItntNtcRcptEdDt(반대의사통지접수종료일자), gmshSchDt(주주총회예정일자), stckBuynRgclExertSttgDt(주식매수청구권행사시작일자), stckBuynRgclExertEdDt(주식매수청구권행사종료일자), orfsSbmsSttgDt(구주권제출시작일자), orfsSbmsEdDt(구주권제출종료일자), trStopSchSttgDt(거래정지예정시작일자), trStopSchEdDt(거래정지예정종료일자), dsceSbmsSttgDt(이의제출시작일자), dsceSbmsEdDt(이의제출종료일자), mracDlnDt(합병기한일자), edRptgGmengDt(종료보고총회일자), mracRgstSchDt(합병등기예정일자), nrfsHndvSchDt(신주권교부예정일자), nstLstgSchDt(신주상장예정일자), dturLstgYn(우회상장여부), otcoDturLstgPsblYn(타법인우회상장가능여부), optnExertRqrmCtt(옵션행사요건내용), buynSchPric(매수예정가격), rgtExertCtt(권리행사내용), paySchCtt(지급예정내용), stckBuynRgclRstcCtt(주식매수청구권제한내용), cntrEfctCtt(계약효력내용), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), astVsTrstCtt(자산대비신탁내용), mngItmsDsntYn(관리종목지정여부), mracRstcYn(합병제한여부), rgscUnltMracYn(주권비상장합병여부), mracOtlCtt(합병개요내용), mracOpntCmpyCtt(합병상대회사내용), rptFileCtt(보고서파일내용)

### getSpilUpDiscInfo_V2
- 요청: basDt(기준일자)
- 응답: basDt*(기준일자), crno(법인등록번호), divMthNm(분할방법명), divPrpsCtt(분할목적내용), divInfcEfftCtt(분할영향효과내용), divRto(분할비율), divBfCmpyCtt(분할이전회사내용), divSubtCmpyNm(분할존속회사명), divSubtCmpyTastAmt(분할존속회사총자산금액), divSubtCmpyTcptAmt(분할존속회사총자본금액), divSubtCmpyTdbtAmt(분할존속회사총부채금액), divSubtCmpyCptlAmt(분할존속회사자본금액), divSubtCmpyFnafBasDt(분할존속회사재무기준일자), divSubtBizSaleAmt(분할존속사업매출금액), divSubtCmpyMainBizNm(분할존속회사주요사업명), afdvLstgMatnYn(분할후상장유지여부), divEstbCmpyNm(분할설립회사명), divEstbCmpyTastAmt(분할설립회사총자산금액), divEstbCmpyTcptAmt(분할설립회사총자본금액), divEstbCmpyTdbtAmt(분할설립회사총부채금액), divEstbCmpyCptlAmt(분할설립회사자본금액), divCmpyEstbBasDt(분할회사설립기준일자), newBizSaleAmt(신규사업매출금액), mainBizNm(주요사업명), rlstPropYn(재상장신청여부), rdcpRto(감자비율), orfsSbmsSttgDt(구주권제출시작일자), orfsSbmsEdDt(구주권제출종료일자), trStopSchSttgDt(거래정지예정시작일자), trStopSchEdDt(거래정지예정종료일자), nstAlctCondCtt(신주배정조건내용), nstPronRsnCtt(신주비례사유내용), nstAlctBasDt(신주배정기준일자), nrfsHndvSchDt(신주권교부예정일자), nstLstgSchDt(신주상장예정일자), gmshSchDt(주주총회예정일자), dsceSbmsSttgDt(이의제출시작일자), dsceSbmsEdDt(이의제출종료일자), divDlnDt(분할기한일자), divRgstSchDt(분할등기예정일자), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), rptFileCtt(보고서파일내용)

### getDiviCombDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), divMracMthNm(분할합병방법명), divMracPrpsCtt(분할합병목적내용), divMracInfcEfftCtt(분할합병영향효과내용), divBfCmpyCtt(분할이전회사내용), divSubtCmpyNm(분할존속회사명), divSubtCmpyTastAmt(분할존속회사총자산금액), divSubtCmpyTcptAmt(분할존속회사총자본금액), divSubtCmpyTdbtAmt(분할존속회사총부채금액), divSubtCmpyCptlAmt(분할존속회사자본금액), divSubtCmpyFnafBasDt(분할존속회사재무기준일자), divSubtBizSaleAmt(분할존속사업매출금액), divSubtCmpyMainBizNm(분할존속회사주요사업명), afdvLstgMatnYn1(분할후상장유지여부1), divEstbCmpyNm(분할설립회사명), divEstbCmpyTastAmt(분할설립회사총자산금액), divEstbCmpyTcptAmt(분할설립회사총자본금액), divEstbCmpyTdbtAmt(분할설립회사총부채금액), divEstbCmpyCptlAmt(분할설립회사자본금액), divCmpyEstbBasDt(분할회사설립기준일자), newBizSaleAmt(신규사업매출금액), mainBizNm(주요사업명), afdvLstgMatnYn2(분할후상장유지여부2), rdcpRto(감자비율), orfsSbmsSttgDt(구주권제출시작일자), orfsSbmsEdDt(구주권제출종료일자), trStopSchSttgDt(거래정지예정시작일자), trStopSchEdDt(거래정지예정종료일자), nstAlctCondCtt(신주배정조건내용), nstPronRsnCtt(신주비례사유내용), nstAlctBasDt(신주배정기준일자), nrfsHndvSchDt(신주권교부예정일자), nstLstgSchDt(신주상장예정일자), mracFrmtNm(합병형태명), mracOpntCmpyNm(합병상대회사명), mracOpntCmpyMainBizNm(합병상대회사주요사업명), cmpyRltNm(회사관계명), mracOpntCmpyTastAmt(합병상대회사총자산금액), mracOpntCmpyTdbtAmt(합병상대회사총부채금액), mracOpntCmpyTcptAmt(합병상대회사총자본금액), mracOpntCmpyCptlAmt(합병상대회사자본금액), mracOpntCmpySaleAmt(합병상대회사매출금액), mracOpntCmpyCrtmNpf(합병상대회사당기순이익), actnAudpnNm(회계감사인명), mracOpntCmpyAudtOpnnCtt(합병상대회사감사의견내용), divMracNstOnskCnt(분할합병신주보통주수), divMracNstClshCnt(분할합병신주종류주수), nwesMracCmpyNm(신설합병회사명), nwesMracCmpyCptlAmt(신설합병회사자본금액), nwesMracCmpyMainBizNm(신설합병회사주요사업명), nwesMracCmpyRlstPropYn(신설합병회사재상장신청여부), divMracRto(분할합병비율), divMracRtoCalcBsisCtt(분할합병비율산출근거내용), extnEvlYn(외부평가여부), divMracDecsBsisRsnCtt(분할합병결정근거사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), divMracCntrDt(분할합병계약일자), sthdFrmBasDt(주주확정기준일자), sthdNmlsLckSttgDt(주주명부폐쇄시작일자), sthdNmlsLckEdDt(주주명부폐쇄종료일자), oppsItntNtcRcptSttgDt(반대의사통지접수시작일자), oppsItntNtcRcptEdDt(반대의사통지접수종료일자), gmshSchDt(주주총회예정일자), stckBuynRgclExertSttgDt(주식매수청구권행사시작일자), stckBuynRgclExertEdDt(주식매수청구권행사종료일자), dsceSbmsSttgDt(이의제출시작일자), dsceSbmsEdDt(이의제출종료일자), divMracDlnDt(분할합병기한일자), edRptgGmengDt(종료보고총회일자), divMracRgstSchDt(분할합병등기예정일자), dturLstgYn(우회상장여부), otcoDturLstgPsblYn(타법인우회상장가능여부), optnExertRqrmCtt(옵션행사요건내용), buynSchPric(매수예정가격), rgtExertCtt(권리행사내용), paySchCtt(지급예정내용), stckBuynRgclRstcCtt(주식매수청구권제한내용), cntrEfctCtt(계약효력내용), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), divMracOtlCtt(분할합병개요내용), mracOpntCmpyCtt(합병상대회사내용), rptFileCtt(보고서파일내용)

### getStocExchTranDiscInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), stckExchClsfNm(주식교환구분명), exchTrnsFrmtNm(교환이전형태명), exchTrnsTrgtCorpNm(교환이전대상법인명), rprNm(대표자명), enpMainBizNm(기업주요사업명), cmpyRltNm(회사관계명), tisuOnskCnt(총발행보통주수), tisuClshCnt(총발행종류주수), stckExchTrgtCorpTastAmt(주식교환대상법인총자산금액), stckExchEnpTdbtAmt(주식교환기업총부채금액), enpTcptAmt(기업총자본금액), enpCptlAmt(기업자본금액), exchBfRto(교환이전비율), exchBfRtoCalcBsisCtt(교환이전비율산출근거내용), extnEvlYn(외부평가여부), stckTrnsDecsBsisRsnCtt(주식이전결정근거사유내용), extnEvlInstNm(외부평가기관명), extnEvlSttgDt(외부평가시작일자), extnEvlEdDt(외부평가종료일자), extnEvlOpnnCtt(외부평가의견내용), exchBfPrpsCtt(교환이전목적내용), exchBfInfcEfftCtt(교환이전영향효과내용), exchBfCntrDt(교환이전계약일자), sthdFrmBasDt(주주확정기준일자), sthdNmlsLckSttgDt(주주명부폐쇄시작일자), sthdNmlsLckEdDt(주주명부폐쇄종료일자), oppsItntNtcRcptSttgDt(반대의사통지접수시작일자), oppsItntNtcRcptEdDt(반대의사통지접수종료일자), gmshSchDt(주주총회예정일자), stckBuynRgclExertSttgDt(주식매수청구권행사시작일자), stckBuynRgclExertEdDt(주식매수청구권행사종료일자), orfsSbmsSttgDt(구주권제출시작일자), orfsSbmsEdDt(구주권제출종료일자), trStopSchTermMnthCnt(거래정지예정기간개월수), exchBfDt(교환이전일자), nrfsHndvSchDt(신주권교부예정일자), nstLstgSchDt(신주상장예정일자), exchAftsPrcoNm(교환이전후완전모회사명), stckBuynRgclExertRqrmCtt(주식매수청구권행사요건내용), buynSchPric(매수예정가격), rgtExertCtt(권리행사내용), paySchCtt(지급예정내용), stckBuynRgclRstcCtt(주식매수청구권제한내용), cntrEfctCtt(계약효력내용), dturLstgYn(우회상장여부), dturLstgPsblYn(우회상장가능여부), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audtCmbrAtndYn(감사위원참석여부), poptCntrCclYn(풋옵션계약체결여부), cntrCtt(계약내용), scrtDclrptSbmsTrgtYn(증권신고서제출대상여부), sbmsExemRsnCtt(제출면제사유내용), ivsRefCtt(투자참고내용), pbanCtt(공시내용), rptFileCtt(보고서파일내용)

### getStocOptiRepo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), lbrrCnt(피용자수), rltCmpyLbrrCnt(관계회사피용자수), stoptOnskCnt(주식매수선택권보통주수), stoptOtshCnt(주식매수선택권기타주수), stoptExertSttgDt(주식매수선택권행사시작일자), stoptExertEdDt(주식매수선택권행사종료일자), onskExertPrc(보통주행사가), otshExertPrc(기타주행사가), stoptGranMthNm(주식매수선택권부여방법명), stoptGranRsolInstNm(주식매수선택권부여결의기관명), stoptGranDt(주식매수선택권부여일자), stoptGranBsisCtt(주식매수선택권부여근거내용), onskGranStckCnt(보통주부여주식수), otshGranStckCnt(기타주부여주식수), bodRsolDt(이사회결의일자), otdrAtndNopeCnt(사외이사참석인원수), otdrAbncNopeCnt(사외이사불참인원수), audpnAtndYn(감사인참석여부), ivsRefCtt(투자참고내용), stoptTrprFnm(주식매수선택권대상자성명), stoptTrprRltNm(주식매수선택권대상자관계명), onskCnt(보통주수), otshCnt(기타주수), stckFrvuCtt(주식공정가치내용), stoptRmkCtt(주식매수선택권비고내용), arasBsisCtt(정관근거내용), stckCtt(주식내용), etcCtt(기타내용), rptFileCtt(보고서파일내용)

### getOutsDireHumaResoAffaRepo_V2
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), otdrMngCtt(사외이사관리내용), otdrFnm(사외이사성명), otdrTrmSttgDt(사외이사임기시작일자), otdrTrmXpryDt(사외이사임기만료일자), otdrNewDsgnYn(사외이사신규선임여부), otdrCrrCtt(사외이사경력내용), otdrNowOcptNm(사외이사현재직업명), otdrDsmsRsnCtt(사외이사해임사유내용), otdrDsmsDt(사외이사해임일자), tdrtCnt(총이사수), totdCnt(총사외이사수), otdrRto(사외이사비율), lgscCorpYn(대규모법인여부), ivsRefCtt(투자참고내용), rptFileCtt(보고서파일내용)

---

## 오픈API_활용자가이드_금융위원회_금융투자협회종합통계정보
- **서비스명(영문)**: `GetKofiaStatisticsInfoService`
- **BASE URL**: `https://apis.data.go.kr/1160100/service/GetKofiaStatisticsInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getTrustScaleInfo` — 업권별신탁규모
  - `getFundTotalNetEssetInfo` — 펀드순자산총액
  - `getCMAStatus` — 일자별CMA현황
  - `getGrantingOfCreditBalanceInfo` — 신용공여잔고추이
  - `GetSecuritiesMarketTotalCapitalI  nfo` — 증시자금추이
  - `getDLSAndDLBInfo` — DLS/DLB발행동향
  - `getELSAndELBInfo` — ELS/ELB발행동향
  - `getDerivationProductTradingInfo` — 국내투자자의 해외파생상품거래동향

### getTrustScaleInfo
- 요청: basYm(기준년월), bzds(업권), tstCtg(신탁구분), kind(종류)  <sub>(+범위/부분일치 변형 3개: begin*/end*/like* 접두)</sub>
- 응답: basYm(기준년월), bzds(업권), tstCtg(신탁구분), kind(종류), iqBs*(조회기준), val(조회기준별 값)

### getFundTotalNetEssetInfo
- 요청: basDt*(기준일자), ctg*(구분), tstMthdCtg*(신탁방식구분)  <sub>(+범위/부분일치 변형 5개: begin*/end*/like* 접두)</sub>
- 응답: basDt*(기준일자), ctg*(구분), tstMthdCtg*(신탁방식구분), nPptTotAmt*(순자산총액)

### getCMAStatus
- 요청: basDt(기준일자), mngInvTgt(운용대상), invrCtg(투자자구분)  <sub>(+범위/부분일치 변형 5개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), mngInvTgt(운용대상), invrCtg(투자자구분), scrtCmpyCnt(증권회사수), actCnt(계좌수), actBal(계좌잔액)

### getGrantingOfCreditBalanceInfo
- 요청: basDt(기준일자)  <sub>(+범위/부분일치 변형 9개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), crdTrFingWhl(신용거래융자 전체), crdTrFingScrs(신용거래융자 유가증권), crdTrFingKosdaq(신용거래융자 코스닥), crdTrLndrWhl(신용거래대주 전체), crdTrLndrScrs(신용거래대주 유가증권), crdTrLndrKosdaq(신용거래대주 코스닥), sbscCapLn(청약자금 대출), dpsgScrtMogFing(예탁증권 담보융자)

### GetSecuritiesMarketTotalCapitalI  nfo
- 요청: basDt(기준일자)  <sub>(+범위/부분일치 변형 5개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), invrDpsgAmt(투자자예탁금), onbdDrvPrdTrRcAdvAmt(장내파생상품거래예수금), toCstRpchCndBndSlgBal(대고객환매조건부채권매도잔고), brkTrdUcolMny(위탁매매미수금), brkTrdUcolMnyVsOppsTrdAmt(위탁매매미수금대비실제반대매매금액), ucolMnyVsOppsTrdRlImpt(미수금대비반대매매비중)

### getDLSAndDLBInfo
- 요청: basDt(기준일자), ctgDlbDls(구분), ctgPrplcPsub(신탁방식구분), presCtg(현황구분)  <sub>(+범위/부분일치 변형 3개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), ctgDlbDls(구분(DLB/DLS)), ctgPrplcPsub(구분(사모/공모)), presCtg(현황구분), amt(금액), ccnt(건수)

### getELSAndELBInfo
- 요청: basDt(기준일자), ctgElbEls(구분), ctgPrplcPsub(신탁방식구분), presCtg(현황구분)  <sub>(+범위/부분일치 변형 3개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), ctgElbEls(구분(ELB/ELS)), ctgPrplcPsub(구분(사모/공모)), presCtg(현황구분), amt(순자산총액), ccnt(순자산총액)

### getDerivationProductTradingInfo
- 요청: basDt(기준일자), byPrdGrp(상품군별), actCtg(계좌구분), ctgBsonCntrForm(계약형태에 따른 구분), prdNm(품목명), brkPn(위탁자), xchNm(거래소명), byNtnl(국가별), prdGrp(상품군)  <sub>(+범위/부분일치 변형 4개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), byPrdGrp(상품군별), actCtg(계좌구분), ctgBsonCntrForm(계약형태에 따른 구분), prdNm(상품명), brkPn(위탁자), xchNm(거래소명), csfBsonCntrForm(계약형태에 따른 분류), trqu(거래량), trPrcUsd(거래대금_USD), byNtnl(국가별), prdGrp(상품군)

---

## 오픈API_활용자가이드_금융위원회_금융회사재무신용정보
- **서비스명(영문)**: `GetFnCoFinaStatCredInfoService_V2`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetFnCoFinaStatCredInfoService_V2`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getFnCoSummFinaStat_V2t` — 금융회사요약재무제표조회
  - `getFnCoBs_V2` — 금융회사재무상태표조회
  - `getFnCoIs_V2` — 금융회사손익계산서조회

### getFnCoSummFinaStat_V2t
- 요청: basDt(기준일자), crno(법인등록번호), bizYear(사업연도)
- 응답: basDt*(기준일자), crno*(법인등록번호), curCd(통화 코드), bizYear*(사업연도), rptCd(보고서코드), rptCdNm(보고서코드명), fnclDcd(재무제표구분코드), fnclDcdNm(재무제표구분코드명), fncoSaleAmt(금융회사매출금액), fncoBzopPft(금융회사영업이익), iclsPalClcAmt(포괄손익계산금액), fncoCrtmNpf(금융회사당기순이익), fncoTastAmt(금융회사총자산금액), enpTdbtAmt(기업총부채금액), fncoTcptAmt(금융회사총자본금액), fncoCptlAmt(금융회사자본금액), fncoDebtRto(금융회사부채비율)

### getFnCoBs_V2
- 요청: basDt(기준일자), crno(법인등록번호), bizYear(사업연도)
- 응답: basDt*(기준일자), crno*(법인등록번호), curCd(통화 코드), bizYear*(사업연도), fnclDcd(재무제표구분코드), fnclDcdNm(재무제표구분코드명), acitId(계정과목ID), acitNm(계정과목명), thqrAcitAmt(당분기계정과목금액), crtmAcitAmt(당기계정과목금액), lsqtAcitAmt(전분기계정과목금액), pvtrAcitAmt(전기계정과목금액), bpvtrAcitAmt(전전기계정과목금액)

### getFnCoIs_V2
- 요청: basDt(기준일자), crno(법인등록번호), bizYear(사업연도)
- 응답: basDt*(기준일자), crno*(법인등록번호), curCd(통화 코드), bizYear*(사업연도), fnclDcd(재무제표구분코드), fnclDcdNm(재무제표구분코드명), acitId(계정과목ID), acitNm(계정과목명), thqrAcitAmt(당분기계정과목금액), crtmAcitAmt(당기계정과목금액), lsqtAcitAmt(전분기계정과목금액), pvtrAcitAmt(전기계정과목금액), bpvtrAcitAmt(전전기계정과목금액)

---

## 오픈API_활용자가이드_금융위원회_금융회사지배구조정보
- **서비스명(영문)**: `GetFnCoGoveInfoService`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetFnCoGoveInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getFnCoStocHoldInfo` — 금융회사주주정보조회
  - `getFnCoReprDireInfo` — 금융회사대표이사정보조회
  - `getFnCoExecRemuStat` — 금융회사임원보수현황조회
  - `getFnCoExecInfo` — 금융회사임원정보조회

### getFnCoStocHoldInfo
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), sthdSqno(주주일련번호), sthdFnm(주주성명), maxSthdRltNm(최대주주관계명), stckCsfNm(주식분류명), fncoEoteStckCnt(금융회사기말주식수), fncoEoteShrRatCtt(금융회사기말지분율내용)

### getFnCoReprDireInfo
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), fncoNm(금융회사명), ceoFnm(대표이사성명), ceoJbttNm(대표이사직위명), rgstExutYn(등기임원여부), ceoFltmsvYn(대표이사상근여부), ceoChrgBzwrCtt(대표이사담당업무내용), ceoMainCrrCtt(대표이사주요경력내용), ownOnskCnt(소유보통주수), ownPfstCnt(소유우선주수), maxSthdRltNm(최대주주관계명), ceoHdfTermCtt(대표이사재직기간내용), ceoTrmXpryDt(대표이사임기만료일자)

### getFnCoExecRemuStat
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), rgstDrtrCnt(등기이사수), rgstDrtrTrmrAmt(등기이사총보수금액), rgstDrtrAvgRmrAmt(등기이사평균보수금액), rgstDrtrRmkCtt(등기이사비고내용), otdrCnt(사외이사수), otdrTrmrAmt(사외이사총보수금액), otdrAvgRmrAmt(사외이사평균보수금액), otdrRmkCtt(사외이사비고내용), audpnCnt(감사인수), audpnTrmrAmt(감사인총보수금액), audpnAvgRmrAmt(감사인평균보수금액), audtRmkCtt(감사비고내용)

### getFnCoExecInfo
- 요청: basDt(기준일자), crno(법인등록번호)
- 응답: basDt*(기준일자), crno*(법인등록번호), dataSqno(데이터일련번호), exutFnm(임원성명), exutBornYm(임원출생년월), exutJbttNm(임원직위명), rgstExutYn(등기임원여부), rgstExutCtt(등기임원내용), fltmsvYn(상근여부), fltmsvCtt(상근내용), chrgBzwrCtt(담당업무내용), mainCrrCtt(주요경력내용), onskOwnStckCnt(보통주소유주식수), pfstOwnStckCnt(우선주소유주식수), exutHdfTermCtt(임원재직기간내용), exutTrmXpryDt(임원임기만료일자), sexCd(성별코드), sexCdNm(성별코드명), exutOwnOnskCnt(임원소유보통주수), exutOwnPfstCnt(임원소유우선주수)

---

## 오픈API_활용자가이드_금융위원회_기업기본정보
- **서비스명(영문)**: `GetCorpBasicInfoService_V2`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getCorpOutline_V2` — 기업개요조회
  - `getAffiliate_V2` — 계열회사조회
  - `getConsSubsComp_V2` — 연결대상종속기업조회

### getCorpOutline_V2
- 요청: crno(법인등록번호), corpNm(법인명)
- 응답: crno*(법인등록번호), corpNm*(법인명), corpEnsnNm(법인영문명), enpPbanCmpyNm(기업공시회사명), enpRprFnm(기업대표자성명), corpRegMrktDcd(법인등록시장구분코드), corpRegMrktDcdNm(법인등록시장구분코드명), corpDcd(법인구분코드), corpDcdNm(법인구분코드명), bzno(사업자등록번호), enpOzpno(기업구우편번호), enpBsadr(기업기본주소), enpDtadr(기업상세주소), enpHmpgUrl(기업홈페이지URL), enpTlno(기업전화번호), enpFxno(기업팩스번호), sicNm(표준산업분류명), enpEstbDt(기업설립일자), enpStacMm(기업결산월), enpXchgLstgDt(기업거래소상장일자), enpXchgLstgAbolDt(기업거래소상장폐지일자), enpKosdaqLstgDt(기업코스닥상장일자), enpKosdaqLstgAbolDt(기업코스닥상장폐지일자), enpKrxLstgDt(기업KONEX상장일자), enpKrxLstgAbolDt(기업KONEX상장폐지일자), smenpYn(중소기업여부), enpMntrBnkNm(기업주거래은행명), enpEmpeCnt(기업종업원수), empeAvgCnwkTermCtt(종업원평균근속기간내용), enpPn1AvgSlryAmt(기업1인평균급여금액), actnAudpnNm(회계감사인명), audtRptOpnnCtt(감사보고서의견내용), enpMainBizNm(기업주요사업명), fssCorpUnqNo(금융감독원법인고유번호), fssCorpChgDtm(금융감독원법인변경일시), fstOpegDt(최초개방일자), lastOpegDt(최종개방일자)

### getAffiliate_V2
- 요청: basDt(기준일자), crno(법인등록번호), afilCmpyNm(계열회사명)
- 응답: basDt*(기준일자), crno*(법인등록번호), afilCmpyNm*(계열회사명), afilCmpyCrno(계열회사법인등록번호), lstgYn(상장여부)

### getConsSubsComp_V2
- 요청: basDt(기준일자), crno(법인등록번호), sbrdEnpNm(종속기업명)
- 응답: basDt*(기준일자), crno*(법인등록번호), sbrdEnpNm*(종속기업명), sbrdEnpEstbDt(종속기업설립일자), sbrdEnpAdr(종속기업주소), sbrdEnpMainBizCtt(종속기업주요사업내용), sbrdEnpLtstEbzyrTastAmt(종속기업최근사업연도말총자산금액), dntRltBsisCtt(지배관계근거내용), mainSbrdEnpYnCtt(주요종속기업여부내용)

---

## 오픈API_활용자가이드_금융위원회_실손보험정보
- **서비스명(영문)**: `GetMedicalReimbursementInsuranceInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getInsuranceInfo` — 실손보험정보

### getInsuranceInfo
- 요청: basDt(기준일자), cmpyCd(회사코드), cmpyNm(회사명), ptrn(유형), mog(담보), prdNm(상품명), age(상품 가입 연령), ofrInstNm(제공기관명)  <sub>(+범위/부분일치 변형 5개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), cmpyCd(회사코드), cmpyNm(회사명), ptrn(유형), mog(담보), prdNm(상품명), age(상품 가입 연령), mlInsRt(남자보험료), fmlInsRt(여자보험료), ofrInstNm(제공기관명)

---

## 오픈API_활용자가이드_금융위원회_일반상품시세정보
- **서비스명(영문)**: `getGeneralProductInfoService`
- **BASE URL**: `https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getOilPriceInfo` — 석유시세
  - `getGoldPriceInfo` — 금 시세
  - `getCertifiedEmissionReductionPriceInfo` — 배출권 시세

### getOilPriceInfo
- 요청: basDt(기준일자), oilCtg(유종구분)  <sub>(+범위/부분일치 변형 11개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), oilCtg(유종구분), wtAvgPrcCptn(가중평균가격_경쟁), wtAvgPrcDisc(가중평균가격_협의), trqu(거래량), trPrc(거래대금)

### getGoldPriceInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명)  <sub>(+범위/부분일치 변형 14개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), srtnCd(단축코드), isinCd(ISIN코드), itmsNm(종목명), clpr(종가), vs(대비), fltRt(등락률), mkp(시가), hipr(고가), lopr(저가), trqu(거래량), trPrc(거래대금)

### getCertifiedEmissionReductionPriceInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명)  <sub>(+범위/부분일치 변형 14개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), srtnCd(단축코드), isinCd(ISIN코드), itmsNm(종목명), clpr(종가), vs(대비), fltRt(등락률), mkp(시가), hipr(고가), lopr(저가), trqu(거래량), trPrc(거래대금)

---

## 오픈API_활용자가이드_금융위원회_주식권리일정정보
- **서비스명(영문)**: `GetStocRighScheService_V2`
- **BASE URL**: `http://apis.data.go.kr/1160100/GetStocRighScheService_V2`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getRighExerReasSche_V2` — 

### getRighExerReasSche_V2
- 요청: basDt(기준일자), issuCmpyKsdCustNo(발행회사한국예탁결제원고객번호), stckIssuCmpyNm(주식발행회사명)
- 응답: basDt*(기준일자), issuCmpyKsdCustNo*(발행회사한국예탁결제원고객번호), crno(법인등록번호), stckIssuCmpyNm*(주식발행회사명), scrsIssuMnbdCd(유가증권발행주체코드), scrsIssuMnbdCdNm(유가증권발행주체코드명), stckIssuRcd(주식발행사유코드), stckIssuRcdNm(주식발행사유코드명), rgtExertRcd(권리행사사유코드), rgtExertRcdNm(권리행사사유코드명), rgtExertSttgDt(권리행사시작일자), rgtExertEdDt(권리행사종료일자), trsnmDptyDcd(명의개서대리인구분코드), trsnmDptyDcdNm(명의개서대리인구분코드명), stckParPrc(주식액면가), stckStacMd(주식결산월일), nmlsLckSttgDt(명부폐쇄시작일자), nmlsLckEdDt(명부폐쇄종료일자)

---

## 오픈API_활용자가이드_금융위원회_주식시세정보
- **서비스명(영문)**: `getStockSecuritiesInfoService`
- **BASE URL**: `https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getStockPriceInfo` — 주식시세
  - `getPreemptiveRightCertificatePriceInfo` — 신주인수권증서시세
  - `getSecuritiesPriceInfo` — 수익증권시세
  - `getPreemptiveRightSecuritiesPriceInfo` — 신주인수권증권시세

### getStockPriceInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명), mrktCls(시장구분)  <sub>(+범위/부분일치 변형 18개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), srtnCd(단축코드), isinCd(ISIN코드), itmsNm(종목명), mrktCtg(시장구분), clpr(종가), vs(대비), fltRt(등락률), mkp(시가), hipr(고가), lopr(저가), trqu(거래량), trPrc(거래대금), lstgStCnt(상장주식수), mrktTotAmt(시가총액)

### getPreemptiveRightCertificatePriceInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명), mrktCtg(시장구분), purRgtScrtItmsNm(목적주권_종목명)  <sub>(+범위/부분일치 변형 18개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), srtnCd(단축코드), isinCd(ISIN코드), itmsNm(종목명), mrktCtg(시장구분), clpr(종가), vs(대비), fltRt(등락률), mkp(시가), hipr(고가), lopr(저가), trqu(거래량), trPrc(거래대금), mrktTotAmt(시가총액), lstgCtfCnt(상장증서수), nstIssPrc(신주발행가), dltDt(상장폐지일), purRgtScrtItmsCd(목적주권_종목코드), purRgtScrtItmsNm(목적주권_종목명), purRgtScrtItmsClpr(목적주권_종가)

### getSecuritiesPriceInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명)  <sub>(+범위/부분일치 변형 16개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), srtnCd(단축코드), isinCd(ISIN코드), itmsNm(종목명), clpr(종가), vs(대비), fltRt(등락률), mkp(시가), hipr(고가), lopr(저가), trqu(거래량), trPrc(거래대금), stLstgCnt(상장좌수), mrktTotAmt(시가총액)

### getPreemptiveRightSecuritiesPriceInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명), mrktCtg(시장구분), purRgtScrtItmsNm(목적주권_종목명)  <sub>(+범위/부분일치 변형 20개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), srtnCd(단축코드), isinCd(ISIN코드), itmsNm(종목명), mrktCtg(시장구분), clpr(종가), vs(대비), fltRt(등락률), mkp(시가), hipr(고가), lopr(저가), trqu(거래량), trPrc(거래대금), mrktTotAmt(시가총액), lstgScrtCnt(상장증권수), exertPric(행사가격), subtPdSttgDt(존속기간_시작일), subtPdEdDt(존속기간_종료일), purRgtScrtItmsCd(목적주권_종목코드), purRgtScrtItmsNm(목적주권_종목명), purRgtScrtItmsClpr(목적주권_종가)

---

## 오픈API_활용자가이드_금융위원회_지수시세정보
- **서비스명(영문)**: `getMarketIndexInfoService`
- **BASE URL**: `https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getStockMarketIndex` — 주가지수시세
  - `getBondMarketIndex` — 채권지수시세
  - `getDerivationProductMarketIndex` — 파생상품지수시세

### getStockMarketIndex
- 요청: basDt(기준일자), idxNm(지수명)  <sub>(+범위/부분일치 변형 18개: begin*/end*/like* 접두)</sub>
- 응답: lsYrEdVsFltRt(전년말대비_ 등락률), basPntm(기준시점), basIdx(기준지수), basDt(기준일자), idxCsf(지수분류명), idxNm(지수명), epyItmsCnt(채용종목 수), clpr(종가), vs(대비), fltRt(등락률), mkp(시가), hipr(고가), lopr(저가), trqu(거래량), trPrc(거래대금), lstgMrktTotAmt(상장시가총액), lsYrEdVsFltRg(전년말대비_ 등락폭), yrWRcrdHgst(연중기록최고), yrWRcrdHgstDt(연중기록최고 일자), yrWRcrdLwst(연중기록최저), yrWRcrdLwstDt(연중기록최저 일자)

### getBondMarketIndex
- 요청: basDt(기준일자), idxNm(지수명)  <sub>(+범위/부분일치 변형 14개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), idxNm(지수명), totBnfIdxClpr(총수익지수 종가), totBnfIdxVs(총수익지수 대비), nPrcIdxClpr(순가격지수 종가), nPrcIdxVs(순가격지수 대비), zrRinvIdxClpr(제로재투자지수 종가), zrRinvIdxVs(제로재투자지수 대비), clRinvIdxClpr(콜재투자지수 종가), clRinvIdxVs(콜재투자지수 대비), mrktPrcIdxClpr(시장가격지수 종가), mrktPrcIdxVs(시장가격지수 대비), durt(듀레이션), cnvt(컨벡시티), ytm(YTM)

### getDerivationProductMarketIndex
- 요청: basDt(기준일자), idxNm(지수명)  <sub>(+범위/부분일치 변형 12개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), idxNm(지수명), vs(대비), fltRt(등락률), mkp(시가), hipr(고가), lopr(저가), trqu(거래량), trPrc(거래대금)

---

## 오픈API_활용자가이드_금융위원회_채권기본정보
- **서비스명(영문)**: `GetBondIssuInfoService_V2`
- **BASE URL**: `http://apis.data.go.kr/1160100/GetBondIssuInfoService_V2`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getBondBasiInfo_V2` — 채권기본정보조회

### getBondBasiInfo_V2
- 요청: basDt(기준일자), crno(법인등록번호), bondIsurNm(채권발행인명)
- 응답: basDt*(기준일자), crno*(법인등록번호), isinCd(ISIN코드), isinCdNm(ISIN코드명), scrsItmsKcd(유가증권종목종류코드), scrsItmsKcdNm(유가증권종목종류코드명), bondIssuCurCd(채권발행통화코드), bondIssuCurCdNm(채권발행통화코드명), bondIsurNm*(채권발행인명), sicNm(표준산업분류명), bondIssuDt(채권발행일자), bondExprDt(채권만기일자), irtChngDcd(금리변동구분코드), irtChngDcdNm(금리변동구분코드명), bondSrfcInrt(채권표면이율), grnDcd(보증구분코드), grnDcdNm(보증구분코드명), bondRnknDcd(채권순위구분코드), bondRnknDcdNm(채권순위구분코드명), optnTcd(옵션유형코드), optnTcdNm(옵션유형코드명), pclrBondKcd(특이채권종류코드), pclrBondKcdNm(특이채권종류코드명), bondIssuAmt(채권발행금액), bondPymtAmt(채권납입금액), bondBal(채권잔액), bondOffrMcd(채권모집방법코드), bondOffrMcdNm(채권모집방법코드명), lstgDt(상장일자), txtnDcd(과세구분코드), txtnDcdNm(과세구분코드명), pamtRdptMcd(원금상환방법코드), pamtRdptMcdNm(원금상환방법코드명), stripsPsblYn(스트립스채권가능여부), stripsNm(스트립스채권명), prisLnkgBondYn(물가연동채권여부), piamPayInstNm(원리금지급기관명), piamPayBrofNm(원리금지급지점명), cptUsgeDcd(자금용도구분코드), cptUsgeDcdNm(자금용도구분코드명), bondRegInstDcd(채권등록기관구분코드), bondRegInstDcdNm(채권등록기관구분코드명), issuDptyNm(발행대리인명), bondUndtInstNm(채권인수기관명), bondGrnInstNm(채권보증기관명), cpbdMngCmpyNm(사채관리회사명), crfndYn(크라우드펀딩여부), prmncBondYn(영구채권여부), qibTrgtScrtYn(QIB대상증권여부), prmncBondTmnDt(영구채권해지일자), rgtExertMnbdDcd(권리행사주체구분코드), rgtExertMnbdDcdNm(권리행사주체구분코드명), intCmpuMcd(이자산정방법코드), intCmpuMcdNm(이자산정방법코드명), qibTmnDt(QIB해지일자), bondIntTcd(채권이자유형코드), bondIntTcdNm(채권이자유형코드명), intPayCyclCtt(이자지급주기내용), nxtmCopnDt(차기이표일자), rbfCopnDt(직전이표일자), bnkHldyIntPydyDcd(은행휴일이자지급일구분코드), bnkHldyIntPydyDcdNm(은행휴일이자지급일구분코드명), sttrHldyIntPydyDcd(법정휴일이자지급일구분코드), sttrHldyIntPydyDcdNm(법정휴일이자지급일구분코드명), intPayMmntDcd(이자지급시기구분코드), intPayMmntDcdNm(이자지급시기구분코드명), elpsIntPayYn(경과이자지급여부), kisScrsItmsKcd(한국신용평가유가증권종목종류코드), kisScrsItmsKcdNm(한국신용평가유가증권종목종류코드명), kbpScrsItmsKcd(한국자산평가유가증권종목종류코드), kbpScrsItmsKcdNm(한국자산평가유가증권종목종류코드명), niceScrsItmsKcd(NICE평가정보유가증권종목종류코드), niceScrsItmsKcdNm(NICE평가정보유가증권종목종류코드명), fnScrsItmsKcd(FN유가증권종목종류코드), fnScrsItmsKcdNm(FN유가증권종목종류코드명)

---

## 오픈API_활용자가이드_금융위원회_채권시세정보
- **서비스명(영문)**: `GetBondSecuritiesInfoService`
- **BASE URL**: `https://apis.data.go.kr/1160100/service/GetBondSecuritiesInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getBondPriceInfo` — 채권시세

### getBondPriceInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명), mrktCtg(시장구분)  <sub>(+범위/부분일치 변형 16개: begin*/end*/like* 접두)</sub>
- 응답: mkpPrc(시가_가격), mkpBnfRt(시가_수익률), hiprPrc(고가_가격), hiprBnfRt(고가_수익률), loprPrc(저가_가격), loprBnfRt(저가_수익률), trqu(거래량), trPrc(거래대금), basDt(기준일자), srtnCd(단축코드), isinCd(ISIN코드), xpYrCnt(만기년수), itmsCtg(종목구분), clprPrc(종가_가격), itmsNm(종목명), mrktCtg(시장구분), clprVs(종가_대비), clprBnfRt(종가_수익률)

---

## 오픈API_활용자가이드_금융위원회_파생상품시세정보
- **서비스명(영문)**: `GetDerivativeProductInfoService`
- **BASE URL**: `https://apis.data.go.kr/1160100/service/GetDerivativeProductInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getStockFuturesPriceInfo` — 선물시세
  - `getOptionsPriceInfo` — 옵션시세

### getStockFuturesPriceInfo
- 요청: basDt(기준일자), isinCd(ISIN코드), itmsNm(종목명), prdCtg(상품구분)  <sub>(+범위/부분일치 변형 14개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), prdCtg(상품구분), srtnCd(단축코드), isinCd(ISIN코드), itmsNm(종목명), clpr(종가), vs(대비), mkp(시가), hipr(고가), lopr(저가), sptPrc(현물가), stmPrc(정산가), trqu(거래량), trPrc(거래대금), opnint(미결제약정)

### getOptionsPriceInfo
- 요청: basDt(기준일자), prdCtg(상품구분), isinCd(ISIN코드), itmsNm(종목명)  <sub>(+범위/부분일치 변형 10개: begin*/end*/like* 접두)</sub>
- 응답: vs(대비), mkp(시가), hipr(고가), lopr(저가), nxtDdBsPrc(익일기준가), iptVlty(내재변동성), trqu(거래량), trPrc(거래대금), opnint(미결제약정), clpr(종가), basDt(기준일자), prdCtg(상품구분), srtnCd(단축코드), isinCd(ISIN코드), itmsNm(종목명)

---

## 오픈API_활용자가이드_금융위원회_펀드상품기본정보
- **서비스명(영문)**: `GetFundProductInfoService`
- **BASE URL**: `https://apis.data.go.kr/1160100/service/GetFundProductInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getStandardCodeInfo` — 펀드표준코드

### getStandardCodeInfo
- 요청: basDt(기준일자), srtnCd(단축코드), fndNm(펀드명), ctg(구분), fndTp(펀드유형)  <sub>(+범위/부분일치 변형 4개: begin*/end*/like* 접두)</sub>
- 응답: basDt(기준일자), srtnCd(단축코드), fndNm(펀드명), ctg(구분), setpDt(설정일), fndTp(펀드유형), prdClsfCd(상품분류코드), asoStdCd(협회표준코드)

---

## 오픈API_활용자가이드_기업_재무정보
- **서비스명(영문)**: `GetFinaStatInfoService_V2`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetFinaStatInfoService_V2`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getSummFinaStat_V2` — 요약재무제표조회
  - `getBs_V2` — 재무상태표조회
  - `getIncoStat_V2` — 손익계산서조회

### getSummFinaStat_V2
- 요청: crno(법인등록번호), bizYear(사업연도)
- 응답: basDt(기준일자), crno*(법인등록번호), curCd(통화 코드), bizYear*(사업연도), fnclDcd(재무제표구분코드), fnclDcdNm(재무제표구분코드명), enpSaleAmt(기업매출금액), enpBzopPft(기업영업이익), iclsPalClcAmt(포괄손익계산금액), enpCrtmNpf(기업당기순이익), enpTastAmt(기업총자산금액), enpTdbtAmt(기업총부채금액), enpTcptAmt(기업총자본금액), enpCptlAmt(기업자본금액), fnclDebtRto(재무제표부채비율)

### getBs_V2
- 요청: crno(법인등록번호), bizYear(사업연도)
- 응답: basDt(기준일자), crno*(법인등록번호), curCd(통화 코드), bizYear*(사업연도), fnclDcd(재무제표구분코드), fnclDcdNm(재무제표구분코드명), acitId(계정과목ID), acitNm(계정과목명), thqrAcitAmt(당분기계정과목금액), crtmAcitAmt(당기계정과목금액), lsqtAcitAmt(전분기계정과목금액), pvtrAcitAmt(전기계정과목금액), bpvtrAcitAmt(전전기계정과목금액)

### getIncoStat_V2
- 요청: crno(법인등록번호), bizYear(사업연도)
- 응답: basDt(기준일자), crno*(법인등록번호), curCd(통화 코드), bizYear*(사업연도), fnclDcd(재무제표구분코드), fnclDcdNm(재무제표구분코드명), acitId(계정과목ID), acitNm(계정과목명), thqrAcitAmt(당분기계정과목금액), crtmAcitAmt(당기계정과목금액), lsqtAcitAmt(전분기계정과목금액), pvtrAcitAmt(전기계정과목금액), bpvtrAcitAmt(전전기계정과목금액)

---

## 오픈API활용자가이드_금융회사기본정보조회서비스
- **서비스명(영문)**: `GetFnCoBasiInfoService`
- **BASE URL**: `http://apis.data.go.kr/1160100/service/GetFnCoBasiInfoService`
- **갱신주기**: 일 1회
- **오퍼레이션**:
  - `getFnCoOutl` — 

### getFnCoOutl
- 요청: basDt(기준일자), crno(법인등록번호), fncoNm(금융회사명)
- 응답: basDt*(기준일자), crno*(법인등록번호), fncoNm*(금융회사명), fncoEnsnNm(금융회사영문명), isinCd(ISIN코드), isinCdNm(ISIN코드명), fncoRprNm(금융회사대표자명), corpRegMrktDcd(법인등록시장구분코드), corpRegMrktDcdNm(법인등록시장구분코드명), bzno(사업자등록번호), fncoAdr(금융회사주소), fncoZpcd(금융회사우편번호), fncoHmpgUrl(금융회사홈페이지URL), fncoTlno(금융회사전화번호), fncoFxno(금융회사팩스번호), sicCd(표준산업분류코드), sicNm(표준산업분류명), fncoEstbDt(금융회사설립일자), fncoStacMm(금융회사결산월), fncoXchgLstgDt(금융회사거래소상장일자), fncoXchgLstgAbolDt(금융회사거래소상장폐지일자), fncoKosdaqLstgDt(금융회사코스닥상장일자), fncoKosdaqLstgAbolDt(금융회사코스닥상장폐지일자), fncoKrxLstgDt(금융회사KONEX상장일자), fncoKrxLstgAbolDt(금융회사KONEX상장폐지일자), fncoSmenpYn(금융회사중소기업여부), mntrFcnFncoCd(주거래금융공동망금융회사코드), mntrFcnFncoCdNm(주거래금융공동망금융회사코드명), fncoEmpeCnt(금융회사종업원수), empeAvgCnwkTermCtt(종업원평균근속기간내용), fncoEmpeAvgSlryAmt(금융회사종업원평균급여금액), actnAudpnNm(회계감사인명), audtRptOpnnCtt(감사보고서의견내용), fncoMainBizNm(금융회사주요사업명), fssCorpUnqNo(금융감독원법인고유번호), fssCorpChgDtm(금융감독원법인변경일시)

---

## 활용가이드_대한무역투자진흥공사_한국_산업별_외국인직접투자통계
- **서비스명(영문)**: `DS00000127`
- **BASE URL**: `http://apis.data.go.kr/B410001/DS00000127`
- **갱신주기**: 1년
- **오퍼레이션**:
  - `getDS00000127` — 

### getDS00000127
- 응답: BASE_YR(기준연도), KSIC_NAME(KSIC명), LEVEL_CD(레벨), STTMN_CNT(신고수), STTMN_AMT(신고금액), COMP_CNT(업체수), INVT_AMT(투자금액)

---
