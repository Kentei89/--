import streamlit as st
import pandas as pd
import calendar as _cal_mod
from datetime import datetime, timedelta, timezone
_KST = timezone(timedelta(hours=9))
import sys, os, json
from korean_lunar_calendar import KoreanLunarCalendar
import firebase_admin
from firebase_admin import credentials, firestore as _fs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from saju import (
    get_saju, get_daewoon, get_sewoon, get_wolun, check_sal,
    analyze_saju, analyze_daewoon_narrative, analyze_sewoon_narrative,
    analyze_this_year, analyze_wolun_detail,
    재회운_분석,
    _score_gunghap_typed, _analyze_gunghap_typed,
    analyze_ohaeng, get_gongmang,
    get_12unsung, get_sipseong,
    CHEONGAN, JIJI, OHAENG_G, OHAENG_J, ANIMALS,
    JIJANGAN, OHAENG_IDX, OHAENG_IDX_J,
    _SAL_DESC, _SAL_MODERN, _SEWOON_SS_DESC, _sewoon_ss,
    OHAENG_NAMES,
    get_ilchin, get_yongki, analyze_ilchin_basic, analyze_ilchin_day, explain_yongshin,
    analyze_romantic_type, judge_strength,
    YUKAHP, CHUNG as JIJI_CHUNG,
)

_JIJI_EMOJI = ['🐀','🐄','🐅','🐇','🐉','🐍','🐎','🐑','🐒','🐓','🐕','🐗']

REL_OPTIONS = {
    '연인':         '인연',
    '썸':           '썸',
    '전 연인':      '전연인',
    '친구':         '친구',
    '형제·자매':    '형제자매',
    '직장 동료':    '직장_동료',
    '직장 동업자':  '직장_동업',
    '직장 상사':    '직장_상사',
    '직장 부하':    '직장_부하',
    '부모':         '부모',
    '자식':         '자식',
}
GRADE_LABELS = {
    '인연':      ['▽ 어려움','△ 주의','○ 보통','◎ 좋음','★ 매우 좋음'],
    '썸':        ['▽ 끌림약함','△ 설렘부족','○ 호감','◎ 강한 끌림','★ 운명적 설렘'],
    '전연인':    ['❌ 재회비권장','⚠ 신중','⚠ 조건부','✅ 권장','✅ 강력권장'],
    '친구':      ['▽ 안맞음','△ 주의','○ 보통','◎ 좋음','★ 베프'],
    '형제자매':  ['▽ 에너지충돌','△ 주의','○ 보통','◎ 좋음','★ 최상'],
    '직장_동료': ['▽ 불화','△ 주의','○ 보통','◎ 좋음','★ 최고동료'],
    '직장_동업': ['▽ 동업위험','△ 주의','○ 보통','◎ 좋음','★ 최고파트너'],
    '직장_상사': ['▽ 갈등','△ 주의','○ 보통','◎ 좋음','★ 최상의상사'],
    '직장_부하': ['▽ 어려운부하','△ 주의','○ 보통','◎ 좋음','★ 최상의부하'],
    '부모':      ['▽ 에너지충돌','△ 주의','○ 보통','◎ 좋음','★ 최상'],
    '자식':      ['▽ 에너지충돌','△ 주의','○ 보통','◎ 좋음','★ 최상'],
}

st.set_page_config(
    page_title="사주 분석",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700&display=swap');

    /* ── 폰트 & 배경 ────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    }
    .stApp {
        background: linear-gradient(160deg, #f0ecff 0%, #faf8ff 50%, #eef2ff 100%);
        min-height: 100vh;
    }
    .main { background: transparent; }
    .main .block-container {
        max-width: 860px !important;
        padding-top: 1.5rem !important;
    }

    /* ── 텍스트 ─────────────────────────────────────────────── */
    p, li, .stMarkdown { color: #2d2250; line-height: 1.85; }
    h2, h3, h4, h5, h6 { color: #3d2a7a !important; }
    strong { color: #2d1f60; }

    /* ── 제목 ───────────────────────────────────────────────── */
    h1 {
        text-align: center;
        font-size: 2.2rem !important;
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        padding-bottom: 0.2rem;
        letter-spacing: -0.5px;
        filter: drop-shadow(0 2px 8px rgba(124,58,237,0.2));
    }

    /* ── 탭 ─────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        justify-content: center;
        border-bottom: 2px solid #e8e0f8;
        padding-bottom: 0;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem; font-weight: 600;
        padding: 9px 22px;
        border-radius: 10px 10px 0 0;
        background: #f0eaff;
        border: 1px solid #ddd4f8; border-bottom: none;
        color: #7c5cb8;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6d28d9, #8b5cf6) !important;
        color: #fff !important;
        border-color: #a78bfa !important;
        box-shadow: 0 -2px 12px rgba(109,40,217,0.2);
    }
    .stTabs [data-baseweb="tab-panel"] { background: transparent; }

    /* ── 버튼 ───────────────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6d28d9, #8b5cf6);
        color: #fff; border: none;
        border-radius: 10px; font-size: 1rem;
        font-weight: 700; padding: 12px 0;
        box-shadow: 0 3px 14px rgba(109,40,217,0.3);
        transition: all 0.2s;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #5b21b6, #7c3aed);
        box-shadow: 0 5px 20px rgba(109,40,217,0.45);
        transform: translateY(-1px);
    }
    .stButton > button:not([kind="primary"]) {
        background: #f5f0ff !important;
        border: 1px solid #d4c4f8 !important;
        color: #6d28d9 !important;
        border-radius: 8px !important;
    }

    /* ── 점수 카드 ──────────────────────────────────────────── */
    .score-card {
        background: linear-gradient(135deg, #6d28d9, #8b5cf6);
        color: white; border-radius: 14px;
        padding: 20px 24px; text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 20px rgba(109,40,217,0.25);
    }
    .score-card .score-num { font-size: 2.8rem; font-weight: 800; line-height: 1; color: #fff; }
    .score-card .score-label { font-size: 0.95rem; opacity: 0.9; margin-top: 5px; color: #ede9fe; }

    /* ── 섹션 헤더 ──────────────────────────────────────────── */
    .sec-header {
        font-size: 1.05rem; font-weight: 700;
        color: #5b21b6; padding: 7px 0 4px 0;
        border-bottom: 2px solid #ede9fe; margin-bottom: 10px;
        letter-spacing: -0.3px;
    }

    /* ── 태그 뱃지 ──────────────────────────────────────────── */
    .badge-green  { background:#d1fae5; color:#065f46; border:1px solid #6ee7b7; padding:4px 12px; border-radius:20px; font-size:0.82rem; margin:2px; display:inline-block; font-weight:600; }
    .badge-orange { background:#fef3c7; color:#92400e; border:1px solid #fcd34d; padding:4px 12px; border-radius:20px; font-size:0.82rem; margin:2px; display:inline-block; font-weight:600; }

    /* ── 구분선 ─────────────────────────────────────────────── */
    hr { border: none; border-top: 1px solid #e8e0f8; margin: 20px 0; }

    /* ── 익스팬더 ───────────────────────────────────────────── */
    .streamlit-expanderHeader {
        font-weight: 600 !important; font-size: 0.97rem !important;
        color: #4c1d95 !important;
        background: #f5f0ff !important;
        border: 1px solid #ddd4f8 !important;
        border-radius: 8px !important; padding: 10px 14px !important;
    }
    .streamlit-expanderContent {
        border: 1px solid #e8e0f8 !important; border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 14px !important; background: #fff !important;
    }

    /* ── caption ───────────────────────────────────────────── */
    .stCaption, .stCaption p { color: #8b77b8 !important; font-size: 0.82rem !important; }

    /* ── 데이터프레임 ───────────────────────────────────────── */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
    [data-testid="stDataFrame"] th { background: #ede9fe !important; color: #4c1d95 !important; }

    /* ── 사이드바 ───────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #f5f0ff !important;
        border-right: 1px solid #ddd4f8;
    }

    /* ── 알림 ───────────────────────────────────────────────── */
    .stAlert { border-radius: 8px !important; }

    /* ── 모바일 ─────────────────────────────────────────────── */
    @media (max-width: 640px) {
        .main .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; max-width: 100% !important; }
        h1 { font-size: 1.4rem !important; }
        .stTabs [data-baseweb="tab"] { font-size: 0.72rem !important; padding: 7px 9px !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 3px !important; }
        .score-card { padding: 12px 14px !important; }
        .score-card .score-num { font-size: 2rem !important; }
        .sec-header { font-size: 0.92rem !important; }
        .stButton > button[kind="primary"] { font-size: 0.88rem !important; padding: 10px 0 !important; }
        .badge-green, .badge-orange { font-size: 0.75rem !important; padding: 3px 8px !important; }
        p, li, .stMarkdown { line-height: 1.7 !important; font-size: 0.93rem !important; }
    }
</style>
""", unsafe_allow_html=True)


def _narr(text: str):
    import re
    lines = [l.strip() for l in text.split('\n')]
    chunks: list[str] = []
    body_buf: list[str] = []

    def flush():
        if body_buf:
            chunks.append('  \n'.join(body_buf))
            body_buf.clear()

    for line in lines:
        if not line:
            flush(); continue
        # 터미널 구분선 (─ ━ = 등 5자 이상) → 건너뜀
        if re.match(r'^[─━═─]{5,}$', line):
            flush(); continue
        # 마크다운 수평선 --- → 그대로
        if line == '---':
            flush(); chunks.append('---'); continue
        # 마크다운 헤딩 ## ### ... → 그대로
        if re.match(r'^#{1,6} ', line):
            flush(); chunks.append(line); continue
        # 마크다운 인용구 > → 그대로
        if line.startswith('> '):
            flush(); chunks.append(line); continue
        # ◈ 메인 제목
        if line.startswith('◈ '):
            flush(); chunks.append(f'### {line[2:]}'); continue
        # ◆ 섹션
        if line.startswith('◆ '):
            flush(); chunks.append(f'---\n#### {line[2:]}'); continue
        # ▶ 서브섹션
        if line.startswith('▶ '):
            flush(); chunks.append(f'**▶ {line[2:]}**'); continue
        # ★ 강조
        if line.startswith('★ '):
            flush(); chunks.append(f'**★ {line[2:]}**'); continue
        # ⚠ ❌ ✅ 판정
        if line[:1] in ('⚠', '❌', '✅'):
            flush(); chunks.append(f'> {line}'); continue
        # → ※ 메모
        if line.startswith('→ ') or line.startswith('※ '):
            flush(); chunks.append(f'> {line}'); continue
        # • 불릿
        if line.startswith('• '):
            body_buf.append(f'- {line[2:]}'); continue
        # [이름] 레이블
        if re.match(r'^\[.+?\]$', line):
            flush(); chunks.append(f'**{line}**'); continue
        body_buf.append(line)

    flush()
    st.markdown('\n\n'.join(chunks))


def _parse_time(raw: str):
    """'1745', '17:45', '17 45' 등을 (hour, minute)으로 파싱. 실패 시 None."""
    s = raw.strip().replace(":", "").replace(" ", "")
    if not s.isdigit():
        return None
    if len(s) <= 2:
        h, m = int(s), 0
    elif len(s) == 3:
        h, m = int(s[0]), int(s[1:])
    else:
        h, m = int(s[:-2]), int(s[-2:])
    if 0 <= h <= 23 and 0 <= m <= 59:
        return h, m
    return None


# ── Firebase 초기화 ──────────────────────────────────────────
_PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")
_FB_KEY_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "saju-9300e-firebase-adminsdk-fbsvc-8d97bee29f.json")

@st.cache_resource
def _get_db():
    if not firebase_admin._apps:
        try:
            s = st.secrets["firebase"]
            info = {
                "type":             s["type"],
                "project_id":       s["project_id"],
                "private_key_id":   s["private_key_id"],
                "private_key":      s["private_key"].replace("\\n", "\n"),
                "client_email":     s["client_email"],
                "client_id":        s["client_id"],
                "auth_uri":         "https://accounts.google.com/o/oauth2/auth",
                "token_uri":        "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(info)
        except Exception:
            cred = credentials.Certificate(_FB_KEY_FILE)
        firebase_admin.initialize_app(cred)
    return _fs.client()

def _load_profiles() -> dict:
    try:
        doc = _get_db().collection("saju").document("profiles").get()
        if doc.exists:
            return doc.to_dict().get("data", {})
    except Exception:
        pass
    if os.path.exists(_PROFILES_FILE):
        try:
            with open(_PROFILES_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_profiles(profiles: dict):
    try:
        _get_db().collection("saju").document("profiles").set({"data": profiles})
    except Exception:
        pass
    try:
        with open(_PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _profile_bar(key: str):
    """프로필 바 — 이름 칩 원클릭 로드"""
    if '_profiles_cache' not in st.session_state:
        st.session_state['_profiles_cache'] = _load_profiles()
    profiles = st.session_state['_profiles_cache']
    names = list(profiles.keys())

    def _load_profile(pname):
        p = profiles.get(pname)
        if not p:
            return
        st.session_state[f"{key}_name"]     = p.get("name", "")
        st.session_state[f"{key}_gender"]   = p.get("gender", "남")
        st.session_state[f"{key}_caltype"]  = p.get("caltype", "양력")
        st.session_state[f"{key}_year"]     = p.get("year", 1990)
        st.session_state[f"{key}_month"]    = p.get("month", 1)
        st.session_state[f"{key}_day"]      = p.get("day", 1)
        st.session_state[f"{key}_notime"]   = p.get("no_time", False)
        st.session_state[f"{key}_time_raw"] = p.get("time_raw", "")
        st.session_state[f"{key}_city"]      = p.get("city", "서울특별시")
        st.session_state[f"{key}_isleap"]   = p.get("is_leap", False)
        st.session_state[f"{key}_relstatus"]= p.get("rel_status", "솔로")

    def _save():
        pname = str(st.session_state.get(f"{key}_name", "")).strip()
        if not pname:
            return
        profiles[pname] = {
            "name":     pname,
            "gender":   st.session_state.get(f"{key}_gender", "남"),
            "caltype":  st.session_state.get(f"{key}_caltype", "양력"),
            "year":     int(st.session_state.get(f"{key}_year", 1990)),
            "month":    int(st.session_state.get(f"{key}_month", 1)),
            "day":      int(st.session_state.get(f"{key}_day", 1)),
            "no_time":  st.session_state.get(f"{key}_notime", False),
            "time_raw": st.session_state.get(f"{key}_time_raw", ""),
            "city":       st.session_state.get(f"{key}_city", "서울특별시"),
            "is_leap":    st.session_state.get(f"{key}_isleap", False),
            "rel_status": st.session_state.get(f"{key}_relstatus", "솔로"),
        }
        _save_profiles(profiles)

    def _delete():
        sel = st.session_state.get(f"{key}_active_profile", "")
        if sel and sel in profiles:
            del profiles[sel]
            _save_profiles(profiles)
            st.session_state.pop(f"{key}_active_profile", None)

    if names:
        st.markdown(
            '<div style="font-size:0.78rem;color:#7c5cb8;margin-bottom:4px;font-weight:600;">저장된 프로필</div>',
            unsafe_allow_html=True,
        )
        chip_cols = st.columns(min(len(names), 4) + 1)
        for idx, pname in enumerate(names[:4]):
            with chip_cols[idx]:
                if st.button(f"👤 {pname}", key=f"{key}_chip_{pname}",
                             use_container_width=True):
                    _load_profile(pname)
                    st.session_state[f"{key}_active_profile"] = pname
                    st.rerun()
        with chip_cols[min(len(names), 4)]:
            st.button("💾 저장", key=f"{key}_prof_save", on_click=_save,
                      use_container_width=True)
    else:
        st.markdown(
            '<div style="font-size:0.78rem;color:#9d7cc8;margin-bottom:6px;">'
            '💡 분석 후 이름 옆 저장 버튼으로 프로필을 저장할 수 있어요.</div>',
            unsafe_allow_html=True,
        )
        st.button("💾 저장", key=f"{key}_prof_save", on_click=_save)

    active = st.session_state.get(f"{key}_active_profile", "")
    if active and active in profiles:
        st.caption(f"현재: {active}  |  삭제하려면 아래 버튼을 누르세요.")
        st.button("🗑 삭제", key=f"{key}_prof_del", on_click=_delete)


def _profile_transfer_panel():
    """사이드바: 프로필 전체 내보내기/가져오기 (기기 간 이동용)"""
    with st.sidebar:
        st.markdown("### 📱 프로필 기기 이동")
        st.caption("다른 기기(아이폰 등)에서 프로필을 쓰려면 아래에서 복사 → 붙여넣기")

        profiles = st.session_state.get('_profiles_cache', _load_profiles())

        # 내보내기
        if profiles:
            export_str = json.dumps(profiles, ensure_ascii=False, indent=2)
            st.text_area("📤 내보내기 (전체 복사)", value=export_str,
                         height=160, key="prof_export_area")
        else:
            st.info("저장된 프로필이 없어요.")

        st.divider()

        # 가져오기
        import_str = st.text_area("📥 가져오기 (붙여넣기 후 버튼 클릭)",
                                   placeholder='{"홍길동": {...}, ...}',
                                   height=120, key="prof_import_area")
        if st.button("✅ 가져오기 적용", use_container_width=True):
            try:
                imported = json.loads(import_str)
                if isinstance(imported, dict) and imported:
                    existing = st.session_state.get('_profiles_cache', {})
                    existing.update(imported)
                    st.session_state['_profiles_cache'] = existing
                    _save_profiles(existing)
                    st.success(f"{len(imported)}개 프로필을 가져왔어요!")
                    st.rerun()
                else:
                    st.error("올바른 프로필 형식이 아니에요.")
            except Exception:
                st.error("JSON 형식이 잘못됐어요. 다시 확인해주세요.")

        st.divider()
        st.caption("v2026.06.05.6")


# 지방시(地方時) 보정 – offset_minutes = round((경도 - 135) × 4)
_CITY_OFFSETS: dict[str, int] = {
    "선택 안함 (보정 없음)": 0,
    # ── 특별시 · 광역시 · 세종 ──────────────────────────
    "서울특별시":           -32,
    "부산광역시":           -24,
    "인천광역시":           -33,
    "대구광역시":           -26,
    "대전광역시":           -30,
    "광주광역시":           -33,
    "울산광역시":           -23,
    "세종특별자치시":       -31,
    # ── 경기도 ─────────────────────────────────────────
    "경기 수원":            -32,
    "경기 성남":            -31,
    "경기 고양":            -33,
    "경기 용인":            -31,
    "경기 부천":            -33,
    "경기 안산":            -33,
    "경기 안양":            -32,
    "경기 남양주":          -30,
    "경기 화성":            -33,
    "경기 평택":            -32,
    "경기 의정부":          -32,
    "경기 시흥":            -33,
    "경기 파주":            -33,
    "경기 김포":            -33,
    "경기 광명":            -33,
    "경기 광주":            -31,
    "경기 군포":            -32,
    "경기 하남":            -31,
    "경기 오산":            -32,
    "경기 이천":            -30,
    "경기 안성":            -31,
    "경기 의왕":            -32,
    "경기 양주":            -32,
    "경기 구리":            -31,
    "경기 포천":            -31,
    "경기 여주":            -29,
    "경기 동두천":          -32,
    "경기 가평":            -30,
    "경기 과천":            -32,
    "경기 연천":            -32,
    "경기 양평":            -30,
    # ── 강원도 ─────────────────────────────────────────
    "강원 춘천":            -29,
    "강원 원주":            -28,
    "강원 강릉":            -24,
    "강원 속초":            -26,
    "강원 삼척":            -23,
    "강원 동해":            -24,
    "강원 태백":            -24,
    "강원 홍천":            -28,
    "강원 횡성":            -28,
    "강원 영월":            -26,
    "강원 평창":            -26,
    "강원 정선":            -25,
    "강원 철원":            -31,
    "강원 화천":            -29,
    "강원 양구":            -28,
    "강원 인제":            -27,
    "강원 고성":            -26,
    "강원 양양":            -25,
    # ── 충청북도 ───────────────────────────────────────
    "충북 청주":            -30,
    "충북 충주":            -28,
    "충북 제천":            -27,
    "충북 보은":            -29,
    "충북 옥천":            -30,
    "충북 영동":            -29,
    "충북 증평":            -30,
    "충북 진천":            -30,
    "충북 괴산":            -29,
    "충북 음성":            -29,
    "충북 단양":            -26,
    # ── 충청남도 ───────────────────────────────────────
    "충남 천안":            -31,
    "충남 공주":            -32,
    "충남 보령":            -34,
    "충남 아산":            -32,
    "충남 서산":            -34,
    "충남 논산":            -32,
    "충남 계룡":            -31,
    "충남 당진":            -33,
    "충남 금산":            -30,
    "충남 부여":            -32,
    "충남 서천":            -33,
    "충남 청양":            -33,
    "충남 홍성":            -33,
    "충남 예산":            -33,
    "충남 태안":            -35,
    # ── 전라북도 ───────────────────────────────────────
    "전북 전주":            -31,
    "전북 군산":            -33,
    "전북 익산":            -32,
    "전북 정읍":            -33,
    "전북 남원":            -30,
    "전북 김제":            -33,
    "전북 완주":            -31,
    "전북 진안":            -30,
    "전북 무주":            -29,
    "전북 장수":            -30,
    "전북 임실":            -31,
    "전북 순창":            -31,
    "전북 고창":            -33,
    "전북 부안":            -33,
    # ── 전라남도 ───────────────────────────────────────
    "전남 목포":            -34,
    "전남 여수":            -29,
    "전남 순천":            -30,
    "전남 나주":            -33,
    "전남 광양":            -29,
    "전남 담양":            -32,
    "전남 곡성":            -31,
    "전남 구례":            -30,
    "전남 고흥":            -31,
    "전남 보성":            -32,
    "전남 화순":            -32,
    "전남 장흥":            -32,
    "전남 강진":            -33,
    "전남 해남":            -34,
    "전남 영암":            -33,
    "전남 무안":            -34,
    "전남 함평":            -34,
    "전남 영광":            -34,
    "전남 장성":            -33,
    "전남 완도":            -33,
    "전남 진도":            -35,
    "전남 신안":            -36,
    # ── 경상북도 ───────────────────────────────────────
    "경북 포항":            -22,
    "경북 경주":            -23,
    "경북 김천":            -28,
    "경북 안동":            -25,
    "경북 구미":            -26,
    "경북 영주":            -26,
    "경북 영천":            -24,
    "경북 상주":            -28,
    "경북 문경":            -27,
    "경북 경산":            -25,
    "경북 군위":            -26,
    "경북 의성":            -25,
    "경북 청송":            -24,
    "경북 영양":            -24,
    "경북 영덕":            -22,
    "경북 청도":            -25,
    "경북 고령":            -27,
    "경북 성주":            -27,
    "경북 칠곡":            -26,
    "경북 예천":            -26,
    "경북 봉화":            -25,
    "경북 울진":            -22,
    "경북 울릉도":          -17,
    # ── 경상남도 ───────────────────────────────────────
    "경남 창원":            -25,
    "경남 진주":            -28,
    "경남 통영":            -26,
    "경남 사천":            -28,
    "경남 김해":            -24,
    "경남 밀양":            -25,
    "경남 거제":            -25,
    "경남 양산":            -24,
    "경남 의령":            -27,
    "경남 함안":            -26,
    "경남 창녕":            -26,
    "경남 고성":            -27,
    "경남 남해":            -28,
    "경남 하동":            -29,
    "경남 산청":            -29,
    "경남 함양":            -29,
    "경남 거창":            -28,
    "경남 합천":            -27,
    # ── 제주 ───────────────────────────────────────────
    "제주 제주시":          -34,
    "제주 서귀포":          -34,
}


def _lunar_to_solar(year: int, month: int, day: int, is_leap: bool):
    """음력 → 양력 변환. 실패 시 None 반환."""
    try:
        cal = KoreanLunarCalendar()
        cal.setLunarDate(year, month, day, is_leap)
        s = cal.SolarIsoFormat()          # 'YYYY-MM-DD'
        y, m, d = map(int, s.split('-'))
        return y, m, d
    except Exception:
        return None


def person_form(key: str, title: str = ""):
    if title:
        st.markdown(f'<div class="sec-header">{title}</div>', unsafe_allow_html=True)
    # 2컬럼 레이아웃 — 모바일에서도 읽기 좋음
    c1, c2 = st.columns(2)
    with c1:
        name     = st.text_input("이름", key=f"{key}_name", placeholder="홍길동")
        gender   = st.radio("성별", ["남", "여"], horizontal=True, key=f"{key}_gender")
        st.radio("연애 상태", ["솔로", "연애중", "기혼·동거"], horizontal=True, key=f"{key}_relstatus")
        cal_type = st.radio("달력", ["양력", "음력"], horizontal=True, key=f"{key}_caltype")
        is_leap  = st.checkbox("윤달", key=f"{key}_isleap",
                               disabled=(cal_type == "양력"),
                               help="음력 윤달 출생자만 체크")
    with c2:
        year     = st.number_input("태어난 년도", 1900, 2025, 1990, key=f"{key}_year")
        month    = st.number_input("월", 1, 12, 1, key=f"{key}_month")
        day      = st.number_input("일", 1, 31, 1, key=f"{key}_day")
        no_time  = st.checkbox("시간 모름", key=f"{key}_notime")
        time_raw = st.text_input(
            "태어난 시간 (예: 1745)", disabled=no_time,
            placeholder="1745 또는 17:45", key=f"{key}_time_raw",
            help="입력 시간은 서울 기준 태양시(평균태양시)로 자동 보정됩니다 (표준시 대비 약 ±32분 오차 발생 가능)"
        )

    _city_keys = list(_CITY_OFFSETS.keys())
    st.selectbox(
        "태어난 지역 (지방시 보정)",
        _city_keys,
        index=_city_keys.index("서울특별시"),
        key=f"{key}_city",
        help="경도 차이로 생기는 표준시와 실제 태양시의 오차를 보정합니다 (최대 ±36분)",
    )

    if no_time:
        hour, minute = 12, 0
    else:
        parsed = _parse_time(time_raw) if time_raw.strip() else None
        if time_raw.strip() and parsed is None:
            st.warning(f"시간 형식이 올바르지 않아요. 예: 1745  →  17시 45분")
        hour, minute = parsed if parsed else (12, 0)

    return name, gender, int(year), int(month), int(day), hour, minute


def _resolve_date(key: str):
    """session_state에서 날짜·시간 읽고, 음력이면 양력 변환.
    반환: (solar_y, solar_m, solar_d, h, mn, no_time, cal_label, city_offset_min)
    city_offset_min은 get_saju()에 직접 전달해 apply_correction()이 정확히 한 번만 보정하게 함."""
    y = int(st.session_state.get(f"{key}_year", 1990))
    m = int(st.session_state.get(f"{key}_month", 1))
    d = int(st.session_state.get(f"{key}_day", 1))
    cal_type = st.session_state.get(f"{key}_caltype", "양력")
    is_leap  = st.session_state.get(f"{key}_isleap", False)
    no_time  = st.session_state.get(f"{key}_notime", False)
    _pt      = _parse_time(st.session_state.get(f"{key}_time_raw", "")) if not no_time else None
    h, mn    = _pt if _pt else (12, 0)

    # 도시 선택 → get_saju()에 넘길 local_offset_min 결정
    city     = st.session_state.get(f"{key}_city", "서울특별시")
    city_off = _CITY_OFFSETS.get(city, -32)   # 기본 서울(-32)

    cal_label = "양력"
    if cal_type == "음력":
        converted = _lunar_to_solar(y, m, d, is_leap)
        if converted is None:
            st.error(f"음력 {y}년 {m}월 {d}일{'(윤달)' if is_leap else ''}을 양력으로 변환할 수 없어요. 날짜를 확인해주세요.")
            st.stop()
        sy, sm, sd = converted
        cal_label = f"음력 {y}/{m}/{d}{'(윤)' if is_leap else ''} → 양력 {sy}/{sm}/{sd}"
        y, m, d = sy, sm, sd

    if not no_time and city != "선택 안함 (보정 없음)":
        sign = "+" if city_off > 0 else ""
        cal_label += f"  |  🌐 지방시 {city}({sign}{city_off}분)"

    return y, m, d, h, mn, no_time, cal_label, city_off


def render_pillars_table(pillars, no_time=False):
    ilgan = pillars[2][0]
    gm    = get_gongmang(*pillars[2])
    order = [2, 1, 0] if no_time else [3, 2, 1, 0]
    hdrs  = ['일주', '월주', '년주'] if no_time else ['시주', '일주', '월주', '년주']
    subs  = ['日', '月', '年'] if no_time else ['時', '日', '月', '年']

    _OH_BG     = {'목':'#bbf7d0','화':'#fecaca','토':'#fde68a','금':'#e2e8f0','수':'#bfdbfe'}
    _OH_BORDER = {'목':'#4ade80','화':'#f87171','토':'#fbbf24','금':'#94a3b8','수':'#60a5fa'}
    _OH_DIV    = {'목':'#86efac','화':'#fca5a5','토':'#fde68a','금':'#cbd5e1','수':'#93c5fd'}
    _TXT_MAIN  = '#111827'   # 큰 글자 (천간·지지)
    _TXT_SUB   = '#374151'   # 작은 설명 텍스트

    def _ss_g(i):
        g = pillars[i][0]
        return '일간' if i == 2 else get_sipseong(ilgan, OHAENG_IDX[g], g % 2)

    cols_html = ''
    for idx, (i, hdr, sub) in enumerate(zip(order, hdrs, subs)):
        g, j    = pillars[i][0], pillars[i][1]
        oh_g    = OHAENG_NAMES[OHAENG_IDX[g]]
        oh_j    = OHAENG_NAMES[OHAENG_IDX_J[j]]
        bg      = _OH_BG.get(oh_g, '#f1f5f9')
        bdc     = _OH_BORDER.get(oh_g, '#cbd5e1')
        div_c   = _OH_DIV.get(oh_g, '#e2e8f0')
        bg_j    = _OH_BG.get(oh_j, '#f1f5f9')
        bdc_j   = _OH_BORDER.get(oh_j, '#cbd5e1')
        is_ilju = (i == 2)
        border  = f'2px solid {bdc}' if is_ilju else f'1px solid {bdc}'
        shadow  = '0 2px 14px rgba(0,0,0,0.12)' if is_ilju else '0 1px 4px rgba(0,0,0,0.06)'
        ss_g    = _ss_g(i)
        ss_j    = get_sipseong(ilgan, OHAENG_IDX_J[j], j % 2)
        unsung  = get_12unsung(ilgan, j)
        jijg    = ' '.join(JIJANGAN[j])
        gm_tag  = '<span style="font-size:0.6rem;background:rgba(255,100,100,0.25);color:#dc2626;border-radius:4px;padding:1px 5px;margin-left:3px;">공망</span>' if j in gm else ''

        cols_html += f'''
        <td style="padding:0 5px;width:{'25' if not no_time else '33.3'}%;vertical-align:top;">
          <div style="border:{border};border-radius:12px;overflow:hidden;
                      text-align:center;box-shadow:{shadow};height:100%;">
            <div style="background:{bg};padding:10px 8px 8px;">
              <div style="font-size:0.68rem;color:{_TXT_SUB};margin-bottom:6px;letter-spacing:0.05em;font-weight:700;">
                {hdr}<span style="opacity:0.6;font-size:0.6rem;">({sub})</span>
              </div>
              <div style="font-size:2rem;font-weight:800;color:{_TXT_MAIN};line-height:1;">
                {CHEONGAN[g]}
              </div>
              <div style="font-size:0.65rem;color:{_TXT_SUB};margin:2px 0 0;">{oh_g} · {ss_g}</div>
            </div>
            <div style="background:{bg_j};padding:8px 8px 10px;border-top:1px solid {bdc_j};">
              <div style="font-size:1.6rem;line-height:1;">{_JIJI_EMOJI[j]}</div>
              <div style="font-size:1.4rem;font-weight:700;color:{_TXT_MAIN};line-height:1.1;">{JIJI[j]}{gm_tag}</div>
              <div style="font-size:0.65rem;color:{_TXT_SUB};margin-top:3px;">{oh_j} · {ss_j}</div>
              <div style="margin-top:6px;border-top:1px solid {bdc_j};padding-top:5px;">
                <div style="font-size:0.62rem;color:{_TXT_SUB};margin-bottom:2px;">{unsung}</div>
                <div style="font-size:0.6rem;color:{_TXT_SUB};opacity:0.8;letter-spacing:0.03em;">{jijg}</div>
              </div>
            </div>
          </div>
        </td>'''

    st.markdown(
        f'<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">'
        f'<table style="width:100%;border-collapse:separate;border-spacing:6px 0;table-layout:fixed;">'
        f'<tr>{cols_html}</tr></table></div>',
        unsafe_allow_html=True,
    )


def render_saju_card(name, pillars, corr_dt, corrections, gender, year,
                     expanded=True, no_time=False, cal_label="양력", card_id="main", rel_status='솔로'):
    is_male = gender == '남'
    gil, hyung = check_sal(pillars)
    yj = pillars[0][1]
    oa = analyze_ohaeng(pillars)


    st.markdown(
        f'<div style="margin-bottom:6px;">'
        f'<span style="font-size:1.45rem;font-weight:800;'
        f'background:linear-gradient(135deg,#6d28d9,#a855f7);'
        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🔮 {name}님의 사주팔자</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    hm_str = corr_dt.strftime('%Y-%m-%d %H:%M')
    cap = f"절입 보정: {hm_str}  ({', '.join(corrections)})"
    if cal_label != "양력":
        cap += f"  |  📅 {cal_label}"
    if no_time:
        cap += "  |  ⚠ 시주(時柱) 미포함"
    st.caption(cap)

    render_pillars_table(pillars, no_time=no_time)

    # 정보 뱃지 행
    _OH_CHIP = {'목':('rgba(220,252,231,0.9)','#166534','#6ee7b7'),
                '화':('rgba(254,226,226,0.9)','#991b1b','#fca5a5'),
                '토':('rgba(254,243,199,0.9)','#92400e','#fcd34d'),
                '금':('rgba(219,234,254,0.9)','#1e3a5f','#93c5fd'),
                '수':('rgba(219,234,254,0.9)','#1e40af','#60a5fa')}
    gm = get_gongmang(*pillars[2])
    info_chips = f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 4px;">'
    info_chips += (f'<span style="background:#f5f0ff;border:1px solid #ddd4f8;'
                   f'color:#5b21b6;padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;">'
                   f'{_JIJI_EMOJI[yj]} {ANIMALS[yj]}띠</span>')
    if gm:
        gm_str = ' '.join(JIJI[x] for x in sorted(gm))
        info_chips += (f'<span style="background:#fff1f2;border:1px solid #fca5a5;'
                       f'color:#be123c;padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;">🕳 공망 {gm_str}</span>')
    for oh, cnt in oa.items():
        if cnt:
            bg, tc, bc = _OH_CHIP.get(oh, ('#f5f0ff','#5b21b6','#ddd4f8'))
            info_chips += (f'<span style="background:{bg};border:1px solid {bc};'
                           f'color:{tc};padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">{oh} {cnt}</span>')
    for g in gil:
        info_chips += f'<span class="badge-green">✦ {g}</span>'
    for h in hyung:
        info_chips += f'<span class="badge-orange">⚠ {h}</span>'
    info_chips += '</div>'
    st.markdown(info_chips, unsafe_allow_html=True)

    with st.expander("🔮 용신·기신 판단 근거", expanded=False):
        st.markdown(explain_yongshin(pillars))

    start_age, forward, daeun = get_daewoon(pillars, corr_dt, is_male)

    # ── 오늘의 일진 미니 카드 ─────────────────────────────────
    _today = datetime.now(_KST)
    try:
        _dg, _dj = get_ilchin(_today.year, _today.month, _today.day)
        _ya, _ki = get_yongki(pillars)
        _dg_oh = OHAENG_NAMES[OHAENG_IDX[_dg]]
        _dj_oh = OHAENG_NAMES[OHAENG_IDX_J[_dj]]
        _is_yong = _dg_oh == _ya or _dj_oh == _ya
        _is_ki   = _dg_oh in _ki or _dj_oh in _ki
        _pair    = frozenset([pillars[2][1], _dj])
        _is_hap  = _pair in YUKAHP
        _is_chung = any(_pair == c for c in JIJI_CHUNG)
        if _is_yong and not _is_ki:
            _grade, _gc = '★ 길일', '#166534'; _gbg = '#d1fae5'; _gbd = '#6ee7b7'
            _gmsg = f'용신({_ya}) 활성 — 오늘 적극 움직이세요'
        elif _is_ki and _is_chung:
            _grade, _gc = '△ 반길', '#92400e'; _gbg = '#fef3c7'; _gbd = '#fcd34d'
            _gmsg = f'충이 기신({", ".join(_ki)})을 깨뜨려요 — 막힌 일이 풀릴 수 있어요'
        elif _is_ki:
            _grade, _gc = '⚠ 흉일', '#991b1b'; _gbg = '#fee2e2'; _gbd = '#fca5a5'
            _gmsg = f'기신({", ".join(_ki)}) 주의 — 중요 결정은 미루세요'
        elif _is_hap:
            _grade, _gc = '● 합일', '#1e40af'; _gbg = '#dbeafe'; _gbd = '#93c5fd'
            _gmsg = '인연·만남에 좋은 날'
        elif _is_chung:
            _grade, _gc = '◎ 충일', '#6d28d9'; _gbg = '#ede9fe'; _gbd = '#a78bfa'
            _gmsg = '변화·이동이 생기기 쉬운 날'
        else:
            _grade, _gc = '○ 평일', '#374151'; _gbg = '#f3f4f6'; _gbd = '#d1d5db'
            _gmsg = '평온하게 흘러가는 날'

        st.markdown(
            f'<div style="background:{_gbg};border:1px solid {_gbd};border-radius:12px;'
            f'padding:12px 16px;margin:10px 0;display:flex;align-items:center;gap:14px;">'
            f'<div style="text-align:center;min-width:52px;">'
            f'  <div style="font-size:1.3rem;font-weight:800;color:{_gc};">'
            f'    {CHEONGAN[_dg]}{JIJI[_dj]}</div>'
            f'  <div style="font-size:0.65rem;color:{_gc};opacity:0.7;">오늘 일진</div>'
            f'</div>'
            f'<div style="flex:1;">'
            f'  <span style="background:{_gc};color:#fff;font-size:0.72rem;font-weight:700;'
            f'    border-radius:6px;padding:2px 8px;margin-right:6px;">{_grade}</span>'
            f'  <span style="font-size:0.88rem;color:{_gc};font-weight:600;">{_gmsg}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception:
        pass

    # ── 기본 분석 ────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.78rem;font-weight:700;color:#6d28d9;'
        'letter-spacing:0.05em;margin:14px 0 4px;">📋 기본 분석</div>',
        unsafe_allow_html=True,
    )
    with st.expander("🎯 올해 운세 — 총평·재물·직업·연애·건강", expanded=True):
        _render_thisyear_section(name, pillars, year, card_id=card_id, rel_status=rel_status)

    with st.expander("📖 사주 해설 — 성격·재물·연애·직업·건강", expanded=False):
        _narr(analyze_saju(name, pillars, gil, hyung))

    with st.expander("💕 이성 적성 — 잘 맞는 이성 타입", expanded=False):
        _narr(analyze_romantic_type(name, pillars, judge_strength(pillars), gender))

    with st.expander("🌙 월운(月運) — 이달·다음달 운세", expanded=False):
        _render_wolun_section(pillars, year, name=name, card_id=card_id, rel_status=rel_status)

    # ── 심화 분석 ────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.78rem;font-weight:700;color:#9d7cc8;'
        'letter-spacing:0.05em;margin:14px 0 4px;">🔬 심화 분석</div>',
        unsafe_allow_html=True,
    )
    with st.expander("🌊 대운(大運) — 10년 주기 큰 흐름", expanded=False):
        _render_daewoon_table(start_age, forward, daeun)
        _narr(analyze_daewoon_narrative(name, pillars, daeun, start_age, forward))

    with st.expander("📅 세운(歲運) — 연도별 운세 표", expanded=False):
        _render_sewoon_section(name, pillars, year, daeun)

    with st.expander("🔖 신살(神殺) — 귀인·흉살 상세 해설", expanded=False):
        _render_sal_detail(pillars)


def _render_thisyear_section(name, pillars, birth_year, card_id="main", rel_status='솔로'):
    cur = datetime.now(_KST).year
    year_range = list(range(cur - 3, cur + 8))
    safe_name = name.replace(" ", "_")
    sel_key = f"thisyear_{safe_name}_{card_id}"
    sel_year = st.select_slider(
        "연도 선택",
        options=year_range,
        value=cur,
        key=sel_key,
    )
    result_text = analyze_this_year(name, pillars, birth_year, sel_year, rel_status)
    st.markdown(result_text)

    share_key = f"share_{safe_name}_{card_id}_{sel_year}"
    if st.button("📋 결과 텍스트 복사", key=share_key, use_container_width=False):
        st.session_state[f"{share_key}_show"] = True
    if st.session_state.get(f"{share_key}_show"):
        st.text_area("아래 전체 선택 후 복사하세요", value=result_text,
                     height=200, key=f"{share_key}_area", label_visibility="collapsed")


def _render_sewoon_section(name, pillars, birth_year, daeun):
    cur = datetime.now(_KST).year
    ilgan = pillars[2][0]
    sewoon = get_sewoon(birth_year, past=5, future=10)

    def _daeun_str(y):
        for _, yr, dg, dj in daeun:
            if yr <= y < yr + 10:
                return f'{CHEONGAN[dg]}{JIJI[dj]}'
        return '─'

    rows = []
    for y, age, yg, yj in sewoon:
        ss_g, ss_j = _sewoon_ss(ilgan, yg, yj)
        grade, desc = _SEWOON_SS_DESC.get(ss_g, ('─', ''))
        rows.append({
            '연도': f'★ {y}' if y == cur else str(y),
            '나이': f'{age}세',
            '세운': f'{CHEONGAN[yg]}{JIJI[yj]}',
            '대운': _daeun_str(y),
            '천간십성': ss_g,
            '지지십성': ss_j,
            '길흉': grade,
            '핵심': desc,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.divider()
    _narr(analyze_sewoon_narrative(name, pillars, birth_year))


def _render_wolun_section(pillars, year, name="", card_id="main", rel_status='솔로'):
    cur = datetime.now(_KST).year
    cur_date = datetime.now(_KST).date()
    ilgan = pillars[2][0]

    safe_name = name.replace(" ", "_") if name else "default"
    sel_key = f"wolun_year_{safe_name}_{card_id}"
    year_range = list(range(cur - 2, cur + 4))
    sel_year = st.select_slider(
        "조회할 연도 선택",
        options=year_range,
        value=cur,
        key=sel_key,
    )

    wolun = get_wolun(sel_year)

    rows = []
    for i, (label, st_date, mg, mj) in enumerate(wolun):
        end_date = wolun[i + 1][1].date() if i + 1 < len(wolun) else None
        is_cur = (st_date.date() <= cur_date and (end_date is None or cur_date < end_date))
        ss_g = get_sipseong(ilgan, OHAENG_IDX[mg], mg % 2)
        ss_j = get_sipseong(ilgan, OHAENG_IDX_J[mj], mj % 2)
        _, desc = _SEWOON_SS_DESC.get(ss_g, ('─', ''))
        rows.append({
            '월': f'★ {label}' if is_cur else label,
            '절기 시작': st_date.strftime('%m/%d'),
            '간지': f'{CHEONGAN[mg]}{JIJI[mj]}',
            '천간십성': ss_g,
            '지지십성': ss_j,
            '핵심 운세': desc,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown(analyze_wolun_detail(name, pillars, sel_year, rel_status=rel_status))


def _render_sal_detail(pillars):
    gil, hyung = check_sal(pillars)
    all_sal = gil + hyung

    if not all_sal:
        st.info("특별히 강조되는 신살이 없어요.")
        return

    gil_items  = [(s, True)  for s in gil]
    hyung_items = [(s, False) for s in hyung]

    for sal_str, is_gil in gil_items + hyung_items:
        sal_key = next((k for k in _SAL_DESC if sal_str.startswith(k)), None)
        desc    = _SAL_DESC.get(sal_key, '')   if sal_key else ''
        modern  = _SAL_MODERN.get(sal_key, '') if sal_key else ''
        color  = "#d4edda" if is_gil else "#fff3cd"
        border = "#28a745" if is_gil else "#ffc107"
        tag    = "✨ 길신" if is_gil else "⚠ 흉살"

        trad_block = (
            f'<div style="margin-top:6px;">'
            f'<span style="font-size:0.72rem;font-weight:600;color:#666;letter-spacing:.04em;">📜 전통 풀이</span><br>'
            f'<span style="font-size:0.88rem;color:#1a1a1a;">{desc}</span>'
            f'</div>'
        ) if desc else ''

        modern_block = (
            f'<div style="margin-top:6px;padding-top:6px;border-top:1px dashed #bbb;">'
            f'<span style="font-size:0.72rem;font-weight:600;color:#666;letter-spacing:.04em;">💡 현대 풀이</span><br>'
            f'<span style="font-size:0.88rem;color:#1a1a1a;">{modern}</span>'
            f'</div>'
        ) if modern else ''

        st.markdown(
            f'<div style="background:{color};border-left:4px solid {border};'
            f'border-radius:6px;padding:10px 14px;margin:6px 0;color:#1a1a1a;">'
            f'<b style="font-size:1rem;color:#1a1a1a;">{sal_str}</b>'
            f' <span style="font-size:0.78rem;color:#555;">{tag}</span>'
            f'{trad_block}{modern_block}'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_daewoon_table(start_age, forward, daeun):
    cur = datetime.now(_KST).year
    st.caption(f"대운 방향: {'순행' if forward else '역행'}  /  {start_age}세 시작")

    rows = []
    for age, yr, dg, dj in daeun:
        rows.append({
            '기간': f"{age}세 ({yr}~{yr+9})",
            '대운': f"{CHEONGAN[dg]}{JIJI[dj]}",
            '오행': f"{OHAENG_G[dg]}{OHAENG_J[dj]}",
            '현재': '★ 현재' if yr <= cur < yr + 10 else '',
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _get_holidays(year: int) -> dict:
    """양력 날짜 → 공휴일 이름 딕셔너리 반환. 음력 연휴는 KoreanLunarCalendar로 변환."""
    h = {}

    # ── 법정 공휴일 (고정) ──────────────────────────────────────
    fixed = {
        (1,  1): "신정",
        (3,  1): "삼일절",
        (5,  5): "어린이날",
        (6,  6): "현충일",
        (8, 15): "광복절",
        (10, 3): "개천절",
        (10, 9): "한글날",
        (12,25): "성탄절",
    }
    for (m, d), name in fixed.items():
        h[(year, m, d)] = name

    # ── 음력 기반 공휴일 변환 ────────────────────────────────────
    lc = KoreanLunarCalendar()

    def _lunar(lm, ld, label):
        try:
            lc.setLunarDate(year, lm, ld, False)
            s = lc.SolarIsoFormat()
            sy, sm, sd = map(int, s.split('-'))
            h[(sy, sm, sd)] = label
        except Exception:
            pass

    # 설날 (음력 1/1) + 전날 + 다음날
    _lunar(1, 1, "설날")
    try:
        lc.setLunarDate(year, 1, 1, False)
        s = lc.SolarIsoFormat()
        sy, sm, sd = map(int, s.split('-'))
        from datetime import timedelta
        d_obj = datetime(sy, sm, sd).date()
        prev = d_obj - timedelta(days=1)
        nxt  = d_obj + timedelta(days=1)
        h[(prev.year, prev.month, prev.day)] = "설날연휴"
        h[(nxt.year,  nxt.month,  nxt.day)]  = "설날연휴"
    except Exception:
        pass

    # 석가탄신일 (음력 4/8)
    _lunar(4, 8, "부처님오신날")

    # 추석 (음력 8/15) + 전날 + 다음날
    _lunar(8, 15, "추석")
    try:
        lc.setLunarDate(year, 8, 15, False)
        s = lc.SolarIsoFormat()
        sy, sm, sd = map(int, s.split('-'))
        from datetime import timedelta
        d_obj = datetime(sy, sm, sd).date()
        prev = d_obj - timedelta(days=1)
        nxt  = d_obj + timedelta(days=1)
        h[(prev.year, prev.month, prev.day)] = "추석연휴"
        h[(nxt.year,  nxt.month,  nxt.day)]  = "추석연휴"
    except Exception:
        pass

    return h


def _render_ilchin_calendar(year, month, pillars=None):
    _OH_BG = {'목':'#f1f8e9','화':'#fde8f0','토':'#fff8e1','금':'#f5f5f5','수':'#e3f2fd'}

    ya_name = ''; ki_names = []; ilji = -1
    if pillars:
        ya_name, ki_names = get_yongki(pillars)
        ilji = pillars[2][1]

    lc = KoreanLunarCalendar()
    holidays = _get_holidays(year)
    days_in_month = _cal_mod.monthrange(year, month)[1]
    first_wd      = (_cal_mod.weekday(year, month, 1) + 1) % 7   # 0=일
    today         = datetime.now(_KST).date()

    cells = [None] * first_wd
    for d in range(1, days_in_month + 1):
        dg, dj = get_ilchin(year, month, d)
        try:
            lc.setSolarDate(year, month, d)
            lunar_str = ('윤' if lc.isIntercalation else '') + f'{lc.lunarMonth}/{lc.lunarDay}'
        except Exception:
            lunar_str = ''

        dj_oh = OHAENG_NAMES[OHAENG_IDX_J[dj]]
        dg_oh = OHAENG_NAMES[OHAENG_IDX[dg]]
        is_yong = is_ki = hap = chung = False
        if pillars:
            is_yong = dg_oh == ya_name or dj_oh == ya_name
            is_ki   = dg_oh in ki_names or dj_oh in ki_names
            pair    = frozenset([ilji, dj])
            hap     = pair in YUKAHP
            chung   = any(pair == c for c in JIJI_CHUNG)

        holiday_name = holidays.get((year, month, d), '')

        cells.append({
            'd': d, 'dg': dg, 'dj': dj,
            'ganji': CHEONGAN[dg] + JIJI[dj],
            'emoji': _JIJI_EMOJI[dj],
            'lunar': lunar_str,
            'bg': _OH_BG.get(dj_oh, '#fff'),
            'is_yong': is_yong, 'is_ki': is_ki,
            'hap': hap, 'chung': chung,
            'is_today': datetime(year, month, d).date() == today,
            'holiday': holiday_name,
        })

    while len(cells) % 7:
        cells.append(None)

    hdr_labels = ['<span style="color:#ef9a9a">일</span>',
                  '월','화','수','목','금',
                  '<span style="color:#90caf9">토</span>']
    html = [
        '<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;margin:4px 0 8px 0;">',
        '<table style="width:100%;min-width:300px;border-collapse:collapse;table-layout:fixed;border-radius:8px;overflow:hidden;">',
        '<colgroup>' + '<col style="width:14.28%;">' * 7 + '</colgroup><tr>',
    ]
    for lbl in hdr_labels:
        html.append(
            f'<th style="background:#4a4a8a;color:#fff;padding:8px 2px;'
            f'text-align:center;font-size:0.82rem;font-weight:700;'
            f'letter-spacing:0.02em;">{lbl}</th>'
        )
    html.append('</tr>')

    for row_i in range(0, len(cells), 7):
        html.append('<tr>')
        for col_i, cell in enumerate(cells[row_i:row_i+7]):
            if cell is None:
                html.append(
                    '<td style="border:1px solid #ebebf2;background:#f5f5fa;'
                    'padding:3px;min-height:72px;"></td>'
                )
                continue

            is_holiday = bool(cell['holiday'])
            is_sunday  = col_i == 0
            is_sat     = col_i == 6

            _yong = cell['is_yong']; _ki = cell['is_ki']
            _hap = cell['hap']; _chung = cell['chung']

            # 배경: 조합 우선
            if cell['is_today']:
                bg = '#ede7f6'
            elif is_holiday:
                bg = '#fdecea'
            elif _yong and _hap:
                bg = '#b9f6ca'   # 대길 — 짙은 초록
            elif _yong and _chung:
                bg = '#e8f5e9'   # 길+변화 — 연초록
            elif _ki and _chung:
                bg = '#fff3e0'   # 반길(충이 기신 깨뜨림) — 연한 황색
            elif _ki and _hap:
                bg = '#fff8e1'   # 기신+합 — 옅은 노란
            elif _yong:
                bg = '#e8f5e9'
            elif _ki:
                bg = '#fff8e1'
            else:
                bg = cell['bg']

            # 테두리: 조합별 색상
            if _yong and _hap:
                bw, bc = '2px', '#00897b'   # 청록
            elif _yong and _chung:
                bw, bc = '2px', '#ff7043'   # 주황 (길+충돌)
            elif _ki and _chung:
                bw, bc = '2px', '#e53935'   # 빨강 (충)
            elif _ki and _hap:
                bw, bc = '2px', '#1e88e5'   # 파랑 (합)
            elif _hap:
                bw, bc = '2px', '#1e88e5'
            elif _chung:
                bw, bc = '2px', '#e53935'
            else:
                bw, bc = '1px', '#e0e0ec'

            if is_holiday or is_sunday:
                dc = '#e53935'
            elif is_sat:
                dc = '#42a5f5'
            else:
                dc = '#1a1a2e'

            today_ring = (
                'outline:2px solid #7c4dff;outline-offset:-2px;border-radius:4px;'
                if cell['is_today'] else ''
            )

            holiday_html = ''
            if cell['holiday']:
                hname = cell['holiday']
                holiday_html = (
                    f'<div style="font-size:0.5rem;color:#c62828;font-weight:700;'
                    f'line-height:1.1;margin-bottom:1px;white-space:nowrap;overflow:hidden;'
                    f'text-overflow:ellipsis;">{hname}</div>'
                )

            tags = ''
            if _yong and _hap:
                tags += '<span style="font-size:0.5rem;background:#00897b;color:#fff;border-radius:3px;padding:0 2px;margin:0 1px 1px 0;display:inline-block;">용신+합</span>'
            elif _yong and _chung:
                tags += '<span style="font-size:0.5rem;background:#ff7043;color:#fff;border-radius:3px;padding:0 2px;margin:0 1px 1px 0;display:inline-block;">용신+충</span>'
            elif _ki and _chung:
                tags += '<span style="font-size:0.5rem;background:#e53935;color:#fff;border-radius:3px;padding:0 2px;margin:0 1px 1px 0;display:inline-block;">충→기신↓</span>'
            elif _ki and _hap:
                tags += '<span style="font-size:0.5rem;background:#7b1fa2;color:#fff;border-radius:3px;padding:0 2px;margin:0 1px 1px 0;display:inline-block;">기신+합</span>'
            else:
                if _yong:
                    tags += '<span style="font-size:0.5rem;background:#43a047;color:#fff;border-radius:3px;padding:0 2px;margin:0 1px 1px 0;display:inline-block;">용신</span>'
                if _ki:
                    tags += '<span style="font-size:0.5rem;background:#fb8c00;color:#fff;border-radius:3px;padding:0 2px;margin:0 1px 1px 0;display:inline-block;">기신</span>'
                if _hap:
                    tags += '<span style="font-size:0.5rem;background:#1e88e5;color:#fff;border-radius:3px;padding:0 2px;margin:0 1px 1px 0;display:inline-block;">합</span>'
                if _chung:
                    tags += '<span style="font-size:0.5rem;background:#e53935;color:#fff;border-radius:3px;padding:0 2px;margin:0 1px 1px 0;display:inline-block;">충</span>'

            html.append(
                f'<td style="border:{bw} solid {bc};background:{bg};padding:4px 3px 3px 4px;'
                f'vertical-align:top;min-height:72px;{today_ring}">'
                f'<div style="font-size:0.9rem;font-weight:700;color:{dc};line-height:1.2;">{cell["d"]}</div>'
                f'{holiday_html}'
                f'<div style="font-size:0.6rem;color:#aaa;line-height:1.2;">음 {cell["lunar"]}</div>'
                f'<div style="font-size:0.78rem;color:#333;font-weight:600;line-height:1.3;">{cell["ganji"]}</div>'
                f'<div style="font-size:0.75rem;line-height:1.2;">{cell["emoji"]}</div>'
                f'<div style="margin-top:1px;">{tags}</div>'
                f'</td>'
            )
        html.append('</tr>')

    html.append('</table></div>')

    st.markdown('\n'.join(html), unsafe_allow_html=True)

    # 범례
    legend_parts = ['🟣 오늘  🔴 공휴일']
    if pillars:
        legend_parts += ['🟢 용신', '🟡 기신', '🔵 합', '⭕ 충', '🟩 용신+합', '🟧 용신+충', '🟥 충→기신↓', '🟪 기신+합']
    st.caption('  |  '.join(legend_parts))
    if pillars:
        with st.expander("📖 용어 설명", expanded=False):
            st.markdown("""
| 표시 | 의미 |
|------|------|
| 🟢 **용신(用神)** | 내 사주에 **필요한 기운**이 흐르는 날. 하고자 하는 일이 잘 풀리는 편. |
| 🟡 **기신(忌神)** | 내 사주에 **해로운 기운**이 흐르는 날. 중요한 결정·계약·시작은 피하는 게 좋음. |
| 🔵 **합(合)** | 일진이 내 사주와 **끌어당겨 합쳐지는** 날. 인연·만남·결합에 유리. |
| ⭕ **충(沖)** | 일진이 내 사주와 **충돌하는** 날. 변화·이동이 생기기 쉬움. |
| 🟩 **용신+합** | ★★ 대길 — 좋은 기운이 더욱 강화. 중요한 일 추진 최적. |
| 🟧 **용신+충** | ★◎ 길+변화 — 좋은 기운이 흔들리지만 돌파의 기회도 있음. 조심하되 과감하게. |
| 🟥 **충→기신↓** | △ 반길 — 충이 기신을 깨뜨려 해로운 기운이 흩어짐. 막혔던 일이 풀릴 수 있음. |
| 🟪 **기신+합** | ▽ 주의 — 기신이 합으로 완화되지만 완전히 사라지진 않음. 큰 결정은 신중하게. |
""")



# ─────────────────────────────────────────────────────────────
_profile_transfer_panel()   # 사이드바: 프로필 내보내기/가져오기
st.markdown("<h1>🔮 사주 분석</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8b77b8; margin-top:-10px; letter-spacing:0.08em; font-size:0.95rem;'>사주팔자 · 궁합 · 재회</p>", unsafe_allow_html=True)
st.caption("v2026.06.05.6")
st.markdown("<hr style='border:none;border-top:1px solid #e8e0f8;margin:12px 0 18px 0;'>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["  🔮  사주 보기  ", "  💕  궁합 보기  ", "  🌸  재회 보기  ", "  📅  일진 달력  "])

# ── 탭 1: 사주 ────────────────────────────────────────────────
with tab1:
    _profile_bar("s")
    with st.form("saju_form"):
        person_form("s", "")
        submitted_s = st.form_submit_button("✨ 사주 분석하기", use_container_width=True, type="primary")

    if submitted_s:
        s_name = st.session_state.get("s_name", "").strip()
        if not s_name:
            st.error("이름을 입력해주세요.")
        else:
            with st.spinner("사주를 풀어드리는 중..."):
                try:
                    s_gender = st.session_state.get("s_gender", "남")
                    sy, sm, sd, s_hour, s_minute, _no, cal_lbl, s_off = _resolve_date("s")
                    pillars, corr_dt, corrections = get_saju(sy, sm, sd, s_hour, s_minute, local_offset_min=s_off)
                    _rel_raw = st.session_state.get("s_relstatus", "솔로")
                    _rel = '기혼' if '기혼' in _rel_raw else _rel_raw
                    st.session_state['saju_res'] = dict(
                        name=s_name, pillars=pillars, corr_dt=corr_dt,
                        corrections=corrections, gender=s_gender, year=sy,
                        no_time=_no, cal_label=cal_lbl, rel_status=_rel,
                    )
                except Exception as e:
                    st.session_state.pop('saju_res', None)
                    st.error(f"오류: {e}"); st.exception(e)

    if 'saju_res' in st.session_state:
        r = st.session_state['saju_res']
        render_saju_card(r['name'], r['pillars'], r['corr_dt'], r['corrections'],
                         r['gender'], r['year'], no_time=r['no_time'], cal_label=r.get('cal_label','양력'),
                         rel_status=r.get('rel_status','솔로'))

# ── 탭 2: 궁합 ────────────────────────────────────────────────
with tab2:
    _pc1, _pc2 = st.columns(2)
    with _pc1:
        _profile_bar("ga")
    with _pc2:
        _profile_bar("gb")
    with st.form("gunghap_form"):
        rel_label = st.selectbox("두 분의 관계", list(REL_OPTIONS.keys()), index=0, key="g_rel_label")
        c1, c2 = st.columns(2)
        with c1:
            person_form("ga", "💙 첫 번째 분")
        with c2:
            person_form("gb", "💜 두 번째 분")
        submitted_g = st.form_submit_button("💕 궁합 분석하기", use_container_width=True, type="primary")

    if submitted_g:
        na = st.session_state.get("ga_name", "").strip()
        nb = st.session_state.get("gb_name", "").strip()
        if not na or not nb:
            st.error("두 분의 이름을 모두 입력해주세요.")
        else:
            with st.spinner("두 분의 인연을 살펴보는 중..."):
                try:
                    ga = st.session_state.get("ga_gender", "남")
                    gb = st.session_state.get("gb_gender", "여")
                    ya, ma, da, ha, mna, no_a, cal_a, off_a = _resolve_date("ga")
                    yb, mb, db, hb, mnb, no_b, cal_b, off_b = _resolve_date("gb")
                    chosen_label = st.session_state.get("g_rel_label", "연인")
                    rel_type = REL_OPTIONS.get(chosen_label, "인연")
                    is_male_a = (ga == "남"); is_male_b = (gb == "남")

                    pa, corr_a, corr_list_a = get_saju(ya, ma, da, ha, mna, local_offset_min=off_a)
                    pb, corr_b, corr_list_b = get_saju(yb, mb, db, hb, mnb, local_offset_min=off_b)
                    score, reasons, rel = _score_gunghap_typed(pa, pb, na, nb, rel_type, is_male_a, is_male_b)
                    narr_text = _analyze_gunghap_typed(pa, pb, na, nb, score, rel, reasons, rel_type, is_male_a, is_male_b)

                    st.session_state['gunghap_res'] = dict(
                        na=na, nb=nb, pa=pa, pb=pb,
                        corr_a=corr_a, corr_b=corr_b, corr_list_a=corr_list_a, corr_list_b=corr_list_b,
                        ga=ga, gb=gb, ya=ya, yb=yb,
                        score=score, reasons=reasons, rel=rel, rel_type=rel_type,
                        chosen_label=chosen_label, narr_text=narr_text,
                        no_a=no_a, no_b=no_b, cal_a=cal_a, cal_b=cal_b,
                    )
                except Exception as e:
                    st.session_state.pop('gunghap_res', None)
                    st.error(f"오류: {e}"); st.exception(e)

    if 'gunghap_res' in st.session_state:
        r = st.session_state['gunghap_res']
        grades = GRADE_LABELS.get(r['rel_type'], GRADE_LABELS['친구'])
        gi = min(4, r['score'] // 20)
        grade_color = "#4CAF50" if r['score'] >= 70 else ("#FF9800" if r['score'] >= 50 else "#f44336")
        st.markdown(
            f'<div class="score-card" style="background: linear-gradient(135deg, {grade_color}cc, {grade_color}88);">'
            f'<div class="score-num">{r["score"]}점</div>'
            f'<div class="score-label">{r["na"]} × {r["nb"]}  |  {r["chosen_label"]}  |  {grades[gi]}</div>'
            f'</div>', unsafe_allow_html=True,
        )
        if r['reasons']:
            with st.expander("점수 근거", expanded=False):
                for reason in r['reasons']:
                    st.write(f"• {reason}")
        with st.expander("📖 궁합 상세 해설", expanded=True):
            _narr(r['narr_text'])
            if st.button("📋 해설 텍스트 복사", key="gunghap_share"):
                st.session_state['gunghap_share_show'] = True
            if st.session_state.get('gunghap_share_show'):
                share_txt = f"{r['na']} × {r['nb']}  {r['chosen_label']}  {r['score']}점\n\n{r['narr_text']}"
                st.text_area("아래 전체 선택 후 복사하세요", value=share_txt,
                             height=200, label_visibility="collapsed")
        col1, col2 = st.columns(2)
        with col1:
            render_saju_card(r['na'], r['pa'], r['corr_a'], r['corr_list_a'], r['ga'], r['ya'], expanded=False, no_time=r['no_a'], cal_label=r.get('cal_a','양력'), card_id="ga")
        with col2:
            render_saju_card(r['nb'], r['pb'], r['corr_b'], r['corr_list_b'], r['gb'], r['yb'], expanded=False, no_time=r['no_b'], cal_label=r.get('cal_b','양력'), card_id="gb")

# ── 탭 3: 재회 ────────────────────────────────────────────────
with tab3:
    _jc1, _jc2 = st.columns(2)
    with _jc1:
        _profile_bar("ja")
    with _jc2:
        _profile_bar("jb")
    with st.form("jaehoe_form"):
        c1, c2 = st.columns(2)
        with c1:
            person_form("ja", "🌸 나 (첫 번째 분)")
        with c2:
            person_form("jb", "🌙 상대방 (두 번째 분)")
        is_blocked = st.checkbox("⛔ 상대방이 나를 차단한 상태예요", key="jaehoe_blocked")
        submitted_j = st.form_submit_button("🌸 재회 가능성 분석하기", use_container_width=True, type="primary")

    if submitted_j:
        ja_name = st.session_state.get("ja_name", "").strip()
        jb_name = st.session_state.get("jb_name", "").strip()
        if not ja_name or not jb_name:
            st.error("두 분의 이름을 모두 입력해주세요.")
        else:
            with st.spinner("재회의 운을 살펴보는 중..."):
                try:
                    from saju import analyze_jaehoe
                    jga = st.session_state.get("ja_gender", "남")
                    jgb = st.session_state.get("jb_gender", "여")
                    jya, jma, jda, jha, jmna, jno_a, jcal_a, joff_a = _resolve_date("ja")
                    jyb, jmb, jdb, jhb, jmnb, jno_b, jcal_b, joff_b = _resolve_date("jb")

                    jpa, jcorr_a, jcorr_list_a = get_saju(jya, jma, jda, jha, jmna, local_offset_min=joff_a)
                    jpb, jcorr_b, jcorr_list_b = get_saju(jyb, jmb, jdb, jhb, jmnb, local_offset_min=joff_b)
                    score_j, reasons_j, rel_j = 재회운_분석(jpa, jpb, ja_name, jb_name)
                    jga_male = (jga == '남'); jgb_male = (jgb == '남')
                    jdw_a = get_daewoon(jpa, jcorr_a, jga_male)
                    jdw_b = get_daewoon(jpb, jcorr_b, jgb_male)
                    jaehoe_text = analyze_jaehoe(
                        jpa, jpb, ja_name, jb_name, score_j, reasons_j, rel_j,
                        dw_a=jdw_a, is_male_a=jga_male, dw_b=jdw_b, is_male_b=jgb_male,
                        is_blocked=st.session_state.get("jaehoe_blocked", False),
                    )
                    st.session_state['jaehoe_res'] = dict(
                        ja_name=ja_name, jb_name=jb_name,
                        jpa=jpa, jpb=jpb, jcorr_a=jcorr_a, jcorr_b=jcorr_b,
                        jcorr_list_a=jcorr_list_a, jcorr_list_b=jcorr_list_b,
                        jga=jga, jgb=jgb, jya=jya, jyb=jyb,
                        score_j=score_j, reasons_j=reasons_j, jaehoe_text=jaehoe_text,
                        no_a=jno_a, no_b=jno_b, cal_a=jcal_a, cal_b=jcal_b,
                    )
                except Exception as e:
                    st.session_state.pop('jaehoe_res', None)
                    st.error(f"오류: {e}"); st.exception(e)

    if 'jaehoe_res' in st.session_state:
        r = st.session_state['jaehoe_res']
        score_titles_j = [
            (75, "재회 기운이 강하게 감지돼요 ✨"),
            (58, "재회의 씨앗이 싹트는 시기예요 🌱"),
            (42, "각자의 성장이 먼저인 시기예요 🌿"),
            (0,  "운의 흐름이 다른 방향을 가리켜요 🍂"),
        ]
        jtitle = next(t for thresh, t in score_titles_j if r['score_j'] >= thresh)
        jcolor = "#7B68EE" if r['score_j'] >= 58 else ("#FF9800" if r['score_j'] >= 42 else "#9E9E9E")
        st.markdown(
            f'<div class="score-card" style="background: linear-gradient(135deg, {jcolor}cc, {jcolor}88);">'
            f'<div class="score-num">{r["score_j"]}점</div>'
            f'<div class="score-label">{r["ja_name"]} × {r["jb_name"]}  |  {jtitle}</div>'
            f'</div>', unsafe_allow_html=True,
        )
        if r['reasons_j']:
            with st.expander("점수 근거", expanded=False):
                for reason in r['reasons_j']:
                    st.write(f"• {reason}")
        with st.expander("📖 재회 상세 해설", expanded=True):
            _narr(r['jaehoe_text'])
        col1, col2 = st.columns(2)
        with col1:
            render_saju_card(r['ja_name'], r['jpa'], r['jcorr_a'], r['jcorr_list_a'], r['jga'], r['jya'], expanded=False, no_time=r['no_a'], cal_label=r.get('cal_a','양력'), card_id="ja")
        with col2:
            render_saju_card(r['jb_name'], r['jpb'], r['jcorr_b'], r['jcorr_list_b'], r['jgb'], r['jyb'], expanded=False, no_time=r['no_b'], cal_label=r.get('cal_b','양력'), card_id="jb")

# ── 탭 4: 일진 달력 ───────────────────────────────────────────
with tab4:
    st.markdown('<div class="sec-header">📅 일진(日辰) 달력</div>', unsafe_allow_html=True)

    _now = datetime.now(_KST)
    c1, c2, c3 = st.columns([2, 2, 4])
    with c1:
        cal_year = int(st.number_input("년도", 2000, 2050, _now.year, key="cal_year"))
    with c2:
        cal_month = int(st.number_input("월", 1, 12, _now.month, key="cal_month"))
    with c3:
        has_saju = 'saju_res' in st.session_state
        saju_name = st.session_state['saju_res']['name'] if has_saju else ''
        label = f"내 사주 기준 길흉 표시" + (f" ({saju_name})" if saju_name else '') + ('' if has_saju else ' (사주 탭에서 먼저 분석하세요)')
        use_personal = st.checkbox(
            label,
            key="cal_use_personal",
            disabled=not has_saju,
            value=has_saju,
        )

    cal_pillars = st.session_state['saju_res']['pillars'] if (use_personal and has_saju) else None

    _render_ilchin_calendar(cal_year, cal_month, cal_pillars)

    st.divider()
    st.markdown('<div class="sec-header">📆 날짜별 상세 분석</div>', unsafe_allow_html=True)

    max_day = _cal_mod.monthrange(cal_year, cal_month)[1]
    sel_day = int(st.number_input(
        "날짜 선택", 1, max_day,
        min(_now.day, max_day) if (cal_year == _now.year and cal_month == _now.month) else 1,
        key="cal_sel_day",
    ))

    try:
        dg_d, dj_d = get_ilchin(cal_year, cal_month, sel_day)
    except Exception:
        st.error("올바른 날짜를 선택하세요.")
        st.stop()

    col_a, col_b = st.columns([1, 3])
    with col_a:
        try:
            _lc = KoreanLunarCalendar()
            _lc.setSolarDate(cal_year, cal_month, sel_day)
            _lunar_d = ('윤' if _lc.isIntercalation else '') + f'{_lc.lunarMonth}월 {_lc.lunarDay}일'
        except Exception:
            _lunar_d = ''
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#f5f0ff,#ede9fe);'
            f'border:1px solid #c4b5fd;border-radius:14px;padding:22px 10px;text-align:center;'
            f'box-shadow:0 2px 12px rgba(109,40,217,0.1);">'
            f'<div style="font-size:2.4rem;font-weight:800;background:linear-gradient(135deg,#6d28d9,#a855f7);'
            f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{CHEONGAN[dg_d]}{JIJI[dj_d]}</div>'
            f'<div style="font-size:1.5rem;margin:6px 0;">{_JIJI_EMOJI[dj_d]} {ANIMALS[dj_d]}</div>'
            f'<div style="font-size:0.82rem;color:#7c5cb8;">{OHAENG_G[dg_d]} · {OHAENG_J[dj_d]}</div>'
            f'<div style="font-size:0.76rem;color:#9d7cc8;margin-top:6px;">음력 {_lunar_d}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_b:
        if cal_pillars:
            st.markdown(analyze_ilchin_day(cal_pillars, cal_year, cal_month, sel_day))
        else:
            st.markdown(analyze_ilchin_basic(cal_year, cal_month, sel_day))
