import streamlit as st
import plotly.graph_objects as go
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
    analyze_ohaeng, analyze_ohaeng_strength, get_gongmang,
    get_12unsung, get_sipseong,
    CHEONGAN, JIJI, OHAENG_G, OHAENG_J, ANIMALS,
    JIJANGAN, JIJANGAN_IDX, OHAENG_IDX, OHAENG_IDX_J,
    _SAL_DESC, _SAL_MODERN, _SEWOON_SS_DESC, _sewoon_ss,
    OHAENG_NAMES,
    get_ilchin, get_yongki, analyze_ilchin_basic, analyze_ilchin_day, explain_yongshin,
    analyze_romantic_type, judge_strength, get_strength_detail,
    get_gyeokguk, get_yongshin, _year_pillar, get_gyeok_clarity, get_cheongan_hwa, get_sangshin, get_johu_desc, get_job_aptitude, get_jiji_hyeong,
    YUKAHP, CHUNG as JIJI_CHUNG, _CHUNGAN_HAP, SAMHAP, _BANGHAP, HYEONG_3,
)

_JIJI_EMOJI = ['🐀','🐄','🐅','🐇','🐉','🐍','🐎','🐑','🐒','🐓','🐕','🐗']

# 납음오행: 30종 (g//2*6 + j//2) % 30 인덱스
# 튜플: (한글명, 한자명, 오행, 짧은설명, 풀이)
_NAEUM = [
    ('해중금','海中金','금','바다 속에 숨겨진 귀한 금',
     '겉으로는 조용하고 내성적이지만 속에 단단한 의지와 재능을 품고 있어요. 인내심이 강하고 기회가 왔을 때 한 번에 빛을 발하는 스타일이에요. 조급함을 버리고 때를 기다리는 것이 이 기운의 가장 큰 강점이에요.'),
    ('노중화','爐中火','화','화로 속에서 단련되는 불',
     '역경 속에서 더욱 강해지는 기질이에요. 열정적이고 추진력이 강하며 한 번 결심하면 끝까지 밀어붙여요. 충동적인 면도 있지만 그 에너지가 창조의 원동력이 돼요. 감정을 다스리는 연습이 삶을 더 풍요롭게 만들어줘요.'),
    ('대림목','大林木','목','큰 숲을 이루는 웅장한 나무',
     '포용력과 리더십이 강하고 사람들이 자연스럽게 모여드는 매력이 있어요. 계획적이고 체계적이며 장기적 목표를 향해 꾸준히 성장해요. 혼자보다 함께할 때 더 큰 성과를 내는 타입이에요.'),
    ('노방토','路傍土','토','길가에 밟히는 친근한 흙',
     '실용적이고 현실적이며 어떤 환경에도 잘 적응해요. 봉사 정신이 강하고 주변 사람들을 편안하게 만드는 능력이 있어요. 모든 발길을 묵묵히 받아들이는 인내심이 강점이지만, 스스로를 챙기는 것도 잊지 마세요.'),
    ('검봉금','劍鋒金','금','칼날처럼 예리한 금',
     '결단력이 강하고 핵심을 꿰뚫어 보는 직관이 탁월해요. 완벽주의적 성향이 있어 기준이 높지만 그만큼 성취도도 높아요. 날카로움이 대인관계에서 마찰이 되지 않도록 부드러움을 함께 기르는 것이 중요해요.'),
    ('산두화','山頭火','화','산꼭대기를 밝히는 봉화',
     '카리스마가 강하고 존재감이 뚜렷하며 주도적으로 이끄는 능력이 있어요. 어두운 상황에서도 빛을 발하는 타입이에요. 혼자 너무 많은 것을 지려는 경향이 있으니 적절한 위임과 쉬어감이 필요해요.'),
    ('간하수','澗下水','수','계곡을 흐르는 맑은 물',
     '청정하고 지혜로운 기질로 직관력과 통찰력이 뛰어나요. 고요한 가운데 깊이가 있고 말보다 행동으로 신뢰를 쌓아요. 감정이 풍부한 만큼 스트레스 관리와 감정 표현의 균형이 중요해요.'),
    ('성두토','城頭土','토','성벽을 이루는 견고한 흙',
     '책임감이 강하고 신뢰할 수 있으며 가족과 주변을 지키는 데서 보람을 느껴요. 변화보다 안정을 선호하지만 그 기반 위에서 꾸준히 성장해요. 지나친 고집은 유연성을 잃게 할 수 있으니 주의하세요.'),
    ('백랍금','白蠟金','금','흰 납처럼 부드러운 금',
     '세련된 감각과 유연한 사고로 다양한 환경에서 빛을 발해요. 예술적 감각이 풍부하고 사교적이에요. 어떤 모양으로도 변할 수 있는 적응력이 강점이지만, 자신만의 중심을 단단히 잡는 것이 중요해요.'),
    ('양류목','楊柳木','목','버들처럼 유연한 나무',
     '강하게 밀어붙이기보다 부드러운 방식으로 상황을 이끌어가는 스타일이에요. 바람에 흔들려도 뿌리를 잃지 않는 내면의 단단함이 있어요. 적응력과 포용력이 뛰어나고, 흔들리는 것처럼 보여도 속은 단단한 사람이에요.'),
    ('천중수','泉中水','수','깊은 샘에서 솟는 물',
     '내면에서 아이디어와 에너지가 끊임없이 솟아나는 창의적 기질이에요. 고요한 곳에서 가장 빛을 발하고, 겉으로는 조용해도 내면에서는 끊임없이 성장해요. 지속력과 깊이가 이 기운의 핵심 강점이에요.'),
    ('옥상토','屋上土','토','지붕 위의 흙',
     '이상이 높고 명예를 중시하며 사회적 위치에 신경을 써요. 높은 곳에 있지만 흔들리기 쉬운 불안정함도 함께 있어요. 현실적 토대를 단단히 하는 것과 실패를 받아들이는 유연함이 이 사람의 핵심 과제예요.'),
    ('벽력화','霹靂火','화','천둥번개처럼 강렬한 불',
     '순간적이고 강렬한 에너지로 임팩트 있는 결과를 만들어내요. 직관이 뛰어나고 결정이 빠르며 혁신적인 아이디어가 강점이에요. 충동성을 다스리면 가장 강한 무기가 되는 기운이에요.'),
    ('송백목','松柏木','목','소나무처럼 강인한 나무',
     '원칙을 지키고 의리가 있으며 어려운 환경에서도 흔들리지 않아요. 외유내강형으로 겉은 부드럽지만 속은 단단해요. 고집스러울 때도 있지만 그 신념이 주변의 신뢰를 만들어줘요.'),
    ('장류수','長流水','수','멀리 흐르는 긴 강물',
     '긴 호흡으로 목표를 향해 나아가는 기질이에요. 방향이 정해지면 멈추지 않는 인내심이 강점이에요. 여러 분야를 넘나들며 경험을 쌓고, 성급함보다 꾸준함이 이 사람의 최고 무기예요.'),
    ('사중금','沙中金','금','모래 속에 묻힌 금',
     '노력과 시간이 쌓이면 진가가 드러나는 기질이에요. 겉으로는 평범해 보여도 내면에 뚜렷한 가치와 재능을 품고 있어요. 한 번 인정받으면 확고해지지만, 조급함을 내려놓는 것이 가장 중요해요.'),
    ('산하화','山下火','화','산 아래 꺼져가는 불',
     '드러내지 않고 조용히 주변을 돌보는 헌신적인 성향이에요. 잔잔하지만 온기로 주변을 따뜻하게 하는 기질이에요. 감정을 표현하는 데 서툴지만 진심이 깊어요. 자신의 온기가 소진되지 않도록 스스로를 챙기세요.'),
    ('평지목','平地木','목','평지에서 자라는 나무',
     '안정적 환경에서 꾸준히 성장하는 실용적이고 현실적인 기질이에요. 화려하지 않지만 믿음직스러운 사람으로 인정받아요. 때로는 도전과 변화를 의식적으로 만들어야 성장이 더 빨라져요.'),
    ('벽상토','壁上土','토','벽 위의 불안정한 흙',
     '민감하고 감수성이 풍부하며 예술적 감각이 뛰어나요. 변화와 적응이 많은 삶을 살지만 그 불안정함이 창의성의 원천이 되기도 해요. 심리적 안정망을 만드는 것이 이 기운의 평생 과제예요.'),
    ('금박금','金箔金','금','얇은 금박처럼 화려한 금',
     '미적 감각이 뛰어나고 사람들에게 첫인상이 강하게 남아요. 화려하고 세련된 기질이지만 내면의 깊이도 단단히 채워야 오래 빛날 수 있어요. 자신의 가치를 포장보다 실력으로 증명하는 연습이 필요해요.'),
    ('복등화','覆燈火','화','엎어진 등불, 꺼지기 직전',
     '역경 속에서 더 강해지고 끝날 것 같은 상황에서도 반전을 만들어내는 저력이 있어요. 드라마틱한 삶의 굴곡이 많지만 그 과정에서 내면이 깊어져요. 감정 소진에 주의하고 꺼지지 않도록 충전의 시간을 챙기세요.'),
    ('천하수','天河水','수','하늘의 은하수',
     '틀에 얽매이지 않고 자신만의 세계를 구축하는 독창성이 강해요. 이상이 높고 꿈이 크지만 현실과의 접지점을 찾는 것이 과제예요. 광활한 상상력이 가장 큰 자산이에요.'),
    ('대역토','大驛土','토','큰 역참의 활동적인 흙',
     '사교성이 뛰어나고 네트워크를 만드는 능력이 강해요. 사람과 정보가 모여드는 활동적인 기질이에요. 바쁘게 움직이는 것이 체질에 맞지만, 중심을 잃지 않고 진짜 깊은 관계를 선별하는 지혜도 필요해요.'),
    ('차천금','釵釧金','금','비녀·팔찌처럼 세련된 금',
     '미적 감각과 우아함이 뛰어나고 사람들에게 매력적으로 보여요. 실용성과 아름다움을 동시에 추구하는 성향으로 예술·패션·디자인 분야에서 빛을 발해요. 겉모습만큼 내실을 쌓는 것이 중요해요.'),
    ('상자목','桑柘木','목','뽕나무처럼 실용적인 나무',
     '현실적이고 손재주가 있으며 주변에 도움이 되는 기질이에요. 화려하지 않지만 없어서는 안 될 사람이에요. 누군가에게 필요한 존재가 되는 것에서 보람을 찾지만, 스스로의 가치를 더 당당하게 표현하는 연습도 필요해요.'),
    ('대계수','大溪水','수','큰 계곡의 풍부한 물',
     '에너지가 넘치고 다양한 경험을 두려워하지 않아요. 감수성이 풍부하고 변화 속에서 성장하는 역동적인 기질이에요. 에너지를 한 방향으로 모아 집중하는 것이 성과를 높이는 핵심이에요.'),
    ('사중토','沙中土','토','모래 속의 유연한 흙',
     '어느 환경에서나 자기 자리를 찾는 적응력이 뛰어나요. 겉으로는 흩어진 것 같아도 내면에는 단단한 중심이 있어요. 경계를 명확히 하는 것이 스스로를 지키고 성장하는 방법이에요.'),
    ('천상화','天上火','화','태양처럼 강렬한 하늘의 불',
     '카리스마가 넘치고 어디서나 존재감이 빛나요. 열정과 에너지가 강해 주변을 환하게 밝히지만 그만큼 소진되기 쉬워요. 자신의 빛을 나눠주면서도 꺼지지 않도록 충전의 시간을 반드시 챙기세요.'),
    ('석류목','石榴木','목','석류나무처럼 단단한 나무',
     '겉은 강하고 신중하지만 내면에는 풍부한 감정과 재능을 품고 있어요. 천천히 신뢰를 쌓고 한 번 믿으면 끝까지 가는 의리가 있어요. 마음을 여는 데 시간이 걸리지만 그만큼 깊고 진한 관계를 만들어요.'),
    ('대해수','大海水','수','드넓은 대해의 물',
     '모든 것을 받아들이는 너그러움과 광대한 시각이 강점이에요. 큰 그림을 보는 능력이 뛰어나지만 작은 일에 소홀해지기 쉬워요. 세부 사항을 챙기는 습관이 이 기운의 잠재력을 더 완성시켜줘요.'),
]
_NAEUM_CLR = {'목':'#15803d','화':'#dc2626','토':'#b45309','금':'#4b5563','수':'#1d4ed8'}

def _get_naeum(g, j):
    idx = (j + 12 * (((g - j) // 2) % 5)) // 2 % 30
    return _NAEUM[idx]  # (한글명, 한자명, 오행, 설명)

def _get_pillar_relations(pillars, no_time=False):
    order = [2, 1, 0] if no_time else [3, 2, 1, 0]
    hdrs  = ['일', '월', '년'] if no_time else ['시', '일', '월', '년']
    chips = []
    for i in range(len(order) - 1):
        pi, pj = order[i], order[i+1]
        g1, j1 = pillars[pi]
        g2, j2 = pillars[pj]
        pair = hdrs[i] + hdrs[i+1]
        fs_g = frozenset({g1, g2})
        if fs_g in _CHUNGAN_HAP:
            chips.append(('천간합', f'{pair}주 {_CHUNGAN_HAP[fs_g]}', '#065f46', '#d1fae5', '#34d399'))
        fs_j = frozenset({j1, j2})
        for cs in JIJI_CHUNG:
            if fs_j == cs:
                chips.append(('지지충', f'{pair}주 {JIJI[j1]}{JIJI[j2]}충', '#991b1b', '#fee2e2', '#fca5a5'))
                break
        if fs_j in YUKAHP:
            chips.append(('육합', f'{pair}주 {YUKAHP[fs_j]}', '#1e40af', '#dbeafe', '#93c5fd'))
    all_j = {pillars[i][1] for i in order}
    for fs, nm in SAMHAP:
        if fs.issubset(all_j):
            chips.append(('삼합', nm, '#6d28d9', '#ede9fe', '#c4b5fd'))
    for fs, nm in _BANGHAP:
        if fs.issubset(all_j):
            chips.append(('방합', nm, '#0369a1', '#e0f2fe', '#7dd3fc'))
    for fs, nm in HYEONG_3:
        if len(fs & all_j) >= 2:
            chips.append(('형', nm, '#9d174d', '#fce7f3', '#f9a8d4'))
    return chips


_TERM_TIPS = {
    # 십성
    '일간': '사주에서 나 자신을 나타내는 핵심 천간',
    '비견': '같은 오행·음양 → 자립심, 자존감, 경쟁',
    '겁재': '같은 오행·반대 음양 → 강한 의욕, 충동, 경쟁심',
    '식신': '일간이 생하는 같은 음양 → 창의력, 표현, 복록',
    '상관': '일간이 생하는 반대 음양 → 표현 욕구, 변화, 관성 극',
    '편재': '일간이 극하는 같은 음양 → 재물, 아버지, 여명의 남편',
    '정재': '일간이 극하는 반대 음양 → 정직한 수입, 절약, 내조',
    '편관': '일간을 극하는 같은 음양 → 권력, 도전, 칠살(七殺)',
    '정관': '일간을 극하는 반대 음양 → 명예, 법, 직장, 여명의 남편',
    '편인': '일간을 생하는 같은 음양 → 학문, 종교, 편협, 도식(倒食)',
    '정인': '일간을 생하는 반대 음양 → 어머니, 학업, 자격증',
    # 십이운성
    '장생': '장생(長生) — 새로운 시작, 성장의 에너지',
    '목욕': '목욕(沐浴) — 감성과 욕망이 강한 매력적 에너지',
    '관대': '관대(冠帶) — 자립을 시작하는 성인식 에너지',
    '건록': '건록(建祿) — 자립·직업·자수성가의 에너지',
    '제왕': '제왕(帝旺) — 가장 강한 전성기의 에너지',
    '쇠':   '쇠(衰) — 한 고비 넘긴 성숙한 에너지',
    '병':   '병(病) — 힘이 빠지며 쉬는 에너지',
    '사':   '사(死) — 오행이 소멸하는 에너지',
    '묘':   '묘(墓) — 창고처럼 보존되는 에너지',
    '절':   '절(絶) — 완전히 소멸, 새 시작 전 에너지',
    '태':   '태(胎) — 잉태처럼 가능성만 있는 에너지',
    '양':   '양(養) — 성장 준비 중인 에너지',
    # 오행
    '목': '목(木) — 봄, 성장, 인(仁), 간·담',
    '화': '화(火) — 여름, 열정, 예(禮), 심장',
    '토': '토(土) — 환절기, 중재, 신(信), 비위',
    '금': '금(金) — 가을, 결단, 의(義), 폐·대장',
    '수': '수(水) — 겨울, 지혜, 지(智), 신장·방광',
    # 합충파해형
    '합':   '합(合) — 두 기운이 결합해 새 오행이 됨. 협력·조화',
    '충':   '충(沖) — 정반대 기운이 충돌. 변화·이동·갈등',
    '파':   '파(破) — 기운이 깨짐. 어긋남·틀어짐',
    '해':   '해(害) — 기운이 서로 해침. 방해·손상',
    '형':   '형(刑) — 기운이 불화. 법적 갈등, 반면 강인함도 키움',
    '공망': '공망(空亡) — 기운이 공백인 상태. 실속 없거나 허무함',
    # 기타
    '신강': '신강(身强) — 일간 세력이 강한 사주. 용신은 극설(克洩)하는 오행',
    '신약': '신약(身弱) — 일간 세력이 약한 사주. 용신은 생부(生扶)하는 오행',
    '중화': '중화(中和) — 일간 세력이 균형을 이룬 사주',
    '용신': '용신(用神) — 사주를 균형 잡아주는 핵심 오행. 이 오행이 강한 시기가 길운',
    '기신': '기신(忌神) — 사주를 해치는 오행. 이 오행이 강한 시기에 주의 필요',
    '대운': '대운(大運) — 10년 단위의 큰 흐름',
    '세운': '세운(歲運) — 1년 단위의 흐름, 그 해의 기운',
    '월운': '월운(月運) — 1달 단위의 흐름',
}

# 천간극(天干剋) — 합·충이 아닌 순수 상극 관계만 포함
# key: frozenset([천간인덱스A, 천간인덱스B])  value: (이름, 오행관계, 설명)
_CHUNGAN_KEUK = {
    frozenset([0, 4]): ('갑무극(甲戊剋)', '목극토', '강한 추진력이 안정과 기반을 흔드는 구조. 실행 과정에서 현실 장벽과 마찰이 생기기 쉬워요.'),
    frozenset([1, 4]): ('을무극(乙戊剋)', '목극토', '부드러운 노력이 현실 장벽에 반복적으로 부딪히는 구조예요.'),
    frozenset([1, 5]): ('을기극(乙己剋)', '목극토', '섬세한 감각이 규범·현실과 충돌해 정신적 갈등이 쌓이기 쉬운 구조예요.'),
    frozenset([2, 6]): ('병경극(丙庚剋)', '화극금', '열정과 감성이 결단력·원칙과 부딪히는 구조. 강한 두 에너지가 충돌해요.'),
    frozenset([3, 6]): ('정경극(丁庚剋)', '화극금', '따뜻한 감수성이 냉철한 원칙에 억눌리기 쉬운 구조예요.'),
    frozenset([3, 7]): ('정신극(丁辛剋)', '화극금', '감성과 예민함이 서로 자극하며 정서적 긴장이 만들어지는 구조예요.'),
    frozenset([4, 8]): ('무임극(戊壬剋)', '토극수', '현실·규범이 직관과 이상을 가로막는 구조. 답답함이 쌓이기 쉬워요.'),
    frozenset([5, 8]): ('기임극(己壬剋)', '토극수', '현실 감각이 이상과 충돌해 실현이 어렵게 느껴지는 구조예요.'),
    frozenset([5, 9]): ('기계극(己癸剋)', '토극수', '규범·현실이 직관과 감수성을 억압하는 구조. 정신적 중압감과 스트레스가 쌓이기 쉬워요.'),
    frozenset([6, 1]): ('경을극(庚乙剋)', '금극목', '단호한 압박이 부드러운 성장을 위축시키는 구조예요.'),
    frozenset([0, 7]): ('신갑극(辛甲剋)', '금극목', '날카로운 판단이 추진력을 억누르는 구조. 실행에 제약이 반복되기 쉬워요.'),
    frozenset([2, 9]): ('계병극(癸丙剋)', '수극화', '냉철한 현실 감각이 열정과 표현력을 식히는 구조예요.'),
}

def _find_cheongan_keuk(pillars):
    gans = [pillars[i][0] for i in range(len(pillars))]
    found = []
    for ii in range(len(gans)):
        for jj in range(ii + 1, len(gans)):
            fs = frozenset([gans[ii], gans[jj]])
            if fs in _CHUNGAN_KEUK:
                found.append(_CHUNGAN_KEUK[fs])
    return found

def _tip(term: str) -> str:
    if term in _TERM_TIPS:
        return (
            f'<abbr title="{_TERM_TIPS[term]}" '
            f'style="text-decoration:underline dotted #9c7dda88; cursor:help; font-style:normal;">'
            f'{term}</abbr>'
        )
    return term

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
        st.caption("v2026.06.10.19")


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
    _pt_hwa_changed, _ = get_cheongan_hwa(pillars)

    _OH_BG     = {'목':'#bbf7d0','화':'#fecaca','토':'#fde68a','금':'#e2e8f0','수':'#bfdbfe'}
    _OH_BORDER = {'목':'#4ade80','화':'#f87171','토':'#fbbf24','금':'#94a3b8','수':'#60a5fa'}
    _OH_DIV    = {'목':'#86efac','화':'#fca5a5','토':'#fde68a','금':'#cbd5e1','수':'#93c5fd'}
    _TXT_MAIN  = '#111827'   # 큰 글자 (천간·지지)
    _TXT_SUB   = '#374151'   # 작은 설명 텍스트

    def _ss_g(i):
        g = pillars[i][0]
        return '일간' if i == 2 else get_sipseong(ilgan, OHAENG_IDX[g], g % 2)

    cols_html = ''
    for i, hdr, sub in zip(order, hdrs, subs):
        g, j    = pillars[i][0], pillars[i][1]
        oh_g    = OHAENG_NAMES[OHAENG_IDX[g]]
        oh_j    = OHAENG_NAMES[OHAENG_IDX_J[j]]
        _is_hwa = i in _pt_hwa_changed
        oh_g_disp = OHAENG_NAMES[_pt_hwa_changed[i]] if _is_hwa else oh_g
        bg      = _OH_BG.get(oh_g_disp, '#f1f5f9')
        bdc     = _OH_BORDER.get(oh_g_disp, '#cbd5e1')
        div_c   = _OH_DIV.get(oh_g_disp, '#e2e8f0')
        bg_j    = _OH_BG.get(oh_j, '#f1f5f9')
        bdc_j   = _OH_BORDER.get(oh_j, '#cbd5e1')
        is_ilju = (i == 2)
        border  = f'2px solid {bdc}' if is_ilju else f'1px solid {bdc}'
        shadow  = '0 2px 14px rgba(0,0,0,0.12)' if is_ilju else '0 1px 4px rgba(0,0,0,0.06)'
        ss_g    = _ss_g(i)
        ss_j    = get_sipseong(ilgan, OHAENG_IDX_J[j], j % 2)
        unsung  = get_12unsung(ilgan, j)
        jijg    = ' '.join(JIJANGAN[j])
        _nm     = _get_naeum(g, j)
        _nm_clr = _NAEUM_CLR.get(_nm[2], '#374151')
        gm_tag  = '<span style="font-size:0.6rem;background:rgba(255,100,100,0.25);color:#dc2626;border-radius:4px;padding:1px 5px;margin-left:3px;">공망</span>' if j in gm else ''
        _UNS_IC = {'장생':'🌱','목욕':'✨','관대':'🎓','건록':'💼','제왕':'👑',
                   '쇠':'🍃','병':'🌙','사':'🕊','묘':'🌿','절':'🌊','태':'🌸','양':'🌼'}
        _UNS_CL = {'장생':'#16a34a','목욕':'#7c3aed','관대':'#1d4ed8','건록':'#0369a1','제왕':'#dc2626',
                   '쇠':'#92400e','병':'#4b5563','사':'#374151','묘':'#065f46','절':'#1e40af','태':'#9333ea','양':'#d97706'}
        uns_icon = _UNS_IC.get(unsung, '')
        uns_clr  = _UNS_CL.get(unsung, _TXT_SUB)

        cols_html += f'''
        <div style="flex:1;min-width:0;padding:0 5px;">
          <div style="border:{border};border-radius:12px;overflow:hidden;
                      text-align:center;box-shadow:{shadow};height:100%;">
            <div style="background:{bg};padding:10px 8px 8px;">
              <div style="font-size:0.68rem;color:{_TXT_SUB};margin-bottom:6px;letter-spacing:0.05em;font-weight:700;">
                {hdr}<span style="opacity:0.6;font-size:0.6rem;">({sub})</span>
              </div>
              <div style="font-size:2rem;font-weight:800;color:{_TXT_MAIN};line-height:1;">
                {CHEONGAN[g]}
              </div>
              {'<div style="font-size:0.58rem;color:#86198f;font-weight:700;margin-top:1px;">⚗️합화→' + oh_g_disp + '</div>' if _is_hwa else ''}
              <div style="font-size:0.65rem;color:{_TXT_SUB};margin:2px 0 0;">{_tip(oh_g_disp)} · {_tip(ss_g)}</div>
            </div>
            <div style="background:{bg_j};padding:8px 8px 10px;border-top:1px solid {bdc_j};">
              <div style="font-size:1.6rem;line-height:1;">{_JIJI_EMOJI[j]}</div>
              <div style="font-size:1.4rem;font-weight:700;color:{_TXT_MAIN};line-height:1.1;">{JIJI[j]}{gm_tag}</div>
              <div style="font-size:0.65rem;color:{_TXT_SUB};margin-top:3px;">{_tip(oh_j)} · {_tip(ss_j)}</div>
              <div style="margin-top:6px;border-top:1px solid {bdc_j};padding-top:5px;">
                <div style="font-size:0.64rem;color:{uns_clr};font-weight:700;margin-bottom:2px;">{uns_icon} {_tip(unsung)}</div>
                <div style="font-size:0.6rem;color:{_TXT_SUB};opacity:0.8;letter-spacing:0.03em;">{jijg}</div>
                <div style="font-size:0.6rem;color:{_nm_clr};font-weight:600;margin-top:3px;">{_nm[1]}</div>
              </div>
            </div>
          </div>
        </div>'''

    _pillar_html = (
        f'<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">'
        f'<div style="display:flex;gap:0;width:100%;align-items:stretch;">'
        f'{cols_html}</div></div>'
    )
    try:
        st.html(_pillar_html)
    except AttributeError:
        st.markdown(_pillar_html, unsafe_allow_html=True)
    _rel_chips = _get_pillar_relations(pillars, no_time=no_time)
    if _rel_chips:
        _rel_html = '<div style="display:flex;flex-wrap:wrap;gap:5px;margin:6px 0 2px;">'
        for _rtag, _rnm, _rtc, _rbg, _rbd in _rel_chips:
            _rel_html += (
                f'<span style="background:{_rbg};border:1px solid {_rbd};color:{_rtc};'
                f'padding:2px 10px;border-radius:10px;font-size:0.72rem;font-weight:700;">'
                f'{_rtag} {_rnm}</span>'
            )
        _rel_html += '</div>'
        try:
            st.html(_rel_html)
        except AttributeError:
            st.markdown(_rel_html, unsafe_allow_html=True)


def _check_gyeok_success(pillars):
    gyeok_name, yong_oh, _ = get_gyeokguk(pillars)
    mj    = pillars[1][1]
    jijis = [p[1] for p in pillars]
    CHUNG_J = {0:6,1:7,2:8,3:9,4:10,5:11,6:0,7:1,8:2,9:3,10:4,11:5}
    pillar_nm = ['년','월','일','시']
    mj_chung = CHUNG_J[mj]
    if mj_chung in jijis:
        pos = pillar_nm[jijis.index(mj_chung)]
        return '패격', f'월지 {JIJI[mj]}가 {pos}지 {JIJI[mj_chung]}와 충(沖) — 격이 흔들림'
    oa = analyze_ohaeng(pillars)
    yong_nm  = OHAENG_NAMES[yong_oh]
    enemy_oh = (yong_oh + 3) % 5
    enemy_nm = OHAENG_NAMES[enemy_oh]
    if oa.get(yong_nm, 0) == 0 and oa.get(enemy_nm, 0) >= 2:
        return '패격', f'용신({yong_nm})이 없고 {enemy_nm}이 강해 격이 손상됨'
    return '성격', f'{gyeok_name} 구조가 온전히 성립됨'


def _make_saju_summary(name, pillars, corr_dt, gender, no_time=False, cal_label="양력") -> str:
    ilgan = pillars[2][0]
    dt_str = corr_dt.strftime('%Y년 %m월 %d일')
    if not no_time:
        dt_str += corr_dt.strftime(' %H시 %M분')

    strength    = judge_strength(pillars)
    gyeok_name, _, ki_list = get_gyeokguk(pillars)
    _, ya_name, _, _, _    = get_yongshin(pillars)
    ki_names    = [OHAENG_NAMES[k] for k in ki_list]
    oa          = analyze_ohaeng(pillars)
    gm          = get_gongmang(*pillars[2])
    gil, hyung  = check_sal(pillars)

    order = [2, 1, 0] if no_time else [3, 2, 1, 0]
    hdrs  = ['일주', '월주', '년주'] if no_time else ['시주', '일주', '월주', '년주']

    sep = '━' * 38
    lines = [sep, f'  {name}님의 사주팔자 분석', sep, '']
    lines += [f'생년월일: {dt_str} ({cal_label})', f'성별:     {gender}', '']

    lines.append('─── 사주 기둥 ───')
    lines.append('  ' + '   '.join(f'[{h}]' for h in hdrs))
    lines.append('  ' + '   '.join(f' {CHEONGAN[pillars[i][0]]}{JIJI[pillars[i][1]]} ' for i in order))
    lines.append('')

    lines.append('─── 십성 · 십이운성 ───')
    for i, hdr in zip(order, hdrs):
        g, j = pillars[i]
        ss_g = '일간' if i == 2 else get_sipseong(ilgan, OHAENG_IDX[g], g % 2)
        ss_j = get_sipseong(ilgan, OHAENG_IDX_J[j], j % 2)
        unsung = get_12unsung(ilgan, j)
        lines.append(f'  {hdr}: 천간 {ss_g} / 지지 {ss_j} / {unsung}')
    lines.append('')

    lines.append('─── 오행 분포 ───')
    oh_str = '  '.join(f'{k} {v}개' for k, v in oa.items() if v)
    lines.append(f'  {oh_str}')
    lines.append('')

    lines.append('─── 핵심 정보 ───')
    lines += [
        f'  신강/신약: {strength}',
        f'  格局:      {gyeok_name}',
        f'  용신(用神): {ya_name}',
        f'  기신(忌神): {", ".join(ki_names) if ki_names else "없음"}',
    ]
    if gm:
        lines.append(f'  공망(空亡): {"·".join(JIJI[x] for x in sorted(gm))}')
    lines.append('')

    if gil:
        lines.append('─── 길신(吉神) ───')
        lines.extend(f'  · {g}' for g in gil)
        lines.append('')
    if hyung:
        lines.append('─── 흉신(凶神) ───')
        lines.extend(f'  · {h}' for h in hyung)
        lines.append('')

    today = datetime.now(_KST).strftime('%Y-%m-%d')
    lines += [sep, f'  생성: {today}  |  사주팔자 앱 v2026.06.10.19', sep]
    return '\n'.join(lines)



def _make_saju_html(name, pillars, corr_dt, gender, no_time=False, cal_label="양력") -> str:
    ilgan   = pillars[2][0]
    dt_str  = corr_dt.strftime('%Y년 %m월 %d일')
    if not no_time:
        dt_str += corr_dt.strftime(' %H시 %M분')

    strength        = judge_strength(pillars)
    gyeok_name, _, ki_list = get_gyeokguk(pillars)
    _, ya_name, _, _, _    = get_yongshin(pillars)
    ki_names        = [OHAENG_NAMES[k] for k in ki_list]
    oa              = analyze_ohaeng(pillars)
    gm              = get_gongmang(*pillars[2])
    gil, hyung      = check_sal(pillars)
    today           = datetime.now(_KST).strftime('%Y-%m-%d')

    order = [2, 1, 0] if no_time else [3, 2, 1, 0]
    hdrs  = ['일주', '월주', '년주'] if no_time else ['시주', '일주', '월주', '년주']

    _OH_CLR    = {'목': '#16a34a', '화': '#dc2626', '토': '#b45309', '금': '#475569', '수': '#1d4ed8'}
    _NM_CLR    = {'목': '#15803d', '화': '#dc2626', '토': '#b45309', '금': '#4b5563', '수': '#1d4ed8'}

    # 기둥 카드
    col_cards = ''
    for idx, hdr in zip(order, hdrs):
        g, j    = pillars[idx]
        ss_g    = '일간' if idx == 2 else get_sipseong(ilgan, OHAENG_IDX[g], g % 2)
        ss_j    = get_sipseong(ilgan, OHAENG_IDX_J[j], j % 2)
        unsung  = get_12unsung(ilgan, j)
        nm      = _get_naeum(g, j)
        nm_clr  = _NM_CLR.get(nm[2], '#374151')
        jijg    = ' '.join(JIJANGAN[j])
        gm_mark = ' ⬛' if j in gm else ''
        g_clr   = _OH_CLR.get(OHAENG_G[g], '#374151')
        j_clr   = _OH_CLR.get(OHAENG_J[j], '#374151')
        is_il   = (idx == 2)
        bg  = 'linear-gradient(135deg,#fdf4ff,#ede9fe)' if is_il else '#f8fafc'
        bd  = '2px solid #8b5cf6' if is_il else '1px solid #e2e8f0'
        col_cards += (
            '<div style="flex:1;min-width:0;border:' + bd + ';border-radius:12px;'
            'background:' + bg + ';padding:12px 8px;text-align:center;">'
            '<div style="font-size:0.7rem;font-weight:700;color:#6b7280;margin-bottom:6px;">' + hdr + '</div>'
            '<div style="font-size:2rem;font-weight:900;letter-spacing:0.05em;">'
            '<span style="color:' + g_clr + ';">' + CHEONGAN[g] + '</span>'
            '<span style="color:' + j_clr + ';">' + JIJI[j] + gm_mark + '</span></div>'
            '<div style="font-size:0.7rem;color:#6b7280;margin:4px 0 2px;">'
            + OHAENG_G[g] + '(' + ss_g + ') / ' + OHAENG_J[j] + '(' + ss_j + ')</div>'
            '<div style="font-size:0.65rem;color:#9ca3af;">' + unsung + '</div>'
            '<div style="font-size:0.65rem;color:#9ca3af;margin-top:2px;">' + jijg + '</div>'
            '<div style="font-size:0.65rem;color:' + nm_clr + ';font-weight:600;margin-top:3px;">' + nm[1] + '</div>'
            + ('<div style="font-size:0.6rem;color:#6b7280;margin-top:4px;line-height:1.5;text-align:left;padding:4px 6px;background:#f8fafc;border-radius:6px;">' + nm[4] + '</div>' if len(nm) > 4 and nm[4] else '')
            + '</div>'
        )
    pillars_html = '<div style="display:flex;gap:8px;margin:12px 0;">' + col_cards + '</div>'

    # 오행 분포
    total_oh = sum(oa.values()) or 1
    oh_bars  = ''
    for oh_name, cnt in oa.items():
        if not cnt:
            continue
        pct = cnt / total_oh * 100
        clr = _OH_CLR.get(oh_name, '#374151')
        oh_bars += (
            '<div style="display:flex;align-items:center;margin-bottom:4px;">'
            '<span style="width:24px;font-size:0.75rem;font-weight:700;color:' + clr + ';">' + oh_name + '</span>'
            '<div style="flex:1;background:#e5e7eb;border-radius:4px;height:10px;margin:0 8px;">'
            '<div style="width:' + f'{pct:.0f}' + '%;background:' + clr + ';height:10px;border-radius:4px;"></div></div>'
            '<span style="font-size:0.72rem;color:#374151;">' + str(cnt) + '개</span>'
            '</div>'
        )

    # 핵심 정보
    gm_str    = '·'.join(JIJI[x] for x in sorted(gm)) if gm else '없음'
    core_rows = [
        ('신강/신약', strength),
        ('格局', gyeok_name),
        ('용신(用神)', ya_name),
        ('기신(忌神)', ', '.join(ki_names) if ki_names else '없음'),
        ('공망(空亡)', gm_str),
    ]
    core_html = ''.join(
        '<tr><td style="padding:5px 10px;font-weight:600;color:#374151;background:#f3f4f6;'
        'border:1px solid #e5e7eb;width:120px;">' + k + '</td>'
        '<td style="padding:5px 12px;border:1px solid #e5e7eb;">' + v + '</td></tr>'
        for k, v in core_rows
    )

    # 신살
    sal_html = ''
    if gil:
        sal_html += '<div style="margin-top:8px;"><b style="color:#16a34a;">✨ 길신:</b> ' + ', '.join(gil) + '</div>'
    if hyung:
        sal_html += '<div style="margin-top:4px;"><b style="color:#dc2626;">⚠ 흉살:</b> ' + ', '.join(hyung) + '</div>'
    sal_section = (
        '<div class="section-title">🎯 신살</div>'
        '<div style="font-size:0.85rem;">' + sal_html + '</div>'
    ) if sal_html else ''

    css = (
        '@media print {'
        '  body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }'
        '  .no-print { display: none; }'
        '}'
        'body {'
        "  font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;"
        '  background: #f9fafb; margin: 0; padding: 24px; color: #111827;'
        '}'
        '.card {'
        '  background: #fff; border-radius: 16px;'
        '  box-shadow: 0 2px 12px rgba(0,0,0,0.08);'
        '  padding: 24px 28px; max-width: 720px; margin: 0 auto;'
        '}'
        '.title {'
        '  font-size: 1.5rem; font-weight: 900;'
        '  background: linear-gradient(135deg, #6d28d9, #a855f7);'
        '  -webkit-background-clip: text; -webkit-text-fill-color: transparent;'
        '  margin-bottom: 4px;'
        '}'
        '.subtitle { font-size: 0.88rem; color: #6b7280; margin-bottom: 18px; }'
        '.section-title {'
        '  font-size: 0.78rem; font-weight: 700; color: #7c3aed;'
        '  letter-spacing: 0.05em; margin: 18px 0 8px;'
        '  border-bottom: 1px solid #ede9fe; padding-bottom: 4px;'
        '}'
        'table { border-collapse: collapse; width: 100%; }'
        '.footer {'
        '  font-size: 0.68rem; color: #9ca3af; text-align: center;'
        '  margin-top: 24px; border-top: 1px solid #e5e7eb; padding-top: 10px;'
        '}'
        '.print-btn {'
        '  display: inline-block; margin-bottom: 16px; padding: 8px 20px;'
        '  background: #7c3aed; color: #fff; border: none; border-radius: 8px;'
        '  font-size: 0.9rem; cursor: pointer; font-family: inherit;'
        '}'
    )

    html = (
        '<!DOCTYPE html>\n<html lang="ko">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<title>' + name + '님의 사주팔자</title>\n'
        '<style>' + css + '</style>\n'
        '</head>\n<body>\n'
        '<div class="no-print" style="max-width:720px;margin:0 auto 12px;">'
        '<button class="print-btn" onclick="window.print()">🖨️ 인쇄 / PDF 저장</button>'
        '</div>\n'
        '<div class="card">\n'
        '<div class="title">🔮 ' + name + '님의 사주팔자</div>\n'
        '<div class="subtitle">생년월일: ' + dt_str + ' (' + cal_label + ') &nbsp;|&nbsp; 성별: ' + gender + '</div>\n'
        '<div class="section-title">📌 사주 기둥</div>\n'
        + pillars_html + '\n'
        '<div class="section-title">🌿 오행 분포</div>\n'
        '<div style="margin:8px 0 4px;">' + oh_bars + '</div>\n'
        '<div class="section-title">⭐ 핵심 정보</div>\n'
        '<table style="margin:8px 0;">' + core_html + '</table>\n'
        + sal_section + '\n'
        '<div class="footer">생성일: ' + today + ' &nbsp;|&nbsp; 사주팔자 앱</div>\n'
        '</div>\n</body>\n</html>'
    )
    return html


_GYEOK_DESC = {
    '비견격': '동료·형제 기운이 강한 독립 추진형',
    '겁재격': '경쟁·도전 기운이 강한 승부사형',
    '식신격': '창의·표현 기운이 강한 재능형',
    '상관격': '개성·예술 기운이 강한 자유 창작형',
    '편재격': '활동·재물 기운이 강한 사업가형',
    '정재격': '안정·현실 기운이 강한 현실 관리형',
    '편관격': '도전·극복 기운이 강한 리더·승부형',
    '정관격': '원칙·질서 기운이 강한 관료·전문가형',
    '편인격': '직관·학문 기운이 강한 연구가형',
    '정인격': '인성·학습 기운이 강한 학자·멘토형',
    '종격':   '한 기운에 모두 따르는 극단형 사주',
    '화격':   '천간 합화로 오행이 변환된 특수 사주',
}

def render_saju_card(name, pillars, corr_dt, corrections, gender, year,
                     expanded=True, no_time=False, cal_label="양력", card_id="main", rel_status='솔로'):
    is_male = gender == '남'
    gil, hyung = check_sal(pillars)
    yj = pillars[0][1]
    oa = analyze_ohaeng(pillars, apply_gan_hwa=True)


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
    for _hy_nm, _hy_kind, _ in get_jiji_hyeong(pillars):
        info_chips += (
            f'<span style="background:#fef2f2;border:1px solid #fca5a5;color:#b91c1c;'
            f'padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;">'
            f'⚡ {_hy_nm}</span>'
        )
    for keuk_nm, oh_rel, keuk_desc in _find_cheongan_keuk(pillars):
        info_chips += (
            f'<span title="{oh_rel} | {keuk_desc}" '
            f'style="background:#eef2ff;border:1px solid #a5b4fc;color:#4338ca;'
            f'padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;cursor:help;">'
            f'🔀 {keuk_nm}</span>'
        )
    _hwa_changed, _hwa_labels = get_cheongan_hwa(pillars)
    for _hl in _hwa_labels:
        info_chips += (
            f'<span style="background:#fdf4ff;border:1px solid #e879f9;color:#86198f;'
            f'padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;">'
            f'⚗️ {_hl}</span>'
        )
    _gsp, _gsp_reason = _check_gyeok_success(pillars)
    _gsp_style = ('background:#f0fdf4;border:1px solid #86efac;color:#166534;' if _gsp == '성격'
                  else 'background:#fff7ed;border:1px solid #fdba74;color:#c2410c;')
    info_chips += (
        f'<span title="{_gsp_reason}" '
        f'style="{_gsp_style}padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;cursor:help;">'
        f'{"✅" if _gsp == "성격" else "⚠️"} {_gsp}</span>'
    )
    _clarity, _clarity_reason = get_gyeok_clarity(pillars)
    _clarity_style = (
        'background:#eff6ff;border:1px solid #93c5fd;color:#1e40af;' if _clarity == '청격(淸格)'
        else 'background:#fff1f2;border:1px solid #fca5a5;color:#be123c;' if _clarity == '탁격(濁格)'
        else 'background:#f9fafb;border:1px solid #d1d5db;color:#374151;'
    )
    _clarity_icon = '✨' if _clarity == '청격(淸格)' else '🌫️' if _clarity == '탁격(濁格)' else '◎'
    info_chips += (
        f'<span title="{_clarity_reason}" '
        f'style="{_clarity_style}padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;cursor:help;">'
        f'{_clarity_icon} {_clarity}</span>'
    )
    info_chips += '</div>'
    st.markdown(info_chips, unsafe_allow_html=True)

    # 신강/신약 게이지 바
    _str8, _str_ratio = get_strength_detail(pillars)
    _STR_CLR = {
        '극왕(極旺)': '#991b1b', '태강(太强)': '#c2410c',
        '신강(身强)': '#d97706', '중화신강':   '#16a34a',
        '중화신약':  '#2563eb', '신약(身弱)':  '#4f46e5',
        '태약(太弱)': '#7c3aed', '극약(極弱)': '#6b21a8',
    }
    _str_col  = _STR_CLR.get(_str8, '#374151')
    _pct_val  = _str_ratio * 100
    st.markdown(
        f'<div style="margin:8px 0 14px;background:#f9fafb;border:1px solid #e5e7eb;'
        f'border-radius:10px;padding:10px 14px;">'
        f'<div style="display:flex;align-items:center;margin-bottom:6px;">'
        f'<span style="font-size:0.72rem;font-weight:700;color:#6b7280;">⚖️ 일간 강도 &nbsp;'
        f'<span style="color:#9ca3af;font-weight:400;">(신약 ↔ 신강)</span></span>'
        f'<span style="margin-left:auto;font-size:0.82rem;font-weight:800;color:{_str_col};">'
        f'{_str8}&nbsp;<span style="font-weight:400;font-size:0.75rem;color:#6b7280;">({_pct_val:.0f}%)</span></span>'
        f'</div>'
        f'<div style="position:relative;height:18px;'
        f'background:linear-gradient(to right,#6d28d9 0%,#3b82f6 18%,#60a5fa 30%,#a7f3d0 42%,#6ee7b7 50%,#fcd34d 58%,#f97316 70%,#dc2626 82%,#991b1b 100%);'
        f'border-radius:6px;">'
        f'<div style="position:absolute;left:42%;top:0;bottom:0;width:1px;background:rgba(0,0,0,0.25);"></div>'
        f'<div style="position:absolute;left:58%;top:0;bottom:0;width:1px;background:rgba(0,0,0,0.25);"></div>'
        f'<div style="position:absolute;left:{_pct_val:.1f}%;top:-5px;'
        f'width:5px;height:28px;background:#1e1b4b;border-radius:3px;'
        f'transform:translateX(-50%);box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:0.62rem;color:#9ca3af;margin-top:3px;padding:0 1px;">'
        f'<span>극약</span><span>태약</span><span>신약</span>'
        f'<span style="color:#16a34a;font-weight:600;">중화</span>'
        f'<span>신강</span><span>태강</span><span>극왕</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # 格局·용신·기신 한눈에 보기 카드
    _gk_name, _gk_yoh, _gk_ki = get_gyeokguk(pillars)
    _, _ys_name, _, _, _       = get_yongshin(pillars)
    _gk_desc  = _GYEOK_DESC.get(_gk_name, '사주 구조의 핵심 유형')
    _ys_oh    = OHAENG_NAMES[_gk_yoh]
    _ki_ohs   = [OHAENG_NAMES[k] for k in _gk_ki]
    _OH_EMO   = {'목': '🌿', '화': '🔥', '토': '🏔️', '금': '💎', '수': '💧'}
    _ys_emo   = _OH_EMO.get(_ys_oh, '')
    _ki_str   = ' · '.join(f"{_OH_EMO.get(k,'')} {k}" for k in _ki_ohs) if _ki_ohs else '없음'
    st.markdown(
        f'<div style="background:#fafafa;border:1px solid #e5e7eb;border-radius:12px;'
        f'padding:12px 16px;margin:8px 0 4px;">'
        f'<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start;">'
        f'<div style="flex:1;min-width:160px;">'
        f'<div style="font-size:0.68rem;font-weight:700;color:#9ca3af;letter-spacing:.05em;margin-bottom:3px;">📐 格局 (사주 구조 유형)</div>'
        f'<div style="font-size:0.92rem;font-weight:800;color:#374151;">{_gk_name}</div>'
        f'<div style="font-size:0.73rem;color:#6b7280;margin-top:2px;">{_gk_desc}</div>'
        f'</div>'
        f'<div style="flex:1;min-width:120px;">'
        f'<div style="font-size:0.68rem;font-weight:700;color:#9ca3af;letter-spacing:.05em;margin-bottom:3px;">🟢 용신 — 내게 좋은 기운</div>'
        f'<div style="font-size:0.92rem;font-weight:800;color:#16a34a;">{_ys_emo} {_ys_oh}</div>'
        f'<div style="font-size:0.73rem;color:#6b7280;margin-top:2px;">{_ys_name} — 이 기운이 강할 때 길운</div>'
        f'</div>'
        f'<div style="flex:1;min-width:120px;">'
        f'<div style="font-size:0.68rem;font-weight:700;color:#9ca3af;letter-spacing:.05em;margin-bottom:3px;">🔴 기신 — 피해야 할 기운</div>'
        f'<div style="font-size:0.92rem;font-weight:800;color:#dc2626;">{_ki_str}</div>'
        f'<div style="font-size:0.73rem;color:#6b7280;margin-top:2px;">이 기운이 강할 때 주의</div>'
        f'</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    with st.expander("📊 오행 분포 차트", expanded=False):
        _str_data  = analyze_ohaeng_strength(pillars)
        _cnt_data  = analyze_ohaeng(pillars, apply_gan_hwa=True)
        _OH_BAR_CLR = {'목':'#4ade80','화':'#f87171','토':'#fbbf24','금':'#94a3b8','수':'#60a5fa'}
        _OH_TXT_CLR = {'목':'#166534','화':'#991b1b','토':'#92400e','금':'#1e3a5f','수':'#1e40af'}
        _yong_nm_chart = OHAENG_NAMES[get_gyeokguk(pillars)[1]]
        _bar_html = '<div style="padding:4px 0;">'
        for _oh_nm in ['목','화','토','금','수']:
            _pct  = _str_data.get(_oh_nm, 0)
            _cnt  = _cnt_data.get(_oh_nm, 0)
            _clr  = _OH_BAR_CLR[_oh_nm]
            _tc   = _OH_TXT_CLR[_oh_nm]
            _is_yong = (_oh_nm == _yong_nm_chart)
            _bg   = 'rgba(255,255,255,0.6)' if not _is_yong else 'rgba(255,250,235,0.9)'
            _bd   = '1px solid #e5e7eb' if not _is_yong else '1px solid #fbbf24'
            _yong_tag = ' <span style="font-size:0.6rem;background:#fef3c7;color:#92400e;border-radius:3px;padding:1px 4px;">용신</span>' if _is_yong else ''
            _bar_html += (
                f'<div style="display:flex;align-items:center;margin-bottom:7px;'
                f'background:{_bg};border:{_bd};border-radius:8px;padding:5px 10px;">'
                f'<div style="width:24px;font-size:0.82rem;font-weight:700;color:{_tc};">{_oh_nm}</div>'
                f'<div style="flex:1;background:#e5e7eb;border-radius:4px;height:16px;margin:0 10px;overflow:hidden;">'
                f'<div style="width:{min(_pct,100):.1f}%;background:{_clr};height:100%;border-radius:4px;"></div></div>'
                f'<div style="width:110px;text-align:right;font-size:0.75rem;color:#374151;">'
                f'{_pct:.1f}% ({_cnt}개){_yong_tag}</div>'
                f'</div>'
            )
        _bar_html += '</div>'
        st.markdown(_bar_html, unsafe_allow_html=True)
        st.caption('계절·지장간 가중치가 반영된 오행 강도 비율입니다.')

    with st.expander("🔮 용신·기신 — 좋은·나쁜 기운 판단 근거", expanded=False):
        st.markdown(explain_yongshin(pillars))

    with st.expander("⚡ 상신(相神) — 용신을 보좌하는 오행", expanded=False):
        _sang_list, _sang_gyeok = get_sangshin(pillars)
        _yong_nm = OHAENG_NAMES[get_gyeokguk(pillars)[1]]
        st.caption(f"格局: {_sang_gyeok}  |  용신: {_yong_nm}")
        if not _sang_list:
            st.info("상신 후보가 없습니다.")
        for _s in _sang_list:
            _s_bg    = "#eff6ff" if _s["exist"] else "#f9fafb"
            _s_bd    = "#93c5fd" if _s["exist"] else "#e5e7eb"
            _s_col   = "#1e40af" if _s["exist"] else "#6b7280"
            _s_icon  = "✅" if _s["exist"] else "⚠️"
            _tuchul  = " · 천간 투출 ✦" if _s["tuchul"] else ""
            _role_desc = (
                f"용신({_yong_nm})을 생(生)해 힘을 보탬"
                if _s["role"] == "생조"
                else "기신을 극(剋)해 용신을 보호"
            )
            _exist_desc = (
                f"사주에 {_s['cnt']}개 존재"
                if _s["exist"]
                else "사주에 없음 — 대운·세운에서 들어올 때 활성화"
            )
            st.markdown(
                f'<div style="background:{_s_bg};border:1px solid {_s_bd};border-radius:10px;'
                f'padding:10px 14px;margin-bottom:8px;">'
                f'<div style="font-size:0.88rem;font-weight:700;color:{_s_col};">'
                f'{_s_icon} {_s["nm"]} — {_s["role"]} ({_role_desc}){_tuchul}</div>'
                f'<div style="font-size:0.8rem;color:#374151;margin-top:4px;">{_exist_desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    with st.expander("🌡️ 조후(調候) — 계절의 균형", expanded=False):
        _jh_season, _jh_em, _jh_ohs, _jh_desc = get_johu_desc(pillars)
        _jh_oa = analyze_ohaeng(pillars, apply_gan_hwa=True)
        st.markdown(
            f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;'
            f'padding:10px 14px;margin-bottom:10px;">'
            f'<span style="font-size:0.9rem;font-weight:700;color:#166534;">{_jh_em} {_jh_season} 출생</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div style="font-size:0.85rem;color:#374151;line-height:1.7;'
            f'background:#fafafa;border-radius:10px;padding:12px 14px;margin-bottom:10px;">'
            f'{_jh_desc}</div>',
            unsafe_allow_html=True
        )
        if _jh_ohs:
            st.markdown('**조후 필요 오행**')
            _OH_CHIP = {'목':('#bbf7d0','#166534','#4ade80'),
                        '화':('#fecaca','#991b1b','#f87171'),
                        '토':('#fde68a','#92400e','#fbbf24'),
                        '금':('#e2e8f0','#1e3a5f','#94a3b8'),
                        '수':('#bfdbfe','#1e40af','#60a5fa')}
            _johu_chips = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px;">'
            for _jo in _jh_ohs:
                _jnm = OHAENG_NAMES[_jo]
                _jcnt = _jh_oa.get(_jnm, 0)
                _jbg, _jtc, _jbd = _OH_CHIP.get(_jnm, ('#f5f0ff','#5b21b6','#ddd4f8'))
                _jexist = '✅ ' if _jcnt >= 1 else '⚠️ '
                _johu_chips += (
                    f'<span style="background:{_jbg};border:1px solid {_jbd};color:{_jtc};'
                    f'padding:5px 14px;border-radius:20px;font-size:0.82rem;font-weight:600;">'
                    f'{_jexist}{_jnm} ({_jcnt}개)</span>'
                )
            _johu_chips += '</div>'
            st.markdown(_johu_chips, unsafe_allow_html=True)

    with st.expander("💼 직업 적성", expanded=False):
        _jb_gyeok, _jb_yong, _jb_desc, _jb_jobs, _jb_yjobs = get_job_aptitude(pillars)
        st.markdown(
            f'<div style="background:#f5f3ff;border:1px solid #ddd4f8;border-radius:10px;'
            f'padding:10px 14px;margin-bottom:10px;">'
            f'<span style="font-size:0.85rem;font-weight:700;color:#6d28d9;">'
            f'{_jb_gyeok} — {_jb_desc}</span></div>',
            unsafe_allow_html=True
        )
        st.markdown('**格局 기반 직업군**')
        _jb_chips = '<div style="display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 12px;">'
        for _jj in _jb_jobs:
            _jb_chips += (
                f'<span style="background:#ede9fe;border:1px solid #c4b5fd;color:#4c1d95;'
                f'padding:5px 13px;border-radius:20px;font-size:0.82rem;font-weight:600;">'
                f'{_jj}</span>'
            )
        _jb_chips += '</div>'
        st.markdown(_jb_chips, unsafe_allow_html=True)
        if _jb_yjobs:
            st.markdown(f'**용신({_jb_yong}) 오행 보조 분야**')
            _yb_chips = '<div style="display:flex;flex-wrap:wrap;gap:7px;margin:6px 0;">'
            for _yj in _jb_yjobs:
                _yb_chips += (
                    f'<span style="background:#f0fdf4;border:1px solid #86efac;color:#166534;'
                    f'padding:5px 13px;border-radius:20px;font-size:0.82rem;font-weight:600;">'
                    f'{_yj}</span>'
                )
            _yb_chips += '</div>'
            st.markdown(_yb_chips, unsafe_allow_html=True)
        st.caption('格局·용신 기반 통계적 경향으로, 실제 적성은 개인 경험·환경과 함께 판단하세요.')

    with st.expander("🌿 오행 보충 조언 — 부족한 기운 채우기", expanded=False):
        _supp_ilgan    = pillars[2][0]
        _supp_yong_idx = get_gyeokguk(pillars)[1]
        _supp_yong_nm  = OHAENG_NAMES[_supp_yong_idx]
        _supp_hee_idx  = (_supp_yong_idx + 4) % 5
        _supp_hee_nm   = OHAENG_NAMES[_supp_hee_idx]
        _supp_str_data = analyze_ohaeng_strength(pillars)
        _supp_low_nm   = min(_supp_str_data, key=_supp_str_data.get)
        _OHAENG_OH_LABEL = {0:'목',1:'화',2:'토',3:'금',4:'수'}
        _supp_targets  = list(dict.fromkeys([_supp_yong_nm, _supp_hee_nm, _supp_low_nm]))
        _ilg_yong_cmt  = _ILGAN_YONGSHIN_COMMENT.get((_supp_ilgan, _supp_yong_nm), '')
        st.markdown(
            f'<div style="font-size:0.78rem;color:#6b7280;margin-bottom:10px;">'
            f'용신 <b style="color:#7c3aed;">{_supp_yong_nm}({_supp_yong_idx+1})</b>·'
            f'희신 <b style="color:#2563eb;">{_supp_hee_nm}</b>·'
            f'최약 <b style="color:#dc2626;">{_supp_low_nm}</b> 기운을 보충하세요.</div>',
            unsafe_allow_html=True,
        )
        if _ilg_yong_cmt:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#fdf4ff,#f5f3ff);'
                f'border:1px solid #e9d5ff;border-radius:10px;padding:11px 14px;margin-bottom:12px;">'
                f'<div style="font-size:0.65rem;color:#9ca3af;font-weight:600;margin-bottom:4px;">✨ {name}님 맞춤 코멘트</div>'
                f'<div style="font-size:0.82rem;color:#4c1d95;line-height:1.65;">{_ilg_yong_cmt}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        for _s_nm in _supp_targets:
            _s = _OH_SUPPLEMENT.get(_s_nm)
            if not _s: continue
            _is_yong = (_s_nm == _supp_yong_nm)
            _s_bg  = 'linear-gradient(135deg,#f5f3ff,#ede9fe)' if _is_yong else '#f9fafb'
            _s_bd  = '#c4b5fd' if _is_yong else '#e5e7eb'
            _s_tc  = '#6d28d9' if _is_yong else '#374151'
            _s_tag = '<span style="font-size:0.65rem;background:#ede9fe;color:#7c3aed;border-radius:3px;padding:1px 6px;margin-left:5px;font-weight:700;">용신</span>' if _is_yong else ''
            _col_chips = ''.join(
                f'<span style="display:inline-flex;align-items:center;gap:3px;background:#f9fafb;border:1px solid #e5e7eb;'
                f'padding:3px 9px;border-radius:12px;font-size:0.75rem;margin-right:4px;">'
                f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{hx};"></span>{nm}'
                f'</span>'
                for hx, nm in _s['colors']
            )
            st.markdown(
                f'<div style="background:{_s_bg};border:1px solid {_s_bd};border-radius:12px;'
                f'padding:13px 16px;margin-bottom:10px;">'
                f'<div style="font-size:0.9rem;font-weight:800;color:{_s_tc};margin-bottom:8px;">'
                f'{_s["icon"]} {_s_nm}({["木","火","土","金","水"][["목","화","토","금","수"].index(_s_nm)]}) 기운 보충{_s_tag}</div>'
                f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:8px;">'
                f'<div style="background:rgba(255,255,255,0.7);border-radius:8px;padding:7px 10px;">'
                f'<div style="font-size:0.65rem;color:#9ca3af;font-weight:600;margin-bottom:3px;">🧭 방향</div>'
                f'<div style="font-size:0.8rem;font-weight:700;color:#374151;">{_s["direction"]}</div>'
                f'</div>'
                f'<div style="background:rgba(255,255,255,0.7);border-radius:8px;padding:7px 10px;">'
                f'<div style="font-size:0.65rem;color:#9ca3af;font-weight:600;margin-bottom:3px;">🔢 행운 숫자</div>'
                f'<div style="font-size:0.8rem;font-weight:700;color:#374151;">{_s["number"]}</div>'
                f'</div>'
                f'<div style="background:rgba(255,255,255,0.7);border-radius:8px;padding:7px 10px;">'
                f'<div style="font-size:0.65rem;color:#9ca3af;font-weight:600;margin-bottom:3px;">🍽️ 음미</div>'
                f'<div style="font-size:0.8rem;font-weight:700;color:#374151;">{_s["taste"]}</div>'
                f'</div>'
                f'</div>'
                f'<div style="margin-bottom:6px;">'
                f'<div style="font-size:0.65rem;color:#9ca3af;font-weight:600;margin-bottom:4px;">🎨 추천 색상</div>'
                f'{_col_chips}</div>'
                f'<div style="margin-bottom:6px;">'
                f'<div style="font-size:0.65rem;color:#9ca3af;font-weight:600;margin-bottom:3px;">🥗 도움되는 음식</div>'
                f'<div style="font-size:0.78rem;color:#374151;">{", ".join(_s["foods"])}</div>'
                f'</div>'
                f'<div style="margin-bottom:6px;">'
                f'<div style="font-size:0.65rem;color:#9ca3af;font-weight:600;margin-bottom:3px;">🎯 추천 활동</div>'
                f'<div style="font-size:0.78rem;color:#374151;">{", ".join(_s["activities"])}</div>'
                f'</div>'
                f'<div style="background:rgba(255,255,255,0.5);border-radius:6px;padding:6px 10px;'
                f'font-size:0.75rem;color:#6b7280;">💡 {_s["tip"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # 공망 상세 해설
    _gm = get_gongmang(*pillars[2])
    _gm_hits = [(i, p[1]) for i, p in enumerate(pillars) if p[1] in _gm]
    if _gm_hits:
        _GM_PILLAR = {0:'년주', 1:'월주', 2:'일주', 3:'시주'}
        _GM_DESC = {
            0: ('뿌리·조상이 약해요', '고향·조상 덕이 적고, 어릴 때 환경이 불안정했을 수 있어요. 대신 자수성가 에너지가 강해져요.'),
            1: ('형제·직장이 흔들려요', '형제 인연이 얇거나 직업의 변동이 많아요. 일에서 실속보다 경험이 먼저 쌓이는 구조예요.'),
            2: ('배우자·건강 주의', '배우자 인연이 늦거나 관계에 공허함이 생기기 쉬워요. 건강은 겉으로 드러나지 않는 부분을 챙기세요.'),
            3: ('자녀·말년이 고독할 수 있어요', '자녀 인연이 적거나 말년에 혼자인 시간이 많아요. 스스로 내면을 채우는 취미나 신앙이 중요해요.'),
        }
        with st.expander("🕳 공망(空亡) — 기둥별 상세 해설", expanded=False):
            for _gi, _gj in _gm_hits:
                _gm_short, _gm_long = _GM_DESC.get(_gi, ('해당 기둥 공망', ''))
                st.markdown(
                    f'<div style="background:#fff1f2;border:1px solid #fca5a5;border-radius:12px;padding:14px 16px;margin-bottom:10px;">'
                    f'<div style="font-size:0.9rem;font-weight:700;color:#be123c;margin-bottom:4px;">'
                    f'{_GM_PILLAR[_gi]} {JIJI[_gj]} 공망 — {_gm_short}</div>'
                    f'<div style="font-size:0.83rem;color:#374151;line-height:1.6;">{_gm_long}</div></div>',
                    unsafe_allow_html=True
                )

    _hy_list = get_jiji_hyeong(pillars)
    if _hy_list:
        with st.expander("⚡ 지지형(地支刑) 상세 해설", expanded=False):
            for _hy_nm, _hy_kind, _hy_desc in _hy_list:
                st.markdown(
                    f'<div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:12px;'
                    f'padding:14px 16px;margin-bottom:10px;">'
                    f'<div style="font-size:0.9rem;font-weight:700;color:#b91c1c;margin-bottom:4px;">'
                    f'⚡ {_hy_nm} — {_hy_kind}</div>'
                    f'<div style="font-size:0.83rem;color:#374151;line-height:1.6;">{_hy_desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

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

    with st.expander("🌿 지장간(支藏干) — 지지 속 숨은 천간", expanded=False):
        ilgan_in = pillars[2][0]
        _HDR_NAMES = ['년주','월주','일주','시주']
        _PILLAR_ROLES = ['조상·뿌리','부모·형제·직업','나·배우자','자녀·말년']
        _JEONGI_LABEL = {3:'정기(正氣)', 2:'중기(中氣)', 1:'여기(餘氣)'}
        st.markdown(
            '<div style="font-size:0.82rem;color:#555;margin-bottom:10px;">'
            '지지 안에 숨어있는 천간(지장간)은 표면에 보이지 않지만 실제로 작용하는 에너지예요.<br>'
            '<b>정기(正氣)</b>가 가장 강하게 작용하고, 중기·여기 순으로 영향력이 약해져요.</div>',
            unsafe_allow_html=True
        )
        order_idx = [2,1,0] if no_time else [3,2,1,0]
        hdr_list  = ['일주','월주','년주'] if no_time else ['시주','일주','월주','년주']
        for col_i, (pi, hdr) in enumerate(zip(order_idx, hdr_list)):
            g_i, j_i = pillars[pi]
            jjgs = JIJANGAN[j_i]  # 지장간 한자 리스트 (여기→정기 순)
            st.markdown(f'**{hdr} ({CHEONGAN[g_i]}{JIJI[j_i]})**')
            _rows = []
            for k, jg_char in enumerate(jjgs):
                # 지장간 인덱스 (한자→인덱스)
                jg_idx = next((gi for gi, c in enumerate(CHEONGAN) if c == jg_char), None)
                if jg_idx is None:
                    continue
                ss = '일간' if (jg_idx == ilgan_in) else get_sipseong(ilgan_in, OHAENG_IDX[jg_idx], jg_idx % 2)
                strength_label = _JEONGI_LABEL.get(len(jjgs) - k, '여기(餘氣)')
                _rows.append(f'{strength_label}: **{jg_char}** ({OHAENG_NAMES[OHAENG_IDX[jg_idx]]} · {ss})')
            for row in _rows:
                st.markdown(f'- {row}')
            if pi == 1:  # 월지
                st.caption('💡 월지 정기가 格局의 핵심이에요.')
            st.markdown('---')

    with st.expander("🌟 일주론(日柱論) — 타고난 특성 상세", expanded=False):
        _render_ilju_card(name, pillars, no_time=no_time)

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
        _render_sewoon_section(name, pillars, year, daeun, card_id=card_id)

    with st.expander("🔖 신살(神殺) — 귀인·흉살 상세 해설", expanded=False):
        _render_sal_detail(pillars)

    # ── 분석 결과 다운로드 ──
    _summary  = _make_saju_summary(name, pillars, corr_dt, gender, no_time, cal_label)
    _html_doc = _make_saju_html(name, pillars, corr_dt, gender, no_time, cal_label)
    _dl_col1, _dl_col2 = st.columns(2)
    _dl_col1.download_button(
        label="📥 텍스트 저장 (.txt)",
        data=_summary.encode('utf-8'),
        file_name=f"{name}_사주분석_{datetime.now(_KST).strftime('%Y%m%d')}.txt",
        mime="text/plain; charset=utf-8",
        key=f"dl_saju_{card_id}",
        use_container_width=True,
    )
    _dl_col2.download_button(
        label="🖨️ 명식 저장 (.html)",
        data=_html_doc.encode('utf-8'),
        file_name=f"{name}_명식_{datetime.now(_KST).strftime('%Y%m%d')}.html",
        mime="text/html; charset=utf-8",
        key=f"dl_html_{card_id}",
        use_container_width=True,
    )


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


_DAEUN_SEWOON_CROSS = {
    # ══ 비견대운 ══
    ('비견', '비견'): '독립·자아 에너지가 대운과 세운 양쪽에서 겹쳐요. 고집이 극대화되어 주변과 마찰이 잦아지기 쉬우니, 내가 옳아도 한 발 물러서는 연습이 이 해의 핵심이에요.',
    ('비견', '겁재'): '경쟁과 손실 위험이 강하게 올라오는 해예요. 동업·보증·공동투자는 절대 피하고, 재물 거래는 반드시 서면으로만 처리하세요.',
    ('비견', '식신'): '독립 에너지가 창의 성과로 자연스럽게 흘러가는 이상적인 조합이에요. 혼자 힘으로 만들어낸 결과물이 인정받는 해예요.',
    ('비견', '상관'): '자기 표현 욕구가 폭발하는 해예요. 창의 에너지를 생산적으로 쏟으면 성과가 나오지만, 말이 앞서 구설이 생기지 않도록 주의하세요.',
    ('비견', '편재'): '자수성가 기회가 찾아오는 해예요. 혼자 벌고 혼자 운용하는 구조가 가장 잘 맞고, 동업 제안은 아무리 좋아 보여도 이 해엔 보류하세요.',
    ('비견', '정재'): '독립 기반 위에 안정 수입이 더해지는 흐름이에요. 꾸준히 쌓아온 실력이 현실적인 수입으로 이어지는 해예요.',
    ('비견', '편관'): '압박과 경쟁이 동시에 몰아치는 체력·심리 소모가 최고조인 해예요. 싸울 싸움과 피할 싸움을 냉정하게 구분하는 것이 이 해를 버티는 전략이에요.',
    ('비견', '정관'): '독립심과 조직 원칙이 충돌하기 쉬운 해예요. 내 방식을 고집하기보다 공식 룰 안에서 움직이면 오히려 인정받는 기회가 생겨요.',
    ('비견', '편인'): '혼자 파고드는 에너지가 강해져 고립이 깊어질 수 있어요. 전문성은 쌓이지만 주변과의 소통을 의식적으로 늘리지 않으면 기회를 놓쳐요.',
    ('비견', '정인'): '귀인이나 멘토가 독립 의지를 뒷받침해주는 흐름이에요. 배움과 지원이 자립의 발판이 되는 해예요.',
    # ══ 겁재대운 ══
    ('겁재', '비견'): '경쟁과 자아 과잉이 동시에 강해지는 해예요. 충동적인 독립 시도나 맞불 경쟁은 손실로 이어지기 쉬우니, 에너지를 하나의 목표에만 집중하세요.',
    ('겁재', '겁재'): '재물 손실과 경쟁 충돌 위험이 10년 중 가장 극대화되는 해예요. 투자·동업·보증은 완전히 차단하고, 지키는 것에만 집중해야 해요.',
    ('겁재', '식신'): '강한 충동 에너지가 창의적 출구를 만나는 해예요. 경쟁 대신 내 결과물을 만드는 데 쏟으면 생각보다 좋은 성과가 나와요.',
    ('겁재', '상관'): '날카로운 표현과 충동이 겹쳐 말실수·구설 위험이 가장 높은 해예요. 계약서 확인과 언행 관리가 이 해의 최우선 과제예요.',
    ('겁재', '편재'): '큰 재물 기회처럼 보이지만 위험도 함께 극대화되는 해예요. 욕심을 한 템포 줄이지 않으면 들어온 것보다 더 많이 나가요.',
    ('겁재', '정재'): '안정을 원하지만 경쟁 기운이 방해하는 해예요. 고정 수입을 지키는 것에 집중하고, 새로운 재물 시도는 내년으로 미루는 게 현명해요.',
    ('겁재', '편관'): '외부 압박과 내부 충동이 동시에 최고조인 해예요. 감정적으로 반응하면 모든 전선에서 불리해지니, 철저히 전략적으로 움직여야 해요.',
    ('겁재', '정관'): '충동과 규율이 충돌하는 해예요. 조직 안에서 규칙을 지키는 것이 답답해도, 이 해엔 공식 룰을 따르는 쪽이 훨씬 유리해요.',
    ('겁재', '편인'): '혼자 고집스럽게 파고드는 에너지가 강해져요. 직관은 날카로워지지만 주변 의견을 차단하면 중요한 정보를 놓칠 수 있어요.',
    ('겁재', '정인'): '귀인의 도움이 충동적 결정을 막아주는 해예요. 중요한 선택 전에 신뢰하는 멘토나 어른의 의견을 반드시 듣고 움직이세요.',
    # ══ 식신대운 ══
    ('식신', '비견'): '창의 에너지가 독립 의지와 만나는 해예요. 내가 직접 만든 것으로 자립하려는 욕구가 강해지고, 그 방향이 현실적으로 맞는 해예요.',
    ('식신', '겁재'): '창의 성과를 경쟁자가 가로채거나 재물이 새는 패턴이 생기기 쉬운 해예요. 저작권·계약서 관리를 철저히 하세요.',
    ('식신', '식신'): '창의·표현·여유 에너지가 두 배로 넘치는 해예요. 즐기면서 일한 것들이 성과로 이어지는 10년 중 가장 행복한 해예요.',
    ('식신', '상관'): '창의 에너지가 폭발적으로 분출되는 해예요. 혁신적 결과물이 나오지만 말이 앞서는 실수도 잦아지니, 표현의 방향만 조율하면 돼요.',
    ('식신', '편재'): '재능이 재물로 연결되는 흐름이 가장 강한 해예요. 콘텐츠·강의·기획 등 내 실력으로 버는 수익 구조를 이 해에 만들어두세요.',
    ('식신', '정재'): '꾸준한 창의 활동이 안정적 수입으로 정착되는 해예요. 무리한 확장 없이 지금 하는 것을 더 잘하는 방향이 가장 유리해요.',
    ('식신', '편관'): '여유로운 대운에 압박이 들어오는 해예요. 무리하지 않고 스스로 속도를 조율하는 사람이 이 해를 가장 잘 보내요.',
    ('식신', '정관'): '창의력이 공식 인정을 받는 해예요. 그동안 만들어온 결과물이 조직이나 기관에서 평가받는 기회가 찾아와요.',
    ('식신', '편인'): '창의·직관 에너지가 겹쳐 아이디어가 풍부해지는 해예요. 생각이 너무 많아 실행이 느려지지 않도록 하나씩 마무리하는 연습이 필요해요.',
    ('식신', '정인'): '귀인의 지원이 창의 활동에 날개를 달아주는 해예요. 배움에 투자하거나 좋은 스승을 만나면 이 해의 에너지가 극대화돼요.',
    # ══ 상관대운 ══
    ('상관', '비견'): '표현 욕구와 자아 고집이 겹쳐 인간관계 마찰이 가장 커지는 해예요. 내가 옳아도 방식을 부드럽게 조율하는 것이 관계와 성과를 동시에 지켜요.',
    ('상관', '겁재'): '말실수와 재물 손실이 동시에 터질 수 있는 해예요. 충동적 언행과 금전 결정을 하루 이상 두고 식힌 뒤 실행하는 습관이 필수예요.',
    ('상관', '식신'): '표현·창의 에너지가 두 배로 넘쳐 가장 생산적인 해예요. 만들고 표현하는 모든 것이 좋은 반응을 얻는 시기예요.',
    ('상관', '상관'): '혁신과 반골 기질이 극대화되는 해예요. 기존 틀을 깨는 시도가 빛을 발하지만, 권위와의 충돌도 최고조이니 싸울 자리를 골라야 해요.',
    ('상관', '편재'): '전문성과 언변이 직접 수익으로 연결되는 해예요. 강의·컨설팅·콘텐츠 수익이 활발해지고, 새 클라이언트를 확보하기 좋은 타이밍이에요.',
    ('상관', '정재'): '창의 에너지가 안정적 수입 구조로 자리잡는 해예요. 기존에 만들어온 콘텐츠나 기술이 꾸준한 수익원이 되는 흐름이에요.',
    ('상관', '편관'): '날카로운 표현과 외부 압박이 맞부딪히는 해예요. 정면 돌파보다 우회 전략이 훨씬 효과적이에요. 말보다 결과물로 증명하세요.',
    ('상관', '정관'): '자유로운 기질과 규율이 부딪히는 해예요. 조직 안에서 자기 방식을 고집하면 손해를 보니, 공식 틀 안에서 창의성을 발휘하는 균형이 필요해요.',
    ('상관', '편인'): '직관과 아이디어가 폭발적으로 쏟아지는 해예요. 생각을 기록하고 하나씩 실행으로 옮기지 않으면 아이디어가 공중에서 사라져요.',
    ('상관', '정인'): '귀인이 날카로운 언행을 중화시켜주는 해예요. 신뢰하는 사람의 조언이 충동적 결정을 막아주고, 좋은 방향으로 이끌어줘요.',
    # ══ 편재대운 ══
    ('편재', '비견'): '재물 확장의 10년에 경쟁자가 등장하는 해예요. 동업·공동투자 분쟁 위험이 높으니 재물 거래는 단독으로, 계약서로만 처리하세요.',
    ('편재', '겁재'): '큰 기회가 오는 동시에 손실 위험도 극대화되는 해예요. 욕심을 반으로 줄이고 분산 투자·소규모 시작 원칙을 반드시 지키세요.',
    ('편재', '식신'): '재물과 창의가 시너지를 내는 이상적인 해예요. 좋아하는 것으로 돈을 버는 구조가 현실이 되는 흐름이에요.',
    ('편재', '상관'): '언변과 활동력이 결합해 영업·협상·거래에서 두드러진 성과가 나오는 해예요. 다만 과잉 자신감에서 비롯된 무리한 약속은 피하세요.',
    ('편재', '편재'): '재물 운용 에너지가 10년 중 가장 강한 해예요. 기회가 크게 열리지만 과욕을 부리면 반대로 크게 잃는 해이기도 해요. 분산이 핵심이에요.',
    ('편재', '정재'): '활발한 재물 확장의 대운에 안정 수입이 더해지는 이상적인 조합이에요. 무리한 도전보다 기존 수익 구조를 다지면서 자산을 쌓는 해예요.',
    ('편재', '편관'): '도전과 기회가 동시에 압박으로 다가오는 해예요. 체력 관리를 최우선으로 하면서 선택과 집중 전략을 유지하면 성과가 나와요.',
    ('편재', '정관'): '사업·투자 기회가 공식 경로로 연결되는 해예요. 기관·조직과의 협업이나 공식 계약에서 좋은 결과가 나오는 흐름이에요.',
    ('편재', '편인'): '아이디어가 재물 기회로 연결되는 해예요. 직관으로 발견한 틈새 기회가 실제 수익이 될 수 있으니 빠르게 검증하고 움직이세요.',
    ('편재', '정인'): '귀인이나 전문가의 조언이 재물 결정을 도와주는 해예요. 큰 거래나 투자 전에 신뢰할 수 있는 전문가 의견을 반드시 구하세요.',
    # ══ 정재대운 ══
    ('정재', '비견'): '안정적으로 쌓아온 기반에 경쟁이 끼어드는 해예요. 내 영역을 지키되 불필요한 경쟁에 에너지를 낭비하지 않는 것이 이 해의 전략이에요.',
    ('정재', '겁재'): '안정 대운에 손실 기운이 들어오는 해예요. 지인 금전 거래와 보증은 절대 피하고, 지금까지 쌓아온 재물을 지키는 것이 최우선이에요.',
    ('정재', '식신'): '꾸준한 관리 위에 창의 수익이 더해지는 해예요. 취미나 부업에서 소소한 수익이 생기고, 그것이 복리처럼 쌓이는 흐름이에요.',
    ('정재', '상관'): '안정 기반에 표현 욕구가 더해지는 해예요. 오래 참아왔던 것을 표현할 기회가 오지만, 기존 관계를 해치지 않는 방식으로 풀어야 해요.',
    ('정재', '편재'): '안정 대운에 활발한 재물 기회가 들어오는 해예요. 평소보다 적극적으로 움직여도 좋지만, 정재 기질답게 검증된 방식에서 벗어나지 마세요.',
    ('정재', '정재'): '안정과 성실의 에너지가 두 배로 쌓이는 해예요. 화려하진 않지만 꾸준히 모은 것이 확실하게 불어나는 10년 중 가장 든든한 해예요.',
    ('정재', '편관'): '안정을 원하는데 외부 압박이 들어오는 해예요. 흔들리지 말고 기존 원칙을 유지하면, 압박이 지나간 뒤 더 단단한 기반이 남아요.',
    ('정재', '정관'): '성실함이 공식 인정으로 돌아오는 해예요. 승진·포상·자격 취득 등 오래 쌓아온 것이 공식적으로 평가받는 타이밍이에요.',
    ('정재', '편인'): '실무보다 공부·연구에 관심이 가는 해예요. 배움에 투자하면 나중에 수익으로 돌아오는 구조이니 장기 안목으로 움직이세요.',
    ('정재', '정인'): '귀인이나 조직의 지원으로 재물 기반이 더욱 탄탄해지는 해예요. 혼자 버는 것 외에 받는 것에서도 실질적인 이득이 생겨요.',
    # ══ 편관대운 ══
    ('편관', '비견'): '외부 압박에 자아 고집까지 더해지는 이중 소모의 해예요. 싸울 싸움과 피할 싸움을 냉정하게 구분하지 않으면 체력과 감정이 동시에 바닥나요.',
    ('편관', '겁재'): '압박과 경쟁이 동시에 최고조인 해예요. 모든 전선에서 싸우려 하지 말고, 가장 중요한 한 곳에만 에너지를 집중하는 전략이 필요해요.',
    ('편관', '식신'): '강한 압박 속에서 창의적 돌파구가 열리는 해예요. 정면 돌파보다 다른 방식·다른 경로로 우회하면 의외로 쉽게 풀리는 흐름이에요.',
    ('편관', '상관'): '압박에 반발심까지 겹쳐 충돌 에너지가 폭발하는 해예요. 말과 행동을 극도로 절제하지 않으면 불필요한 적을 만들기 쉬워요.',
    ('편관', '편재'): '도전 속에서 재물 기회가 찾아오는 해예요. 위기를 기회로 바꾸는 편관의 돌파력이 빛나지만, 무리한 확장은 부담이 돼요.',
    ('편관', '정재'): '압박 속에서 안정을 지키려는 해예요. 새로운 시도보다 현재 자리와 수입을 지키는 수비 전략이 이 해에 가장 현명해요.',
    ('편관', '편관'): '압박과 도전이 10년 중 가장 강한 해예요. 버티면 진짜 실력이 남지만, 혼자 감당하지 말고 신뢰할 수 있는 사람과 짐을 나누세요.',
    ('편관', '정관'): '외부 압박이 공식 평가로 이어지는 해예요. 힘든 과정을 버텨낸 것이 승진·인정·자격 취득으로 돌아오는 반전이 있어요.',
    ('편관', '편인'): '압박이 내면 성찰과 직관을 깊게 만드는 해예요. 고독하지만 전문성이 크게 성장하고, 이 시기의 내공이 다음 대운의 핵심 자산이 돼요.',
    ('편관', '정인'): '귀인이나 윗사람의 지원이 압박을 완충해주는 해예요. 혼자 해결하려 하지 말고 도움을 구하는 것이 이 해를 가장 효율적으로 넘기는 방법이에요.',
    # ══ 정관대운 ══
    ('정관', '비견'): '원칙과 자아 독립심이 충돌하는 해예요. 조직이나 공식 룰과 마찰이 생기기 쉬우니, 내 의견은 공식 채널로 절차에 맞게 전달하세요.',
    ('정관', '겁재'): '안정적 대운에 경쟁·손실 기운이 끼어드는 해예요. 조직 내 경쟁이나 이권 다툼이 생길 수 있으니 말을 아끼고 성과로 증명하세요.',
    ('정관', '식신'): '원칙 위에 창의가 더해지는 이상적인 해예요. 규율을 지키면서도 새로운 아이디어가 인정받는 흐름으로, 기획·제안에서 좋은 반응이 와요.',
    ('정관', '상관'): '원칙과 반골 기질이 맞부딪히는 해예요. 옳더라도 방식이 틀리면 역효과가 나는 시기이니, 불만은 공식 절차로 조용히 표현하세요.',
    ('정관', '편재'): '안정적 대운에 재물 활동이 활발해지는 해예요. 공식 경로의 계약·협업·거래에서 좋은 성과가 나오고, 인맥을 통한 기회가 구체화돼요.',
    ('정관', '정재'): '원칙과 성실이 두 배로 쌓이는 해예요. 묵묵히 해온 것이 공식적으로 인정받고, 재물도 안정적으로 쌓이는 10년 중 가장 탄탄한 해예요.',
    ('정관', '편관'): '공식 원칙과 외부 압박이 동시에 오는 해예요. 규율 안에서 압박을 처리하면 오히려 신뢰가 쌓이고, 리더십을 발휘할 기회가 생겨요.',
    ('정관', '정관'): '원칙·인정·공식 포지션 에너지가 극대화되는 해예요. 승진·표창·공식 임명 등 오래 기다려온 인정이 현실이 되는 흐름이에요.',
    ('정관', '편인'): '공식 역할과 내면 탐구가 겹치는 해예요. 배움이나 전문성 강화에 투자하면 현재 포지션이 더욱 탄탄해지는 흐름이에요.',
    ('정관', '정인'): '귀인·윗사람의 지원이 공식 포지션을 강화해주는 해예요. 좋은 평판이 더 좋은 기회를 불러오는 선순환이 만들어지는 시기예요.',
    # ══ 편인대운 ══
    ('편인', '비견'): '고독한 탐구 에너지에 자아 독립심이 더해지는 해예요. 혼자 파고드는 힘이 극대화되지만, 고립이 깊어지지 않도록 주변과의 접점을 유지하세요.',
    ('편인', '겁재'): '고립과 손실 위험이 겹치는 해예요. 충동적인 결정이나 지인 권유의 투자는 이 해에 특히 위험하니, 신중하게 검토하고 움직이세요.',
    ('편인', '식신'): '직관과 창의가 시너지를 내는 해예요. 연구·기획·창작에서 독창적인 결과물이 나오고, 전문성이 외부에서 인정받기 시작하는 흐름이에요.',
    ('편인', '상관'): '직관과 표현 욕구가 겹쳐 창의 에너지가 폭발하는 해예요. 혼자 작업한 것들이 대외적으로 알려지는 기회가 찾아와요.',
    ('편인', '편재'): '아이디어가 재물 기회로 연결되는 해예요. 직관으로 발견한 틈새 시장이 실제 수익이 될 수 있으니 빠르게 검증하고 소규모로 시작하세요.',
    ('편인', '정재'): '깊은 전문성이 안정적 수입으로 연결되는 흐름이에요. 오래 쌓아온 실력이 꾸준한 수입원으로 자리잡는 해예요.',
    ('편인', '편관'): '고독한 탐구와 외부 압박이 겹치는 해예요. 혼자 감당하려 하지 말고 도움을 구하는 것이 이 해를 가장 효율적으로 넘기는 방법이에요.',
    ('편인', '정관'): '직관·전문성이 공식 인정을 받는 해예요. 오래 연구해온 분야에서 자격·논문·공식 평가로 실력이 인정받는 흐름이에요.',
    ('편인', '편인'): '직관과 고독이 10년 중 가장 극대화되는 해예요. 내면 탐구와 전문성은 최고조에 달하지만 고립이 깊어질 수 있으니 소통을 의식적으로 늘리세요.',
    ('편인', '정인'): '직관과 배움이 시너지를 내는 해예요. 좋은 스승이나 귀인을 만나 전문성이 한 단계 도약하는 전환점이 되는 흐름이에요.',
    # ══ 정인대운 ══
    ('정인', '비견'): '지원과 독립 의지가 충돌하는 해예요. 귀인의 도움을 받으면서도 내 방식대로 하고 싶은 욕구가 강해지니, 도움을 받을 때는 감사히 받고 방향만 스스로 결정하세요.',
    ('정인', '겁재'): '귀인의 지원이 경쟁·손실 기운을 막아주는 역할을 하는 해예요. 중요한 결정 전에 신뢰할 수 있는 어른이나 전문가의 의견을 꼭 구하세요.',
    ('정인', '식신'): '배움과 창의가 시너지를 내는 이상적인 해예요. 공부한 것이 바로 성과로 이어지고, 즐기면서 배우는 모든 것이 실력이 되는 흐름이에요.',
    ('정인', '상관'): '배움 욕구와 표현 욕구가 동시에 강해지는 해예요. 배운 것을 콘텐츠나 강의로 풀어내면 외부에서 좋은 반응을 얻는 타이밍이에요.',
    ('정인', '편재'): '지원·배움 위에 재물 기회가 찾아오는 해예요. 전문성이 수익으로 연결되는 흐름이에요. 귀인 소개나 조직 지원으로 새 기회가 열려요.',
    ('정인', '정재'): '배움과 안정이 두 배로 쌓이는 해예요. 실력이 수입으로 안정적으로 정착되고, 귀인의 지지가 재물 기반을 더욱 탄탄하게 만들어줘요.',
    ('정인', '편관'): '귀인이나 윗사람의 지원이 외부 압박을 막아주는 해예요. 혼자 버티려 하지 말고 도움을 구하는 것이 이 해를 가장 효율적으로 넘기는 방법이에요.',
    ('정인', '정관'): '배움과 공식 인정이 맞물리는 해예요. 자격·시험·승진 등 오래 준비해온 것이 공식적으로 결실을 맺는 10년 중 가장 보람 있는 해예요.',
    ('정인', '편인'): '배움 에너지가 두 배로 강해지는 해예요. 깊은 연구와 전문성 탐구에 몰두하기 좋고, 이 시기에 쌓은 지식이 평생 자산이 돼요.',
    ('정인', '정인'): '귀인·지원·배움 에너지가 극대화되는 해예요. 좋은 사람들에게 둘러싸여 실력과 인품이 함께 성장하는 10년 중 가장 따뜻한 해예요.',
}


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

    cross_text = _DAEUN_SEWOON_CROSS.get((dg_ss, get_sipseong(ilgan, OHAENG_IDX[yg], yg % 2)), '')

    lines = [
        '---',
        f'🌊 **대운 맥락** — {CHEONGAN[dg]}{JIJI[dj]} 대운({age}세~) × {target_year}년 세운',
        '',
        f'**[ {label} ]** {msg}{amplify}',
    ]
    if cross_text:
        lines.append(f'> {cross_text}')
    if extra:
        lines.append(extra)
    lines.append('')
    return '\n'.join(lines)


_COMBO_CHIP = {
    '최길': ('#065f46', '#d1fae5', '#34d399'),
    '순풍': ('#065f46', '#ecfdf5', '#6ee7b7'),
    '안정': ('#166534', '#f0fdf4', '#86efac'),
    '반전': ('#1e40af', '#eff6ff', '#93c5fd'),
    '완충': ('#6d28d9', '#f5f3ff', '#c4b5fd'),
    '경계': ('#c2410c', '#fff7ed', '#fed7aa'),
    '주의': ('#991b1b', '#fff1f2', '#fca5a5'),
    '수비': ('#9d174d', '#fce7f3', '#f9a8d4'),
}

def _get_combo_label(pillars, daeun, target_year):
    ilgan = pillars[2][0]
    ya_oh, ya_name, _, _, _ = get_yongshin(pillars)
    _, _, ki_list = get_gyeokguk(pillars)
    ki_names = [OHAENG_NAMES[k] for k in ki_list]
    cur_dae = None
    for _a, _yr, _dg, _dj in daeun:
        if _yr <= target_year < _yr + 10:
            cur_dae = (_dg, _dj); break
    if cur_dae is None:
        return ''
    _dg, _dj = cur_dae
    dae_is_yong = (OHAENG_NAMES[OHAENG_IDX[_dg]] == ya_name or OHAENG_NAMES[OHAENG_IDX_J[_dj]] == ya_name)
    dae_is_ki   = (OHAENG_NAMES[OHAENG_IDX[_dg]] in ki_names or OHAENG_NAMES[OHAENG_IDX_J[_dj]] in ki_names)
    _yg, _yj = _year_pillar(target_year)
    sew_is_yong = (OHAENG_NAMES[OHAENG_IDX[_yg]] == ya_name or OHAENG_NAMES[OHAENG_IDX_J[_yj]] == ya_name)
    sew_is_ki   = (OHAENG_NAMES[OHAENG_IDX[_yg]] in ki_names or OHAENG_NAMES[OHAENG_IDX_J[_yj]] in ki_names)
    return {
        (True,False,True,False):'최길',(True,False,False,True):'주의',
        (False,True,True,False):'반전',(False,True,False,True):'수비',
        (True,False,False,False):'안정',(False,True,False,False):'완충',
        (False,False,True,False):'순풍',(False,False,False,True):'경계',
    }.get((dae_is_yong, dae_is_ki, sew_is_yong, sew_is_ki), '')

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

_ILJI_SIPSEONG_DESC = {
    '비견': ('🤝', '배우자가 나와 비슷한 에너지를 가진 타입이에요. 동등한 관계를 추구하지만 경쟁의식이 생기기 쉬워요. 각자의 영역을 인정하는 것이 핵심이에요.'),
    '겁재': ('⚔️', '배우자가 강한 자존심과 주도성을 가진 타입이에요. 관계에서 주도권 경쟁이 생기기 쉬워요. 역할 분담이 명확할수록 관계가 안정돼요.'),
    '식신': ('🎨', '배우자가 재능 있고 여유로운 타입이에요. 삶을 즐길 줄 알고 창의적이에요. 함께 있으면 편안하고 풍요로운 에너지가 흘러요.'),
    '상관': ('🎭', '배우자가 개성 강하고 자유로운 영혼 타입이에요. 재능이 넘치지만 틀에 얽매이기 싫어해요. 자유를 주는 것이 관계의 핵심이에요.'),
    '편재': ('💫', '배우자가 사교적이고 활동적이에요. 재물 감각이 있고 외향적인 매력을 지닌 타입이에요. 넓은 인맥이 강점이에요.'),
    '정재': ('🏡', '배우자가 성실하고 현실적이에요. 안정을 중시하고 책임감이 강해요. 가정적이고 믿음직한 동반자예요.'),
    '편관': ('⚡', '배우자가 카리스마 있고 강렬해요. 강한 추진력을 가진 타입이에요. 때로 압박감을 줄 수 있으니 서로 여백이 필요해요.'),
    '정관': ('🏛️', '배우자가 원칙적이고 책임감이 강해요. 사회적으로 신뢰받는 타입으로 안정적인 관계를 만들어줘요.'),
    '편인': ('📚', '배우자가 독특하고 학문적이에요. 자신만의 세계가 뚜렷한 타입이에요. 감정 표현보다 지적 교감을 더 중요하게 여겨요.'),
    '정인': ('🌸', '배우자가 포용력 있고 따뜻해요. 안정적인 타입으로 배려심이 깊어요. 정서적 안정감을 주는 동반자예요.'),
}

def _render_baewuja_section(pillars, gender):
    ilgan = pillars[2][0]
    ilji  = pillars[2][1]
    sp    = _ILJI_SPOUSE[ilji]
    unsung = get_12unsung(ilgan, ilji)
    us_icon, us_desc = _UNSUNG_SPOUSE_DESC.get(unsung, ('', ''))
    hap_name   = _ILJI_SPOUSE[sp['hap_ji']]['name']
    chung_name = _ILJI_SPOUSE[sp['chung_ji']]['name']
    gender_str = '남편' if gender == '여' else '아내'

    # 일지 정기 십성 계산
    jjgan_idx = JIJANGAN_IDX[ilji][-1]
    jjgan_oh  = OHAENG_IDX[jjgan_idx]
    ss        = get_sipseong(ilgan, jjgan_oh, jjgan_idx % 2)
    ss_icon, ss_desc = _ILJI_SIPSEONG_DESC.get(ss, ('', ''))

    # 배우자 궁 충 손상 여부
    chung_ji_idx = (ilji + 6) % 12
    other_jijis  = [pillars[i][1] for i in range(4) if i != 2]
    is_chung_dmg = chung_ji_idx in other_jijis

    # 배우자성 직접 해당 여부 (남=재성, 여=관성)
    bae_ss_set   = {'편재', '정재'} if gender != '여' else {'편관', '정관'}
    is_bae_direct = ss in bae_ss_set
    bae_nm       = '처성' if gender != '여' else '부성'

    chung_tag = '<span style="color:#dc2626;font-weight:700;">&nbsp;⚡ 배우자 궁 충</span>' if is_chung_dmg else ''
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#fdf4ff,#ede9fe);border:1px solid #c4b5fd;'
        f'border-radius:12px;padding:14px 18px;margin-bottom:12px;">'
        f'<div style="font-size:0.75rem;font-weight:700;color:#7c3aed;margin-bottom:4px;">💍 배우자 자리(日支宮)</div>'
        f'<div style="font-size:1.1rem;font-weight:800;color:#374151;">{JIJI[ilji]} — {sp["name"]}</div>'
        f'<div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">'
        f'십이운성: <b>{unsung}</b> {us_icon} &nbsp;·&nbsp; 일지 십성: <b>{ss}</b> {ss_icon}{chung_tag}'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'**{gender_str} 성향**\n\n{sp["desc"]}')
    st.markdown(f'**관계 스타일**\n\n{sp["style"]}')
    if us_desc:
        st.markdown(f'**배우자 자리 에너지**\n\n{us_desc}')

    # 일지 십성 기반 배우자 특성
    if ss_desc:
        tag_col = '#7c3aed' if is_bae_direct else '#374151'
        tag_bg  = '#f5f3ff' if is_bae_direct else '#f9fafb'
        tag_bd  = '#c4b5fd' if is_bae_direct else '#e5e7eb'
        direct_tag = (
            f'<span style="font-size:0.7rem;background:#ede9fe;color:#7c3aed;'
            f'border-radius:4px;padding:1px 7px;margin-left:6px;font-weight:700;">'
            f'{bae_nm} 직접 해당</span>'
        ) if is_bae_direct else ''
        st.markdown(
            f'<div style="background:{tag_bg};border:1px solid {tag_bd};border-radius:10px;'
            f'padding:12px 16px;margin:10px 0;">'
            f'<div style="font-size:0.78rem;font-weight:700;color:{tag_col};margin-bottom:4px;">'
            f'{ss_icon} 일지 십성 — {ss}{direct_tag}</div>'
            f'<div style="font-size:0.83rem;color:#374151;line-height:1.6;">{ss_desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # 배우자 궁 충 손상 경고
    if is_chung_dmg:
        st.markdown(
            f'<div style="background:#fff1f2;border:1px solid #fca5a5;border-radius:10px;'
            f'padding:12px 16px;margin:10px 0;">'
            f'<div style="font-size:0.78rem;font-weight:700;color:#b91c1c;margin-bottom:4px;">⚡ 배우자 궁 충(冲) 손상</div>'
            f'<div style="font-size:0.83rem;color:#374151;line-height:1.6;">'
            f'일지 {JIJI[ilji]}이 사주 내 {JIJI[chung_ji_idx]}와 충을 이루고 있어요. '
            f'배우자 자리가 흔들려 결혼·관계 유지에 불안정함이 나타날 수 있어요. '
            f'이별이나 갈등을 반복하기 쉬운 구조이므로 소통과 배려를 의식적으로 챙겨야 해요.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

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

_ILJU_CORE = {
    (0,0):  '지적 호기심과 추진력으로 선두를 이끄는 헌신적 개척자',
    (0,2):  '강한 독립심과 카리스마로 자신의 길을 개척하는 원칙주의 자수성가형',
    (0,4):  '깊은 전문성과 포용력으로 든든한 안정을 만드는 큰 그릇',
    (0,6):  '뜨거운 열정과 탁월한 표현력으로 무대를 장악하는 솔직한 리더',
    (0,8):  '냉철한 분석력으로 위기를 기회로 바꾸는 전략적 실행가',
    (0,10): '원칙과 완벽주의로 고독하게 전문성을 쌓아가는 고집스러운 장인',
    (1,1):  '끈질긴 생명력과 인내로 현실을 탄탄하게 쌓아가는 실용주의자',
    (1,3):  '풍부한 감성과 창의성으로 세상과 유연하게 소통하는 예술가형',
    (1,5):  '신비로운 집중력과 전략으로 조용히 목표를 달성하는 숨은 강자',
    (1,7):  '따뜻한 배려와 감성으로 주변 사람을 품는 인화(人和)의 달인',
    (1,9):  '높은 자존감과 완벽주의로 세련되게 빛나는 보석형 인물',
    (1,11): '낭만적 이상과 지적 감성으로 깊은 세계를 탐구하는 철학자형',
    (2,0):  '열정적 지혜와 리더십으로 주변을 밝히는 태양 같은 존재',
    (2,2):  '타고난 카리스마와 강력한 추진력으로 집단을 이끄는 태양형 리더',
    (2,4):  '다재다능한 포용력으로 모든 것을 아우르는 전방위 리더',
    (2,6):  '극렬한 열정과 솔직한 직진으로 강렬한 존재감을 발하는 불꽃형',
    (2,8):  '냉철한 분석력과 뛰어난 변화 적응력으로 기회를 창출하는 전략가',
    (2,10): '굳은 원칙과 고집으로 한 분야의 권위자가 되는 전문가형',
    (3,1):  '섬세한 인내와 현실 감각으로 꾸준히 기반을 다지는 안정형',
    (3,3):  '풍부한 감수성과 창의력으로 따뜻한 세계를 만드는 감성 예술가',
    (3,5):  '강렬한 집중력과 뜨거운 열정으로 욕망을 현실로 만드는 실행가',
    (3,7):  '높은 감성 지능과 따뜻한 예술성으로 사람의 마음을 움직이는 인물',
    (3,9):  '섬세한 완벽주의와 강한 자존심으로 최고를 추구하는 장인',
    (3,11): '낭만적 지혜와 이상주의로 세상을 더 아름답게 꿈꾸는 사상가',
    (4,0):  '믿음직한 포용력과 중용의 덕으로 기둥 같은 역할을 하는 대인(大人)',
    (4,2):  '대범한 리더십과 도전 정신으로 새로운 영역을 개척하는 선봉장',
    (4,4):  '산처럼 묵직한 저력과 고집으로 끝내 해내는 불굴의 의지형',
    (4,6):  '열정적 리더십과 직선적 실행력으로 집단을 이끄는 에너지 넘치는 지도자',
    (4,8):  '실용적 분석력과 뛰어난 변화 적응력으로 환경을 이용하는 전략가',
    (4,10): '완고한 원칙과 인내로 오랜 시간에 걸쳐 큰 성취를 이루는 불굴형',
    (5,1):  '성실한 현실 감각과 인내로 탄탄한 재물 기반을 쌓는 최고의 관리자',
    (5,3):  '감성과 배려로 유연하게 인간관계를 엮어가는 조율의 달인',
    (5,5):  '집중력과 전략으로 현실적 목표를 착실하게 달성하는 실행가',
    (5,7):  '섬세한 포용력과 온화함으로 편안한 안정감을 주는 토대형 인물',
    (5,9):  '정밀함과 높은 자존감으로 완성도 있는 결과물을 만드는 장인',
    (5,11): '지혜로운 이상주의와 학문으로 깊이 있는 전문가를 지향하는 사색가',
    (6,0):  '날카로운 통찰력과 냉철함으로 전략을 설계하는 지혜로운 실행가',
    (6,2):  '거침없는 카리스마와 직선적 도전 정신으로 모든 장벽을 부수는 개척자',
    (6,4):  '든든한 저력과 전문성으로 두터운 신뢰를 쌓는 안정적 권위자',
    (6,6):  '폭발적 열정과 추진력으로 강렬하게 결과를 만드는 에너지 충만형',
    (6,8):  '냉철한 완벽주의와 강한 독립심으로 최고 수준을 고집하는 강인한 전문가',
    (6,10): '고독한 원칙주의로 한 분야의 깊은 전문성을 쌓아가는 권위자',
    (7,1):  '냉철한 섬세함과 인내로 원석을 다듬어 빛나는 보석을 만드는 장인',
    (7,3):  '탁월한 예술성과 감수성으로 유연하게 세상을 아름답게 표현하는 감각파',
    (7,5):  '전략적 날카로움과 집중력으로 조용하지만 강하게 성과를 내는 숨은 강자',
    (7,7):  '온화한 감성과 깊은 배려로 사람의 마음을 자연스럽게 끌어당기는 자석형',
    (7,9):  '극도로 정밀한 완벽주의와 강한 자존심으로 타협 없는 최고를 추구하는 보석형',
    (7,11): '낭만적 지혜와 예술성으로 깊은 전문성과 감성을 겸비한 예술가형 전문가',
    (8,0):  '깊은 통찰력과 유연성으로 세상의 흐름을 읽어내는 물의 지혜자',
    (8,2):  '왕성한 활동력과 다재다능함으로 끊임없이 새로운 도전을 즐기는 탐험가',
    (8,4):  '거대한 포용력과 숨겨진 저력으로 다양성을 품는 큰 물의 에너지',
    (8,6):  '수화(水火)의 역동적 충돌로 강렬하고 다이나믹한 삶의 에너지를 뿜는 인물',
    (8,8):  '지혜로운 분석력과 뛰어난 변화 적응력으로 어떤 환경에서도 길을 찾는 전략가',
    (8,10): '원칙과 깊이로 고집스럽게 전문성을 추구하는 묵직한 수행자',
    (9,1):  '꼼꼼한 인내와 뛰어난 현실 감각으로 재물을 착실히 쌓는 관리형',
    (9,3):  '풍부한 감성과 창의력으로 유연하게 세상과 소통하는 예술가형',
    (9,5):  '신비로운 집중력과 전략적 사고로 깊은 잠재력을 발휘하는 숨은 실력자',
    (9,7):  '높은 감성 지능과 온화한 배려로 사람들의 마음을 따뜻하게 안내하는 인물',
    (9,9):  '극도로 섬세한 완벽주의와 정밀함으로 최고 수준의 결과물을 만드는 장인',
    (9,11): '깊은 이상주의와 지혜로 내면의 세계를 탐구하는 현자(賢者)',
}

_UNS_ICON = {
    '장생':'🌱','목욕':'✨','관대':'🎓','건록':'💼','제왕':'👑',
    '쇠':'🍃','병':'🌙','사':'🕊','묘':'🌿','절':'🌊','태':'🌸','양':'🌼',
}
_UNS_SHORT = {
    '장생':'성장·시작','목욕':'감성·매력','관대':'패기·도전','건록':'자립·전문',
    '제왕':'절정·카리스마','쇠':'성숙·안정','병':'감수성·깊이','사':'변화·전환',
    '묘':'숙성·집중','절':'비움·재시작','태':'잉태·가능성','양':'양육·준비',
}

def _render_ilju_card(name, pillars, no_time=False):
    from saju import _ilju_text, UNSUNG_DESC, get_12unsung
    ilgan = pillars[2][0]
    ilji  = pillars[2][1]
    ilju_name = CHEONGAN[ilgan] + JIJI[ilji]
    extra = _ILJU_EXTRA.get((ilgan, ilji), {})
    _core  = _ILJU_CORE.get((ilgan, ilji), '')
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
    if _core:
        st.markdown(
            f'<div style="background:#f5f3ff;border-left:3px solid #8b5cf6;'
            f'border-radius:0 8px 8px 0;padding:8px 14px;margin-bottom:10px;">'
            f'<span style="font-size:0.88rem;font-weight:700;color:#5b21b6;">{_core}</span>'
            f'</div>',
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
    # ── 십이운성(十二運星) ──────────────────────────────────────────
    st.markdown('---')
    st.markdown('**🌙 십이운성(十二運星) — 각 주의 에너지 단계**')
    _order  = [0, 1, 2] if no_time else [0, 1, 2, 3]
    _labels = ['년주', '월주', '일주'] if no_time else ['년주', '월주', '일주', '시주']
    _cols   = st.columns(len(_order))
    for col, idx, lbl in zip(_cols, _order, _labels):
        _g, _j = pillars[idx]
        _uns = get_12unsung(ilgan, _j)
        _icon  = _UNS_ICON.get(_uns, '')
        _short = _UNS_SHORT.get(_uns, _uns)
        _is_il = (idx == 2)
        _bg    = 'linear-gradient(135deg,#fdf4ff,#ede9fe)' if _is_il else '#f8fafc'
        _bdr   = '2px solid #c4b5fd' if _is_il else '1px solid #e2e8f0'
        col.markdown(
            f'<div style="background:{_bg};border:{_bdr};border-radius:10px;'
            f'padding:10px 6px;text-align:center;">'
            f'<div style="font-size:0.65rem;color:#6b7280;font-weight:600;margin-bottom:2px;">{lbl}</div>'
            f'<div style="font-size:1.3rem;line-height:1.2;">{_icon}</div>'
            f'<div style="font-size:0.9rem;font-weight:800;color:#374151;">{_uns}</div>'
            f'<div style="font-size:0.6rem;color:#6b7280;margin-top:1px;">{_short}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown('')
    il_uns = get_12unsung(ilgan, ilji)
    il_desc = UNSUNG_DESC.get(il_uns, '')
    if il_desc:
        st.markdown(f'**일주 {_UNS_ICON.get(il_uns,"")} {il_uns} — 상세**')
        st.markdown(il_desc)
    # ────────────────────────────────────────────────────────────
    st.markdown('')
    if base_text:
        st.markdown(base_text)


def _render_thisyear_section(name, pillars, birth_year, card_id="main", rel_status='솔로', daeun=None):
    cur = datetime.now(_KST).year
    if daeun:
        dae_start = min(yr for _, yr, _, _ in daeun)
        dae_end   = max(yr for _, yr, _, _ in daeun) + 9
        year_range = list(range(min(dae_start, cur - 3), max(dae_end, cur + 8) + 1))
    else:
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


# 일간(0-9) × 용신오행('목'/'화'/'토'/'금'/'수') 맞춤 코멘트
_ILGAN_YONGSHIN_COMMENT = {
    (0,'목'): '갑목이 木 기운을 용신으로 삼으면 같은 나무의 힘이 더해지는 구조예요. 동료·파트너와의 협력으로 빠르게 성장하고, 의지를 모아 큰 나무를 이루세요.',
    (0,'화'): '갑목에게 火 기운은 내가 가진 에너지를 세상에 드러내는 불꽃이에요. 배운 것을 표현하고 사람들과 소통하는 활동이 당신의 가능성을 활짝 열어줘요.',
    (0,'토'): '갑목에게 土 기운은 뿌리내릴 땅이자 현실적인 결과를 만드는 자리예요. 구체적인 목표와 현실적인 계획에 집중할수록 재물과 성취가 따라와요.',
    (0,'금'): '갑목에게 金 기운은 나를 다듬고 방향을 잡아주는 칼이에요. 규칙과 책임을 통해 나무가 곧게 자라듯, 원칙과 기강이 당신을 더 강하게 만들어요.',
    (0,'수'): '갑목에게 水 기운은 깊이 있는 성장을 가능하게 하는 물이에요. 공부·경험·선배의 조언이 뿌리를 튼튼하게 하고, 큰 성장을 위한 자양분이 돼요.',
    (1,'목'): '을목이 木 기운을 용신으로 삼으면 넝쿨이 지지대를 만난 것처럼 힘이 배가돼요. 주변의 협력자를 잘 활용해 원하는 자리까지 유연하게 올라가세요.',
    (1,'화'): '을목에게 火 기운은 섬세한 감성을 세상과 연결하는 통로예요. 자신의 이야기와 표현을 아끼지 않을수록 사람들이 당신의 매력에 끌려와요.',
    (1,'토'): '을목에게 土 기운은 유연함이 현실로 이어지는 토대예요. 아이디어를 실행으로 옮기고 구체적인 성과를 만들어내는 활동이 운을 열어줘요.',
    (1,'금'): '을목에게 金 기운은 내가 뻗어나가는 방향을 정리해주는 가위예요. 명확한 역할과 책임을 받아들일수록 성장의 속도가 붙어요.',
    (1,'수'): '을목에게 水 기운은 뿌리에 스며드는 촉촉한 자양분이에요. 배움과 사색을 통해 내면을 채울수록 밖으로 드러나는 힘도 커져요.',
    (2,'목'): '병화에게 木 기운은 활활 타오르는 불에 땔감을 더하는 원천이에요. 배경을 쌓고 실력을 키울수록 당신의 빛이 더 오래, 더 강하게 타올라요.',
    (2,'화'): '병화가 火 기운을 용신으로 삼으면 태양이 더 밝게 빛나는 구조예요. 리더십과 존재감을 적극적으로 표출할수록 주변을 이끄는 힘이 커져요.',
    (2,'토'): '병화에게 土 기운은 열정이 결실로 이어지는 연결고리예요. 아이디어에서 끝내지 않고 실행까지 마무리하는 습관이 큰 성과를 만들어요.',
    (2,'금'): '병화에게 金 기운은 넘치는 에너지가 가치로 바뀌는 통로예요. 재물을 다루고 현실적인 이익을 관리하는 능력이 당신의 강점이 돼요.',
    (2,'수'): '병화에게 水 기운은 강렬함을 절제해주는 균형추예요. 원칙과 규율이 열정에 방향을 잡아줄 때 훨씬 더 큰 영향력이 생겨요.',
    (3,'목'): '정화에게 木 기운은 촛불을 오래 태우는 심지 같은 존재예요. 충분한 배움과 내면의 성찰이 당신의 깊은 감수성을 더욱 빛나게 해줘요.',
    (3,'화'): '정화가 火 기운을 용신으로 삼으면 내면의 빛이 더 따뜻하게 퍼지는 구조예요. 진심 어린 표현과 감성적인 교류가 관계를 따뜻하게 이어줘요.',
    (3,'토'): '정화에게 土 기운은 섬세한 능력이 현실에서 인정받는 열쇠예요. 일 처리를 꼼꼼히 마무리하고 결과물을 착실히 쌓아갈수록 인정이 따라와요.',
    (3,'금'): '정화에게 金 기운은 예리한 감각이 가치를 만드는 도구예요. 재물을 현명하게 다루고 분석력을 활용하면 경제적 안정이 빠르게 다가와요.',
    (3,'수'): '정화에게 水 기운은 빛이 너무 강하지 않도록 잡아주는 어둠이에요. 겸손함과 절제를 통해 본래의 섬세함이 더욱 깊어질 수 있어요.',
    (4,'목'): '무토에게 木 기운은 넓은 대지를 깨우는 생기예요. 규율과 책임을 부여받을수록 크고 안정적인 역량이 발휘되는 구조예요.',
    (4,'화'): '무토에게 火 기운은 굳은 땅을 따뜻하게 데워주는 햇살이에요. 신뢰할 수 있는 배경과 지원자가 생기면 당신의 능력이 훨씬 잘 발휘돼요.',
    (4,'토'): '무토가 土 기운을 용신으로 삼으면 산이 더 높아지는 구조예요. 두터운 원칙과 안정감이 강점이 되고, 든든한 존재감으로 신뢰를 얻어요.',
    (4,'금'): '무토에게 金 기운은 땅 속의 보물을 드러내는 역할이에요. 재능을 표현하고 기술을 갈고닦을수록 당신의 가치가 바깥으로 빛나요.',
    (4,'수'): '무토에게 水 기운은 메마른 땅을 적시는 생명수예요. 유연성과 융통성을 발휘할수록 고집에서 벗어나 현실적인 이익이 늘어나요.',
    (5,'목'): '기토에게 木 기운은 부드러운 흙을 단단하게 잡아주는 뿌리예요. 리더십 있는 인물이나 역할이 주어질 때 당신의 능력이 가장 잘 발휘돼요.',
    (5,'화'): '기토에게 火 기운은 촉촉한 흙을 데워주는 온기예요. 신뢰할 수 있는 지원자나 멘토가 옆에 있을 때 가장 안정적으로 성장해요.',
    (5,'토'): '기토가 土 기운을 용신으로 삼으면 비옥한 밭이 더 풍요로워지는 구조예요. 성실함과 꾸준함으로 주변에 신뢰와 결실을 함께 나눠줄 수 있어요.',
    (5,'금'): '기토에게 金 기운은 섬세한 손재주가 더욱 빛나는 원천이에요. 실용적인 기술과 표현 능력을 갈고닦을수록 인정과 수익이 자연스럽게 따라와요.',
    (5,'수'): '기토에게 水 기운은 영양분을 녹여서 흡수하는 촉매예요. 다양한 경험과 지식을 흡수해 실용적으로 활용하는 능력이 강해져요.',
    (6,'목'): '경금에게 木 기운은 날카로운 칼이 깎아야 할 재료예요. 도전하고 개척할 대상이 생길수록 당신의 추진력과 능력이 빛을 발해요.',
    (6,'화'): '경금에게 火 기운은 나를 단련하고 벼리는 용광로예요. 엄격한 기준과 통제가 더해질수록 원칙 있는 리더십으로 신뢰를 쌓을 수 있어요.',
    (6,'토'): '경금에게 土 기운은 날카로움을 보호하고 뒷받침해주는 배경이에요. 든든한 지원자나 탄탄한 기반이 생길 때 능력이 가장 안정적으로 발휘돼요.',
    (6,'금'): '경금이 金 기운을 용신으로 삼으면 강철이 더욱 단단해지는 구조예요. 원칙과 기준을 더욱 확고하게 세울수록 신뢰도와 영향력이 커져요.',
    (6,'수'): '경금에게 水 기운은 날카로움이 지혜로 이어지는 흐름이에요. 실력을 갈고닦고 전략적으로 흘러가는 능력이 더욱 강해질 수 있어요.',
    (7,'목'): '신금에게 木 기운은 예리한 감각이 실용적으로 쓰이는 무대예요. 다채로운 도전과 현장 경험이 당신의 섬세함을 더욱 가치 있게 만들어요.',
    (7,'화'): '신금에게 火 기운은 빛나는 보석을 더욱 선명하게 드러내는 열기예요. 명확한 원칙과 책임감이 더해질 때 당신의 우아한 능력이 더욱 빛나요.',
    (7,'토'): '신금에게 土 기운은 보석의 가치를 지켜주는 토양이에요. 안정적인 환경과 지원자가 있을 때 당신의 섬세한 능력이 가장 잘 꽃피워요.',
    (7,'금'): '신금이 金 기운을 용신으로 삼으면 보석이 더욱 정교해지는 구조예요. 완벽함을 추구하는 성향이 강점이 되고, 전문성이 높아질수록 진가를 인정받아요.',
    (7,'수'): '신금에게 水 기운은 예리함이 섬세한 직관으로 이어지는 흐름이에요. 지식과 통찰을 깊이 흡수할수록 독보적인 전문가로 성장해요.',
    (8,'목'): '임수에게 木 기운은 넘치는 에너지를 성장과 결실로 이끄는 흐름이에요. 생산적인 활동에 에너지를 쏟을수록 재능이 구체적인 성과로 연결돼요.',
    (8,'화'): '임수에게 火 기운은 방대한 흐름을 현실적인 이익으로 연결하는 열원이에요. 재물과 경제적 활동에 집중할수록 풍요로움이 쌓여가요.',
    (8,'토'): '임수에게 土 기운은 흐르는 강물에 방향을 만들어주는 제방이에요. 원칙과 규율이 잡힐수록 방대한 에너지가 더욱 효율적으로 쓰여요.',
    (8,'금'): '임수에게 金 기운은 물이 맑게 솟아오르는 원천이에요. 배움과 지식, 조언자가 풍부할수록 지혜가 더욱 깊고 강하게 흘러요.',
    (8,'수'): '임수가 水 기운을 용신으로 삼으면 강물이 더욱 거세지는 구조예요. 유연하고 포용적인 리더십으로 주변 사람들을 자연스럽게 이끌 수 있어요.',
    (9,'목'): '계수에게 木 기운은 빗물이 스며들어 새싹을 틔우듯 재능이 결실로 이어지는 흐름이에요. 작은 노력도 성실히 쌓아갈수록 의미 있는 성과가 나와요.',
    (9,'화'): '계수에게 火 기운은 섬세한 감성이 현실적인 가치로 연결되는 따뜻한 불빛이에요. 감성 자원을 성과로 이어가는 활동에서 운이 열려요.',
    (9,'토'): '계수에게 土 기운은 맑은 빗물을 담아두는 항아리예요. 체계와 규율을 받아들일수록 섬세함이 흐트러지지 않고 안정적으로 유지돼요.',
    (9,'금'): '계수에게 金 기운은 직관이 더욱 날카로운 통찰로 이어지는 원천이에요. 깊이 있는 학습과 전문 지식을 쌓을수록 독보적인 능력이 빛나요.',
    (9,'수'): '계수가 水 기운을 용신으로 삼으면 빗물이 모여 맑은 샘을 이루는 구조예요. 감수성과 직관을 더욱 깊게 발휘하고, 세밀한 통찰력이 강점이 돼요.',
}

_OH_SUPPLEMENT = {
    '목': {
        'icon': '🌿', 'organ': '간·담·눈·근육',
        'colors': [('#22c55e','초록'), ('#3b82f6','파랑'), ('#14b8a6','청록')],
        'direction': '동쪽', 'number': '3, 8', 'taste': '신맛',
        'foods': ['레몬·매실·사과 등 신 과일', '시금치·브로콜리 등 녹색 채소', '식초 활용 요리'],
        'items': ['화분·식물 키우기', '목재 소품·책상', '초록·파랑 계열 소품'],
        'activities': ['아침 스트레칭·요가', '숲속 산책·등산', '창의적 글쓰기·계획 세우기'],
        'tip': '동쪽 창가 자리나 식물이 잘 자라는 환경이 좋아요.',
    },
    '화': {
        'icon': '🔥', 'organ': '심장·소장·혀·혈관',
        'colors': [('#ef4444','빨강'), ('#f97316','주황'), ('#ec4899','분홍')],
        'direction': '남쪽', 'number': '2, 7', 'taste': '쓴맛',
        'foods': ['씀바귀·여주 등 쓴 채소', '붉은 과일 (토마토·딸기·석류)', '홍차·루이보스티'],
        'items': ['캔들·조명 밝히기', '빨강·주황 계열 소품', '삼각형 패턴'],
        'activities': ['달리기·자전거 등 활기찬 운동', '사교 모임·네트워킹', '음악 듣기·댄스'],
        'tip': '남향 자리나 밝은 조명 환경에서 에너지가 살아나요.',
    },
    '토': {
        'icon': '🏔️', 'organ': '위·비장·근육·입',
        'colors': [('#eab308','황색'), ('#92400e','갈색'), ('#d4b896','베이지')],
        'direction': '중앙', 'number': '5, 10', 'taste': '단맛',
        'foods': ['단호박·고구마·옥수수', '꿀·대추·견과류', '황색 채소 (당근·생강)'],
        'items': ['도자기·토기 소품', '황토·베이지 인테리어', '사각형 패턴'],
        'activities': ['명상·마음챙김', '정원 가꾸기·텃밭', '요리·베이킹'],
        'tip': '안정된 중앙 자리, 흙냄새 나는 자연 환경이 좋아요.',
    },
    '금': {
        'icon': '💎', 'organ': '폐·대장·피부·코',
        'colors': [('#f8fafc','흰색'), ('#94a3b8','은색'), ('#e2e8f0','회색')],
        'direction': '서쪽', 'number': '4, 9', 'taste': '매운맛',
        'foods': ['무·배·도라지', '마늘·고추·생강', '흰색 음식 (두부·마)'],
        'items': ['금속 소품·악기', '흰색·실버 인테리어', '원형·구형 패턴'],
        'activities': ['호흡법·명상', '정리정돈·미니멀라이프', '가을 산행·건식 사우나'],
        'tip': '서쪽 창가나 깔끔하게 정돈된 환경이 금 기운을 강화해요.',
    },
    '수': {
        'icon': '💧', 'organ': '신장·방광·귀·뼈',
        'colors': [('#1e40af','남색'), ('#1d4ed8','짙은 파랑'), ('#1e1b4b','검정')],
        'direction': '북쪽', 'number': '1, 6', 'taste': '짠맛',
        'foods': ['미역·다시마·해산물', '검은콩·흑깨·블루베리', '된장·간장 등 발효 음식'],
        'items': ['수족관·탁상 분수', '검정·남색 소품', '물결·파도 패턴'],
        'activities': ['수영·목욕·반신욕', '독서·사색·글쓰기', '밤 산책·달 보기'],
        'tip': '북쪽 방향이나 물이 보이는 환경에서 집중력과 지혜가 강화돼요.',
    },
}

_WONJIN_PAIRS = [
    frozenset([0,7]), frozenset([1,6]), frozenset([2,9]),
    frozenset([3,8]), frozenset([4,11]), frozenset([5,10]),
]

def _sewoon_hyeong_wonjin(pil_jijis, sw_ji):
    pil_set = set(pil_jijis)
    hyeong = []
    if sw_ji in {0, 3} and ({0, 3} - {sw_ji}) & pil_set:
        hyeong.append('자묘형')
    if sw_ji in {2, 5, 8} and {2, 5, 8} & pil_set:
        hyeong.append('인사신형')
    if sw_ji in {1, 7, 10} and {1, 7, 10} & pil_set:
        hyeong.append('축술미형')
    if sw_ji in {4, 6, 9, 11} and sw_ji in pil_set:
        hyeong.append('자형')
    wonjin = []
    for _pair in _WONJIN_PAIRS:
        if sw_ji in _pair:
            _other = next(iter(_pair - {sw_ji}))
            if _other in pil_set:
                wonjin.append(f'원진({JIJI[sw_ji]}{JIJI[_other]})')
    return hyeong, wonjin

def _render_sewoon_section(name, pillars, birth_year, daeun, card_id="main"):
    cur = datetime.now(_KST).year
    ilgan = pillars[2][0]
    sewoon = get_sewoon(birth_year, past=5, future=10)

    def _daeun_str(y):
        for _, yr, dg, dj in daeun:
            if yr <= y < yr + 10:
                return f'{CHEONGAN[dg]}{JIJI[dj]}'
        return '─'

    _GRADE_TL = {
        '대길': ('#065f46','#d1fae5','#34d399','⬆⬆'),
        '길':   ('#166534','#f0fdf4','#86efac','⬆'),
        '중립': ('#1e40af','#eff6ff','#93c5fd','→'),
        '주의': ('#c2410c','#fff7ed','#fdba74','⬇'),
        '흉':   ('#991b1b','#fff1f2','#fca5a5','⬇⬇'),
        '대흉': ('#7f1d1d','#fce7f3','#f9a8d4','⚠'),
    }
    tl_html = '<div style="position:relative;padding-left:28px;margin:8px 0;">'
    tl_html += '<div style="position:absolute;left:12px;top:0;bottom:0;width:2px;background:#e5e7eb;"></div>'
    pil_jijis = [p[1] for p in pillars]
    daeun_yrs = {yr for _, yr, _, _ in daeun}
    _sw_gm = get_gongmang(*pillars[2])
    for y, age, yg, yj in sewoon:
        ss_g, ss_j = _sewoon_ss(ilgan, yg, yj)
        grade, desc = _SEWOON_SS_DESC.get(ss_g, ('중립', ''))
        tc, bg, bd, icon = _GRADE_TL.get(grade, ('#374151','#f9fafb','#e5e7eb','→'))
        is_cur = (y == cur)
        dot_bg = tc if not is_cur else '#f59e0b'
        dot_border = '3px solid #f59e0b' if is_cur else f'2px solid {bd}'
        card_bg = '#fffbeb' if is_cur else bg
        card_bd = '#fbbf24' if is_cur else bd
        cur_tag = '<span style="font-size:0.62rem;background:#fef3c7;color:#92400e;border-radius:3px;padding:1px 5px;margin-left:5px;font-weight:700;">올해</span>' if is_cur else ''
        daeun_s = _daeun_str(y)
        grade_chip = (
            f'<span style="background:{bg};border:1px solid {bd};color:{tc};'
            f'padding:2px 9px;border-radius:10px;font-size:0.75rem;font-weight:700;">'
            f'{icon} {grade}</span>'
        )
        _hy, _wj = _sewoon_hyeong_wonjin(pil_jijis, yj)
        _hw_chips = ''.join(
            f'<span style="background:#fef2f2;border:1px solid #fca5a5;color:#b91c1c;'
            f'padding:1px 7px;border-radius:8px;font-size:0.7rem;font-weight:600;margin-right:4px;">⚡ {h}</span>'
            for h in _hy
        ) + ''.join(
            f'<span style="background:#fff7ed;border:1px solid #fed7aa;color:#c2410c;'
            f'padding:1px 7px;border-radius:8px;font-size:0.7rem;font-weight:600;margin-right:4px;">😤 {w}</span>'
            for w in _wj
        )
        _hw_row = f'<span style="margin-left:8px;">{_hw_chips}</span>' if _hw_chips else ''
        # 대운 교체 시점 체크
        if y in daeun_yrs:
            _da_tag, _da_st = '🔄 대운 교체', 'background:#fef3c7;border:1px solid #fcd34d;color:#92400e;'
        elif (y + 1) in daeun_yrs:
            _da_tag, _da_st = '⏳ 교체 임박', 'background:#fff7ed;border:1px solid #fed7aa;color:#c2410c;'
        elif (y - 1) in daeun_yrs:
            _da_tag, _da_st = '✨ 새 대운', 'background:#f5f3ff;border:1px solid #c4b5fd;color:#7c3aed;'
        else:
            _da_tag, _da_st = '', ''
        _da_chip = (
            f'<span style="{_da_st}padding:1px 7px;border-radius:8px;'
            f'font-size:0.7rem;font-weight:700;margin-left:5px;">{_da_tag}</span>'
        ) if _da_tag else ''
        _cl = _get_combo_label(pillars, daeun, y)
        if _cl and _cl in _COMBO_CHIP:
            _ctc, _cbg, _cbd = _COMBO_CHIP[_cl]
            _combo_chip = (
                f'<span style="color:{_ctc};background:{_cbg};border:1px solid {_cbd};'
                f'padding:1px 7px;border-radius:8px;font-size:0.7rem;font-weight:700;margin-left:5px;">'
                f'대운×세운 {_cl}</span>'
            )
        else:
            _combo_chip = ''
        _gm_chip = (
            '<span style="background:#1f2937;color:#f9fafb;border:1px solid #374151;'
            'padding:1px 7px;border-radius:8px;font-size:0.7rem;font-weight:700;margin-left:5px;">'
            '⬛ 공망</span>'
        ) if yj in _sw_gm else ''
        tl_html += (
            f'<div style="position:relative;margin-bottom:9px;">'
            f'<div style="position:absolute;left:-20px;top:11px;width:10px;height:10px;'
            f'border-radius:50%;background:{dot_bg};border:{dot_border};"></div>'
            f'<div style="background:{card_bg};border:1px solid {card_bd};border-radius:10px;padding:9px 13px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div style="font-size:0.88rem;font-weight:700;color:#111827;">'
            f'{y}년{cur_tag} '
            f'<span style="font-size:0.78rem;font-weight:400;color:#6b7280;">{age}세 · {CHEONGAN[yg]}{JIJI[yj]}년 · 대운 {daeun_s}</span>'
            f'</div>{grade_chip}</div>'
            f'<div style="font-size:0.8rem;color:#374151;margin-top:4px;">'
            f'천간 {ss_g} · 지지 {ss_j}{_hw_row}{_da_chip}{_combo_chip}{_gm_chip}</div>'
            f'</div></div>'
        )
    tl_html += '</div>'
    st.markdown(tl_html, unsafe_allow_html=True)
    st.divider()
    _narr(analyze_sewoon_narrative(name, pillars, birth_year))

    # 세운 월운 연동
    st.markdown(
        '<div style="font-size:0.82rem;font-weight:700;color:#6d28d9;margin:14px 0 6px;">'
        '🌙 월운 상세 조회</div>',
        unsafe_allow_html=True,
    )
    _sw_yrs = [_y for _y, *_ in sewoon]
    _safe_n = (name or 'default').replace(' ', '_')
    _sw_sel_yr = st.selectbox(
        '세운 연도 선택 → 해당 연도 12개월 월운',
        options=_sw_yrs,
        index=_sw_yrs.index(cur) if cur in _sw_yrs else 0,
        format_func=lambda _y: f'{_y}년 ({_y - birth_year + 1}세)',
        key=f'sw_wolun_{_safe_n}_{card_id}',
    )
    _render_wolun_section(
        pillars, birth_year, name=name,
        card_id=f'sw_{_safe_n}_{card_id}', fixed_year=_sw_sel_yr,
    )


def _render_wolun_section(pillars, year, name="", card_id="main", rel_status='솔로', fixed_year=None):
    cur = datetime.now(_KST).year
    cur_date = datetime.now(_KST).date()
    ilgan = pillars[2][0]

    safe_name = name.replace(" ", "_") if name else "default"
    if fixed_year is not None:
        sel_year = fixed_year
    else:
        sel_key = f"wolun_year_{safe_name}_{card_id}"
        year_range = list(range(cur - 2, cur + 4))
        sel_year = st.select_slider(
            "조회할 연도 선택",
            options=year_range,
            value=cur,
            key=sel_key,
        )

    wolun = get_wolun(sel_year)

    _, ya_name, _, _, _ = get_yongshin(pillars)
    _, _, ki_list = get_gyeokguk(pillars)
    ki_ohs = {OHAENG_NAMES[k] for k in ki_list}

    _GRADE_COLOR = {
        '대길': ('#1b5e20', '#e8f5e9', '#2e7d32'),
        '길':   ('#2e7d32', '#f1f8e9', '#4caf50'),
        '중립': ('#1565c0', '#e3f2fd', '#1976d2'),
        '주의': ('#e65100', '#fff3e0', '#ff9800'),
        '흉':   ('#b71c1c', '#ffebee', '#ef5350'),
        '대흉': ('#7f0000', '#fce4ec', '#c62828'),
    }

    months = []
    cur_idx = None
    for i, (label, st_dt, mg, mj) in enumerate(wolun):
        end_dt = wolun[i + 1][1].date() if i + 1 < len(wolun) else None
        is_cur = (st_dt.date() <= cur_date and (end_dt is None or cur_date < end_dt))
        if is_cur:
            cur_idx = i
        ss_g = get_sipseong(ilgan, OHAENG_IDX[mg], mg % 2)
        ss_j = get_sipseong(ilgan, OHAENG_IDX_J[mj], mj % 2)
        grade, desc = _SEWOON_SS_DESC.get(ss_g, ('중립', ''))
        mg_oh = OHAENG_NAMES[OHAENG_IDX[mg]]
        months.append({
            'label': label,
            'date': st_dt.strftime('%m/%d'),
            'gaji': f'{CHEONGAN[mg]}{JIJI[mj]}',
            'ss_g': ss_g,
            'ss_j': ss_j,
            'grade': grade,
            'desc': desc,
            'is_cur': is_cur,
            'is_next': False,
            'is_yong': mg_oh == ya_name,
            'is_ki':   mg_oh in ki_ohs,
        })

    if cur_idx is not None and cur_idx + 1 < len(months):
        months[cur_idx + 1]['is_next'] = True

    # ── 이달/다음달 강조 카드 (현재 연도만 표시) ──
    if sel_year == cur:
        cur_m  = next((m for m in months if m['is_cur']),  None)
        next_m = next((m for m in months if m['is_next']), None)
        if cur_m or next_m:
            cols = st.columns(2)
            pairs = [(cols[0], cur_m, '🌙 이달', '#7c4dff'),
                     (cols[1], next_m, '🔮 다음달', '#546e7a')]
            for col, mdata, badge, bcol in pairs:
                if not mdata:
                    continue
                tc, bg, ac = _GRADE_COLOR.get(mdata['grade'], ('#546e7a', '#f5f5f5', '#78909c'))
                _border = f'2px solid {bcol}' if mdata['is_cur'] else '1px solid #ddd'
                _short = mdata['desc'][:65] + '…' if len(mdata['desc']) > 65 else mdata['desc']
                if mdata['is_yong']:
                    _yk_badge = '<span style="font-size:0.7rem;font-weight:700;color:#065f46;background:#d1fae5;border:1px solid #6ee7b7;border-radius:10px;padding:2px 9px;margin-left:6px;">🟢 용신달</span>'
                elif mdata['is_ki']:
                    _yk_badge = '<span style="font-size:0.7rem;font-weight:700;color:#991b1b;background:#fee2e2;border:1px solid #fca5a5;border-radius:10px;padding:2px 9px;margin-left:6px;">🔴 기신달</span>'
                else:
                    _yk_badge = ''
                with col:
                    st.markdown(f"""
<div style="background:{bg}; border:{_border}; border-radius:14px; padding:16px; text-align:center; min-height:165px;">
  <div style="font-size:0.72rem; color:{bcol}; font-weight:700; margin-bottom:6px; letter-spacing:0.05em;">{badge}</div>
  <div style="font-size:1.55rem; font-weight:800; letter-spacing:0.05em; margin-bottom:2px;">{mdata['gaji']}</div>
  <div style="font-size:0.78rem; color:#666; margin-bottom:8px;">{mdata['label']} · {mdata['date']}{_yk_badge}</div>
  <div style="display:inline-block; font-size:0.72rem; font-weight:700; color:{tc}; background:{ac}22; padding:3px 10px; border-radius:20px; margin-bottom:10px;">{mdata['grade']} · {_tip(mdata['ss_g'])}</div>
  <div style="font-size:0.78rem; color:#444; line-height:1.55; text-align:left;">{_short}</div>
</div>""", unsafe_allow_html=True)
            st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

    # ── 12달 미니 카드 그리드 ──
    st.markdown("<div style='margin-top:14px; margin-bottom:6px; font-size:0.85rem; color:#555; font-weight:600;'>📅 월별 운세 한눈에 보기</div>", unsafe_allow_html=True)
    grid_cols = st.columns(4)
    for i, m in enumerate(months):
        tc, bg, ac = _GRADE_COLOR.get(m['grade'], ('#546e7a', '#f5f5f5', '#78909c'))
        border_style = f'1px solid {ac}88'
        card_bg = bg
        label_extra = ''
        if m['is_cur']:
            label_extra = ' ★'
            border_style = '2px solid #7c4dff'
            card_bg = '#f3eeff'
        elif m['is_next']:
            label_extra = ' ▷'
        if m['is_yong']:
            _g_yk = '<div style="font-size:0.6rem;font-weight:700;color:#065f46;background:#d1fae5;border-radius:8px;padding:1px 6px;margin-top:3px;display:inline-block;">🟢 용신달</div>'
        elif m['is_ki']:
            _g_yk = '<div style="font-size:0.6rem;font-weight:700;color:#991b1b;background:#fee2e2;border-radius:8px;padding:1px 6px;margin-top:3px;display:inline-block;">🔴 기신달</div>'
        else:
            _g_yk = ''
        with grid_cols[i % 4]:
            st.markdown(f"""
<div style="background:{card_bg}; border:{border_style}; border-radius:10px; padding:10px 8px; text-align:center; margin-bottom:10px;">
  <div style="font-size:0.68rem; color:#888; margin-bottom:2px;">{m['label']}{label_extra}</div>
  <div style="font-size:1.1rem; font-weight:700; margin-bottom:3px;">{m['gaji']}</div>
  <div style="font-size:0.65rem; font-weight:600; color:{tc}; background:{ac}22; display:inline-block; padding:2px 7px; border-radius:10px; margin-bottom:2px;">{m['grade']}</div>
  <div style="font-size:0.63rem; color:#777;">{_tip(m['ss_g'])}</div>
  {_g_yk}
</div>""", unsafe_allow_html=True)

    st.divider()
    with st.expander("📖 월별 상세 해설 펼치기", expanded=False):
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
st.caption("v2026.06.10.19")
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

def _render_gunghap_visual(r):
    """궁합 결과 시각 요약 카드 (점수 카드 아래, 해설 위)"""
    rel    = r['rel']
    score  = r['score']
    na, nb = r['na'], r['nb']
    reasons = r.get('reasons', [])

    hap_list  = rel.get('합',[]) + rel.get('삼합',[]) + rel.get('방합',[]) + rel.get('천간합',[])
    neg_list  = rel.get('충',[]) + rel.get('원진',[]) + rel.get('형',[]) + rel.get('파',[]) + rel.get('해',[]) + rel.get('천간충',[])
    ilji_hap  = any('일지합' in rs for rs in reasons)
    bae_both  = any('쌍방 배우자성' in rs or ('배우자성 +10' in rs and nb in rs) for rs in reasons)
    bae_a     = any(f'[배우자성' in rs and nb in rs for rs in reasons)
    bae_b     = any(f'[배우자성' in rs and na in rs for rs in reasons)
    yong_comp = any('용신보완' in rs for rs in reasons)
    oh_comp   = any('오행보완' in rs for rs in reasons)

    # ── 합·충 2열 카드 ──
    ca, cb = st.columns(2)
    ca.markdown(
        f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:12px 14px;">'
        f'<div style="font-size:0.72rem;font-weight:700;color:#16a34a;margin-bottom:6px;">🤝 연결되는 에너지</div>'
        + (''.join(f'<div style="font-size:0.8rem;color:#374151;margin-bottom:2px;">✅ {h}</div>' for h in hap_list[:5])
           if hap_list else '<div style="font-size:0.8rem;color:#6b7280;">없음</div>')
        + f'</div>', unsafe_allow_html=True)
    cb.markdown(
        f'<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:12px 14px;">'
        f'<div style="font-size:0.72rem;font-weight:700;color:#dc2626;margin-bottom:6px;">⚡ 긴장되는 에너지</div>'
        + (''.join(f'<div style="font-size:0.8rem;color:#374151;margin-bottom:2px;">⚠ {n}</div>' for n in neg_list[:5])
           if neg_list else '<div style="font-size:0.8rem;color:#6b7280;">없음</div>')
        + f'</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    # ── 영역별 상성 4칸 ──
    def _badge(ok, label):
        if ok is True:
            return f'<span style="background:#dcfce7;color:#16a34a;font-size:0.72rem;font-weight:700;border-radius:6px;padding:2px 8px;">✅ {label}</span>'
        elif ok == 'warn':
            return f'<span style="background:#fef3c7;color:#d97706;font-size:0.72rem;font-weight:700;border-radius:6px;padding:2px 8px;">⚠ {label}</span>'
        else:
            return f'<span style="background:#f1f5f9;color:#64748b;font-size:0.72rem;font-weight:700;border-radius:6px;padding:2px 8px;">➖ {label}</span>'

    comm_ok   = True if rel.get('천간합') else ('warn' if rel.get('천간충') else None)
    pull_ok   = True if (ilji_hap or bae_both) else (True if (bae_a or bae_b) else None)
    long_ok   = True if (rel.get('삼합') or rel.get('방합') or yong_comp) else (True if oh_comp else None)
    risk_cnt  = len(neg_list)
    risk_ok   = None if risk_cnt == 0 else ('warn' if risk_cnt <= 2 else False)

    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, badge_val, desc in [
        (c1, '💬', '소통 상성',  comm_ok,  '천간 합·충 기준'),
        (c2, '💕', '끌림·인연', pull_ok,  '일지합·배우자성 기준'),
        (c3, '🔗', '장기 상성', long_ok,  '삼합·용신 보완 기준'),
        (c4, '⚡', '갈등 리스크', risk_ok, f'부정 요소 {risk_cnt}개'),
    ]:
        col.markdown(
            f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;'
            f'padding:10px 8px;text-align:center;">'
            f'<div style="font-size:1.1rem;">{icon}</div>'
            f'<div style="font-size:0.72rem;font-weight:700;color:#374151;margin:2px 0;">{title}</div>'
            f'<div style="margin:4px 0;">{_badge(badge_val, "좋음" if badge_val is True else ("주의" if badge_val=="warn" else "보통"))}</div>'
            f'<div style="font-size:0.6rem;color:#9ca3af;">{desc}</div>'
            f'</div>', unsafe_allow_html=True)

    # ── 레이더 차트 ──
    def _val(v):
        if v is True:     return 5.0
        if v == 'warn':   return 3.0
        if v is False:    return 1.0
        return 2.5
    _r_comm  = _val(comm_ok)
    _r_pull  = _val(pull_ok)
    _r_long  = _val(long_ok)
    _r_stab  = 5.0 - (_val(risk_ok) - 1.0) * 0.8 if risk_ok is not None else 4.5
    _r_total = min(5.0, max(1.0, (score - 50) / 10.0))
    _radar_vals   = [_r_comm, _r_pull, _r_long, _r_stab, _r_total]
    _radar_labels = ['소통', '끌림', '장기', '안정', '종합']
    _fig = go.Figure(data=go.Scatterpolar(
        r=_radar_vals + [_radar_vals[0]],
        theta=_radar_labels + [_radar_labels[0]],
        fill='toself',
        fillcolor='rgba(139,119,184,0.25)',
        line=dict(color='#8b77b8', width=2.5),
        marker=dict(size=6, color='#8b77b8'),
    ))
    _fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 5], visible=True, showticklabels=False, gridcolor='#e5e7eb'),
            angularaxis=dict(tickfont=dict(size=13, color='#374151'), gridcolor='#e5e7eb'),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=30),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(_fig, use_container_width=True)

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
        _render_gunghap_visual(r)
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
