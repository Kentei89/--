import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from saju import (
    get_saju, get_daewoon, get_sewoon, check_sal,
    analyze_saju, analyze_gunghap, 궁합_점수,
    check_relations, analyze_ohaeng, get_gongmang,
    get_12unsung, get_sipseong,
    CHEONGAN, JIJI, OHAENG_G, OHAENG_J, ANIMALS,
    JIJANGAN, OHAENG_IDX, OHAENG_IDX_J,
)

st.set_page_config(page_title="사주 & 궁합", page_icon="☯", layout="centered")
st.title("☯ 사주 & 궁합 분석")

def person_form(key):
    c1, c2 = st.columns(2)
    with c1:
        name   = st.text_input("이름", key=f"{key}_name")
        gender = st.radio("성별", ["남", "여"], horizontal=True, key=f"{key}_gender")
        year   = st.number_input("년도", 1900, 2025, 1990, key=f"{key}_year")
        month  = st.number_input("월", 1, 12, 1, key=f"{key}_month")
    with c2:
        day    = st.number_input("일", 1, 31, 1, key=f"{key}_day")
        hour   = st.number_input("시 (0~23)", 0, 23, 12, key=f"{key}_hour")
        minute = st.number_input("분 (0~59)", 0, 59, 0, key=f"{key}_minute")
    return name, gender, int(year), int(month), int(day), int(hour), int(minute)

def render_pillars(pillars):
    ilgan = pillars[2][0]
    gm    = get_gongmang(*pillars[2])
    order = [3, 2, 1, 0]
    hdrs  = ['시주(時)', '일주(日)', '월주(月)', '년주(年)']

    def ss_g(i):
        g = pillars[i][0]
        return '일간' if i == 2 else get_sipseong(ilgan, OHAENG_IDX[g], g % 2)

    rows = {
        '천간':    [CHEONGAN[pillars[i][0]] for i in order],
        '십성':    [ss_g(i) for i in order],
        '지지':    [JIJI[pillars[i][1]] + (' 공망' if pillars[i][1] in gm else '') for i in order],
        '지지십성': [get_sipseong(ilgan, OHAENG_IDX_J[pillars[i][1]], pillars[i][1] % 2) for i in order],
        '12운성':  [get_12unsung(ilgan, pillars[i][1]) for i in order],
        '지장간':  [' '.join(JIJANGAN[pillars[i][1]]) for i in order],
    }
    df = pd.DataFrame(rows, index=hdrs).T
    st.dataframe(df, use_container_width=True)

def render_saju(name, pillars, corr_dt, corrections, gender, year):
    gil, hyung = check_sal(pillars)
    is_male    = gender == '남'

    st.subheader(f"☯ {name} 사주팔자")
    st.caption(f"보정 시간: {corr_dt.strftime('%Y-%m-%d %H:%M')}  ({', '.join(corrections)})")

    render_pillars(pillars)

    yj = pillars[0][1]
    gm = get_gongmang(*pillars[2])
    oa = analyze_ohaeng(pillars)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**띠:** {JIJI[yj]}({ANIMALS[yj]})")
    with c2:
        if gm:
            st.write(f"**공망:** {' '.join(JIJI[x] for x in sorted(gm))}")
    with c3:
        st.write("**오행:** " + " ".join(f"{k}({v})" for k, v in oa.items()))

    if gil:   st.success(f"**길신:** {', '.join(gil)}")
    if hyung: st.warning(f"**흉살:** {', '.join(hyung)}")

    rel = check_relations([p[1] for p in pillars])
    rel_str = "  |  ".join(f"**{k}**: {', '.join(v)}" for k, v in rel.items() if v)
    if rel_str:
        st.write(rel_str)

    with st.expander("📖 사주 해설", expanded=True):
        st.text(analyze_saju(name, pillars, gil, hyung))

    with st.expander("🔮 대운 & 세운", expanded=False):
        start_age, forward, daeun = get_daewoon(pillars, corr_dt, is_male)
        sewoon = get_sewoon(year)
        render_daewoon(start_age, forward, daeun, sewoon)

def render_daewoon(start_age, forward, daeun, sewoon):
    cur = datetime.now().year

    st.markdown(f"**대운** ({'순행' if forward else '역행'}, {start_age}세 시작)")
    rows = []
    for age, yr, dg, dj in daeun:
        rows.append({
            '기간': f"{age}세({yr})~{age+9}세",
            '대운': f"{CHEONGAN[dg]}{JIJI[dj]}",
            '오행': f"{OHAENG_G[dg]}{OHAENG_J[dj]}",
            '현재': '◀' if yr <= cur < yr + 10 else '',
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("**세운 (현재 기준 10년)**")
    cur_dg, cur_dj = None, None
    for age, yr, dg, dj in daeun:
        if yr <= cur < yr + 10:
            cur_dg, cur_dj = dg, dj
            break
    dw_str = f"{CHEONGAN[cur_dg]}{JIJI[cur_dj]}" if cur_dg is not None else "─"

    sw_rows = []
    for y, age, yg, yj in sewoon:
        sw_rows.append({
            '연도': f"{y}년",
            '나이': f"{age}세",
            '세운': f"{CHEONGAN[yg]}{JIJI[yj]}",
            '대운': dw_str,
            '':    '◀ 올해' if y == cur else '',
        })
    st.dataframe(pd.DataFrame(sw_rows), use_container_width=True, hide_index=True)

mode = st.radio("분석 유형", ["🔮 사주 보기", "♥ 궁합 보기"], horizontal=True)
st.divider()

if mode == "🔮 사주 보기":
    with st.form("saju_form"):
        name, gender, year, month, day, hour, minute = person_form("s")
        submitted = st.form_submit_button("사주 분석하기", use_container_width=True, type="primary")

    if submitted:
        if not name.strip():
            st.error("이름을 입력해주세요.")
        else:
            with st.spinner("분석 중..."):
                try:
                    pillars, corr_dt, corrections = get_saju(year, month, day, hour, minute)
                    render_saju(name, pillars, corr_dt, corrections, gender, year)
                except Exception as e:
                    st.error(f"오류 발생: {e}")

elif mode == "♥ 궁합 보기":
    with st.form("gunghap_form"):
        st.write("**첫 번째 분**")
        na, ga, ya, ma, da, ha, mna = person_form("ga")
        st.divider()
        st.write("**두 번째 분**")
        nb, gb, yb, mb, db, hb, mnb = person_form("gb")
        submitted = st.form_submit_button("궁합 분석하기", use_container_width=True, type="primary")

    if submitted:
        if not na.strip() or not nb.strip():
            st.error("두 분의 이름을 모두 입력해주세요.")
        else:
            with st.spinner("분석 중..."):
                try:
                    pa, corr_a, corr_list_a = get_saju(ya, ma, da, ha, mna)
                    pb, corr_b, corr_list_b = get_saju(yb, mb, db, hb, mnb)

                    render_saju(na, pa, corr_a, corr_list_a, ga, ya)
                    st.divider()
                    render_saju(nb, pb, corr_b, corr_list_b, gb, yb)
                    st.divider()

                    score, reasons, rel = 궁합_점수(pa, pb)
                    st.subheader(f"♥ {na} × {nb} 궁합")

                    grades = ['▽ 어려움', '△ 주의', '○ 보통', '◎ 좋음', '★ 매우 좋음']
                    gi = min(4, score // 20)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("궁합 점수", f"{score}점")
                    with c2:
                        st.write(f"**등급:** {grades[gi]}")

                    for r in reasons:
                        st.write(f"• {r}")

                    with st.expander("📖 궁합 해설", expanded=True):
                        st.text(analyze_gunghap(pa, pb, na, nb, score, rel))

                except Exception as e:
                    st.error(f"오류 발생: {e}")
