#!/usr/bin/env python3
# patch_daewoon_sewoon.py — 대운×세운 조합 분석 추가

import sys

APP = r"g:\내 드라이브\코딩\사주\saju_app.py"

with open(APP, 'r', encoding='utf-8') as f:
    src = f.read()

# ── 1. 헬퍼 함수 삽입 (_render_thisyear_section 바로 앞) ─────────────────
HELPER = '''
def _daeun_sewoon_combo(pillars, daeun, target_year):
    """대운 x 세운 조합 분석 텍스트 반환"""
    from saju import get_sewoon, _year_pillar
    ilgan = pillars[2][0]
    ya_oh, ya_name, _, _, _ = get_yongshin(pillars)
    _, _, ki_list = get_gyeokguk(pillars)
    ki_names = [OHAENG_NAMES[k] for k in ki_list]

    # 해당 연도의 대운 찾기
    cur_dae = None
    for age, yr, dg, dj in daeun:
        if yr <= target_year < yr + 10:
            cur_dae = (age, yr, dg, dj)
            break
    if cur_dae is None:
        return ''

    age, yr, dg, dj = cur_dae
    dg_oh = OHAENG_NAMES[OHAENG_IDX[dg]]
    dj_oh = OHAENG_NAMES[OHAENG_IDX_J[dj]]
    dg_ss = get_sipseong(ilgan, OHAENG_IDX[dg], dg % 2)
    dj_ss = get_sipseong(ilgan, OHAENG_IDX_J[dj], dj % 2)

    dae_is_yong = (dg_oh == ya_name or dj_oh == ya_name)
    dae_is_ki   = (dg_oh in ki_names or dj_oh in ki_names)

    # 세운 오행
    yg, yj = _year_pillar(target_year)
    yg_oh = OHAENG_NAMES[OHAENG_IDX[yg]]
    yj_oh = OHAENG_NAMES[OHAENG_IDX_J[yj]]
    sew_is_yong = (yg_oh == ya_name or yj_oh == ya_name)
    sew_is_ki   = (yg_oh in ki_names or yj_oh in ki_names)

    # 대운 지지 × 세운 지지 충 여부
    dj_sew_chung = any(frozenset([dj, yj]) == c for c in JIJI_CHUNG)
    dj_sew_hap   = frozenset([dj, yj]) in YUKAHP

    # 조합 메시지
    _combo_map = {
        (True,  False, True,  False): ('최길', '대운·세운 모두 용신이에요. 인생에서 손꼽히는 전성기예요. 크게 움직여도 좋은 해예요.'),
        (True,  False, False, True ): ('주의', '좋은 대운이 기신 세운을 상당 부분 막아줘요. 신중하게 움직이면 피해를 크게 줄일 수 있어요.'),
        (False, True,  True,  False): ('반전', '기신 대운이지만 세운이 용신이에요. 올해만큼은 숨통이 트이고 움직일 기회가 찾아와요.'),
        (False, True,  False, True ): ('수비', '대운·세운 모두 기신이에요. 올해는 안정 유지와 수비 전략이 최선이에요. 큰 도전은 내년 이후로.'),
        (True,  False, False, False): ('안정', '용신 대운이 탄탄하게 받쳐줘요. 세운이 중립이니 무리 없이 안정적으로 전진하는 해예요.'),
        (False, True,  False, False): ('완충', '기신 대운 속에서 세운이 중립이에요. 크게 나쁘지는 않지만 무리한 확장은 피하는 게 좋아요.'),
        (False, False, True,  False): ('순풍', '세운 용신이 이 해를 이끌어줘요. 대운이 중립이니 세운의 흐름에 맞게 적극 움직이세요.'),
        (False, False, False, True ): ('경계', '세운 기신에 주의가 필요한 해예요. 대운이 중립이라 버텨낼 수 있지만 중요 결정은 신중하게.'),
        (False, False, False, False): ('평온', '대운·세운 모두 중립이에요. 급격한 변화 없이 꾸준히 쌓아가기 좋은 해예요.'),
    }
    key = (dae_is_yong, dae_is_ki, sew_is_yong, sew_is_ki)
    label, msg = _combo_map.get(key, ('', ''))

    # 충/합 보조 설명
    extra = ''
    if dj_sew_chung:
        extra = f'  \\n> ⚡ 대운 지지({JIJI[dj]})와 세운 지지({JIJI[yj]})가 **충(冲)**이에요. 이사·직장 변동·관계 변화가 생길 수 있어요.'
    elif dj_sew_hap:
        extra = f'  \\n> 🤝 대운 지지({JIJI[dj]})와 세운 지지({JIJI[yj]})가 **합(合)**이에요. 안정적으로 흘러가는 흐름이에요.'

    # 십성 증폭 (대운 × 세운 같은 십성)
    amplify = ''
    if dg_ss == get_sipseong(ilgan, OHAENG_IDX[yg], yg % 2):
        amplify = f' **{dg_ss}** 에너지가 대운·세운 양쪽에서 겹쳐 이 해에 특히 강하게 작용해요.'

    if not label:
        return ''

    lines = [
        '---',
        f'🌊 **대운 맥락** — {CHEONGAN[dg]}{JIJI[dj]} 대운({age}세~) × {target_year}년 세운',
        '',
        f'**[ {label} ]** {msg}{amplify}',
    ]
    if extra:
        lines.append(extra)
    lines.append('')
    return '\\n'.join(lines)

'''

ANCHOR = 'def _render_thisyear_section('
if ANCHOR not in src:
    sys.stdout.buffer.write(b'ERROR: anchor not found\\n')
    sys.exit(1)

src = src.replace(ANCHOR, HELPER + ANCHOR, 1)
sys.stdout.buffer.write(b'Step1: helper inserted\\n')

# ── 2. _render_thisyear_section 시그니처에 daeun 파라미터 추가 ──────────────
OLD_SIG = 'def _render_thisyear_section(name, pillars, birth_year, card_id="main", rel_status=\'솔로\'):'
NEW_SIG = 'def _render_thisyear_section(name, pillars, birth_year, card_id="main", rel_status=\'솔로\', daeun=None):'

if OLD_SIG not in src:
    sys.stdout.buffer.write(b'ERROR: sig not found\\n')
    sys.exit(1)
src = src.replace(OLD_SIG, NEW_SIG, 1)
sys.stdout.buffer.write(b'Step2: sig updated\\n')

# ── 3. 함수 내부에 대운 맥락 렌더링 추가 (result_text 출력 바로 앞) ─────────
OLD_RENDER = '    result_text = analyze_this_year(name, pillars, birth_year, sel_year, rel_status)\n    st.markdown(result_text)'
NEW_RENDER = (
    '    result_text = analyze_this_year(name, pillars, birth_year, sel_year, rel_status)\n'
    '    if daeun:\n'
    '        _combo = _daeun_sewoon_combo(pillars, daeun, sel_year)\n'
    '        if _combo:\n'
    '            st.markdown(_combo)\n'
    '    st.markdown(result_text)'
)

if OLD_RENDER not in src:
    sys.stdout.buffer.write(b'ERROR: render anchor not found\\n')
    sys.exit(1)
src = src.replace(OLD_RENDER, NEW_RENDER, 1)
sys.stdout.buffer.write(b'Step3: render updated\\n')

# ── 4. 호출부에 daeun 전달 ───────────────────────────────────────────────
OLD_CALL = '_render_thisyear_section(name, pillars, year, card_id=card_id, rel_status=rel_status)'
NEW_CALL = '_render_thisyear_section(name, pillars, year, card_id=card_id, rel_status=rel_status, daeun=daeun)'

if OLD_CALL not in src:
    sys.stdout.buffer.write(b'ERROR: call site not found\\n')
    sys.exit(1)
src = src.replace(OLD_CALL, NEW_CALL, 1)
sys.stdout.buffer.write(b'Step4: call site updated\\n')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
sys.stdout.buffer.write(b'done\\n')