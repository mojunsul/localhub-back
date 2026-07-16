# 서울시 자치구별 모범음식점 지정 현황 스키마

## 파일명

```text
서울시 {자치구} 모범음식점 지정 현황.json
```

현재 서울 25개 자치구 파일을 포함합니다.

## 최상위 구조

| 필드 | 설명 |
|---|---|
| `DESCRIPTION` | 원본 필드 설명 |
| `DATA` | 모범음식점 지정 기록 배열 |

## 주요 DATA 필드

| 원본 필드 | 설명 | 챗봇 내부 필드 |
|---|---|---|
| `upso_nm` | 업소명 | `title` |
| `site_addr_rd` | 도로명주소 | `address` |
| `site_addr` | 지번주소 | `jibun_address` |
| `admdng_nm` | 행정동명 | `district_dong` |
| `upso_site_telno` | 전화번호 | `tel` |
| `main_edf` | 주된 음식 | `main_food` |
| `snt_uptae_nm` | 업태명 | `business_type` |
| `asgn_yy` | 지정연도 | `designation_year` |
| `asgn_ymd` | 지정일자 | `designation_date` |
| `asgn_sno` | 지정번호 | `designation_number` |
| `perm_nt_no` | 허가·신고번호 | `permit_number` |
| `trdp_area` | 영업장 면적 | `business_area` |

## 내부 검색 규칙

- 파일명에서 자치구를 추출합니다.
- 카테고리는 `모범음식점`으로 지정합니다.
- 업소명, 자치구, 행정동, 주소, 주된 음식, 업태, 지정연도를 검색합니다.
- 동일 허가번호가 여러 지정연도에 있으면 최신 지정일자를 우선합니다.
- 원본 JSON은 수정하지 않습니다.
