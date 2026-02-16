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

**미션: 위 아웃라인과 자료를 바탕으로 완성도 높은 블로그 글을 작성하세요**

[😊 플럭시 페르소나]
- 말투: 친근한 구어체 (~해요, ~이에요, ~니다 혼용)
- 시작: 공감 가는 질문이나 최근 이슈로 자연스럽게 시작
- 설명: 고등학생도 이해할 수 있게, 어려운 용어는 쉽게 풀어쓰기
- 데이터: 구체적인 숫자, 날짜, 사례를 반드시 포함
- 마무리: "이 글이 도움이 되셨길 바랍니다. 다음에 또 유익한 정보로 찾아올게요!"

[⚠️ 절대 금지]
- AI 티 나는 딱딱한 문체
- 이모티콘 남발 (문단당 0~1개만)
- "안녕하세요 여러분" 같은 진부한 인사
- 추상적이고 뻔한 조언
- 출처 없는 통계나 수치

[📝 형식 규칙]
- HTML 태그 사용: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em>
- 문단은 3~5줄로 짧게 (가독성)
- 중요한 숫자나 용어는 <strong> 처리
- 리스트는 <ul>/<li> 활용

[📊 필수 포함 요소]
1. 최신 데이터나 통계 (날짜 명시)
2. 실제 사례 또는 예시
3. 독자가 바로 실행할 수 있는 구체적 팁
4. 섹션별 명확한 소제목 (<h2>, <h3>)

**출력 형식: 제목 없이 본문만 (HTML 형식)**
"""
        content = generate_content_with_retry(prompt, use_search=False)
        
        # HTML 코드블록 제거
        content = content.replace('```html', '').replace('```', '').strip()
        
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
당신은 블로그 콘텐츠 품질 검수 전문가입니다.

**주제:** {topic}

**작성된 글:**
{content}

---

**미션: 위 글을 검토하고 개선점을 찾아 최종 버전을 출력하세요**

[🔍 검사 항목]
1. 가독성: 문단이 너무 길지 않은가?
2. 구체성: 추상적 표현 대신 구체적 예시/숫자가 있는가?
3. 실용성: 독자가 실제로 활용할 만한 정보인가?
4. 자연스러움: AI가 쓴 티가 나지 않는가?
5. HTML 구조: 태그가 올바르게 사용되었는가?

[✏️ 개선 방향]
- 너무 긴 문장은 짧게 쪼개기
- 애매한 표현은 명확하게 수정
- 부족한 부분에 구체적 예시 추가
- 불필요한 반복 제거

**출력: 개선된 최종 본문 (HTML 형식, 제목 제외)**
"""
        improved_content = generate_content_with_retry(prompt, use_search=False)
        improved_content = improved_content.replace('```html', '').replace('```', '').strip()
        
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

def generate_image_url(prompt, service="flux-pro"):
    """여러 이미지 생성 서비스 지원 (퀄리티 순)"""
    encoded_prompt = urllib.parse.quote(prompt)
    seed = int(time.time())
    
    services = {
        # 최고 퀄리티 모델 우선
        "flux-pro": f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&model=flux-pro&nologo=true&seed={seed}",
        "flux": f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&model=flux&nologo=true&seed={seed}",
        "flux-realism": f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&model=flux-realism&nologo=true&seed={seed}",
        "turbo": f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&model=turbo&nologo=true&seed={seed}",
        "pollinations": f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&enhance=true&seed={seed}",
    }
    
    return services.get(service, services["flux-pro"])

def upload_image_to_wp(image_prompt, title, max_retries=3):
    """🆕 개선: 이미지 업로드 (다중 서비스 + 재시도 로직)"""
    print(f"🖼️ 이미지 생성 및 업로드 시작...")
    
    # 시도할 서비스 목록 (최고 퀄리티 순)
    services = ["flux-pro", "flux", "flux-realism", "turbo", "pollinations"]
    
    for service in services:
        print(f"🎨 {service} 모델로 이미지 생성 시도...")
        
        for attempt in range(max_retries):
            try:
                # 이미지 URL 생성
                image_url = generate_image_url(image_prompt, service)
                print(f"📡 [{attempt+1}/{max_retries}] 다운로드 중... ({image_url[:80]}...)")
                
                # 이미지 다운로드 (타임아웃 30초)
                response = requests.get(image_url, timeout=30)
                
                if response.status_code != 200:
                    print(f"⚠️ 이미지 다운로드 실패 (상태코드: {response.status_code})")
                    continue
                
                image_data = response.content
                
                # 이미지 크기 확인 (최소 10KB)
                if len(image_data) < 10000:
                    print(f"⚠️ 이미지 크기가 너무 작음 ({len(image_data)} bytes)")
                    continue
                
                print(f"✅ 이미지 다운로드 완료 ({len(image_data)} bytes)")
                
                # WordPress 업로드
                filename = f"fluxy_blog_{int(time.time())}.png"
                credentials = f"{WP_USER}:{WP_APP_PASS}"
                token = base64.b64encode(credentials.encode()).decode()
                
                headers = {
                    "Authorization": f"Basic {token}",
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "image/png"
                }
                
                media_url = WP_URL.replace("/posts", "/media")
                print(f"📤 WordPress 업로드 중... ({media_url})")
                
                wp_response = requests.post(
                    media_url, 
                    headers=headers, 
                    data=image_data, 
                    verify=False, 
                    timeout=30
                )
                
                if wp_response.status_code == 201:
                    media_id = wp_response.json()['id']
                    media_link = wp_response.json().get('source_url', '링크 없음')
                    print(f"🎉 업로드 성공! Media ID: {media_id}")
                    print(f"🔗 이미지 URL: {media_link}\n")
                    return media_id
                else:
                    print(f"⚠️ WordPress 업로드 실패: {wp_response.status_code}")
                    print(f"응답: {wp_response.text[:200]}")
                    
            except requests.Timeout:
                print(f"⏱️ 타임아웃 발생 (시도 {attempt+1}/{max_retries})")
                time.sleep(2)
            except Exception as e:
                print(f"❌ 에러 발생: {e}")
                time.sleep(2)
        
        print(f"⚠️ {service} 모델 실패, 다음 모델 시도...\n")
    
    print("❌ 모든 이미지 모델 실패. 이미지 없이 진행합니다.")
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
