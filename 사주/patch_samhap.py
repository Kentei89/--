#!/usr/bin/env python3
# patch_samhap.py — 삼합/방합 judge_strength 반영 + analyze_ohaeng 방합 추가

import sys, re

TARGET = r"g:\내 드라이브\코딩\사주\saju.py"

with open(TARGET, 'r', encoding='utf-8') as f:
    src = f.read()

# ── 1. BANGHAP_OH 상수 추가 (SAMHAP_OH 바로 뒤) ────────────────────────────
OLD_CONST = (
    "SAMHAP_OH = {\n"
    "    frozenset([2,6,10]):'화', frozenset([11,3,7]):'목',\n"
    "    frozenset([4,8,0]):'수',  frozenset([5,9,1]):'금',\n"
    "}"
)
NEW_CONST = (
    "SAMHAP_OH = {\n"
    "    frozenset([2,6,10]):'화', frozenset([11,3,7]):'목',\n"
    "    frozenset([4,8,0]):'수',  frozenset([5,9,1]):'금',\n"
    "}\n"
    "BANGHAP_OH = {\n"
    "    frozenset([2,3,4]):'목',  frozenset([5,6,7]):'화',\n"
    "    frozenset([8,9,10]):'금', frozenset([11,0,1]):'수',\n"
    "}"
)
if OLD_CONST not in src:
    sys.stdout.buffer.write(b'ERROR: SAMHAP_OH not found\n')
    sys.exit(1)
src = src.replace(OLD_CONST, NEW_CONST, 1)
sys.stdout.buffer.write(b'Step1: BANGHAP_OH added\n')

# ── 2. analyze_ohaeng 에 방합 처리 추가 ────────────────────────────────────
OLD_HAP = (
    "        # 육합 (삼합에 포함되지 않은 지지만)\n"
    "        for i in range(len(jijis)):\n"
    "            for k in range(i+1, len(jijis)):\n"
    "                fs = frozenset([jijis[i], jijis[k]])\n"
    "                if fs in YUKAHP_OH and i not in hap_oh and k not in hap_oh:\n"
    "                    hap_oh[i] = YUKAHP_OH[fs]\n"
    "                    hap_oh[k] = YUKAHP_OH[fs]"
)
NEW_HAP = (
    "        # 방합 (삼합에 포함되지 않은 지지만)\n"
    "        for fs, oh in BANGHAP_OH.items():\n"
    "            if fs.issubset(ji_set):\n"
    "                for idx, j in enumerate(jijis):\n"
    "                    if j in fs and idx not in hap_oh:\n"
    "                        hap_oh[idx] = oh\n"
    "        # 육합 (삼합/방합에 포함되지 않은 지지만)\n"
    "        for i in range(len(jijis)):\n"
    "            for k in range(i+1, len(jijis)):\n"
    "                fs = frozenset([jijis[i], jijis[k]])\n"
    "                if fs in YUKAHP_OH and i not in hap_oh and k not in hap_oh:\n"
    "                    hap_oh[i] = YUKAHP_OH[fs]\n"
    "                    hap_oh[k] = YUKAHP_OH[fs]"
)
if OLD_HAP not in src:
    sys.stdout.buffer.write(b'ERROR: analyze_ohaeng hap section not found\n')
    sys.exit(1)
src = src.replace(OLD_HAP, NEW_HAP, 1)
sys.stdout.buffer.write(b'Step2: analyze_ohaeng banghap added\n')

# ── 3. judge_strength 에 삼합/방합 보너스 추가 ────────────────────────────
OLD_JUDGE = (
    "    total = sup + opp\n"
    "    if total == 0: return '중화(中和)'\n"
    "    ratio = sup / total\n"
    "    if ratio >= 0.58:   return '신강(身强)'\n"
    "    elif ratio <= 0.42: return '신약(身弱)'\n"
    "    else:               return '중화(中和)'"
)
NEW_JUDGE = (
    "    # 삼합/방합 보너스 — 지지 3개가 모여 오행이 강해지는 효과\n"
    "    jijis = [p[1] for p in pillars]\n"
    "    ji_set = set(jijis)\n"
    "    _OH_IDX = {'목':0,'화':1,'토':2,'금':3,'수':4}\n"
    "    _SENG = [1, 2, 3, 4, 0]   # i가 생하는 오행 인덱스\n"
    "    il_oh = OHAENG_IDX[ilgan]\n"
    "    def _side(oh_name):\n"
    "        r = _OH_IDX[oh_name]\n"
    "        if r == il_oh: return 'sup'          # 비겁\n"
    "        if _SENG[r] == il_oh: return 'sup'   # 인성\n"
    "        return 'opp'                          # 식상/재/관\n"
    "    for fs, oh in SAMHAP_OH.items():\n"
    "        if fs.issubset(ji_set):\n"
    "            if _side(oh) == 'sup': sup += 1.5\n"
    "            else: opp += 1.5\n"
    "    for fs, oh in BANGHAP_OH.items():\n"
    "        if fs.issubset(ji_set):\n"
    "            if _side(oh) == 'sup': sup += 1.0\n"
    "            else: opp += 1.0\n"
    "    total = sup + opp\n"
    "    if total == 0: return '중화(中和)'\n"
    "    ratio = sup / total\n"
    "    if ratio >= 0.58:   return '신강(身强)'\n"
    "    elif ratio <= 0.42: return '신약(身弱)'\n"
    "    else:               return '중화(中和)'"
)
if OLD_JUDGE not in src:
    sys.stdout.buffer.write(b'ERROR: judge_strength end not found\n')
    sys.exit(1)
src = src.replace(OLD_JUDGE, NEW_JUDGE, 1)
sys.stdout.buffer.write(b'Step3: judge_strength samhap/banghap bonus added\n')

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(src)
sys.stdout.buffer.write(b'done\n')