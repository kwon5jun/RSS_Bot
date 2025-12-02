def check_filter(item: dict) -> bool:
    
    # 통과시킬 키워드 제목, 내용
    keywords = ["긴급", "경고", "취약", "보안", "위협", "해킹", "유출", "랜섬웨어", "악성코드"]
    
    # 차단시킬 키워드 제목, 내용
    blacklist = ["게임", "광고", "이벤트", "쿠폰", "할인", "프로모션", "특가", "팝업"
                , "출시", "브랜드", "세일", "프랜차이즈", "[리뷰]", "[인사]", "[부고]"]
    
    # 차단시킬 작성자
    blackcreators = [] #["IP전략연구소" ]

    title = (item.get("title") or "").lower()
    desc = (item.get("description") or "").lower()
    creator = (item.get("creator") or "").lower()

    # 특정 키워드가 있으면 바로 통과
    if any(k.lower() in title or k.lower() in desc for k in keywords):
        return True
    # 특정 키워드가 없으면 블랙리스트 검사 후 차단
    if any(b.lower() in title or b.lower() in desc for b in blacklist):
        return False
    # 특정 작성자 차단
    if any(bc.lower() in creator for bc in blackcreators):
        return False
    # 다 없으면 통과
    return True