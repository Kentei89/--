import sys, math
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')

CHEONGAN = ['갑','을','병','정','무','기','경','신','임','계']
JIJI     = ['자','축','인','묘','진','사','오','미','신','유','술','해']
OHAENG_G = ['목','목','화','화','토','토','금','금','수','수']
OHAENG_J = ['수','토','목','목','토','화','화','토','금','금','토','수']
ANIMALS  = ['쥐','소','범','토끼','용','뱀','말','양','원숭이','닭','개','돼지']
OHAENG_NAMES = ['목','화','토','금','수']

OHAENG_IDX   = [0,0,1,1,2,2,3,3,4,4]
OHAENG_IDX_J = [4,2,0,0,2,1,1,2,3,3,2,4]

JANGSAENG = [11,6,2,9,2,9,5,0,8,3]
UNSUNG_12 = ['장생','목욕','관대','건록','제왕','쇠','병','사','묘','절','태','양']

_SS = {
    (0,True):'비견', (0,False):'겁재',
    (1,True):'식신', (1,False):'상관',
    (2,False):'편재',(2,True):'정재',
    (3,True):'편관', (3,False):'정관',
    (4,True):'편인', (4,False):'정인',
}

def get_sipseong(ilgan, t_ohaeng, t_euyang):
    diff = (t_ohaeng - OHAENG_IDX[ilgan]) % 5
    return _SS[(diff, ilgan%2 == t_euyang)]

def get_12unsung(cheongan, jiji):
    s = JANGSAENG[cheongan]
    pos = (jiji - s) % 12 if cheongan % 2 == 0 else (s - jiji) % 12
    return UNSUNG_12[pos]

def get_gongmang(dg, dj):
    for k in range(6):
        if (dg + 10*k) % 12 == dj:
            group = (dg + 10*k) // 10
            base  = (10 - group * 2) % 12
            return {base, (base + 1) % 12}
    return set()

JIJANGAN = [
    ['임','계'],           # 자(0)
    ['계','신','기'],      # 축(1)
    ['무','병','갑'],      # 인(2)
    ['갑','을'],           # 묘(3)
    ['을','계','무'],      # 진(4)
    ['무','경','병'],      # 사(5)
    ['병','기','정'],      # 오(6)
    ['정','을','기'],      # 미(7)
    ['무','임','경'],      # 신(8)
    ['경','신'],           # 유(9)
    ['신','정','무'],      # 술(10)
    ['무','갑','임'],      # 해(11)
]

ILGAN_DESC = {
    0:('갑목(甲木)','큰 나무','원칙주의·리더십·직진형. 큰 나무처럼 곧고 강함. 고집이 있으나 추진력이 뛰어남.'),
    1:('을목(乙木)','넝쿨','유연함·적응력·끈기. 넝쿨처럼 환경에 맞춰 자람. 인간관계가 넓고 부드러움.'),
    2:('병화(丙火)','태양','열정·외향적·솔직함. 태양처럼 밝고 활발. 리더 기질이 있으나 지속력 필요.'),
    3:('정화(丁火)','촛불','섬세함·예술적·집중력. 촛불처럼 내면이 깊음. 직관력이 뛰어나고 감성이 풍부.'),
    4:('무토(戊土)','큰 산','안정·포용·신중함. 산처럼 묵직하고 믿음직함. 변화보다 안정을 선호.'),
    5:('기토(己土)','밭','실용적·꼼꼼·내성적. 밭처럼 생산적. 세밀하고 실속을 챙기나 소심할 수 있음.'),
    6:('경금(庚金)','바위','의리·강직·결단력. 바위처럼 단단함. 원칙을 지키나 융통성이 부족할 수 있음.'),
    7:('신금(辛金)','보석','세련됨·예민·완벽주의. 보석처럼 빛남. 자존심이 강하고 미적 감각이 뛰어남.'),
    8:('임수(壬水)','강물','지혜·융통성·외교적. 강물처럼 막힘없이 흘러감. 아이디어가 풍부하고 포용력 있음.'),
    9:('계수(癸水)','빗물','총명함·감수성·내성적. 빗물처럼 스며듦. 직관력과 기억력이 뛰어나고 섬세함.'),
}

SINSAL_DESC = {
    '천을귀인':'가장 강력한 귀인성. 위기 상황에서 반드시 도움의 손길이 찾아오며 대인 관계가 원만합니다.',
    '문창귀인':'학문과 문서 운이 강합니다. 총명하고 글재주가 뛰어나며 시험·자격증 운도 좋습니다.',
    '태극귀인':'귀한 기운이 전 생애에 걸쳐 작용합니다. 어렵고 힘든 상황에서도 뜻밖의 전화위복이 찾아옵니다.',
    '장성살':'강한 추진력과 리더십. 군·경·무직에 유리하고 승진 기회가 많습니다.',
    '도화살':'자연스러운 매력으로 이성에게 인기가 많습니다. 예술·연예 분야 소질도 있으나 이성 문제 주의.',
    '역마살':'이동·변화·출장·해외 인연이 많습니다. 한곳 정착이 어려울 수 있으나 활동적인 직업에 유리합니다.',
    '화개살':'고독하고 종교·예술·학문 기질이 있습니다. 정신적 수련과 인연이 깊으며 말년이 풍요롭습니다.',
    '양인살':'의지와 추진력이 강하나 급하고 충동적 성향 주의. 무관·의료 분야에 적합합니다.',
    '현침살':'예리하고 분석적. 의료·법률·정밀 분야에 인연이 있으나 수술·사고에 주의가 필요합니다.',
    '망신살':'이성 문제, 금전 관련 망신이 특히 우려됩니다. 언행을 신중히 하고 구설을 피하세요.',
    '겁살':'도난·손재수 주의. 예기치 않은 재물 손실이 발생할 수 있으니 보안에 유의하세요.',
    '월살':'고독함이 있어 배우자나 주변의 도움이 약할 수 있습니다. 독립심을 키우는 것이 중요합니다.',
    '탕화살':'화재·뜨거운 것·급격한 변화에 주의. 자동차 사고 등 사고수가 있을 수 있습니다.',
}

UNSUNG_DESC = {
    '장생':'성장기·새출발의 기운. 발전의 씨앗이 움트는 시기로 무엇을 시작해도 순조롭게 진행됩니다.',
    '목욕':'감수성이 예민하고 호기심이 왕성합니다. 풍류를 즐기고 자유분방한 기질이 있습니다.',
    '관대':'자신감과 혈기가 넘치며 사회 진출기를 상징합니다. 적극적인 도전이 성과를 냅니다.',
    '건록':'독립·자수성가의 기운. 왕성한 활동력으로 스스로 길을 개척하는 힘이 있습니다.',
    '제왕':'최고 전성기이자 리더십의 상징. 고집이 강해질 수 있으니 유연함도 함께 길러야 합니다.',
    '쇠':'안정기·보수적 성향. 노련함과 완숙미가 있으며 안정적인 운영 능력이 뛰어납니다.',
    '병':'체력이 약화되고 예민해지는 시기. 학문·예술·내적 성찰에 적합한 기운입니다.',
    '사':'내면을 충실히 하고 집중력이 강합니다. 연구·학문·깊이 있는 전문직에 적합합니다.',
    '묘':'저장·축적의 기운. 외부로는 침체해 보이나 내부적으로 에너지를 비축하는 시기입니다.',
    '절':'단절·변화의 기운. 새로운 환경에 적응하는 능력이 요구되며 변화가 성장의 계기가 됩니다.',
    '태':'잠재력이 태동하는 시기. 철저한 준비와 계획이 이후 성공의 초석이 됩니다.',
    '양':'성장 준비·육성기. 조력자와의 인연이 깊으며 주변의 도움 속에 역량이 발전합니다.',
}

# ── 한국 시간 보정 ───────────────────────────────────

_DST = [
    (datetime(1948,6,1),  datetime(1948,9,13)),
    (datetime(1949,4,3),  datetime(1949,9,11)),
    (datetime(1950,4,1),  datetime(1950,9,10)),
    (datetime(1951,5,6),  datetime(1951,9,9)),
    (datetime(1955,5,5),  datetime(1955,9,9)),
    (datetime(1956,5,20), datetime(1956,9,30)),
    (datetime(1957,5,5),  datetime(1957,9,22)),
    (datetime(1958,5,4),  datetime(1958,9,21)),
    (datetime(1959,5,3),  datetime(1959,9,20)),
    (datetime(1960,5,1),  datetime(1960,9,18)),
    (datetime(1987,5,10), datetime(1987,10,11)),
    (datetime(1988,5,8),  datetime(1988,10,9)),
]

def apply_correction(dt):
    corrections = []
    for s, e in _DST:
        if s <= dt < e:
            dt -= timedelta(hours=1)
            corrections.append('서머타임 -1시간')
            break
    dt -= timedelta(minutes=32)
    corrections.append('지방시 -32분')
    return dt, corrections

# ── 태양황경 계산 ────────────────────────────────────

def _jd(y, m, d):
    if m <= 2: y -= 1; m += 12
    A = y // 100; B = 2 - A + A // 4
    return int(365.25*(y+4716)) + int(30.6001*(m+1)) + d + B - 1524.5

def _jd_to_dt(jd):
    jd += 0.5; Z = int(jd); F = jd - Z
    a = int((Z-1867216.25)/36524.25)
    A = Z if Z < 2299161 else Z+1+a-a//4
    B=A+1524; C=int((B-122.1)/365.25); D=int(365.25*C); E=int((B-D)/30.6001)
    day=B-D-int(30.6001*E)
    m=E-1 if E<14 else E-13
    y=C-4716 if m>2 else C-4715
    h=F*24
    return datetime(y, m, day, int(h), int((h%1)*60))

def _sun_lon(JDE):
    T = (JDE-2451545)/36525
    L0 = (280.46646 + 36000.76983*T + 0.0003032*T*T) % 360
    M  = math.radians((357.52911 + 35999.05029*T - 0.0001537*T*T) % 360)
    C  = (1.914602-0.004817*T-0.000014*T*T)*math.sin(M)
    C += (0.019993-0.000101*T)*math.sin(2*M) + 0.000289*math.sin(3*M)
    omega = 125.04 - 1934.136*T
    return (L0 + C - 0.00569 - 0.00478*math.sin(math.radians(omega))) % 360

def solar_term(year, lon):
    JDE = _jd(year, 1, 15)
    for _ in range(50):
        diff = lon - _sun_lon(JDE)
        if diff > 180:  diff -= 360
        if diff < -180: diff += 360
        if abs(diff) < 1e-5: break
        JDE += diff / 360 * 365.25
    return _jd_to_dt(JDE + 9/24)

# ── 사주 계산 ────────────────────────────────────────

_JEOLGI = [(285,1),(315,2),(345,3),(15,4),(45,5),(75,6),
           (105,7),(135,8),(165,9),(195,10),(225,11),(255,0)]

def _month_jiji(birth_dt):
    y = birth_dt.year
    candidates = [(solar_term(y-1, 255), 0)]
    for lon, jj in _JEOLGI:
        candidates.append((solar_term(y, lon), jj))
    candidates.sort(key=lambda x: x[0])
    result = 0
    for dt, jj in candidates:
        if birth_dt >= dt: result = jj
        else: break
    return result

def _year_pillar(year):
    idx = (year - 1984) % 60
    return idx % 10, idx % 12

def _month_pillar(yg, mj):
    mi    = (mj - 2) % 12
    start = [2,4,6,8,0][yg % 5]
    return (start + mi) % 10, mj

def _day_pillar(year, month, day):
    diff = (datetime(year,month,day) - datetime(2023,1,1)).days
    idx  = (55 + diff) % 60
    return idx % 10, idx % 12

def _hour_pillar(dg, hour, minute=0):
    total_min = hour * 60 + minute
    if total_min >= 23*60 or total_min < 1*60:
        hj = 0
    else:
        hj = (total_min + 60) // 120
    start = [0,2,4,6,8][dg % 5]
    return (start + hj) % 10, hj

def get_saju(year, month, day, hour, minute=0):
    raw_dt   = datetime(year, month, day, hour, minute)
    corr_dt, corrections = apply_correction(raw_dt)

    ipchun = solar_term(year, 315)
    ey     = year-1 if corr_dt < ipchun else year

    yg, yj  = _year_pillar(ey)
    mj       = _month_jiji(corr_dt)
    mg, mj2  = _month_pillar(yg, mj)
    dg, dj   = _day_pillar(corr_dt.year, corr_dt.month, corr_dt.day)
    hg, hj   = _hour_pillar(dg, corr_dt.hour, corr_dt.minute)

    return [(yg,yj),(mg,mj2),(dg,dj),(hg,hj)], corr_dt, corrections

# ── 합·충·형·파·해 테이블 ──────────────────────────────

YUKAHP = {
    frozenset([0,1]):'자축합(토)', frozenset([2,11]):'인해합(목)',
    frozenset([3,10]):'묘술합(화)', frozenset([4,9]):'진유합(금)',
    frozenset([5,8]):'사신합(수)', frozenset([6,7]):'오미합(토)',
}
SAMHAP = [
    (frozenset([2,6,10]), '인오술 삼합(화)'),
    (frozenset([11,3,7]), '해묘미 삼합(목)'),
    (frozenset([4,8,0]),  '신자진 삼합(수)'),
    (frozenset([5,9,1]),  '사유축 삼합(금)'),
]
CHUNG    = [frozenset([i,(i+6)%12]) for i in range(6)]
PA       = [frozenset(p) for p in [(0,3),(1,10),(2,11),(4,7),(5,8),(6,9)]]
HAE      = [frozenset(p) for p in [(0,7),(1,6),(2,5),(3,4),(8,11),(9,10)]]
WONJIN   = [frozenset(p) for p in [(0,7),(1,6),(2,9),(3,8),(4,11),(5,10)]]
HYEONG_3 = [(frozenset([2,5,8]),'인사신 삼형'),(frozenset([1,10,7]),'축술미 삼형')]
JAJI     = [0, 3, 11]

def check_sal(pillars):
    jijis = [p[1] for p in pillars]
    gans  = [p[0] for p in pillars]
    yj, _, dj, _ = jijis
    ilgan = gans[2]
    gil, hyung = [], []
    sg, sh = set(), set()
    def _g(x):
        if x not in sg: sg.add(x); gil.append(x)
    def _h(x):
        if x not in sh: sh.add(x); hyung.append(x)

    _CY = {0:{1,7},1:{0,8},2:{11,9},3:{11,9},4:{1,7},
           5:{0,8},6:{1,7},7:{6,2},8:{3,5},9:{3,5}}
    for j in jijis:
        if j in _CY[ilgan]: _g(f'천을귀인({JIJI[j]})'); break

    _MC = [5,6,8,9,8,9,11,0,2,3]
    if _MC[ilgan] in jijis: _g(f'문창귀인({JIJI[_MC[ilgan]]})')

    _TG = {0:{0,6},1:{0,6},4:{0,6},5:{0,6},
           2:{3,9},3:{3,9},6:{4,10},7:{4,10},8:{1,7},9:{1,7}}
    for j in jijis:
        if j in _TG.get(ilgan, set()): _g(f'태극귀인({JIJI[j]})'); break

    _YI = {0:3, 2:6, 4:6, 6:9, 8:0}
    if ilgan in _YI and _YI[ilgan] in jijis:
        _h(f'양인살({JIJI[_YI[ilgan]]})')

    if sum(1 for g in gans if g in {0,7,8}) >= 2:
        _h('현침살')

    def _grp(j):
        for i, s in enumerate([{2,6,10},{5,9,1},{8,0,4},{11,3,7}]):
            if j in s: return i
        return -1

    TBLS = [
        ('장성살', [6,9,0,3],   True),
        ('도화살', [3,0,9,6],   False),
        ('역마살', [8,5,2,11],  False),
        ('화개살', [10,7,4,1],  False),
        ('망신살', [2,11,8,5],  False),
        ('겁살',   [11,8,5,2],  False),
        ('월살',   [1,10,7,4],  False),
        ('탕화살', [5,0,3,6],   False),
    ]
    for base_j in [yj, dj]:
        g = _grp(base_j)
        if g < 0: continue
        for name, arr, is_gil in TBLS:
            t = arr[g]
            if t in jijis:
                s = f'{name}({JIJI[t]})'
                if is_gil: _g(s)
                else: _h(s)

    return gil, hyung

def check_relations(ja, jb=None):
    both = list(ja) + (list(jb) if jb else [])
    if jb is None:
        pairs = [(ja[i],ja[k]) for i in range(4) for k in range(i+1,4)]
    else:
        pairs = [(a,b) for a in ja for b in jb]
    r = {'합':[],'삼합':[],'충':[],'형':[],'파':[],'해':[],'원진':[]}

    for a, b in pairs:
        fs = frozenset([a,b])
        if fs in YUKAHP and YUKAHP[fs] not in r['합']:
            r['합'].append(YUKAHP[fs])
        if fs in CHUNG:
            n = f'{JIJI[a]}{JIJI[b]}충'
            if n not in r['충']: r['충'].append(n)
        if fs in PA:
            n = f'{JIJI[a]}{JIJI[b]}파'
            if n not in r['파']: r['파'].append(n)
        if fs in HAE:
            n = f'{JIJI[a]}{JIJI[b]}해'
            if n not in r['해']: r['해'].append(n)
        if fs in WONJIN:
            n = f'{JIJI[a]}{JIJI[b]}원진'
            if n not in r['원진']: r['원진'].append(n)

    for grp, name in HYEONG_3:
        if len(grp & set(both)) >= 2 and name not in r['형']:
            r['형'].append(name)
    for jj in JAJI:
        if both.count(jj) >= 2:
            n = f'{JIJI[jj]}자형'
            if n not in r['형']: r['형'].append(n)

    for grp, name in SAMHAP:
        cnt = len(grp & set(both))
        if cnt >= 2:
            label = name if cnt == 3 else name.replace('삼합','반합')
            if label not in r['삼합']: r['삼합'].append(label)
    return r

def analyze_ohaeng(pillars):
    cnt = {o:0 for o in ['목','화','토','금','수']}
    for g, j in pillars:
        cnt[OHAENG_G[g]] += 1
        cnt[OHAENG_J[j]] += 1
    return cnt

# ── 대운·세운 계산 ─────────────────────────────────────

_JJ_LON = [255,285,315,345,15,45,75,105,135,165,195,225]

def get_daewoon(pillars, birth_dt, is_male, n=8):
    yg = pillars[0][0]
    mg, mj = pillars[1]
    yang_year = yg % 2 == 0
    forward = (is_male and yang_year) or (not is_male and not yang_year)

    if forward:
        next_lon = _JJ_LON[(mj + 1) % 12]
        y = birth_dt.year
        jeol = solar_term(y, next_lon)
        if jeol <= birth_dt:
            jeol = solar_term(y + 1, next_lon)
        days = (jeol - birth_dt).days
    else:
        cur_lon = _JJ_LON[mj]
        y = birth_dt.year
        jeol = solar_term(y, cur_lon)
        if jeol > birth_dt:
            jeol = solar_term(y - 1, cur_lon)
        days = (birth_dt - jeol).days

    start_age = round(days / 3)
    daeun = []
    for i in range(1, n + 1):
        age = start_age + (i - 1) * 10
        yr  = birth_dt.year + age
        dg = (mg + i) % 10 if forward else (mg - i) % 10
        dj = (mj + i) % 12 if forward else (mj - i) % 12
        daeun.append((age, yr, dg, dj))
    return start_age, forward, daeun

def get_sewoon(birth_year, n=10):
    cur = datetime.now().year
    result = []
    for y in range(cur, cur + n):
        yg, yj = _year_pillar(y)
        result.append((y, y - birth_year, yg, yj))
    return result

def print_daewoon(start_age, forward, daeun, sewoon):
    cur = datetime.now().year
    print(f'\n{"─"*62}')
    print(f'  ◈ 대운  ({"순행" if forward else "역행"}, {start_age}세 시작)')
    print(f'{"─"*62}')
    for age, yr, dg, dj in daeun:
        mark = ' ◀ 현재' if yr <= cur < yr + 10 else ''
        print(f'  {age:>2}세({yr})~{age+9}세:  {CHEONGAN[dg]}{JIJI[dj]}'
              f'  ({OHAENG_G[dg]}{OHAENG_J[dj]}){mark}')
    print(f'\n{"─"*62}')
    print(f'  ◈ 세운 (현재 기준 10년)')
    print(f'{"─"*62}')
    cur_dg, cur_dj = None, None
    for age, yr, dg, dj in daeun:
        if yr <= cur < yr + 10:
            cur_dg, cur_dj = dg, dj; break
    daewoon_str = f'{CHEONGAN[cur_dg]}{JIJI[cur_dj]}' if cur_dg is not None else '─'
    print(f'  {"연도":>5}  {"나이":>3}  {"세운":^4}  {"대운":^4}')
    for y, age, yg, yj in sewoon:
        mark = ' ◀ 올해' if y == cur else ''
        print(f'  {y}년  {age:>3}세  {CHEONGAN[yg]}{JIJI[yj]:^3}  {daewoon_str:^4}{mark}')

# ── 신강/신약 판단 ────────────────────────────────────

def judge_strength(pillars):
    ilgan = pillars[2][0]
    sup = opp = 0
    for i, (g, j) in enumerate(pillars):
        if i == 2: continue
        w = 2 if i == 1 else 1
        for ss, wt in [(get_sipseong(ilgan, OHAENG_IDX[g], g%2), 1),
                       (get_sipseong(ilgan, OHAENG_IDX_J[j], j%2), w)]:
            if ss in ('비견','겁재','편인','정인'): sup += wt
            elif ss in ('식신','상관','편재','정재','편관','정관'): opp += wt
    if sup >= opp + 3:   return '신강(身强)'
    elif opp >= sup + 3: return '신약(身弱)'
    else:                return '중화(中和)'

# ── 핵심 알고리즘: 득령·조후·용신 ───────────────────────

# 오행(목=0,화=1,토=2,금=3,수=4)별 계절별 왕상휴수사 점수 [봄,여름,가을,겨울]
WANG_SANG_SCORE = {
    0: [ 2,  0, -2,  1],   # 목: 봄=旺, 여름=休, 가을=死, 겨울=相
    1: [ 1,  2, -1, -2],   # 화: 봄=相, 여름=旺, 가을=囚, 겨울=死
    2: [-2,  1,  0, -1],   # 토: 봄=死, 여름=相, 가을=休, 겨울=囚
    3: [-1, -2,  2,  0],   # 금: 봄=囚, 여름=死, 가을=旺, 겨울=休
    4: [ 0, -1,  1,  2],   # 수: 봄=休, 여름=囚, 가을=相, 겨울=旺
}

def get_season(mj):
    if mj in (2, 3, 4):   return '봄',  0
    elif mj in (5, 6, 7): return '여름', 1
    elif mj in (8, 9, 10):return '가을', 2
    else:                  return '겨울', 3   # 11, 0, 1

def get_deukryeong(pillars):
    """득령(得令): 일간이 태어난 월지(계절)의 기운을 얻었는지 판별"""
    ilgan = pillars[2][0]
    mj    = pillars[1][1]
    ilgan_oh = OHAENG_IDX[ilgan]
    season_name, season_idx = get_season(mj)
    score = WANG_SANG_SCORE[ilgan_oh][season_idx]
    # 토 일간이 환절기(진술축미)에 태어나면 특별히 旺으로 처리
    if mj in (4, 7, 10, 1) and ilgan_oh == 2:
        score = 2
    got = score >= 1   # 旺(2) 또는 相(1)이면 득령
    return got, score, season_name

def get_johu(pillars):
    """조후(調候): 월지 기준 사주의 온도와 필요 오행 반환"""
    mj = pillars[1][1]
    if mj in (11, 0, 1):       # 겨울(해자축) → 화(火) 필요
        return '겨울', 1, '차가운', '화(火)'
    elif mj in (5, 6, 7):      # 여름(사오미) → 수(水) 필요
        return '여름', 4, '뜨거운', '수(水)'
    elif mj in (2, 3, 4):      # 봄
        return '봄',  None, '온화한', None
    else:                       # 가을
        return '가을', None, '서늘한', None

def get_yongshin(pillars):
    """용신(用神) 확정: 조후 우선, 억부 보조"""
    ilgan    = pillars[2][0]
    ilgan_oh = OHAENG_IDX[ilgan]
    strength = judge_strength(pillars)
    season_name, johu_oh, temp_adj, johu_name = get_johu(pillars)
    oa = analyze_ohaeng(pillars)

    if johu_oh is not None:
        # 조후가 긴급한 겨울·여름은 조후 우선
        yongshin_oh = johu_oh
        basis = '조후(調候)'
    elif '신강' in strength:
        # 신강 → 일간 기운을 설기할 오행 (식상 우선, 재성 차선)
        cand1 = (ilgan_oh + 1) % 5   # 식상 오행
        cand2 = (ilgan_oh + 2) % 5   # 재성 오행
        yongshin_oh = cand1 if oa.get(OHAENG_NAMES[cand1], 0) <= oa.get(OHAENG_NAMES[cand2], 0) else cand2
        basis = '억부(억강)'
    elif '신약' in strength:
        # 신약 → 일간을 생해줄 인성 오행
        yongshin_oh = (ilgan_oh + 4) % 5
        basis = '억부(부약)'
    else:
        # 중화 → 사주에서 가장 부족한 오행
        yongshin_oh = min(range(5), key=lambda x: oa.get(OHAENG_NAMES[x], 0))
        basis = '균형 보완'

    return yongshin_oh, OHAENG_NAMES[yongshin_oh], basis, season_name, temp_adj

# ── 용신별 개운 데이터 ────────────────────────────────

YONGSHIN_GAEUN = {
    0: {'color':'초록색·청록색', 'number':'3, 8', 'direction':'동쪽',
        'hobby':'등산, 원예, 숲 산책, 목공예, 꽃꽂이'},
    1: {'color':'붉은색·주황색·분홍', 'number':'2, 7', 'direction':'남쪽',
        'hobby':'캠핑, 모닥불, 격렬한 운동, 요리, 조명 인테리어'},
    2: {'color':'황토색·베이지·노랑', 'number':'5, 10', 'direction':'중앙·북동·북서',
        'hobby':'도예, 명상, 텃밭 가꾸기, 요가, 황토방 체험'},
    3: {'color':'흰색·금색·은색', 'number':'4, 9', 'direction':'서쪽',
        'hobby':'악기 연주, 금속 공예, 골프, 트레킹, 정밀 공예'},
    4: {'color':'검정색·남색·파랑', 'number':'1, 6', 'direction':'북쪽',
        'hobby':'수영, 독서, 낚시, 명상, 바다·강 여행'},
}

# ── 통변 헬퍼 함수 ────────────────────────────────────

def _personality_text(ilgan, season_name, yongshin_name, strength):
    il_name, il_keyword, _ = ILGAN_DESC[ilgan]

    season_core = {
        '봄': (
            f'봄의 생동감 속에 태어난 {il_name} 일간입니다. '
            f'새싹이 돋아나는 기운처럼 새로운 시작과 도전에 강한 열정을 보입니다. '
            f'{il_keyword}의 기질에 봄의 활기가 더해져 진취적이고 창의적인 에너지가 넘칩니다. '
            f'다만 봄의 나무가 지나치게 무성해지면 가지치기가 필요하듯, '
            f'과도한 열정이 산만함으로 이어지지 않도록 집중력을 유지하는 것이 중요합니다. '
            f'용신인 {yongshin_name}의 기운을 활용해 이 에너지를 올바른 방향으로 집중시키십시오.'
        ),
        '여름': (
            f'뜨거운 여름에 태어난 {il_name} 일간입니다. '
            f'강렬한 태양 아래 {il_keyword}의 기질이 더욱 뜨겁게 달아올라 열정과 추진력이 극에 달합니다. '
            f'외향적이고 표현이 강하며 승부욕이 높지만, 과열된 기운으로 인해 감정 기복이 생기거나 '
            f'주변과 마찰이 잦을 수 있습니다. '
            f'용신인 {yongshin_name}은 이 뜨거운 사주를 식혀주는 역할을 합니다. '
            f'{yongshin_name}의 기운을 자주 가까이하여 내면의 온도를 조절하는 것이 인생의 핵심 과제입니다.'
        ),
        '가을': (
            f'결실의 계절 가을에 태어난 {il_name} 일간입니다. '
            f'{il_keyword}의 기질에 가을의 서늘한 기운이 더해져 냉철하고 분석적이며 실용적인 성향이 강합니다. '
            f'감정보다 이성을 앞세우고 원칙과 완벽주의적 성향이 두드러집니다. '
            f'책임감이 강하고 계획적이지만, 지나치게 냉정해 보여 타인에게 차갑게 느껴질 수 있습니다. '
            f'용신인 {yongshin_name}의 기운으로 딱딱한 기질에 유연함과 따스함을 불어넣어야 합니다.'
        ),
        '겨울': (
            f'한겨울에 태어난 {il_name} 일간입니다. '
            f'차갑고 고요한 겨울의 기운 속에 {il_keyword}의 기질이 응축되어 있습니다. '
            f'겉으로는 과묵하고 냉정해 보이지만 내면에는 깊은 감수성과 강한 의지가 숨어 있습니다. '
            f'혼자만의 시간을 즐기고 고독을 두려워하지 않으나, '
            f'때로는 얼어붙은 감정으로 인해 고립감을 느낄 수 있습니다. '
            f'용신인 {yongshin_name}은 이 사주의 냉기를 녹여 생동감을 불어넣는 핵심 기운입니다. '
            f'{yongshin_name}을 가까이할수록 삶의 온기와 활기를 되찾게 됩니다.'
        ),
    }

    base = season_core[season_name]

    if '신강' in strength:
        base += (
            f'\n  현재 일간의 기운이 매우 강한 신강(身强) 사주입니다. '
            f'자기 확신이 강하고 의지가 굳어 독립적으로 일을 추진하는 힘이 있습니다. '
            f'다만 고집이 지나쳐 타협과 협력에 어려움을 겪을 수 있으니, '
            f'용신 {yongshin_name}의 기운이 오는 운에서 진정한 발복과 성취가 이루어집니다.'
        )
    elif '신약' in strength:
        base += (
            f'\n  일간의 기운이 약한 신약(身弱) 사주입니다. '
            f'주변 환경과 인간관계에 민감하게 반응하며 타인의 도움이 성공의 열쇠가 됩니다. '
            f'외부 압박에 흔들리기 쉬우나, '
            f'용신 {yongshin_name}의 기운이 강한 환경에 있을 때 비로소 내면의 잠재력을 발휘합니다.'
        )
    else:
        base += (
            f'\n  균형 잡힌 중화(中和) 사주입니다. '
            f'특정 기운에 치우치지 않아 다양한 환경에 잘 적응하며 안정적인 삶을 영위할 수 있습니다. '
            f'용신 {yongshin_name}을 활용해 운의 흐름을 타면 더욱 빛납니다.'
        )
    return base


def _yongshin_detail(yongshin_oh, ilgan, strength, season_name):
    il_name = ILGAN_DESC[ilgan][0]
    texts = {
        0: (
            f'목(木)이 용신입니다. 목은 성장·도전·진취성을 상징합니다. '
            f'{il_name} 일간에게 목의 기운은 새로운 아이디어와 창의적 에너지를 공급해 줍니다. '
            f'봄이나 동쪽 방향, 초록 계열의 환경이 이 사주에 생기를 불어넣습니다. '
            f'나무와 관련된 직업(출판·교육·환경·패션)이나 초록 자연 속에 있을 때 운이 열립니다. '
            f'갑(甲)·을(乙)년이나 인(寅)·묘(卯)월에 좋은 기회가 찾아옵니다.'
        ),
        1: (
            f'화(火)가 용신입니다. 화는 열정·광명·확장을 상징합니다. '
            f'{il_name} 일간에게 화의 기운은 차가운 기운을 녹이고 삶에 온기와 활기를 불어넣습니다. '
            f'밝은 조명, 남쪽, 붉은 계열 환경이 도움이 됩니다. '
            f'화와 관련된 직업(방송·디자인·요식업·에너지)에서 두각을 나타냅니다. '
            f'병(丙)·정(丁)년이나 사(巳)·오(午)월에 인생의 전환점이 찾아올 가능성이 높습니다.'
        ),
        2: (
            f'토(土)가 용신입니다. 토는 안정·포용·중재를 상징합니다. '
            f'{il_name} 일간에게 토의 기운은 흔들리는 마음을 잡아주고 현실적 기반을 다지게 합니다. '
            f'황토색 인테리어, 중앙 위치, 자연과 연결된 환경이 도움이 됩니다. '
            f'부동산·농업·건설·중개업 등이 인연 있는 분야입니다. '
            f'무(戊)·기(己)년이나 진(辰)·술(戌)·축(丑)·미(未)월에 안정과 성취가 강화됩니다.'
        ),
        3: (
            f'금(金)이 용신입니다. 금은 의리·결단·정밀함을 상징합니다. '
            f'{il_name} 일간에게 금의 기운은 예리한 판단력과 강단을 부여하여 결정적인 순간에 힘을 발휘하게 합니다. '
            f'흰색·금속 소품, 서쪽 방향이 도움이 됩니다. '
            f'금융·법조·의료·군·경찰 분야와 인연이 있습니다. '
            f'경(庚)·신(辛)년이나 신(申)·유(酉)월에 결정적 기회와 성취가 찾아옵니다.'
        ),
        4: (
            f'수(水)가 용신입니다. 수는 지혜·유연성·생명력을 상징합니다. '
            f'{il_name} 일간에게 수의 기운은 과열된 기운을 식히고 깊은 통찰력과 융통성을 부여합니다. '
            f'물 가까운 곳, 북쪽, 파란색 환경이 도움이 됩니다. '
            f'정보통신·유통·무역·학문·연구 분야가 인연 있는 직업군입니다. '
            f'임(壬)·계(癸)년이나 해(亥)·자(子)월에 인생의 흐름이 크게 좋아집니다.'
        ),
    }
    return texts[yongshin_oh]


def _hobby_desc(yongshin_oh):
    texts = {
        0: (
            '나무와 생명을 가까이하는 활동이 기운을 보강합니다. '
            '특히 숲 속 걷기, 식물 키우기, 목공예는 심리적 안정과 함께 '
            '목의 기운을 직접 흡수하는 효과가 있습니다. 동쪽 방향 여행도 권장합니다.'
        ),
        1: (
            '불과 빛을 활용하는 활동이 효과적입니다. '
            '캠핑이나 모닥불 앞에 앉는 것만으로도 화의 기운이 보강되며, '
            '격렬한 운동이나 댄스로 몸에 열기를 만드는 것도 좋습니다. '
            '밝고 화사한 공간에서 시간을 보내세요.'
        ),
        2: (
            '흙을 직접 만지는 활동이 토의 기운을 강화합니다. '
            '텃밭 가꾸기, 도예, 황토방 체험이 특히 좋습니다. '
            '복잡한 도시보다 자연에서 명상하거나 걷는 시간을 자주 가지세요. '
            '안정적이고 규칙적인 생활 리듬 자체가 개운법이 됩니다.'
        ),
        3: (
            '금속을 다루거나 정밀함이 요구되는 활동이 금의 기운을 높입니다. '
            '악기 연주(특히 현악기나 관악기), 금속 공예, 칼질이 필요한 요리, '
            '골프나 테니스도 좋습니다. 가을에 서쪽 방향으로 여행을 떠나보세요.'
        ),
        4: (
            '물과 친해지는 활동이 수의 기운을 채워줍니다. '
            '수영, 바다·강·호수 여행, 낚시가 대표적입니다. '
            '독서나 글쓰기, 명상으로 내면을 깊게 탐구하는 것도 '
            '수의 지혜로운 에너지를 키우는 훌륭한 방법입니다.'
        ),
    }
    return texts[yongshin_oh]


def _finance_text(ilgan, strength, yongshin_oh, oa):
    yn = OHAENG_NAMES[yongshin_oh]
    il_name = ILGAN_DESC[ilgan][0]

    by_strength = {
        '신강(身强)': (
            f'{il_name} 사주가 신강하니 재물을 끌어당기는 힘이 있습니다. '
            f'의지가 강하고 추진력이 좋아 재물운을 스스로 만들어 가는 형국입니다. '
            f'다만 고집이 강해 좋은 투자 기회를 논리적으로 분석하기보다 '
            f'직감으로 결정하는 경향이 있습니다. '
            f'용신 {yn}의 기운이 강한 시기(해·월)에 사업 확장이나 투자 결정을 내리면 성과가 큽니다. '
            f'재물을 혼자 독점하기보다 나누고 베풀 때 오히려 더 크게 들어오는 구조입니다. '
            f'직장보다 사업 또는 전문직이 더 큰 재물과 인연이 됩니다.'
        ),
        '신약(身弱)': (
            f'{il_name} 사주가 신약하니 재물이 들어와도 유지하기 어려운 구조가 있습니다. '
            f'수입보다 지출이 잦고, 타인의 부탁이나 감정에 이끌려 불필요한 소비를 하기 쉽습니다. '
            f'가장 중요한 재물 관리법은 적립식 저축과 고정 지출 통제입니다. '
            f'용신 {yn}의 기운이 오는 운에서는 뜻밖의 귀인과 금전적 도움이 생깁니다. '
            f'타인 명의로 보증을 서거나 공동 투자를 하면 손해를 볼 수 있으니 '
            f'철저히 본인 명의로만 관리하세요. '
            f'안정적인 월급 직장이 재물 유지에 가장 유리한 구조입니다.'
        ),
        '중화(中和)': (
            f'{il_name} 사주가 중화되어 재물 기복이 크지 않고 꾸준한 재물 흐름을 유지하는 형국입니다. '
            f'극단적인 대박보다는 성실함으로 꾸준히 쌓아가는 방식이 적합합니다. '
            f'용신 {yn}의 기운이 강한 해에는 추가 수입이나 승진·사업 확장 기회가 생깁니다. '
            f'투자는 분산 투자 전략이 안정적이며, 단기 투기보다 장기 재테크가 유리합니다.'
        ),
    }

    by_yongshin = {
        0: f'목 용신으로 성장하는 분야(스타트업·교육·창업)에서 재물이 빛을 발합니다.',
        1: f'화 용신으로 홍보·마케팅·대인 영업 분야에서 가장 큰 수입이 들어옵니다.',
        2: f'토 용신으로 부동산·실물 자산이 장기적으로 안정적인 재물 기반이 됩니다.',
        3: f'금 용신으로 금융·보험·전문 자격증 기반 수입 구조가 가장 유리합니다.',
        4: f'수 용신으로 지식·정보·콘텐츠 기반 수익이나 무역·유통이 재물과 인연이 깊습니다.',
    }

    result = by_strength.get(strength, by_strength['중화(中和)'])
    result += '\n  ' + by_yongshin[yongshin_oh]
    return result


def _love_text(ilgan, strength, yongshin_oh, has_dohwa, has_cheonul):
    yn = OHAENG_NAMES[yongshin_oh]

    by_ilgan = {
        0: (
            '갑목 일간은 원칙과 주관이 강해 연애에서도 자신이 주도하는 경향이 있습니다. '
            '이상형이 뚜렷하고 한번 마음을 준 사람에게 깊이 헌신하지만, '
            '고집이 지나쳐 상대를 답답하게 할 수 있습니다. '
            '상대방의 의견을 경청하고 먼저 양보하는 연습이 관계를 더욱 깊게 만들어 줍니다.'
        ),
        1: (
            '을목 일간은 유연하고 친근하여 이성에게 자연스럽게 다가갑니다. '
            '넝쿨처럼 상대방에게 의지하거나 감싸려는 경향이 있어 헌신적이지만, '
            '집착으로 이어지지 않도록 적당한 거리 유지가 중요합니다. '
            '혼자만의 시간을 소중히 여기는 상대를 배려하는 마음이 관계의 깊이를 더합니다.'
        ),
        2: (
            '병화 일간은 밝고 에너지 넘치는 매력으로 이성을 끌어당깁니다. '
            '연애에서 적극적이고 로맨틱하나 금방 식는 경향이 있어 지속적인 노력이 필요합니다. '
            '상대방의 감정을 세밀하게 살피고 꾸준한 애정 표현을 유지하는 것이 '
            '장기적인 관계 유지의 핵심입니다.'
        ),
        3: (
            '정화 일간은 섬세하고 감성적이어서 깊고 진실한 사랑을 추구합니다. '
            '표면적인 화려함보다 마음의 교감을 중시하며, '
            '한번 상처받으면 회복이 느린 편입니다. '
            '감정을 솔직하게 표현하고 내면의 불안을 상대와 나누는 것이 관계 발전에 도움이 됩니다.'
        ),
        4: (
            '무토 일간은 듬직하고 신뢰감이 있어 연애에서 안정적인 파트너 역할을 합니다. '
            '감정 표현이 다소 서툴러 상대방에게 무뚝뚝하거나 무관심하게 보일 수 있습니다. '
            '작은 일에도 관심과 애정을 표현하는 연습이 관계를 따뜻하게 만들어 줍니다.'
        ),
        5: (
            '기토 일간은 세심하고 성실하여 연애에서 헌신적인 모습을 보입니다. '
            '완벽주의적 성향으로 상대방에게도 높은 기준을 요구하는 경향이 있습니다. '
            '상대의 단점보다 장점에 집중하고 여유롭게 관계를 즐기는 태도가 필요합니다.'
        ),
        6: (
            '경금 일간은 의리와 직설적인 성격으로 연애에서도 솔직한 표현을 합니다. '
            '다소 강하고 거칠게 느껴질 수 있으나 '
            '한번 맺은 인연을 끝까지 책임지는 깊은 의리가 있습니다. '
            '부드러운 표현 방식을 익히고 상대의 감정에 더 민감하게 반응하는 노력이 필요합니다.'
        ),
        7: (
            '신금 일간은 세련되고 품격 있는 매력으로 이성의 시선을 끕니다. '
            '자존심이 강하고 이상형의 기준이 높아 인연을 만나기까지 시간이 걸릴 수 있습니다. '
            '완벽한 인연을 기다리기보다 함께 성장하는 인연을 찾는 열린 마음이 '
            '더 행복한 연애로 이어집니다.'
        ),
        8: (
            '임수 일간은 지적이고 유머 있는 매력으로 다양한 인연을 만납니다. '
            '자유를 사랑하고 구속을 싫어하여 진지한 관계로 발전하는 데 시간이 필요합니다. '
            '상대방에게 신뢰를 주기 위한 꾸준한 관심과 성실한 태도가 관계를 깊게 만들어 줍니다.'
        ),
        9: (
            '계수 일간은 감수성이 풍부하고 직관적이어서 '
            '첫눈에 상대방의 마음을 꿰뚫어 보는 능력이 있습니다. '
            '섬세하고 로맨틱하지만 내성적인 면이 있어 먼저 다가가기보다 기다리는 경향이 있습니다. '
            '자신의 감정을 조금 더 용기 있게 표현하는 것이 더 많은 인연의 문을 열어줍니다.'
        ),
    }

    result = by_ilgan[ilgan]

    if has_dohwa:
        result += (
            '\n  도화살의 기운으로 이성에게 자연스러운 매력과 아우라가 있습니다. '
            '자연스럽게 인기를 끌지만 그만큼 구설이나 불필요한 오해를 살 수 있습니다. '
            '이성 관계에서의 경계선을 명확히 하고 진지한 상대와의 관계에 집중하는 것이 현명합니다.'
        )
    if has_cheonul:
        result += (
            '\n  천을귀인의 기운으로 인생의 결정적인 순간에 좋은 이성 귀인이 나타납니다. '
            '어려울 때 손을 내밀어 주는 인연이 평생의 반려자가 될 가능성이 높습니다.'
        )

    result += (
        f'\n  용신 {yn}의 기운을 가진 분이나 {yn}을 좋아하는 분과의 인연이 '
        f'심리적 안정과 행복을 동시에 가져다주는 이상적인 만남이 됩니다.'
    )
    return result


def _job_text(ilgan, strength, yongshin_oh, ss_cnt):
    yn = OHAENG_NAMES[yongshin_oh]
    il_name = ILGAN_DESC[ilgan][0]

    by_yongshin = {
        0: (
            '목(木) 용신으로 성장·창조·생명을 다루는 직업이 천직에 가깝습니다. '
            '교육·출판·언론·환경·농업·의약품·패션·인테리어 등 나무와 성장을 상징하는 분야에서 두각을 나타냅니다. '
            '아이디어와 기획이 중심이 되는 업무에서 빛을 발하며, '
            '새로운 프로젝트를 처음부터 키워나가는 역할에서 가장 큰 성취감을 느낍니다.'
        ),
        1: (
            '화(火) 용신으로 밝음·열정·소통을 다루는 직업이 잘 맞습니다. '
            '방송·연예·디자인·요식업·에너지·전기전자·홍보·마케팅 분야가 인연이 깊습니다. '
            '대중 앞에 서거나 많은 사람과 소통하는 환경에서 능력이 극대화됩니다. '
            '내향적인 환경보다 활발하고 역동적인 조직 문화에서 두드러진 성과를 냅니다.'
        ),
        2: (
            '토(土) 용신으로 안정·신뢰·중재를 다루는 직업이 천성에 맞습니다. '
            '부동산·건설·농업·유통·행정·사회복지·상담·중개 분야에서 기반을 튼튼히 다져 성공합니다. '
            '빠른 변화보다 오랫동안 신뢰를 쌓아 인정받는 방식이 이 사주에 어울립니다. '
            '한 분야의 전문가로 오래 일할수록 사회적 위치가 높아지는 구조입니다.'
        ),
        3: (
            '금(金) 용신으로 결단·정밀·원칙을 다루는 직업이 적합합니다. '
            '금융·법조·의료·군·경·회계·기계·금속·외과 관련 분야에서 탁월한 능력을 발휘합니다. '
            '정확성과 원칙이 중시되는 환경에서 두각을 나타내며, '
            '어렵고 복잡한 문제를 명쾌하게 해결하는 능력으로 인정받습니다.'
        ),
        4: (
            '수(水) 용신으로 지식·유통·소통을 다루는 직업이 잘 어울립니다. '
            '정보통신·IT·연구·학문·무역·유통·저술·철학·심리 분야에서 깊이 있는 성취를 이룹니다. '
            '남들이 모르는 정보와 지식을 다루는 분야에서 독보적인 위치에 오를 수 있으며, '
            '꾸준히 공부하고 전문성을 쌓을수록 더 큰 기회가 찾아옵니다.'
        ),
    }

    by_strength = {
        '신강(身强)': (
            '신강 사주로 조직 내 리더 위치에 있거나 독립적인 환경에 있을 때 더욱 빛납니다. '
            '사업·창업·전문직으로 자신만의 영역을 구축하는 것이 이상적입니다. '
            '직장 생활을 한다면 팀장 이상의 책임 있는 자리에서 진가를 발휘합니다.'
        ),
        '신약(身弱)': (
            '신약 사주로 안정된 조직 내에서 전문성을 키우는 방식이 적합합니다. '
            '직장은 규모가 크고 체계적인 곳을 선택하고, 갑작스러운 창업이나 독립은 신중히 결정하세요. '
            '귀인과 동료의 도움을 잘 받아들이는 자세가 경력 발전에 중요합니다.'
        ),
        '중화(中和)': (
            '중화 사주로 조직과 독립 어느 쪽도 무난하게 적응합니다. '
            '초반 직장에서 기반을 다진 후 전문 분야에서 독립하는 수순이 이상적입니다.'
        ),
    }

    result = by_yongshin[yongshin_oh]
    result += '\n  ' + by_strength.get(strength, by_strength['중화(中和)'])

    gwan_cnt = ss_cnt.get('정관', 0) + ss_cnt.get('편관', 0)
    siksang_cnt = ss_cnt.get('식신', 0) + ss_cnt.get('상관', 0)
    if gwan_cnt == 0:
        result += '\n  관성이 없어 자유로운 환경이나 자영업·프리랜서가 더 잘 맞을 수 있습니다.'
    if siksang_cnt >= 2:
        result += '\n  식상이 강해 창의적이고 표현하는 직업(창작·강의·기획·예술)에서 탁월한 역량을 발휘합니다.'

    return result


def _health_text(ilgan, strength, yongshin_oh, zero, season_name, hyung):
    OHAENG_JANG = {
        '목': '간·담낭', '화': '심장·소장·혈압',
        '토': '위·비장·췌장·소화기', '금': '폐·대장·기관지', '수': '신장·방광·생식기'
    }
    yn = OHAENG_NAMES[yongshin_oh]

    season_health = {
        '봄': (
            '봄에 태어나 간·담낭 기능에 관심을 기울이세요. '
            '봄의 활발한 기운으로 에너지는 넘치지만 과로나 스트레스가 간에 부담을 줄 수 있습니다. '
            '음주를 절제하고 충분한 수면을 취하는 것이 간 건강을 지키는 핵심입니다.'
        ),
        '여름': (
            '여름에 태어나 심장·혈압·소장 건강에 유의하세요. '
            '뜨거운 사주에 더위가 더해지면 심혈관 질환이나 열성 질환이 나타날 수 있습니다. '
            '수분 섭취와 체온 조절에 각별히 신경 쓰고, 스트레스를 즉각 해소하는 습관을 들이세요.'
        ),
        '가을': (
            '가을에 태어나 폐·대장·기관지 건강을 챙기세요. '
            '건조한 가을 기운이 호흡기를 약하게 할 수 있으며, 피부 건조증에도 주의가 필요합니다. '
            '규칙적인 유산소 운동과 충분한 수분 섭취가 호흡기 건강을 지켜줍니다.'
        ),
        '겨울': (
            '겨울에 태어나 신장·방광·관절 건강에 유의하세요. '
            '차가운 사주 기운으로 냉증이나 혈액순환 장애, 관절 통증이 나타나기 쉽습니다. '
            '몸을 항상 따뜻하게 유지하고 규칙적인 운동으로 혈액순환을 원활히 하는 것이 중요합니다. '
            '찬 음식과 냉방에 각별히 주의하세요.'
        ),
    }

    result = season_health.get(season_name, '')

    if zero:
        result += (
            f'\n  부족한 오행({", ".join(zero)})과 연관된 장기에 취약점이 있습니다: '
            + ', '.join([f'{o}→{OHAENG_JANG[o]}' for o in zero if o in OHAENG_JANG])
            + '. 해당 부위 정기 검진을 권장합니다.'
        )

    if any('현침살' in s for s in hyung):
        result += (
            '\n  현침살이 있어 의료 기구나 수술과 인연이 있습니다. '
            '건강 이상 신호를 무시하지 말고 조기에 병원을 방문하세요. '
            '정기적인 종합검진이 특히 중요합니다.'
        )
    if any('탕화살' in s for s in hyung):
        result += (
            '\n  탕화살로 화재·열·사고에 주의가 필요합니다. '
            '조리나 기계 작업 시 안전수칙을 철저히 지키고, 자동차 사고에도 각별히 조심하세요.'
        )

    food_by_yongshin = {
        0: '신맛 음식(식초·레몬·매실)과 녹황색 채소가 목의 기운을 보강합니다.',
        1: '쓴맛 음식(쑥·녹차·고구마줄기)과 붉은 과일이 심장과 순환을 도웁니다.',
        2: '단맛(고구마·호박·대추)과 노란 채소가 소화기를 튼튼하게 합니다.',
        3: '매운맛(고추·마늘·생강)과 흰색 음식이 폐와 대장을 강화합니다.',
        4: '짠맛(해산물·된장·미역)과 검은 식품(흑미·검은콩)이 신장을 보강합니다.',
    }
    result += f'\n  용신 {yn}을 강화하는 음식을 가까이하면 전반적인 건강 기운이 높아집니다. ' + food_by_yongshin[yongshin_oh]
    return result


# ── 사주 해설 (통변) ──────────────────────────────────

def analyze_saju(name, pillars, gil, hyung):
    ilgan    = pillars[2][0]
    mj       = pillars[1][1]
    il_name  = ILGAN_DESC[ilgan][0]

    yongshin_oh, yongshin_name, basis, season_name, temp_adj = get_yongshin(pillars)
    deukryeong, dr_score, _  = get_deukryeong(pillars)
    strength = judge_strength(pillars)
    oa = analyze_ohaeng(pillars)

    # 십성 집계
    ss_cnt = {}
    for i, (g, j) in enumerate(pillars):
        if i != 2:
            ss = get_sipseong(ilgan, OHAENG_IDX[g], g%2)
            ss_cnt[ss] = ss_cnt.get(ss, 0) + 1
        ss = get_sipseong(ilgan, OHAENG_IDX_J[j], j%2)
        ss_cnt[ss] = ss_cnt.get(ss, 0) + 1

    out = [f'\n{"─"*62}', f'  ◈ {name}  사주 해설  (전문가 통변)', f'{"─"*62}']

    # ① 총평 & 성격
    out.append(f'\n  ▶ 총평 & 성격')
    out.append(f'  {_personality_text(ilgan, season_name, yongshin_name, strength)}')

    # 득령 해설
    if deukryeong:
        out.append(
            f'\n  [득령(得令)] 태어난 계절({season_name})에서 일간 {il_name}이(가) 왕성한 기운을 얻었습니다. '
            f'타고난 기질이 뚜렷하고 의지력과 추진력이 강합니다. '
            f'자신의 색깔이 분명하여 개성이 강하게 나타나며, 외부 환경에 쉽게 흔들리지 않습니다.'
        )
    else:
        out.append(
            f'\n  [실령(失令)] 태어난 계절({season_name})에서 일간 {il_name}이(가) 기운을 충분히 얻지 못했습니다. '
            f'타인의 도움과 환경의 조화가 중요하며, '
            f'용신({yongshin_name})의 기운을 가까이할수록 삶의 균형과 에너지가 회복됩니다. '
            f'주변 환경과 인간관계가 성패를 크게 좌우합니다.'
        )

    # ② 용신 해설
    out.append(f'\n  ▶ 용신(用神): {yongshin_name}  [{basis}]')
    out.append(f'  {_yongshin_detail(yongshin_oh, ilgan, strength, season_name)}')

    # ③ 맞춤 개운법
    gaeun = YONGSHIN_GAEUN[yongshin_oh]
    out.append(f'\n  ▶ 맞춤 개운법  (용신 기준: {yongshin_name})')
    out.append(f'  • 행운의 색상: {gaeun["color"]}')
    out.append(f'    이 색상의 옷, 지갑, 소품을 곁에 두면 {yongshin_name}의 기운을 보강할 수 있습니다.')
    out.append(f'  • 행운의 숫자: {gaeun["number"]}')
    out.append(f'    중요한 일의 날짜, 연락처 끝자리, 비밀번호 등에 활용해 보세요.')
    out.append(f'  • 행운의 방향: {gaeun["direction"]}')
    out.append(f'    책상·침대 머리 방향, 이사 방향을 이쪽으로 맞추면 기운 보강에 좋습니다.')
    out.append(f'  • 추천 취미·활동: {gaeun["hobby"]}')
    out.append(f'    {_hobby_desc(yongshin_oh)}')

    # ④ 재물운
    out.append(f'\n  ▶ 재물운')
    out.append(f'  {_finance_text(ilgan, strength, yongshin_oh, oa)}')

    # ⑤ 연애·이성운
    out.append(f'\n  ▶ 연애·이성운')
    has_dohwa  = any('도화살' in s for s in hyung)
    has_cheonul = any('천을귀인' in s for s in gil)
    out.append(f'  {_love_text(ilgan, strength, yongshin_oh, has_dohwa, has_cheonul)}')

    # ⑥ 직업·직장운
    out.append(f'\n  ▶ 직업·직장운')
    out.append(f'  {_job_text(ilgan, strength, yongshin_oh, ss_cnt)}')

    # ⑦ 건강운
    zero = [k for k, v in oa.items() if v == 0]
    out.append(f'\n  ▶ 건강운')
    out.append(f'  {_health_text(ilgan, strength, yongshin_oh, zero, season_name, hyung)}')

    # ⑧ 주요 신살
    all_sal = [(s, True) for s in gil] + [(s, False) for s in hyung]
    if all_sal:
        out.append(f'\n  ▶ 주요 신살 해설')
        for sal, is_gil in all_sal:
            key  = sal.split('(')[0]
            desc = SINSAL_DESC.get(key, '')
            mark = '길' if is_gil else '흉'
            if desc:
                out.append(f'  [{mark}] {sal}: {desc}')

    # ⑨ 일주 12운성
    uns = get_12unsung(ilgan, pillars[2][1])
    out.append(f'\n  ▶ 일주 12운성: {uns}')
    out.append(f'  {UNSUNG_DESC.get(uns, "")}')

    return '\n'.join(out)


# ── 궁합 점수 ────────────────────────────────────────

def 궁합_점수(pa, pb):
    ja = [p[1] for p in pa]; jb = [p[1] for p in pb]
    score = 60; reasons = []
    rel = check_relations(ja, jb)

    weights = {'합':8,'삼합':10,'충':-10,'형':-7,'파':-5,'해':-5,'원진':-8}
    for k, w in weights.items():
        for v in rel[k]:
            score += w
            reasons.append(f'[{k} {"+"+str(w) if w>0 else str(w)}] {v}')

    da, db = ja[2], jb[2]
    if frozenset([da,db]) in YUKAHP:
        score += 15; reasons.append('[일지합 +15] 부부 인연 강함')
    if frozenset([da,db]) in CHUNG:
        score -= 15; reasons.append('[일지충 -15] 부부 갈등 주의')

    oa, ob = analyze_ohaeng(pa), analyze_ohaeng(pb)
    comp = [k for k in oa if oa[k]==0 and ob[k]>0]
    if comp:
        score += len(comp)*3
        reasons.append(f'[오행보완 +{len(comp)*3}] {",".join(comp)} 부족분 보완')

    # 용신 교차 보너스
    ya_oh = get_yongshin(pa)[0]
    yb_oh = get_yongshin(pb)[0]
    ya_name = OHAENG_NAMES[ya_oh]
    yb_name = OHAENG_NAMES[yb_oh]
    if ob.get(ya_name, 0) > 0:
        score += 10; reasons.append(f'[용신보완 +10] B가 A의 용신({ya_name}) 보유')
    if oa.get(yb_name, 0) > 0:
        score += 10; reasons.append(f'[용신보완 +10] A가 B의 용신({yb_name}) 보유')

    return max(0, min(100, score)), reasons, rel


def 궁합_점수_named(pa, pb, na, nb):
    ja = [p[1] for p in pa]; jb = [p[1] for p in pb]
    score = 60; reasons = []
    rel = check_relations(ja, jb)

    weights = {'합':8,'삼합':10,'충':-10,'형':-7,'파':-5,'해':-5,'원진':-8}
    for k, w in weights.items():
        for v in rel[k]:
            score += w
            reasons.append(f'[{k} {"+"+str(w) if w>0 else str(w)}] {v}')

    da, db = ja[2], jb[2]
    if frozenset([da,db]) in YUKAHP:
        score += 15; reasons.append('[일지합 +15] 부부 인연 강함')
    if frozenset([da,db]) in CHUNG:
        score -= 15; reasons.append('[일지충 -15] 부부 갈등 주의')

    oa, ob = analyze_ohaeng(pa), analyze_ohaeng(pb)
    comp = [k for k in oa if oa[k]==0 and ob[k]>0]
    if comp:
        score += len(comp)*3
        reasons.append(f'[오행보완 +{len(comp)*3}] {",".join(comp)} 부족분 보완')

    ya_oh = get_yongshin(pa)[0]
    yb_oh = get_yongshin(pb)[0]
    ya_name = OHAENG_NAMES[ya_oh]
    yb_name = OHAENG_NAMES[yb_oh]
    if ob.get(ya_name, 0) > 0:
        score += 10; reasons.append(f'[용신보완 +10] {nb}가 {na}의 용신({ya_name}) 보유')
    if oa.get(yb_name, 0) > 0:
        score += 10; reasons.append(f'[용신보완 +10] {na}가 {nb}의 용신({yb_name}) 보유')

    return max(0, min(100, score)), reasons, rel


# ── 궁합 해설 (스토리텔링) ────────────────────────────

def analyze_gunghap(pa, pb, na, nb, score, rel):
    ia, ib   = pa[2][0], pb[2][0]
    oa_oh    = OHAENG_IDX[ia]
    ob_oh    = OHAENG_IDX[ib]

    ya_oh, ya_name, ya_basis, ya_season, ya_temp = get_yongshin(pa)
    yb_oh, yb_name, yb_basis, yb_season, yb_temp = get_yongshin(pb)

    oa_counts = analyze_ohaeng(pa)
    ob_counts = analyze_ohaeng(pb)
    a_yn_in_b = ob_counts.get(ya_name, 0) > 0
    b_yn_in_a = oa_counts.get(yb_name, 0) > 0

    diff = (ob_oh - oa_oh) % 5

    out = [f'\n{"─"*62}', f'  ◈ 궁합 상세 해설  (전문가 통변)', f'{"─"*62}']

    # ① 일간 오행 관계 스토리
    out.append(f'\n  ▶ 두 분의 타고난 기운 관계')
    il_story = {
        0: (
            f'{na}님({ILGAN_DESC[ia][0]})과 {nb}님({ILGAN_DESC[ib][0]})은 같은 오행으로 '
            f'성격과 가치관이 유사해 처음 만났을 때부터 통하는 부분이 많습니다. '
            f'서로를 잘 이해하고 공감대가 크지만, 같은 주장을 고집하다 보면 '
            f'경쟁심이나 자존심 대결로 이어질 수 있습니다. '
            f'서로의 역할 분담을 명확히 하고 의식적으로 다른 점을 존중하는 것이 중요합니다.'
        ),
        1: (
            f'{na}님({ILGAN_DESC[ia][0]})의 기운이 {nb}님({ILGAN_DESC[ib][0]})을 자연스럽게 생하는 구조입니다. '
            f'{na}님이 {nb}님에게 에너지와 영감을 공급하는 역할을 맡게 됩니다. '
            f'한쪽이 일방적으로 베푸는 관계가 되지 않도록 '
            f'{nb}님도 충분한 감사와 보답을 표현해야 균형이 유지됩니다.'
        ),
        4: (
            f'{nb}님({ILGAN_DESC[ib][0]})의 기운이 {na}님({ILGAN_DESC[ia][0]})을 자연스럽게 생하는 구조입니다. '
            f'{nb}님이 {na}님에게 안정과 힘을 제공하는 형국입니다. '
            f'{na}님이 {nb}님의 도움을 당연하게 여기지 않고 관계 속에서 '
            f'자신의 기여를 찾아야 건강하고 오래가는 관계가 됩니다.'
        ),
        2: (
            f'{na}님({ILGAN_DESC[ia][0]})의 기운이 {nb}님({ILGAN_DESC[ib][0]})을 강하게 극하는 구조입니다. '
            f'{na}님이 관계를 주도하고 {nb}님이 따라가는 형태가 되기 쉽습니다. '
            f'{nb}님이 압박감이나 위축감을 느끼지 않도록 '
            f'{na}님이 의식적으로 배려와 경청을 실천해야 합니다. '
            f'상하 관계가 아닌 동반자 관계로 유지하려는 두 분 모두의 노력이 필요합니다.'
        ),
        3: (
            f'{nb}님({ILGAN_DESC[ib][0]})의 기운이 {na}님({ILGAN_DESC[ia][0]})을 강하게 극하는 구조입니다. '
            f'{nb}님이 관계를 주도하고 {na}님이 따르는 경향이 생깁니다. '
            f'{na}님의 자존감을 지켜주고 대화에서 동등한 발언권을 보장하는 것이 '
            f'관계 유지의 핵심입니다.'
        ),
    }
    out.append(f'  {il_story[diff]}')

    # ② 용신 교차 분석 (핵심 스토리텔링)
    out.append(f'\n  ▶ 용신 교차 분석  (두 사주의 본질적 궁합)')
    out.append(f'  {na}님의 용신: {ya_name} ({ya_basis})  /  {nb}님의 용신: {yb_name} ({yb_basis})')

    if a_yn_in_b and b_yn_in_a:
        out.append(f'\n  ★ 용신 쌍방 보완 — 최고 수준의 궁합입니다!')
        out.append(
            f'  {na}님에게 가장 필요한 {ya_name}의 기운을 {nb}님의 사주가 충분히 가지고 있으며,'
        )
        out.append(
            f'  반대로 {nb}님에게 필요한 {yb_name}의 기운을 {na}님의 사주가 보완해 줍니다.'
        )
        out.append(
            f'  두 분은 서로가 서로의 삶에 없어서는 안 되는 존재가 됩니다.'
        )
        out.append(
            f'  {na}님은 {nb}님 곁에서 삶의 균형과 에너지를 얻고,'
            f'  {nb}님은 {na}님 곁에서 부족한 기운을 채워 더욱 빛나게 됩니다.'
        )
        out.append(
            f'  함께할수록 두 분 모두의 운이 열리는 진정한 천생연분 구조입니다. '
            f'  이 인연을 소중히 여기고 꾸준히 감사함을 표현하며 함께 성장해 나가시길 바랍니다.'
        )
    elif a_yn_in_b:
        out.append(
            f'  {nb}님의 사주에 {na}님의 용신인 {ya_name}의 기운이 있어,'
        )
        out.append(
            f'  {nb}님은 {na}님에게 심리적 안정과 활력을 공급해 주는 소중한 존재입니다.'
        )
        out.append(
            f'  {na}님은 {nb}님 곁에 있을 때 자신도 모르게 편안함과 운이 열리는 것을 느낍니다.'
        )
        out.append(
            f'  다만 {na}님의 용신을 {nb}님이 일방적으로 채워주는 구조이므로,'
            f'  {na}님이 {nb}님에게 필요한 {yb_name}의 기운을 어떻게 보완해 줄지 고민이 필요합니다.'
        )
        out.append(
            f'  {na}님이 받는 것 이상으로 {nb}님에게 헌신하고 감사를 표현할 때 이 궁합은 최고로 빛납니다.'
        )
    elif b_yn_in_a:
        out.append(
            f'  {na}님의 사주에 {nb}님의 용신인 {yb_name}의 기운이 있어,'
        )
        out.append(
            f'  {na}님은 {nb}님에게 없어서는 안 될 든든한 지원자가 됩니다.'
        )
        out.append(
            f'  {nb}님은 {na}님 곁에서 에너지와 삶의 방향성을 얻습니다.'
        )
        out.append(
            f'  단 {nb}님이 {na}님에게만 의존하지 않도록 독립적인 내면의 힘을 기르는 것이 중요합니다.'
        )
        out.append(
            f'  {na}님도 {nb}님에게 필요한 것을 꾸준히 채워주려는 의식적 노력이 관계를 더욱 깊게 만듭니다.'
        )
    else:
        out.append(
            f'  두 분의 용신이 서로의 사주에 직접적으로 나타나지 않는 구조입니다.'
        )
        out.append(
            f'  이는 서로가 상대방의 필요를 자연스럽게 채워주기보다 '
            f'의식적인 노력과 소통이 더 많이 요구되는 관계임을 의미합니다.'
        )
        out.append(
            f'  서로의 다름을 인정하고 상대가 원하는 것을 배우려는 적극적인 자세가 '
            f'이 궁합을 빛나게 하는 핵심 열쇠입니다. '
            f'사랑과 노력이 더해질수록 관계가 깊어지는 구조입니다.'
        )

    # 용신 충(冲) 파괴 경고
    ja_list = [p[1] for p in pa]
    jb_list = [p[1] for p in pb]
    ya_jijis = [j for j in range(12) if OHAENG_IDX_J[j] == ya_oh]
    yb_jijis = [j for j in range(12) if OHAENG_IDX_J[j] == yb_oh]

    ya_hit = any(frozenset([j, jb]) in CHUNG for j in ya_jijis for jb in jb_list)
    yb_hit = any(frozenset([j, ja]) in CHUNG for j in yb_jijis for ja in ja_list)

    if ya_hit or yb_hit:
        out.append(f'\n  ⚠ 주의: 서로의 용신을 건드리는 충(冲) 관계가 감지됩니다.')
        if ya_hit:
            out.append(
                f'  상대방({nb}님)의 사주가 {na}님의 용신({ya_name})을 충하여 '
                f'함께할 때 {na}님의 에너지가 소모되는 느낌을 받을 수 있습니다.'
            )
        if yb_hit:
            out.append(
                f'  {na}님의 사주가 {nb}님의 용신({yb_name})을 충하여 '
                f'{nb}님이 관계 속에서 피로감을 느낄 수 있습니다.'
            )
        out.append(
            f'  큰 결정은 반드시 함께 논의한 뒤 신중히 내리고, '
            f'상대방의 에너지가 고갈될 때 충분한 회복 시간을 주는 배려가 필요합니다.'
        )

    # ③ 지지 관계 상세 스토리
    if rel.get('합'):
        out.append(f'\n  ▶ 지지 합: {", ".join(rel["합"])}')
        out.append(
            f'  사주의 지지끼리 자연스럽게 합을 이루고 있습니다. '
            f'두 분은 처음 만났을 때부터 묘한 끌림을 느끼고 자연스럽게 가까워지는 에너지가 있습니다. '
            f'합이 되는 오행의 기운이 사주 전체에 긍정적인 영향을 미쳐 함께할 때 시너지가 납니다. '
            f'공동의 목표나 프로젝트를 함께할 때 특히 강한 결속력이 발휘됩니다.'
        )
    if rel.get('삼합'):
        out.append(f'\n  ▶ 삼합/반합: {", ".join(rel["삼합"])}')
        out.append(
            f'  삼합의 기운은 두 사람을 하나의 강한 팀으로 묶어주는 에너지입니다. '
            f'함께 일하거나 공동의 목표를 가질 때 놀라운 성과를 낼 수 있는 궁합입니다. '
            f'사업 파트너나 공동 창업으로도 훌륭한 조합이 될 수 있으며, '
            f'서로의 강점을 합쳐 혼자서는 이루기 어려운 큰 성과를 달성합니다.'
        )
    if rel.get('충'):
        out.append(f'\n  ▶ 지지 충: {", ".join(rel["충"])}')
        out.append(
            f'  충의 기운으로 크고 작은 의견 충돌이 생기기 쉽습니다. '
            f'서로의 방식이나 가치관이 정면으로 부딪히는 지점이 있어 '
            f'특히 중요한 결정을 내릴 때 갈등이 표면에 드러납니다. '
            f'그러나 충은 단순한 갈등이 아니라 서로를 자극하여 성장하게 하는 에너지이기도 합니다. '
            f'감정적으로 반응하기보다 상대의 다른 시각에서 배울 점을 찾는 자세를 가지면 '
            f'오히려 이 긴장감이 두 분 모두를 더 높은 수준으로 끌어올리는 원동력이 됩니다.'
        )
    if rel.get('원진'):
        out.append(f'\n  ▶ 원진: {", ".join(rel["원진"])}')
        out.append(
            f'  원진은 서로 멀어지려는 힘으로 함께 있을 때 묘한 답답함이나 불편함을 느낄 수 있습니다. '
            f'사소한 오해가 쌓이면 큰 갈등으로 발전하기 쉬우므로 '
            f'감정이 상했을 때 즉각 표현하지 말고 한 박자 쉬고 이야기하는 습관이 필요합니다. '
            f'꾸준한 대화와 작은 감사 표현이 원진의 부정적 기운을 중화하는 가장 좋은 방법입니다. '
            f'물리적으로 잠시 떨어지는 시간이 오히려 관계에 활력을 줄 수 있습니다.'
        )
    if rel.get('형'):
        out.append(f'\n  ▶ 형: {", ".join(rel["형"])}')
        out.append(
            f'  형의 기운으로 서로 자신의 방식이 옳다고 생각하여 마찰이 생기기 쉽습니다. '
            f'"내 방식대로 해야 한다"는 고집을 내려놓고 상대방의 방식도 수용하는 유연함이 '
            f'이 궁합을 건강하게 유지하는 핵심입니다. '
            f'서로의 규칙과 원칙을 존중하되 강요하지 않는 태도가 필요합니다.'
        )

    # ④ 오행 보완 스토리
    oa_a, oa_b = analyze_ohaeng(pa), analyze_ohaeng(pb)
    comp_ab = [k for k in oa_a if oa_a[k] == 0 and oa_b[k] > 0]
    comp_ba = [k for k in oa_b if oa_b[k] == 0 and oa_a[k] > 0]
    if comp_ab or comp_ba:
        OHAENG_JANG2 = {'목':'간·담','화':'심장·혈관','토':'위·소화기','금':'폐·대장','수':'신장·정신력'}
        out.append(f'\n  ▶ 오행 보완 분석')
        if comp_ab:
            out.append(
                f'  {na}님 사주에 부족한 {", ".join(comp_ab)}을(를) {nb}님이 가지고 있습니다. '
                f'{nb}님은 {na}님이 삶에서 취약한 부분을 자연스럽게 채워주는 소중한 존재입니다. '
                f'특히 {", ".join([f"{k}({OHAENG_JANG2.get(k,k)})" for k in comp_ab])} 관련 영역에서 '
                f'{na}님이 {nb}님에게 의지하고 도움받는 상황이 자주 생깁니다.'
            )
        if comp_ba:
            out.append(
                f'  {nb}님 사주에 부족한 {", ".join(comp_ba)}을(를) {na}님이 가지고 있습니다. '
                f'{na}님은 {nb}님의 부족한 기운을 메워주는 역할을 자연스럽게 하게 됩니다. '
                f'두 분이 각자의 부족한 부분을 서로 채워줄 때 관계가 더욱 깊어집니다.'
            )

    # ⑤ 최종 총평
    out.append(f'\n  ▶ 최종 총평')
    if score >= 85:
        out.append(
            f'  종합 {score}점으로 매우 드문 천생연분급 궁합입니다. '
            f'두 분의 사주는 오행·용신·지지 관계 모든 면에서 서로를 완성시켜 주는 조합입니다. '
            f'함께할 때 두 분 모두의 운이 열리며 가정·재물·건강 모든 방면에서 시너지를 냅니다. '
            f'이 인연을 소중히 여기고 꾸준히 감사함을 표현하며 함께 성장해 나가시길 바랍니다.'
        )
    elif score >= 70:
        out.append(
            f'  종합 {score}점으로 좋은 궁합입니다. '
            f'서로 보완되는 기운이 많아 함께할 때 각자보다 훨씬 큰 힘을 발휘합니다. '
            f'위에 언급된 주의사항을 참고하여 의식적으로 보완한다면 '
            f'오래도록 안정적이고 행복한 관계를 이어갈 수 있는 좋은 인연입니다.'
        )
    elif score >= 55:
        out.append(
            f'  종합 {score}점으로 무난한 궁합입니다. '
            f'보완되는 기운도 있고 부딪히는 기운도 있는 현실적인 관계입니다. '
            f'사랑만으로 모든 것을 해결하려 하기보다 서로의 다름을 인정하고 '
            f'구체적인 소통 방식과 역할을 정해 나가는 것이 이 궁합을 빛나게 하는 열쇠입니다. '
            f'노력하는 만큼 관계가 깊어지는 구조입니다.'
        )
    elif score >= 40:
        out.append(
            f'  종합 {score}점으로 도전적인 궁합입니다. '
            f'두 분의 기운이 상충되는 부분이 많아 함께할 때 마찰이 빈번할 수 있습니다. '
            f'그러나 어려운 궁합일수록 두 분이 각자를 성장시키는 관계가 됩니다. '
            f'작은 것에 감사하고 표현하는 습관, 그리고 상대를 이해하려는 지속적 노력이 '
            f'이 도전을 함께 이겨내는 힘이 됩니다.'
        )
    else:
        out.append(
            f'  종합 {score}점으로 매우 신중한 접근이 필요한 궁합입니다. '
            f'사주의 기운이 여러 면에서 충돌하여 함께할 때 서로가 힘들어지는 구조입니다. '
            f'억지로 맞추려 하기보다 각자의 시간과 공간을 충분히 존중하고 '
            f'서로의 역할과 경계선을 명확히 정하는 것이 관계 유지에 필수적입니다. '
            f'관계를 지속하려 한다면 두 분 모두의 강한 의지와 지속적인 노력이 필요합니다.'
        )

    return '\n'.join(out)


# ── 출력 ─────────────────────────────────────────────

def _wlen(s):
    return sum(2 if ord(c) > 0x2E7F else 1 for c in s)

def _cell(s, w):
    p = max(0, w - _wlen(s))
    return ' '*(p//2) + s + ' '*(p - p//2)

def print_saju(name, pillars, corr_dt, corrections):
    ilgan = pillars[2][0]
    gm    = get_gongmang(*pillars[2])
    gil, hyung = check_sal(pillars)

    order = [3, 2, 1, 0]
    hdrs  = ['시주(時)', '일주(日)', '월주(月)', '년주(年)']

    def _ss_g(i):
        g = pillars[i][0]
        return '일간' if i == 2 else get_sipseong(ilgan, OHAENG_IDX[g], g%2)
    def _ss_j(i):
        return get_sipseong(ilgan, OHAENG_IDX_J[pillars[i][1]], pillars[i][1]%2)
    def _jj(i):
        j = pillars[i][1]
        return JIJI[j] + ('[공]' if j in gm else '')

    CW, LW = 10, 8
    div = '  ' + '─'*(LW+1) + '┼' + ('─'*CW+'┼')*4

    def _row(label, vals):
        cells = '│'.join(_cell(v, CW) for v in vals)
        return f'  {_cell(label,LW)} │{cells}│'

    print(f'\n{"═"*62}')
    print(f'  ◈ {name}  사주팔자')
    print(f'  보정: {corr_dt.strftime("%Y-%m-%d %H:%M")}  ({", ".join(corrections)})')
    print(f'{"═"*62}')
    print(_row('', hdrs))
    print(div)
    print(_row('천간',   [CHEONGAN[pillars[i][0]] for i in order]))
    print(_row('십성',   [_ss_g(i) for i in order]))
    print(div)
    print(_row('지지',   [_jj(i) for i in order]))
    print(_row('십성 ',  [_ss_j(i) for i in order]))
    print(_row('12운성', [get_12unsung(ilgan, pillars[i][1]) for i in order]))
    print(div)
    print(_row('지장간', [''.join(JIJANGAN[pillars[i][1]]) for i in order]))
    print(div)

    yj = pillars[0][1]
    print(f'  년주 지지: {JIJI[yj]}  ({ANIMALS[yj]}띠)')
    if gm:
        print(f'  공망: {" ".join(JIJI[x] for x in sorted(gm))}')

    oa = analyze_ohaeng(pillars)
    print(f'  오행: ', end='')
    for k, v in oa.items():
        print(f'{k}{"■"*v}({v}) ', end='')
    print()

    if gil:   print(f'  길신: {", ".join(gil)}')
    if hyung: print(f'  흉살: {", ".join(hyung)}')

    rel = check_relations([p[1] for p in pillars])
    for k, vs in rel.items():
        if vs: print(f'  {k}: {", ".join(vs)}')

    print(analyze_saju(name, pillars, gil, hyung))

def print_gunghap(pa, pb, na, nb):
    score, reasons, rel = 궁합_점수_named(pa, pb, na, nb)
    print(f'\n{"━"*62}')
    print(f'  ♥  {na}  ×  {nb}  궁합')
    print(f'{"━"*62}')
    ja = [JIJI[p[1]] for p in pa]; jb = [JIJI[p[1]] for p in pb]
    print(f'  {na}: 년{ja[0]} 월{ja[1]} 일{ja[2]} 시{ja[3]}')
    print(f'  {nb}: 년{jb[0]} 월{jb[1]} 일{jb[2]} 시{jb[3]}')

    grades = ['▽ 어려움','△ 주의','○ 보통','◎ 좋음','★ 매우 좋음']
    gi = min(4, score // 20)
    print(f'\n  궁합 점수: {score}점  {grades[gi]}')
    print()
    for r in reasons: print(f'    {r}')
    print(analyze_gunghap(pa, pb, na, nb, score, rel))

# ── 입력 및 메인 ──────────────────────────────────────

def input_person(name):
    print(f'\n  [{name}] 생년월일시 입력')
    y  = int(input('    년도 (예: 1990)          : '))
    m  = int(input('    월   (1~12)              : '))
    d  = int(input('    일   (1~31)              : '))
    h  = int(input('    시   (0~23, 모를경우 12)  : '))
    mn = int(input('    분   (0~59, 모를경우 0)   : '))
    return y, m, d, h, mn

def main():
    print('\n' + '═'*62)
    print('           사주 & 궁합 분석 프로그램')
    print('═'*62)
    print('  1. 사주 보기')
    print('  2. 궁합 보기')
    choice = input('\n  선택 (1 또는 2): ').strip()

    if choice == '1':
        name   = input('  이름: ')
        gender = input('  성별 (남/여): ').strip()
        is_male = gender == '남'
        y, m, d, h, mn = input_person(name)
        pillars, corr_dt, corrections = get_saju(y, m, d, h, mn)
        print_saju(name, pillars, corr_dt, corrections)
        dw = get_daewoon(pillars, corr_dt, is_male)
        sw = get_sewoon(y)
        print_daewoon(*dw, sw)

    elif choice == '2':
        na = input('  첫 번째 분 이름: ')
        ga = input('  성별 (남/여): ').strip()
        y, m, d, h, mn = input_person(na)
        pa, corr_a, corr_list_a = get_saju(y, m, d, h, mn)
        dw_a = get_daewoon(pa, corr_a, ga == '남')
        sw_a = get_sewoon(y)

        nb = input('\n  두 번째 분 이름: ')
        gb = input('  성별 (남/여): ').strip()
        y, m, d, h, mn = input_person(nb)
        pb, corr_b, corr_list_b = get_saju(y, m, d, h, mn)
        dw_b = get_daewoon(pb, corr_b, gb == '남')
        sw_b = get_sewoon(y)

        print_saju(na, pa, corr_a, corr_list_a)
        print_daewoon(*dw_a, sw_a)
        print_saju(nb, pb, corr_b, corr_list_b)
        print_daewoon(*dw_b, sw_b)
        print_gunghap(pa, pb, na, nb)

    print('\n' + '═'*62)
    input('\n  Enter 를 누르면 종료합니다...')

if __name__ == '__main__':
    main()
