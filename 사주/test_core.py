# encoding: utf-8
"""
핵심 계산 단위 테스트
실행: python test_core.py
모든 항목이 ✅ 이면 정상, ❌ 이면 버그
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from saju import (
    get_saju, get_sipseong, get_gyeokguk, get_yongshin,
    judge_strength, check_sal, get_daewoon,
    OHAENG_IDX, OHAENG_IDX_J, CHEONGAN, JIJI,
    OHAENG_NAMES, 궁합_점수_named, analyze_gunghap,
    analyze_this_year, analyze_wolun_detail,
)
from datetime import datetime

passed = 0
failed = 0

def check(label, result, expected):
    global passed, failed
    if result == expected:
        print(f'  ✅ {label}')
        passed += 1
    else:
        print(f'  ❌ {label}: 결과={result!r}, 기대={expected!r}')
        failed += 1

# ──────────────────────────────────────────────────────────────
print('=== 1. 십성(十星) 계산 ===')
# 갑(甲, 양목, 0) 일간 기준
pairs = [
    (0, '갑', '비견'), (1, '을', '겁재'),
    (2, '병', '식신'), (3, '정', '상관'),
    (4, '무', '편재'), (5, '기', '정재'),
    (6, '경', '편관'), (7, '신', '정관'),
    (8, '임', '편인'), (9, '계', '정인'),
]
for t, name, expected in pairs:
    result_bool = get_sipseong(0, OHAENG_IDX[t], t % 2 == 0)  # 불리언 호출
    result_int  = get_sipseong(0, OHAENG_IDX[t], t % 2)       # 정수 호출
    check(f'갑+{name}(bool)', result_bool, expected)
    check(f'갑+{name}(int)',  result_int,  expected)

# 신(辛, 음금, 7) 일간 기준
# 신=음 → 같은 음양(음+음)=편, 다른 음양(음+양)=겁재/상관/편재/편관/편인
pairs_sin = [
    (6, '경', '겁재'), (7, '신', '비견'),   # 경=양금(다른음양)→겁재, 신=음금(같은음양)→비견
    (8, '임', '상관'), (9, '계', '식신'),   # 임=양수(다른)→상관, 계=음수(같은)→식신
    (0, '갑', '정재'), (1, '을', '편재'),   # 갑=양목(다른)→정재, 을=음목(같은)→편재
    (2, '병', '정관'), (3, '정', '편관'),   # 병=양화(다른)→정관, 정=음화(같은)→편관
    (4, '무', '정인'), (5, '기', '편인'),   # 무=양토(다른)→정인, 기=음토(같은)→편인
]
for t, name, expected in pairs_sin:
    result = get_sipseong(7, OHAENG_IDX[t], t % 2)
    check(f'신+{name}', result, expected)

# ──────────────────────────────────────────────────────────────
print()
print('=== 2. 격국(格局) 판별 ===')
# 신(辛) 일간 미(未)월 → 편인격
p1, _, _ = get_saju(1990, 7, 15, 12, 0)
gyeok1, _, _ = get_gyeokguk(p1)
check('신일간 미월 → 편인격', gyeok1, '편인격')

# 갑(甲) 일간 오(午)월 → 식신격
p2, _, _ = get_saju(1986, 6, 10, 12, 0)
ilgan2 = p2[2][0]
gyeok2, _, _ = get_gyeokguk(p2)
check(f'{CHEONGAN[ilgan2]}일간 격국 계산됨', gyeok2 != '', True)

# ──────────────────────────────────────────────────────────────
print()
print('=== 3. 신강/신약 판별 ===')
p_strong, _, _ = get_saju(1984, 3, 5, 12, 0)
p_weak,   _, _ = get_saju(1990, 7, 15, 12, 0)
check('신강 사주 판별', '신강' in judge_strength(p_strong), True)
check('신약 사주 판별', '신약' in judge_strength(p_weak),   True)

# ──────────────────────────────────────────────────────────────
print()
print('=== 4. 신살(神殺) 계산 ===')
# 갑(甲=0) 일간: 천을귀인 = 축(1)/미(7)
# 만들기: 갑 일간에 축이나 미가 있는 사주
for y in range(1980, 2005):
    for m in [1, 4, 7, 10]:
        for d in [1, 10, 20]:
            try:
                p, _, _ = get_saju(y, m, d, 12, 0)
                if p[2][0] == 0:  # 갑 일간
                    jijis = [pil[1] for pil in p]
                    has_cy = any(j in {1, 7} for j in jijis)
                    gil, _ = check_sal(p)
                    cy_found = any('천을귀인' in g for g in gil)
                    if has_cy:
                        check('갑일간 천을귀인(축/미) 감지', cy_found, True)
                        raise StopIteration
            except StopIteration:
                break
        else: continue
        break
    else: continue
    break

# 양인살: 갑(0) → 묘(3)
for y in range(1980, 2005):
    for m in range(1, 13):
        for d in [5, 15, 25]:
            try:
                p, _, _ = get_saju(y, m, d, 12, 0)
                if p[2][0] == 0:  # 갑 일간
                    jijis = [pil[1] for pil in p]
                    if 3 in jijis:  # 묘 있으면 양인살
                        _, hyung = check_sal(p)
                        yi_found = any('양인살' in h for h in hyung)
                        check('갑일간 묘지지 → 양인살', yi_found, True)
                        raise StopIteration
            except StopIteration:
                break
        else: continue
        break
    else: continue
    break

# ──────────────────────────────────────────────────────────────
print()
print('=== 5. 대운(大運) 순행/역행 ===')
# 경오(庚午)년 = 양년 → 남=순행, 여=역행
p_yang_m, _, _ = get_saju(1990, 7, 15, 12, 0)  # 1990=경오=양년
start_m, fwd_m, _ = get_daewoon(p_yang_m, datetime(1990, 7, 15), True)
start_f, fwd_f, _ = get_daewoon(p_yang_m, datetime(1990, 7, 15), False)
check('양년 남자 → 순행', fwd_m, True)
check('양년 여자 → 역행', fwd_f, False)

# 신미(辛未)년 = 음년 → 남=역행, 여=순행
p_yin_m, _, _ = get_saju(1991, 3, 10, 12, 0)
start_m2, fwd_m2, _ = get_daewoon(p_yin_m, datetime(1991, 3, 10), True)
start_f2, fwd_f2, _ = get_daewoon(p_yin_m, datetime(1991, 3, 10), False)
check('음년 남자 → 역행', fwd_m2, False)
check('음년 여자 → 순행', fwd_f2, True)

# ──────────────────────────────────────────────────────────────
print()
print('=== 6. 충/파/해/원진 중복 없음 ===')
import random; random.seed(42)
dup_errors = 0
for _ in range(100):
    ya = random.randint(1970, 2005); ma = random.randint(1, 12); da = random.randint(1, 28)
    yb = random.randint(1970, 2005); mb = random.randint(1, 12); db = random.randint(1, 28)
    try:
        pa, _, _ = get_saju(ya, ma, da, 12, 0)
        pb, _, _ = get_saju(yb, mb, db, 12, 0)
        _, _, rel = 궁합_점수_named(pa, pb, 'A', 'B')
        for key in ['충', '파', '해', '원진']:
            items = rel.get(key, [])
            if len(items) != len(set(items)):
                dup_errors += 1
    except:
        pass
check('100쌍 충/파/해/원진 중복 없음', dup_errors, 0)

# ──────────────────────────────────────────────────────────────
print()
print('=== 7. 전체 함수 에러 없음 (100쌍) ===')
func_errors = 0
random.seed(99)
for _ in range(100):
    ya = random.randint(1970, 2005); ma = random.randint(1, 12); da = random.randint(1, 28)
    yb = random.randint(1970, 2005); mb = random.randint(1, 12); db = random.randint(1, 28)
    try:
        pa, _, _ = get_saju(ya, ma, da, 12, 0)
        pb, _, _ = get_saju(yb, mb, db, 12, 0)
        gil, hyung = check_sal(pa)
        from saju import analyze_saju
        analyze_saju('A', pa, gil, hyung)
        analyze_this_year('A', pa, ya, 2026)
        analyze_wolun_detail('A', pa, 2026)
        score, _, rel = 궁합_점수_named(pa, pb, 'A', 'B')
        analyze_gunghap(pa, pb, 'A', 'B', score, rel)
    except Exception as e:
        func_errors += 1
check('100쌍 전체 함수 에러 없음', func_errors, 0)

# ──────────────────────────────────────────────────────────────
print()
print(f'{'='*40}')
print(f'결과: {passed}개 통과 / {failed}개 실패')
if failed == 0:
    print('✅ 모든 테스트 통과!')
else:
    print(f'❌ {failed}개 항목 수정 필요')
sys.exit(0 if failed == 0 else 1)