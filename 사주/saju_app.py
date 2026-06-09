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
    get_gyeokguk, get_yongshin, _year_pillar,
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
        st.caption("v2026.06.08.21")


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
    gm_hit_jijis = [j for i, (g, j) in enumerate(pillars) if j in gm and i != 2]
    if gm_hit_jijis:
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
        _render_thisyear_section(name, pillars, year, card_id=card_id, rel_status=rel_status, daeun=daeun)

    with st.expander("📖 사주 해설 — 성격·재물·연애·직업·건강", expanded=False):
        _narr(analyze_saju(name, pillars, gil, hyung, gender))

    with st.expander("🌟 일주론(日柱論) — 타고난 특성 상세", expanded=False):
        _render_ilju_card(name, pillars)

    with st.expander("💍 배우자 자리(日支宮) — 배우자 성향·합충 인연", expanded=False):
        _render_baewuja_section(pillars, gender)

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



# ── Gemini 고민상담 헬퍼 ──────────────────────────────────────────────────

def _build_saju_ctx(r: dict, sel_year: int) -> str:
    """사주 정보를 Gemini 프롬프트용 텍스트로 변환"""
    pillars = r['pillars']
    ilgan   = pillars[2][0]
    strength = judge_strength(pillars)
    gyeok_name, _, ki_list = get_gyeokguk(pillars)
    ya_oh, ya_name, _, _, _ = get_yongshin(pillars)
    ki_names = [OHAENG_NAMES[k] for k in ki_list]
    yg, yj = _year_pillar(sel_year)
    ss_g = get_sipseong(ilgan, OHAENG_IDX[yg], yg % 2)
    return (
        f"- 이름: {r['name']}\n"
        f"- 일간: {CHEONGAN[ilgan]}({OHAENG_NAMES[OHAENG_IDX[ilgan]]})\n"
        f"- 格局: {gyeok_name}\n"
        f"- 신강/신약: {strength}\n"
        f"- 용신: {ya_name}\n"
        f"- 기신: {', '.join(ki_names) if ki_names else '없음'}\n"
        f"- {sel_year}년 세운: {CHEONGAN[yg]}{JIJI[yj]}년 ({ss_g}운)\n"
        f"- 연애 상태: {r.get('rel_status', '솔로')}"
    )


def _ask_gemini(question: str, saju_ctx: str, history=None) -> str:
    """Gemini 사주 기반 고민 답변 요청 — history 있으면 멀티턴 대화 유지"""
    try:
        from google import genai as _genai
    except ImportError:
        return "⚠️ google-genai 패키지가 설치되지 않았어요. `pip install google-genai` 실행 후 재시작하세요."
    api_key = ""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    if not api_key:
        import os, re as _re
        _sp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.streamlit', 'secrets.toml')
        try:
            with open(_sp, 'r', encoding='utf-8') as _f:
                _m = _re.search(r'^GEMINI_API_KEY\s*=\s*"([^"]+)"', _f.read(), _re.MULTILINE)
            if _m:
                api_key = _m.group(1)
        except Exception:
            pass
    if not api_key:
        api_key = st.session_state.get("_gemini_api_key", "")
    if not api_key:
        return "⚠️ Gemini API 키를 사이드바에 입력해주세요."
    try:
        client = _genai.Client(api_key=api_key)
        _sys = (
            "당신은 사주팔자 전문 상담사입니다. "
            "아래 사주 정보를 바탕으로 사용자의 고민에 실용적인 조언을 해주세요. "
            "이전 대화가 있으면 맥락을 이어서 답변하세요.\n\n"
            f"[사주 정보]\n{saju_ctx}\n\n"
            "답변 조건:\n"
            "- 사주 정보(일간, 格局, 용신/기신, 올해 세운)를 구체적으로 언급\n"
            "- 올해 운세 흐름과 연결해서 답변\n"
            "- 실용적이고 구체적인 행동 조언 포함\n"
            "- '언제 만나나요', '몇 월에', '몇 년도에' 등 시기를 묻는 질문에는 반드시 구체적인 시기를 답할 것. "
            "  용신 오행이 강한 월지(예: 금 용신이면 申월·酉월, 수 용신이면 亥월·子월)나 "
            "  세운·월운 흐름을 근거로 '○월 무렵', '하반기 ○~○월' 처럼 명확하게 제시. 모호하게 회피 금지.\n"
            "- 한국어로 자연스럽게, 400자 내외"
        )
        # 멀티턴: history[0]에 시스템 컨텍스트를 붙여 첫 메시지로, 이후 교대 구조 유지
        if history and len(history) > 1:
            _contents = [{"role": "user", "parts": [{"text": _sys + "\n\n" + history[0]["content"]}]}]
            for _m in history[1:]:
                _role = "user" if _m["role"] == "user" else "model"
                _contents.append({"role": _role, "parts": [{"text": _m["content"]}]})
        else:
            _contents = _sys + f"\n\n[고민]\n{question}"
        import time as _time
        _models = ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
        _last_err = None
        for _mdl in _models:
            for _try in range(3):
                try:
                    resp = client.models.generate_content(model=_mdl, contents=_contents)
                    return resp.text
                except Exception as _e:
                    _last_err = _e
                    if "503" in str(_e) or "UNAVAILABLE" in str(_e):
                        _time.sleep(3 + _try * 2)
                        continue
                    break
        return f"⚠️ 잠시 후 다시 시도해주세요. ({_last_err})"
    except Exception as e:
        return f"⚠️ API 오류: {e}"


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
        extra = f'  \n> ⚡ 대운 지지({JIJI[dj]})와 세운 지지({JIJI[yj]})가 **충(冲)**이에요. 이사·직장 변동·관계 변화가 생길 수 있어요.'
    elif dj_sew_hap:
        extra = f'  \n> 🤝 대운 지지({JIJI[dj]})와 세운 지지({JIJI[yj]})가 **합(合)**이에요. 안정적으로 흘러가는 흐름이에요.'

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
    return '\n'.join(lines)


# 일지(日支)별 배우자 자리 데이터
_ILJI_SPOUSE = {
    0:  {'name':'子(자)', 'desc':'총명하고 사교적이에요. 감수성이 풍부하고 섬세한 감각을 가진 타입으로, 겉은 활발해 보여도 내면에 깊은 감정이 흐르는 복합적인 매력이 있어요.', 'style':'지적 대화와 감정 공감을 중시해요. 함께 새로운 것을 탐구하는 관계에서 활력이 생겨요.', 'hap_ji':1,  'chung_ji':6},
    1:  {'name':'丑(축)', 'desc':'성실하고 꼼꼼하며 안정을 추구해요. 겉은 무뚝뚝해 보여도 속은 따뜻하고 책임감이 강한 타입이에요. 묵묵히 헌신하는 스타일이에요.', 'style':'티는 잘 안 내지만 조용히 노력하고 헌신해요. 신뢰를 쌓는 데 시간이 걸리지만 오래 가는 관계예요.', 'hap_ji':0,  'chung_ji':7},
    2:  {'name':'寅(인)', 'desc':'활동적이고 리더십이 강해요. 솔직하고 직선적이며 독립심이 강한 타입이에요. 함께 있으면 에너지가 넘치고 진취적인 분위기가 만들어져요.', 'style':'서로 각자의 영역을 존중하며 함께 성장하는 관계가 맞아요. 고집이 있는 편이라 솔직한 소통이 중요해요.', 'hap_ji':11, 'chung_ji':8},
    3:  {'name':'卯(묘)', 'desc':'섬세하고 예술적 감각이 있어요. 감성이 풍부하고 순수하며 상대의 마음을 잘 읽고 배려하는 따뜻한 타입이에요.', 'style':'감정 교류가 깊은 관계예요. 일상 속 작은 것에도 의미를 부여하며 공감하는 시간이 관계를 키워줘요.', 'hap_ji':10, 'chung_ji':9},
    4:  {'name':'辰(진)', 'desc':'포용력이 넓고 현실적이에요. 든든한 버팀목이 되어주는 깊은 내면의 힘을 가진 타입이에요. 묵직하고 신중하며 한번 결정하면 흔들리지 않아요.', 'style':'신뢰를 쌓는 데 시간이 걸리지만 쌓이면 매우 탄탄한 관계가 돼요. 실용적인 대화와 공동 목표가 관계를 강하게 해요.', 'hap_ji':9,  'chung_ji':10},
    5:  {'name':'巳(사)', 'desc':'지적이고 계획적이에요. 우아하고 세련되며 내면에 강한 의지와 고집이 있는 타입이에요. 생각이 깊고 신중하게 행동해요.', 'style':'서로의 지적 성취를 응원하는 관계가 잘 맞아요. 지적 공감대가 있어야 관계가 깊어질 수 있어요.', 'hap_ji':8,  'chung_ji':11},
    6:  {'name':'午(오)', 'desc':'열정적이고 활발해요. 솔직하고 카리스마 있으며 감정 표현이 직접적인 타입이에요. 강한 에너지로 주변에 활기를 불어넣어요.', 'style':'서로의 열정이 시너지를 내는 관계예요. 감정 기복이 클 수 있어 서로를 진정시켜주는 여유가 필요해요.', 'hap_ji':7,  'chung_ji':0},
    7:  {'name':'未(미)', 'desc':'온화하고 배려심이 깊어요. 예술적 감각과 따뜻한 마음을 가진 타입으로, 주변 사람에게 편안함과 포근함을 주는 분위기가 있어요.', 'style':'서로를 따뜻하게 감싸주는 안정적인 관계예요. 감정을 솔직하게 나누는 대화가 관계를 더욱 깊게 만들어줘요.', 'hap_ji':6,  'chung_ji':1},
    8:  {'name':'申(신)', 'desc':'영리하고 분석적이에요. 유연하고 재치 있으며 상황 판단력이 빠른 타입이에요. 적응력이 뛰어나고 다양한 분야에 재능을 보여요.', 'style':'지적 자극과 유머가 있는 관계가 잘 맞아요. 변화에 유연하게 대처하며 함께 새로운 도전을 즐기는 관계예요.', 'hap_ji':5,  'chung_ji':2},
    9:  {'name':'酉(유)', 'desc':'세련되고 완벽주의 성향이 있어요. 섬세하고 미적 감각이 뛰어나며 자신만의 기준이 뚜렷한 타입이에요. 꼼꼼하게 처리하는 스타일이에요.', 'style':'서로의 기준을 존중하는 관계예요. 세심하게 챙겨주는 배려가 관계를 단단하게 만들어줘요.', 'hap_ji':4,  'chung_ji':3},
    10: {'name':'戌(술)', 'desc':'의리 있고 충직해요. 진지하고 헌신적이며 한번 마음을 준 사람에게 깊이 헌신하는 타입이에요. 신뢰를 매우 중요하게 생각해요.', 'style':'신의와 믿음을 바탕으로 한 깊은 관계예요. 장기적인 동반자로 함께하는 것을 진지하게 소중히 여기는 관계예요.', 'hap_ji':3,  'chung_ji':4},
    11: {'name':'亥(해)', 'desc':'자유롭고 지혜로워요. 포용력과 공감 능력이 뛰어나며 넓은 시야를 가진 타입이에요. 깊은 사유와 따뜻한 감성이 공존하는 매력이 있어요.', 'style':'서로의 자유를 존중하면서도 깊은 유대감을 나누는 관계예요. 감정보다 이해와 공감이 관계의 뿌리가 돼요.', 'hap_ji':2,  'chung_ji':5},
}

_UNSUNG_SPOUSE_DESC = {
    '장생': ('🌱', '배우자 자리가 성장하는 에너지예요. 배우자가 함께 발전하는 긍정적 시너지를 가져다줘요.'),
    '목욕': ('✨', '배우자 자리에 감각적 매력이 있어요. 배우자가 매력적이지만 감정 기복이 있을 수 있어, 서로의 감성을 이해하는 게 중요해요.'),
    '관대': ('🎓', '배우자 자리가 활발한 에너지예요. 배우자가 사회적으로 적극적이고 의욕이 넘치는 타입이에요.'),
    '건록': ('💼', '배우자 자리가 자립적 에너지예요. 배우자가 독립심이 강하고 스스로 길을 개척하는 타입이에요. 서로의 영역을 존중하는 것이 핵심이에요.'),
    '제왕': ('👑', '배우자 자리가 강력한 에너지예요. 배우자가 강한 카리스마와 에너지를 가진 타입이에요. 강한 개성이 부딪히지 않도록 상호 존중이 중요해요.'),
    '쇠':   ('🍃', '배우자 자리가 안정적 에너지예요. 배우자가 노련하고 차분한 분위기를 가졌어요. 신중하고 안정적인 관계가 이어져요.'),
    '병':   ('🌙', '배우자 자리에 섬세한 에너지가 있어요. 배우자가 감수성이 풍부하고 내면이 깊은 타입이에요. 서로 섬세하게 배려하는 관계가 중요해요.'),
    '사':   ('🕊️', '배우자 자리에 변화의 에너지가 있어요. 배우자와의 인연이 특별하고 깊지만, 관계에서 변화를 함께 넘기는 인내가 필요해요.'),
    '묘':   ('🌿', '배우자 자리에 숙명적 에너지가 있어요. 배우자와의 인연이 깊은 인연으로 이어지는 구조예요. 서로를 깊이 이해하는 관계예요.'),
    '절':   ('🌊', '배우자 자리에 변화의 에너지가 있어요. 배우자와의 인연에 변화가 생길 수 있어요. 인연을 소중히 지키는 노력이 필요해요.'),
    '태':   ('🌸', '배우자 자리에 시작의 에너지가 있어요. 배우자와 함께 새로운 시작을 만들어가는 관계예요.'),
    '양':   ('🌼', '배우자 자리에 따뜻한 에너지가 있어요. 배우자가 포용력 있고 따뜻한 타입이에요. 서로를 성장시켜주는 관계가 펼쳐져요.'),
}

def _render_baewuja_section(pillars, gender):
    from saju import get_unsung, JIJI
    ilgan = pillars[2][0]
    ilji  = pillars[2][1]
    sp    = _ILJI_SPOUSE[ilji]
    unsung = get_unsung(ilgan, ilji)
    us_icon, us_desc = _UNSUNG_SPOUSE_DESC.get(unsung, ('', ''))
    hap_name   = _ILJI_SPOUSE[sp['hap_ji']]['name']
    chung_name = _ILJI_SPOUSE[sp['chung_ji']]['name']
    gender_str = '남편' if gender == '여' else '아내'

    st.markdown(
        f'<div style="background:linear-gradient(135deg,#fdf4ff,#ede9fe);border:1px solid #c4b5fd;'
        f'border-radius:12px;padding:14px 18px;margin-bottom:12px;">'
        f'<div style="font-size:0.75rem;font-weight:700;color:#7c3aed;margin-bottom:4px;">💍 배우자 자리(日支宮)</div>'
        f'<div style="font-size:1.1rem;font-weight:800;color:#374151;">{JIJI[ilji]} — {sp["name"]}</div>'
        f'<div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">십이운성: <b>{unsung}</b> {us_icon}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'**{gender_str} 성향**\n\n{sp["desc"]}')
    st.markdown(f'**관계 스타일**\n\n{sp["style"]}')
    if us_desc:
        st.markdown(f'**배우자 자리 에너지**\n\n{us_desc}')
    st.markdown('')
    col_a, col_b = st.columns(2)
    col_a.markdown(
        f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:10px 14px;">'
        f'<div style="font-size:0.72rem;font-weight:700;color:#1d4ed8;margin-bottom:4px;">🤝 합이 되는 인연</div>'
        f'<div style="font-size:0.85rem;color:#374151;">일지가 <b>{hap_name}</b>인 이성과<br>자연스럽게 끌리고 합이 이루어져요.</div>'
        f'</div>', unsafe_allow_html=True)
    col_b.markdown(
        f'<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:10px 14px;">'
        f'<div style="font-size:0.72rem;font-weight:700;color:#c2410c;margin-bottom:4px;">⚡ 충이 되는 인연</div>'
        f'<div style="font-size:0.85rem;color:#374151;">일지가 <b>{chung_name}</b>인 이성과는<br>에너지 충돌이 생기기 쉬워요.</div>'
        f'</div>', unsafe_allow_html=True)

# ilju extra data
_ILJU_EXTRA = {
    (0,0):  {'kw':['개척정신','지적호기심','헌신적'],'health':'간·담·눈  /  신장·방광 이중 관리','wealth':'지식·기획 기반 수입, 꾸준한 장기 축적형'},
    (0,2):  {'kw':['독립심','카리스마','원칙주의'],'health':'간·근육·힘줄  /  과로 면역 저하 주의','wealth':'자수성가형, 사업·창업에서 큰 성과'},
    (0,4):  {'kw':['포용력','전문성','안정감'],'health':'간·담  /  소화기·관절 이중 주의','wealth':'전문직·부동산 꾸준 축적, 급변보다 안정 지향'},
    (0,6):  {'kw':['열정','표현력','솔직함'],'health':'간·담  /  심장·혈압·체력 소모 주의','wealth':'교육·미디어·콘텐츠 기반, 활동할수록 수입 증가'},
    (0,8):  {'kw':['분석력','위기대처','냉철함'],'health':'간·담  /  폐·기관지·스트레스성 질환 주의','wealth':'IT·금융·의료 분야 강세, 도전 환경에서 성과 극대화'},
    (0,10): {'kw':['원칙주의','완벽주의','고독'],'health':'간·담  /  위장·피부·과로 주의','wealth':'연구·전문직 장기 축적, 투기성 투자 불리'},
    (1,1):  {'kw':['생명력','인내','현실감각'],'health':'간·근육  /  관절·소화기·냉증 주의','wealth':'재물 관리 탁월, 꾸준한 저축·부동산 친화적'},
    (1,3):  {'kw':['창의성','감성','적응력'],'health':'간·담·눈  /  신경계·피로 누적 주의','wealth':'예술·콘텐츠·교육 기반, 좋아하는 것이 수익'},
    (1,5):  {'kw':['전략적','신비감','집중력'],'health':'간·근육  /  심장·혈압·소화기 주의','wealth':'금융·법률·기획 강세, 조용히 쌓다 한번에 성과'},
    (1,7):  {'kw':['따뜻함','배려','감성'],'health':'간·담  /  소화기·면역·피로 주의','wealth':'서비스·복지·상담 강세, 꾸준하고 안정적 수입'},
    (1,9):  {'kw':['완벽주의','자존감','세련됨'],'health':'간·근육  /  폐·대장·피부·뼈 주의','wealth':'기술·패션·보석 강세, 고품질 기준이 고수익으로'},
    (1,11): {'kw':['이상주의','낭만','지적감성'],'health':'간·담  /  신장·방광·호르몬 주의','wealth':'학문·예술·철학 기반, 이상을 현실로 연결이 핵심'},
    (2,0):  {'kw':['열정','지혜','리더십'],'health':'심장·혈관·뇌  /  신장·방광·부종 주의','wealth':'교육·방송·리더십 포지션 강세, 재물 기복 있으나 회복 빠름'},
    (2,2):  {'kw':['태양형','카리스마','추진력'],'health':'심장·혈압·뇌혈관  /  간·근육 과로 주의','wealth':'사업·공직·리더형 직종 강세, 직관적 투자 성향'},
    (2,4):  {'kw':['포용력','다재다능','리더형'],'health':'심장·혈관  /  소화기·피부·관절 주의','wealth':'다방면 재능으로 다각도 수입, 부동산 친화적'},
    (2,6):  {'kw':['극열','열정','솔직담백'],'health':'심장·혈압·뇌혈관 집중 관리  /  여름 특히 주의','wealth':'에너지 기반 직종 강세, 재물 들어오고 나감이 활발'},
    (2,8):  {'kw':['분석력','냉철함','변화적응'],'health':'심장·혈관  /  폐·기관지·피부 주의','wealth':'IT·금융·분석직 강세, 변화 속 기회 포착 능력 탁월'},
    (2,10): {'kw':['원칙','고집','전문성'],'health':'심장·혈관  /  위장·피부·건조증 주의','wealth':'법률·종교·연구 강세, 전문성 깊어질수록 수입 안정'},
    (3,1):  {'kw':['섬세함','인내','현실적'],'health':'심장·소장  /  관절·소화기·냉증 주의','wealth':'꾸준한 저축형, 안정적 직장 기반 수입 유리'},
    (3,3):  {'kw':['감수성','창의','따뜻함'],'health':'심장·혈관  /  간·담·눈 피로 주의','wealth':'예술·감성 기반 수입, 창작물이 장기 자산'},
    (3,5):  {'kw':['열정','집중력','욕망'],'health':'심장·혈압 과부하  /  소화기 화기 주의','wealth':'금융·기획·비즈니스 강세, 집중력이 재물을 끌어당김'},
    (3,7):  {'kw':['감성지능','따뜻함','예술성'],'health':'심장·소장  /  소화기·면역·과로 주의','wealth':'서비스·상담·예술 강세, 진심이 고객을 만드는 형'},
    (3,9):  {'kw':['섬세함','완벽주의','고집'],'health':'심장·혈관  /  폐·대장·뼈·피부 주의','wealth':'기술·예술 강세, 완성도 높은 결과물이 프리미엄 수익'},
    (3,11): {'kw':['지혜','낭만','이상주의'],'health':'심장·소장  /  신장·방광·호르몬 주의','wealth':'학문·상담·예술 기반, 진심 어린 전문성이 장기 자산'},
    (4,0):  {'kw':['믿음직함','포용력','중용'],'health':'위장·비장·소화기  /  신장·방광·부종 주의','wealth':'안정 지향형, 부동산·금융·공직에서 꾸준 축적'},
    (4,2):  {'kw':['대범함','리더십','도전정신'],'health':'위장·소화기  /  간·근육·과로 주의','wealth':'사업·리더십 직종 강세, 큰 그림을 그리는 투자 성향'},
    (4,4):  {'kw':['고집','저력','묵직함'],'health':'위장·비장·소화기 집중 관리  /  토 중복 주의','wealth':'부동산·건설·토지 강세, 장기 보유 전략이 유리'},
    (4,6):  {'kw':['열정','리더십','직선적'],'health':'위장·소화기  /  심장·혈압·체력 소모 주의','wealth':'공직·에너지 기반 강세, 재물 흐름 활발하고 씀씀이도 큼'},
    (4,8):  {'kw':['실용적','분석력','변화적응'],'health':'위장·소화기  /  폐·기관지·호흡기 주의','wealth':'IT·물류·금융 강세, 변화하는 환경에서 기회 빠르게 포착'},
    (4,10): {'kw':['원칙','완고함','인내'],'health':'위장·비장·피부  /  건조증·과로 주의','wealth':'부동산·법조·연구 강세, 오래 쌓은 것이 큰 자산'},
    (5,1):  {'kw':['성실','현실감각','인내'],'health':'위장·비장 집중 관리  /  관절·냉증·소화불량 주의','wealth':'재물 관리 최상, 꾸준한 저축·부동산 축적형'},
    (5,3):  {'kw':['감성','배려','유연성'],'health':'위장·소화기  /  간·담·신경계 피로 주의','wealth':'서비스·교육·예술 기반, 관계에서 수입이 생기는 형'},
    (5,5):  {'kw':['집중력','전략적','현실적'],'health':'위장·소화기  /  심장·혈압·화기 주의','wealth':'금융·사업·전략 기획 강세, 목표 지향적 재물 축적'},
    (5,7):  {'kw':['섬세함','포용력','온화함'],'health':'위장·비장·소화기 집중 관리  /  토 중복 주의','wealth':'안정적 수입 기반, 음식·복지·상담 분야 친화적'},
    (5,9):  {'kw':['정밀함','자존감','완성도'],'health':'위장·소화기  /  폐·대장·피부 주의','wealth':'기술·품질 기반 수입, 완성도가 프리미엄 수익 창출'},
    (5,11): {'kw':['지혜','이상주의','학문'],'health':'위장·소화기  /  신장·방광·호르몬 주의','wealth':'학문·연구·상담 기반, 전문 지식이 최고의 재물 도구'},
    (6,0):  {'kw':['의지','지혜','냉철함'],'health':'폐·대장·기관지  /  신장·방광·부종 주의','wealth':'금융·IT·전략 강세, 지식과 실행력 결합이 큰 성과'},
    (6,2):  {'kw':['카리스마','도전정신','직선적'],'health':'폐·대장·피부  /  간·근육·과로 주의','wealth':'사업·무역·스포츠 강세, 거침없이 도전해 재물 창출'},
    (6,4):  {'kw':['포용력','전문성','저력'],'health':'폐·기관지·피부  /  소화기·관절 주의','wealth':'부동산·기술·법조 강세, 탄탄한 기반 위 꾸준 축적'},
    (6,6):  {'kw':['열정','충동','추진력'],'health':'폐·대장  /  심장·혈압·체력 소모 집중 주의','wealth':'활동적·에너지 기반 강세, 재물 들어오고 나감이 빠른 형'},
    (6,8):  {'kw':['완벽주의','냉철함','독립'],'health':'폐·기관지·피부·뼈 집중 관리  /  금 중복 주의','wealth':'기술·의료·금융 강세, 기준 높아 고수익 지향'},
    (6,10): {'kw':['원칙','고독','전문성'],'health':'폐·대장·피부  /  위장·건조증 주의','wealth':'법률·연구·기술 강세, 한 분야 깊이 파면 큰 수익'},
    (7,1):  {'kw':['섬세함','인내','냉철함'],'health':'폐·대장·피부  /  관절·냉증·소화기 주의','wealth':'재물 관리 탁월, 보석·미용·정밀 기술 강세'},
    (7,3):  {'kw':['예술성','감수성','유연성'],'health':'폐·기관지·피부  /  간·담·눈 피로 주의','wealth':'예술·패션·콘텐츠 기반, 감각이 수익으로 직결'},
    (7,5):  {'kw':['전략적','날카로움','집중력'],'health':'폐·대장·피부  /  심장·혈압·소화기 주의','wealth':'금융·법률·전략 강세, 판단력이 재물의 핵심 무기'},
    (7,7):  {'kw':['온화함','감성','배려'],'health':'폐·기관지·피부  /  소화기·면역 주의','wealth':'서비스·예술·상담 강세, 사람 중심으로 수익 창출'},
    (7,9):  {'kw':['완벽주의','자존심','정밀함'],'health':'폐·대장·뼈·피부 집중 관리  /  금 중복 주의','wealth':'기술·의료·보석 최강, 완성도가 프리미엄 가치'},
    (7,11): {'kw':['지혜','낭만','예술성'],'health':'폐·대장·피부  /  신장·방광·호르몬 주의','wealth':'학문·예술·상담 기반, 전문성과 감성 결합이 수익원'},
    (8,0):  {'kw':['지혜','통찰력','유연성'],'health':'신장·방광·골수 집중 관리  /  수 중복 주의','wealth':'정보·금융·전략 기반, 흐름 읽는 능력이 최고 재테크'},
    (8,2):  {'kw':['활동력','다재다능','도전'],'health':'신장·방광  /  간·근육·과로 주의','wealth':'무역·사업·IT 강세, 활동이 많을수록 수입도 증가'},
    (8,4):  {'kw':['포용력','저력','다양성'],'health':'신장·방광  /  소화기·관절·피부 주의','wealth':'부동산·금융·법조 강세, 내부에 쌓인 자원이 큰 힘'},
    (8,6):  {'kw':['열정','충돌','다이나믹'],'health':'신장·방광  /  심장·혈압·탈수 주의','wealth':'활발한 수입·지출 반복, 재물 흐름이 빠른 역동형'},
    (8,8):  {'kw':['지혜','분석력','변화'],'health':'신장·방광  /  폐·기관지·호흡기 주의','wealth':'IT·금융·전략 강세, 변화 환경에서 수익 기회 포착'},
    (8,10): {'kw':['원칙','고집','깊이'],'health':'신장·방광  /  위장·피부·건조증 주의','wealth':'법조·연구·전문직 강세, 장기 축적으로 노년 자산 탄탄'},
    (9,1):  {'kw':['인내','현실감각','꼼꼼함'],'health':'신장·방광·생식기  /  관절·냉증·소화기 주의','wealth':'재물 관리 탁월, 부동산·금융 장기 축적형'},
    (9,3):  {'kw':['감성','창의','유연성'],'health':'신장·방광  /  간·담·눈·신경 피로 주의','wealth':'예술·콘텐츠·교육 기반, 감성이 수익으로 연결'},
    (9,5):  {'kw':['집중력','신비감','전략적'],'health':'신장·방광·호르몬  /  심장·혈압 주의','wealth':'금융·기획·전략 강세, 조용한 실행으로 큰 성과'},
    (9,7):  {'kw':['감성지능','온화함','배려'],'health':'신장·방광  /  소화기·면역·피로 주의','wealth':'상담·서비스·복지 강세, 진심이 수익을 만드는 형'},
    (9,9):  {'kw':['섬세함','완벽주의','정밀함'],'health':'신장·방광·골수  /  폐·대장·뼈 주의','wealth':'정밀 기술·금융·의료 강세, 완성도 높은 결과물이 고수익'},
    (9,11): {'kw':['지혜','이상주의','내면깊이'],'health':'신장·방광·생식기 집중 관리  /  수 중복 주의','wealth':'학문·철학·상담·예술 기반, 깊은 전문성이 최고 자산'},
}


def _render_ilju_card(name, pillars):
    from saju import _ilju_text
    ilgan = pillars[2][0]
    ilji  = pillars[2][1]
    ilju_name = CHEONGAN[ilgan] + JIJI[ilji]
    extra = _ILJU_EXTRA.get((ilgan, ilji), {})
    base_text = _ilju_text(ilgan, ilji)
    kw_html = ''
    for kw in extra.get('kw', []):
        kw_html += (
            f'<span style="background:#ede9fe;color:#6d28d9;font-size:0.78rem;'
            f'font-weight:700;border-radius:20px;padding:3px 10px;margin:2px 3px;'
            f'display:inline-block;">#{kw}</span>'
        )
    st.markdown(
        f'<div style="font-size:1.05rem;font-weight:800;color:#374151;margin-bottom:6px;">'  
        f'\U0001f4d6 {ilju_name}\uc77c\uc8fc \u2014 {name}\ub2d8\uc758 \ud0c0\uace0\ub09c \ubcf8\uc9c8</div>'
        f'<div style="margin-bottom:8px;">{kw_html}</div>',
        unsafe_allow_html=True,
    )
    health = extra.get('health', '')
    wealth = extra.get('wealth', '')
    if health or wealth:
        col_a, col_b = st.columns(2)
        if health:
            col_a.markdown(
                f'<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;'
                f'padding:10px 14px;">'
                f'<div style="font-size:0.72rem;font-weight:700;color:#dc2626;margin-bottom:4px;">\U0001f33f \uac74\uac15 \ucde8\uc57d \ubd80\uc704</div>'
                f'<div style="font-size:0.85rem;color:#374151;">{health}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        if wealth:
            col_b.markdown(
                f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;'
                f'padding:10px 14px;">'
                f'<div style="font-size:0.72rem;font-weight:700;color:#16a34a;margin-bottom:4px;">\U0001f4b0 \uc7ac\ubb3c \ud328\ud134</div>'
                f'<div style="font-size:0.85rem;color:#374151;">{wealth}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.markdown('')
    if base_text:
        st.markdown(base_text)


def _render_thisyear_section(name, pillars, birth_year, card_id="main", rel_status='솔로', daeun=None):
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
    if daeun:
        _combo = _daeun_sewoon_combo(pillars, daeun, sel_year)
        if _combo:
            st.markdown(_combo)
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
st.caption("v2026.06.08.21")
st.markdown("<hr style='border:none;border-top:1px solid #e8e0f8;margin:12px 0 18px 0;'>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["  🔮  사주 보기  ", "  💕  궁합 보기  ", "  🌸  재회 보기  ", "  📅  일진 달력  ", "  💭  고민 상담  "])

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


# ── 탭 5: 고민 상담 ─────────────────────────────────────────────────────────
with tab5:
    # 사이드바에 API 키 입력
    with st.sidebar:
        st.markdown("---")
        st.markdown(
            '<div style="font-size:0.8rem;font-weight:700;color:#6d28d9;margin-bottom:4px;">💭 고민 상담 설정</div>',
            unsafe_allow_html=True,
        )
        _gkey_in = st.text_input(
            "Gemini API 키",
            value=st.session_state.get("_gemini_api_key", ""),
            type="password",
            key="_gemini_key_input",
            placeholder="AIza...",
            help="aistudio.google.com 에서 무료 발급",
        )
        if _gkey_in:
            st.session_state["_gemini_api_key"] = _gkey_in

    if 'saju_res' not in st.session_state:
        st.info("먼저 🔮 사주 보기 탭에서 사주를 분석해주세요.")
    else:
        r5 = st.session_state['saju_res']
        n5 = r5['name']
        cur5 = datetime.now(_KST).year

        st.markdown(
            f'<div style="font-size:1.1rem;font-weight:800;color:#6d28d9;margin-bottom:2px;">💭 {n5}님 사주 기반 고민 상담</div>',
            unsafe_allow_html=True,
        )
        st.caption("사주 데이터를 자동으로 불러와 Gemini AI가 맞춤 답변을 드려요.")

        # 연도 선택
        _cy5 = st.select_slider(
            "기준 연도",
            options=list(range(cur5 - 2, cur5 + 6)),
            value=cur5,
            key="concern_year_sel",
        )

        # 사주 컨텍스트 미리보기
        _ctx5 = _build_saju_ctx(r5, _cy5)
        with st.expander(f"📋 {n5}님 사주 정보 (AI에게 전달되는 내용)", expanded=False):
            st.code(_ctx5, language=None)

        # API 키 없으면 안내
        _has_key = st.session_state.get("_gemini_api_key", "")
        try:
            _has_key = _has_key or st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
        if not _has_key:
            import os, re as _re2
            _sp2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.streamlit', 'secrets.toml')
            try:
                with open(_sp2, 'r', encoding='utf-8') as _f2:
                    _m2 = _re2.search(r'^GEMINI_API_KEY\s*=\s*"([^"]+)"', _f2.read(), _re2.MULTILINE)
                if _m2:
                    _has_key = _m2.group(1)
            except Exception:
                pass
        if not _has_key:
            st.warning("사이드바에 Gemini API 키를 입력하면 상담이 시작돼요.\n\n👉 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 무료 발급 (구글 계정 필요)")

        # 채팅 히스토리
        _hist_key = f"concern_hist_{n5}"
        if _hist_key not in st.session_state:
            st.session_state[_hist_key] = []

        for _msg5 in st.session_state[_hist_key]:
            with st.chat_message(_msg5['role']):
                st.markdown(_msg5['content'])

        if _concern5 := st.chat_input(f"{n5}님의 고민을 입력하세요... (예: 이직 제안받았어요, 투자해도 될까요?)"):
            st.session_state[_hist_key].append({'role': 'user', 'content': _concern5})
            with st.chat_message('user'):
                st.markdown(_concern5)
            with st.chat_message('assistant'):
                with st.spinner('사주를 풀어드리는 중...'):
                    _ans5 = _ask_gemini(_concern5, _ctx5, history=st.session_state[_hist_key])
                st.markdown(_ans5)
            st.session_state[_hist_key].append({'role': 'assistant', 'content': _ans5})

        if st.session_state.get(_hist_key):
            if st.button("🗑️ 대화 초기화", key="clear_concern_hist"):
                st.session_state[_hist_key] = []
                st.rerun()
