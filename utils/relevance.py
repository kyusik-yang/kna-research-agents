"""Shared relevance filter for Korean political science papers."""

# Journal patterns (case-insensitive partial match)
POLSCI_JOURNAL_PATTERNS = [
    # Korean political science
    "정치학회보", "의정연구", "의정논총", "정당학회보", "국제정치논총",
    "한국과 국제정치", "입법학연구", "입법과 정책", "현대정치연구",
    "선거연구", "한국정치연구", "정치학회", "정치외교사", "세계정치",
    "한국정치", "정치정보연구",
    # Korean public admin / policy
    "행정학보", "정책학회보", "정부학연구", "행정논총", "행정논집",
    "행정연구", "지방행정", "지방자치", "지방정부",
    # Korean social science
    "사회과학연구", "한국사회학",
    # English-language
    "political science", "political studies", "politics",
    "legislative", "parliamentary", "electoral studies",
    "public administration", "public policy", "governance",
    "asian survey", "pacific review", "pacific affairs",
    "korea observer", "korean studies", "east asian",
    "democratization", "party politics", "comparative politic",
    "journal of politics", "government and opposition",
]

KOREA_TITLE_TERMS = [
    "korea", "korean", "한국", "국회", "대한민국", "south korea",
    "national assembly",
]

POLSCI_TITLE_TERMS = [
    "legislat", "parliament", "party", "politic", "election", "voter",
    "voting", "democrat", "ideolog", "polariz", "committee", "congress",
    "bureaucra", "입법", "정당", "선거", "위원회", "정치", "의원", "법안",
    "표결", "투표", "행정", "정책",
]


def is_relevant_paper(title, journal=""):
    """Check if a paper is relevant to Korean political science.

    Korea mention in title is ALWAYS required.
    Known polsci journals: Korea terms sufficient.
    Unknown journals: Korea + polsci terms both required.
    """
    j = (journal or "").lower()
    t = (title or "").lower()
    has_korea = any(term in t for term in KOREA_TITLE_TERMS)
    if not has_korea:
        return False
    for pat in POLSCI_JOURNAL_PATTERNS:
        if pat.lower() in j:
            return True
    has_polsci = any(term in t for term in POLSCI_TITLE_TERMS)
    return has_polsci
