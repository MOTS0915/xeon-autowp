# -*- coding: utf-8 -*-
import os
import requests
import base64
import urllib3
import urllib.parse
from google import genai
import time
import random
import json

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경변수 로드
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASS = os.environ.get("WP_APP_PASS")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# 🚀 모델 설정
MODELS_TO_TRY = ["gemini-2.0-flash-exp", "gemini-2.0-flash-lite", "gemini-flash-latest"]

def generate_content_with_retry(prompt, use_search=False):
    """AI 콘텐츠 생성 (웹 서치 옵션 포함)"""
    for model in MODELS_TO_TRY:
        try:
            print(f"📡 연결 시도 중... (Model: {model})")
            
            # Google Search 도구 활성화
            tools = []
            if use_search:
                tools = ['google_search_retrieval']
                print("🔍 Google Search 활성화")
            
            config_params = {
                "model": model,
                "contents": prompt
            }
            
            if tools:
                config_params["config"] = genai.types.GenerateContentConfig(tools=tools)
            
            response = client.models.generate_content(**config_params)
            return response.text
        except Exception as e:
            print(f"⚠️ {model} 에러 발생: {e}")
            print("⏳ 3초 후 다른 모델로 재시도합니다...")
            time.sleep(3)
            continue
            
    raise Exception("❌ 모든 AI 모델이 응답하지 않습니다.")

def get_recent_posts():
    """기존 작성 글 조회"""
    print("📚 기존에 작성한 글 목록을 조회합니다...")
    try:
        response = requests.get(WP_URL, params={'per_page': 20}, verify=False)
        if response.status_code == 200:
            posts = response.json()
            titles = [post['title']['rendered'] for post in posts]
            print(f"✅ 최근 글 {len(titles)}개를 확인했습니다.")
            return titles
        else:
            print("⚠️ 글 목록 조회 실패 (무시하고 진행)")
            return []
    except Exception as e:
        print(f"⚠️ 글 목록 조회 중 에러: {e}")
        return []

def get_search_friendly_topic(existing_titles):
    """🆕 개선: 더 구체적이고 검색 친화적인 주제 선정"""
    print("🕵️‍♀️ 트렌디하고 검색 가능성 높은 주제 발굴 중...")
    
    exclude_list = ", ".join(existing_titles) if existing_titles else "없음"
    
    try:
        prompt = f"""
당신은 SEO 전문가이자 경제 블로거입니다.
오늘 날짜는 {time.strftime('%Y년 %m월 %d일')}입니다.

**미션: 2040 세대가 "지금 당장" 검색할 만한 경제/금융 주제 1개 추천**

[✅ 좋은 주제의 조건]
1. 구체성: "주식 투자"(X) → "2025년 2월 반도체 업황과 투자 포인트"(O)
2. 시의성: 최근 1주일 이내 이슈와 연결
3. 실용성: 읽고 나서 바로 행동할 수 있는 내용
4. 검색량: 실제로 사람들이 검색할 법한 키워드 포함

[🎯 추천 분야]
- 최신 경제 뉴스 분석 (금리, 환율, 부동산, 물가 등)
- 핫한 종목/섹터 분석 (AI, 2차전지, 바이오 등)
- 재테크 실전 가이드 (ETF, 배당주, 연금저축 등)
- 경제 용어 쉽게 풀이

[⛔ 중복 금지 - 아래 주제들과 비슷한 건 절대 피할 것]
{exclude_list}

**출력 형식: 주제만 한 줄로 (예시: "미국 빅테크 실적 발표 앞두고 주목할 포인트 3가지")**
"""
        topic = generate_content_with_retry(prompt, use_search=False).strip()
        topic = topic.replace('"', '').replace("'", '').replace('**', '').strip()
        
        # 여러 줄인 경우 첫 줄만
        if '\n' in topic:
            topic = topic.split('\n')[0].strip()
        
        print(f"✨ 선정된 주제: {topic}")
        return topic
    except Exception as e:
        print(f"❌ 주제 선정 실패: {e}")
        return "2025년 개인투자자를 위한 ETF 포트폴리오 구성 전략"

def research_topic(topic):
    """🆕 1단계: 주제에 대한 심층 리서치"""
    print(f"🔍 [{topic}] 관련 최신 정보 수집 중...")
    
    try:
        prompt = f"""
당신은 경제 전문 리서처입니다.
주제: "{topic}"

**미션: 이 주제로 블로그 글을 쓰기 위한 사전 조사**

[🔍 조사할 내용]
1. 최신 뉴스/데이터 (최근 1주일 이내)
2. 핵심 통계 수치 및 출처
3. 전문가 의견이나 시장 전망
4. 일반인이 궁금해할 3가지 질문
5. 실용적인 투자/재테크 팁

**웹 검색을 적극 활용하여 최신 정보를 찾아주세요.**
**출력 형식: 조사 결과를 요약 정리 (불릿 포인트 형식)**
"""
        research_result = generate_content_with_retry(prompt, use_search=True)
        print("✅ 리서치 완료!")
        print(f"📊 수집된 정보 미리보기:\n{research_result[:300]}...\n")
        return research_result
    except Exception as e:
        print(f"⚠️ 리서치 실패, 기본 정보로 진행: {e}")
        return f"{topic}에 대한 기본 정보를 바탕으로 작성합니다."

def create_outline(topic, research_data):
    """🆕 2단계: 글의 아웃라인 생성"""
    print("📝 글 구조 설계 중...")
    
    try:
        prompt = f"""
당신은 베테랑 블로그 에디터입니다.

**주제:** {topic}

**리서치 자료:**
{research_data}

**미션: 위 자료를 바탕으로 블로그 글의 아웃라인을 작성하세요**

[📋 아웃라인 구조]
1. 도입부 (후킹 문장 + 왜 이 주제가 중요한지)
2. 본문 섹션 3~4개 (각 섹션의 핵심 메시지)
   - 섹션마다 구체적인 데이터나 사례 포함
3. 실전 활용 팁 (독자가 바로 적용할 수 있는 것)
4. 마무리 (핵심 요약 + 다음 행동 제안)

[✅ 필수 요구사항]
- 각 섹션은 명확한 소제목으로 구분
- 2040 세대 눈높이에 맞춘 쉬운 설명
- 추상적 내용(X) → 구체적 숫자와 예시(O)

**출력 형식:**
제목: [SEO 최적화된 제목]

1. 도입부
   - 핵심 메시지: ...

2. [섹션1 제목]
   - 핵심 메시지: ...
   - 포함할 데이터: ...

3. [섹션2 제목]
   ...

(이하 생략)
"""
        outline = generate_content_with_retry(prompt, use_search=False)
        print("✅ 아웃라인 생성 완료!\n")
        print(f"📐 구조 미리보기:\n{outline[:400]}...\n")
        return outline
    except Exception as e:
        print(f"⚠️ 아웃라인 생성 실패: {e}")
        return f"제목: {topic}\n\n기본 구조로 진행합니다."

def write_full_content(topic, outline, research_data):
    """🆕 3단계: 아웃라인을 바탕으로 본문 작성"""
    print("✍️ 본문 작성 중... (플럭시 페르소나)")
    
    try:
        prompt = f"""
당신은 블로거 '플럭시(Fluxy)'입니다.
오늘 날짜: {time.strftime('%Y년 %m월 %d일')}

**주제:** {topic}

**글 구조:**
{outline}

**참고 자료:**
{research_data}

---

**미션: 위 아웃라인과 자료를 바탕으로 블로그 글을 작성하세요**

[📝 플럭시의 글쓰기 스타일 - 반드시 준수할 것]

**구조:**
- 도입부: 독자에게 질문 던지기 → 왜 지금 이 주제가 중요한지 → 본론 예고
- 본문: ## 제목으로 3~4개 섹션 구분 (명확한 번호와 제목)
- 각 섹션: 핵심 주제 설명 → 구체적 숫자/데이터 → 실전 예시
- 마무리: 핵심 요약 + 독자 행동 유도 + 따뜻한 응원

**말투 (매우 중요!):**
- 존댓말 ~합니다/~입니다 위주
- 가끔 ~이에요/~거든요/~거죠 섞어서 자연스럽게
- "아직도 ~하시나요?" "~해 보세요" 같은 독자 참여형 문장
- 질문 하나 → 바로 답 제시하는 구조 자주 활용
- **절대 금지: "블로그 콘텐츠 품질 검수 전문가", "요청하신", "개선한 최종 버전" 같은 AI/드래프트 느낌 문구**

**데이터 제시 방식:**
- "약 XX억 원", "XX% 상승", "XX배 증가" 등 구체적 숫자 필수
- 날짜는 정확하게: "2026년 2월", "올해 상반기" 등
- 비교 자주 사용: "작년 대비", "이전과 달리", "과거 XX했지만 이제는 YY"

**문단 구성:**
- 한 문단 = 3~5줄 (너무 길면 X)
- 중요 문장은 **볼드** 처리
- 리스트는 "* " 불릿 포인트로만 (번호 1. 2. 3. 사용 금지)

**예시 (기존 글 톤):**
"아직도 ISA 계좌를 '연 2,000만 원짜리'라고 생각하시나요? **2026년부터는 완전히 다른 판이 열립니다.** 그동안 한도가 작아 아쉬웠던 분들이라면 오늘 포스팅을 꼭 끝까지 읽어주세요."

[✅ 필수 포함 요소]
1. 도입부 첫 문장은 반드시 질문이나 공감형으로
2. 최소 3개 이상의 구체적 숫자/통계 포함
3. 섹션마다 1~2개 실전 예시 (가상 시나리오 OK)
4. 마무리는 3줄 체크리스트나 행동 유도 문장
5. 마지막은 "이 글이 도움이 되셨길 바랍니다. 다음에 또 유익한 정보로 찾아올게요!"

[❌ 절대 금지]
- "블로그 콘텐츠 품질 검수", "요청하신", "개선했습니다" 등 메타 언급
- "안녕하세요 여러분", "오늘은 ~에 대해 알아보겠습니다" 같은 진부한 시작
- 이모티콘 (📈💡 같은 것) - 텍스트로만 작성
- 너무 딱딱하거나 학술적인 문체
- 추상적 조언 ("열심히 해보세요" 같은 것)

**HTML 형식:**
- 대제목: <h2>섹션 제목</h2>
- 중제목: <h3>하위 제목</h3>
- 본문: <p>문단 내용</p>
- 리스트: <ul><li>항목</li></ul>
- 강조: <strong>강조 텍스트</strong>

**출력: 제목 없이 본문만 HTML 형식으로**
(html 코드블록 마크다운 없이 순수 HTML만 출력)
"""
        content = generate_content_with_retry(prompt, use_search=False)
        
        # HTML 코드블록 제거
        content = content.replace('```html', '').replace('```', '').strip()
        
        # 메타 언급 제거 (혹시 모를 실수 방지)
        meta_phrases = [
            "블로그 콘텐츠 품질 검수",
            "요청하신 원고",
            "개선한 최종 버전",
            "검토하고",
            "재구성했습니다"
        ]
        for phrase in meta_phrases:
            if phrase in content:
                # 해당 문단 전체 제거
                lines = content.split('\n')
                content = '\n'.join([line for line in lines if phrase not in line])
        
        print("✅ 본문 작성 완료!\n")
        return content
    except Exception as e:
        print(f"❌ 본문 작성 실패: {e}")
        raise

def quality_check_and_improve(topic, content):
    """🆕 4단계: 품질 검증 및 개선"""
    print("🔍 AI 품질 검사 진행 중...")
    
    try:
        prompt = f"""
당신은 블로그 에디터입니다.

**주제:** {topic}

**작성된 글:**
{content}

---

**미션: 위 글에서 문제점을 찾아 개선하되, 절대 '드래프트' 느낌이 나지 않도록 하세요**

[🔍 필수 검사 항목]
1. **메타 언급 완전 제거:** "블로그 콘텐츠", "요청하신", "검토", "개선", "재구성" 같은 단어가 하나라도 있으면 해당 문장 전체 삭제
2. **AI 티 제거:** "~하고자 합니다", "살펴보겠습니다" 같은 딱딱한 표현을 "~해요", "~볼까요?" 등으로 변경
3. **구체성 확인:** 모든 주장에 숫자나 구체적 예시가 있는지 확인
4. **문단 길이:** 6줄 이상 문단은 2개로 분리
5. **자연스러운 흐름:** 섹션 간 연결이 부드러운지 확인

[✅ 개선 방향]
- 진부한 인사말 제거 ("안녕하세요", "오늘은 ~에 대해")
- 질문형 문장 → 바로 답 주는 구조로
- 추상적 표현 → 구체적 예시로 교체
- 너무 긴 문장 → 2개로 분리

[❌ 절대 금지]
- "개선했습니다", "수정했습니다" 같은 메타 설명 추가
- 원문에 없던 새로운 섹션 추가
- 스타일을 완전히 바꾸기 (기존 톤 유지)

**출력: 개선된 본문만 (HTML 형식, 제목 제외, 메타 설명 절대 금지)**
"""
        improved_content = generate_content_with_retry(prompt, use_search=False)
        improved_content = improved_content.replace('```html', '').replace('```', '').strip()
        
        # 2차 필터링: 혹시 모를 메타 언급 강제 제거
        meta_kill_list = [
            "블로그 콘텐츠 품질 검수",
            "요청하신 원고",
            "개선한 최종 버전",
            "검토하고",
            "재구성했습니다",
            "수정했습니다",
            "다듬고",
            "품질을 극대화",
            "에디터로서",
            "검수 전문가"
        ]
        
        for meta_phrase in meta_kill_list:
            if meta_phrase in improved_content:
                # 해당 문구가 포함된 문단 전체 제거
                paras = improved_content.split('</p>')
                improved_content = '</p>'.join([p for p in paras if meta_phrase not in p])
        
        print("✅ 품질 개선 완료!\n")
        return improved_content
    except Exception as e:
        print(f"⚠️ 품질 검사 실패, 원본 사용: {e}")
        return content

def extract_title_from_outline(outline):
    """아웃라인에서 제목 추출"""
    for line in outline.split('\n'):
        if '제목:' in line or line.startswith('#'):
            title = line.replace('제목:', '').replace('#', '').strip()
            if 5 < len(title) < 100:
                return title
    return None

def get_dynamic_image_prompt(topic, content_summary):
    """🆕 개선: 글 내용을 반영한 이미지 프롬프트 생성"""
    print("🎨 주제에 딱 맞는 이미지 컨셉 구상 중...")
    try:
        prompt = f"""
당신은 경제 블로그 전문 비주얼 디렉터입니다.

**블로그 주제:** {topic}
**글 핵심 내용:** {content_summary[:400]}

**미션: 위 글의 핵심을 시각적으로 표현할 썸네일 이미지 프롬프트를 작성하세요**

[🎯 주제 분석 및 시각화 전략]
1. 주제의 핵심 키워드 추출 (예: ISA → 비과세 통장 이미지, 배당주 → 배당금 흐름)
2. 구체적인 비주얼 요소 지정 (차트, 아이콘, 심볼, 배경)
3. 한글 텍스트는 주제의 핵심 단어만 (3~5단어)

[✅ 좋은 예시]
- ISA 한도 상향 → "Korean text 'ISA 비과세 한도 UP', tax free savings account concept, money growing, charts showing benefits, modern financial illustration"
- 배당주 분석 → "Korean text '배당 투자 전략', dividend stocks concept, money flow arrows, calendar showing dividend dates, professional blue theme"
- 반도체 전망 → "Korean text '반도체 섹터', semiconductor chip illustration, technology innovation, global supply chain, futuristic design"

[🎨 스타일 가이드]
- 전문적이면서 깔끔한 인포그래픽 스타일
- 색상: 파란색/녹색 계열 (신뢰감), 주황색 포인트 (활력)
- 레이아웃: 중앙 정렬, 여백 충분, 가독성 최우선
- 퀄리티: "high quality, professional design, 4K"

[❌ 절대 금지]
- 실존 인물, 기업 로고, 저작권 있는 캐릭터
- 복잡한 주식 차트만 가득한 이미지
- 너무 추상적이거나 주제와 무관한 이미지

**출력 형식: 영문 프롬프트만 (한글 텍스트 포함, 100단어 이내)**
"""
        image_prompt = generate_content_with_retry(prompt, use_search=False).strip()
        
        # 따옴표 및 불필요한 기호 제거
        image_prompt = image_prompt.replace('"', '').replace("'", '').replace('`', '')
        image_prompt = image_prompt.replace('\n', ' ').replace('  ', ' ')
        
        # 너무 길면 자르기
        if len(image_prompt) > 400:
            image_prompt = image_prompt[:400]
        
        print(f"✨ 생성된 프롬프트: {image_prompt}\n")
        return image_prompt
    except Exception as e:
        print(f"⚠️ 이미지 프롬프트 생성 실패, 기본값 사용: {e}")
        # 기본값도 주제를 반영하도록
        return f"Korean text related to {topic}, financial blog thumbnail, modern infographic style, professional design, blue and white color scheme, high quality 4K"

def generate_image_url(prompt, service="replicate"):
    """여러 이미지 생성 서비스 지원 (안정성 순)"""
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(1000, 999999)
    timestamp = int(time.time())
    
    # 한글 텍스트 추출 (있으면)
    korean_text = ""
    if "Korean text" in prompt:
        # 'Korean text' 뒤의 단어들 추출
        parts = prompt.split("Korean text")[1].split(",")[0].strip()
        korean_text = parts.replace("'", "").replace('"', '').strip()
    
    services = {
        # 안정적인 서비스 우선
        "replicate": f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&private=true&seed={seed}",
        "pollinations-simple": f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}",
        "dalle-mini": f"https://pollinations.ai/p/{encoded_prompt}",
        
        # 백업 옵션들
        "flux-basic": f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&model=flux&seed={seed}",
        "default": f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&enhance=true&seed={seed}",
    }
    
    return services.get(service, services["replicate"])

def create_fallback_image_html(topic):
    """이미지 생성 실패 시 SVG 대체 이미지 생성"""
    print("🎨 SVG 대체 이미지 생성 중...")
    
    # 주제에서 핵심 키워드 추출
    keywords = topic[:30] if len(topic) > 30 else topic
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2563eb;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#grad1)"/>
  <text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" fill="white" font-size="48" font-weight="bold" font-family="Arial, sans-serif">
    {keywords}
  </text>
  <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="24" font-family="Arial, sans-serif">
    PLUXEON 경제 블로그
  </text>
</svg>'''
    
    return svg_content

def upload_image_to_wp(image_prompt, title, max_retries=2):
    """🆕 개선: 이미지 업로드 (다중 서비스 + SVG 폴백)"""
    print(f"🖼️ 이미지 생성 및 업로드 시작...")
    print(f"📌 프롬프트: {image_prompt[:100]}...\n")
    
    # 시도할 서비스 목록
    services = ["replicate", "pollinations-simple", "flux-basic", "default"]
    
    for service in services:
        print(f"🎨 {service} 서비스로 이미지 생성 시도...")
        
        for attempt in range(max_retries):
            try:
                # 이미지 URL 생성
                image_url = generate_image_url(image_prompt, service)
                print(f"📡 [{attempt+1}/{max_retries}] 이미지 생성 중...")
                
                # User-Agent 추가로 차단 우회
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                img_response = requests.get(image_url, headers=headers, timeout=45)
                
                # 530 에러는 서비스 과부하 - 재시도 가치 있음
                if img_response.status_code == 530:
                    print(f"⚠️ 서비스 과부하 (HTTP 530) - 5초 후 재시도...")
                    time.sleep(5)
                    continue
                elif img_response.status_code != 200:
                    print(f"⚠️ 이미지 다운로드 실패 (HTTP {img_response.status_code})")
                    time.sleep(3)
                    continue
                
                image_data = img_response.content
                
                # 이미지 크기 확인 (최소 5KB)
                if len(image_data) < 5000:
                    print(f"⚠️ 이미지 크기가 너무 작음 ({len(image_data)} bytes)")
                    time.sleep(3)
                    continue
                
                print(f"✅ 이미지 다운로드 성공! ({len(image_data):,} bytes)")
                
                # WordPress 업로드
                filename = f"fluxy_{int(time.time())}.png"
                credentials = f"{WP_USER}:{WP_APP_PASS}"
                token = base64.b64encode(credentials.encode()).decode()
                
                wp_headers = {
                    "Authorization": f"Basic {token}",
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "image/png"
                }
                
                media_url = WP_URL.replace("/posts", "/media")
                print(f"📤 WordPress 업로드 시작...")
                
                wp_response = requests.post(
                    media_url, 
                    headers=wp_headers, 
                    data=image_data, 
                    verify=False, 
                    timeout=45
                )
                
                print(f"📊 WordPress 응답 코드: {wp_response.status_code}")
                
                if wp_response.status_code == 201:
                    media_id = wp_response.json()['id']
                    media_link = wp_response.json().get('source_url', '링크 없음')
                    print(f"🎉 업로드 성공!")
                    print(f"🆔 Media ID: {media_id}")
                    print(f"🔗 이미지 URL: {media_link}\n")
                    return media_id
                else:
                    print(f"⚠️ WordPress 업로드 실패!")
                    print(f"📄 응답 내용: {wp_response.text[:300]}")
                    
                    if wp_response.status_code == 401:
                        print("❌ 인증 실패! WP_USER와 WP_APP_PASS를 확인하세요.")
                    elif wp_response.status_code == 403:
                        print("❌ 권한 부족! 앱 비밀번호에 미디어 업로드 권한이 있는지 확인하세요.")
                    
                    time.sleep(3)
                    
            except requests.Timeout:
                print(f"⏱️ 타임아웃 발생 (45초 초과)")
                time.sleep(3)
            except requests.RequestException as e:
                print(f"❌ 네트워크 에러: {e}")
                time.sleep(3)
            except Exception as e:
                print(f"❌ 예상치 못한 에러: {e}")
                time.sleep(3)
        
        print(f"⚠️ {service} 서비스 모든 시도 실패\n")
    
    # 모든 시도 실패 시 SVG 폴백
    print("🎨 모든 이미지 서비스 실패 - SVG 대체 이미지 생성 시도...")
    try:
        svg_content = create_fallback_image_html(title)
        svg_bytes = svg_content.encode('utf-8')
        
        credentials = f"{WP_USER}:{WP_APP_PASS}"
        token = base64.b64encode(credentials.encode()).decode()
        
        wp_headers = {
            "Authorization": f"Basic {token}",
            "Content-Disposition": f"attachment; filename=fluxy_{int(time.time())}.svg",
            "Content-Type": "image/svg+xml"
        }
        
        media_url = WP_URL.replace("/posts", "/media")
        wp_response = requests.post(
            media_url,
            headers=wp_headers,
            data=svg_bytes,
            verify=False,
            timeout=30
        )
        
        if wp_response.status_code == 201:
            media_id = wp_response.json()['id']
            print(f"✅ SVG 이미지 업로드 성공! Media ID: {media_id}\n")
            return media_id
        else:
            print(f"⚠️ SVG 업로드도 실패: {wp_response.status_code}")
    except Exception as e:
        print(f"❌ SVG 폴백 실패: {e}")
    
    print("💡 이미지 없이 글만 발행합니다.\n")
    return None

def auto_posting():
    """메인 자동 포스팅 프로세스"""
    print("=" * 70)
    print("🚀 플럭시 블로그 봇 V5.0 - 프리미엄 에디션")
    print("   [리서치 → 아웃라인 → 본문 → 품질검증 → 발행]")
    print("=" * 70)
    print()
    
    try:
        # STEP 1: 주제 선정
        recent_titles = get_recent_posts()
        topic = get_search_friendly_topic(recent_titles)
        print(f"🎯 최종 주제: {topic}\n")
        time.sleep(2)
        
        # STEP 2: 리서치
        research_data = research_topic(topic)
        time.sleep(2)
        
        # STEP 3: 아웃라인 생성
        outline = create_outline(topic, research_data)
        time.sleep(2)
        
        # STEP 4: 본문 작성
        content = write_full_content(topic, outline, research_data)
        time.sleep(2)
        
        # STEP 5: 품질 검증 및 개선
        final_content = quality_check_and_improve(topic, content)
        
        # 제목 추출
        title = extract_title_from_outline(outline)
        if not title:
            title = topic
        
        print(f"📌 최종 제목: {title}\n")
        
        # STEP 6: 이미지 생성 및 업로드
        content_summary = final_content[:500] if len(final_content) > 500 else final_content
        image_prompt = get_dynamic_image_prompt(topic, content_summary)
        
        # 개선된 업로드 함수 호출 (URL이 아닌 프롬프트 전달)
        featured_media_id = upload_image_to_wp(image_prompt, title)
        time.sleep(1)
        
        # STEP 7: 워드프레스 발행
        print("📤 워드프레스 발행 중...")
        credentials = f"{WP_USER}:{WP_APP_PASS}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }
        
        post_data = {
            "title": title,
            "content": final_content,
            "status": "publish",
            "categories": [1]
        }
        
        if featured_media_id:
            post_data["featured_media"] = featured_media_id
        
        response = requests.post(WP_URL, headers=headers, json=post_data, verify=False)
        
        if response.status_code == 201:
            post_id = response.json()['id']
            post_url = response.json().get('link', 'URL 없음')
            print()
            print("=" * 70)
            print("🎉 포스팅 성공!")
            print(f"📝 제목: {title}")
            print(f"🆔 ID: {post_id}")
            print(f"🔗 URL: {post_url}")
            print("=" * 70)
        else:
            print(f"❌ 발행 실패: {response.status_code}")
            print(f"상세: {response.text}")
            
    except Exception as e:
        print(f"\n❌❌❌ 치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_image_generation(topic="2026년 ISA 한도 상향 투자 전략"):
    """🧪 이미지 생성 테스트 전용 함수"""
    print("=" * 70)
    print("🧪 이미지 생성 테스트 모드")
    print("=" * 70)
    print()
    
    # 샘플 콘텐츠
    sample_content = f"{topic}에 대한 블로그 글입니다. 비과세 혜택과 배당 투자 전략을 다룹니다."
    
    # 이미지 프롬프트 생성
    image_prompt = get_dynamic_image_prompt(topic, sample_content)
    
    # 이미지 업로드 테스트
    media_id = upload_image_to_wp(image_prompt, topic)
    
    if media_id:
        print(f"\n✅ 테스트 성공! Media ID: {media_id}")
        print("WordPress 미디어 라이브러리에서 확인하세요.")
    else:
        print("\n❌ 테스트 실패. 위 로그를 확인하세요.")

if __name__ == "__main__":
    # 테스트 모드 실행: python script.py test
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_image_generation()
    else:
        auto_posting()
