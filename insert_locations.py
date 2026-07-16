import os
import json
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Location, Post  # Post 모델 임포트 추가

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(BASE_DIR, "data", "서울")

CATEGORY_MAPPING = {
    "서울_관광지.json": "12",
    "서울_문화시설.json": "14",
    "서울_축제공연행사.json": "15",
    "서울_여행코스.json": "25",
    "서울_숙박.json": "32",
    "서울_쇼핑.json": "38",
    "서울_레포츠.json": "39"
}

# 익명 게시판에 등록할 5가지 카테고리(후기, 동행, 질문, 추천, 기타) 기반 더미 데이터 리스트입니다. (총 15개)
DUMMY_POSTS = [
    {
        "category": "동행",
        "title": "이번 주말에 경복궁 야간 개장 같이 가실 분 계신가요?",
        "content": "날씨도 선선한데 한복 입고 경복궁 야간 관람하고 싶네요. 사진 서로 예쁘게 찍어주실 동행 멤버 구합니다!",
        "password": "my_test_password123",
        "views": 15,
        "tags": "경복궁,동행구함,야간개장"
    },
    {
        "category": "질문",
        "title": "홍대 근처에 주차 편하고 조용한 카페 있을까요?",
        "content": "노트북 작업 좀 하려고 하는데 주차가 지원되거나 근처 공영주차장 이용하기 쉬운 조용한 북카페 추천 부탁드립니다.",
        "password": "password1234",
        "views": 4,
        "tags": "홍대,카페추천,주차가능"
    },
    {
        "category": "추천",
        "title": "서울 벚꽃 명소 숨겨진 꿀스팟 공유합니다",
        "content": "여의도는 사람이 너무 많잖아요. 은평구 불광천이랑 서대문구 안산 허브공원 쪽이 산책길도 예쁘고 한적해서 인생샷 건지기 딱 좋습니다.",
        "password": "info_pass_99",
        "views": 42,
        "tags": "벚꽃명소,봄나들이,숨은명소"
    },
    {
        "category": "기타",
        "title": "퇴근길 한강 뷰 보면서 자전거 타니까 힐링되네요",
        "content": "오늘 업무 때문에 엄청 스트레스 받았는데 따릉이 빌려서 여의도 공원 한 바퀴 돌고 나니 가슴이 뻥 뚫립니다. 다들 고생하셨어요.",
        "password": "testpwd_free",
        "views": 8,
        "tags": "퇴근길,힐링,따릉이"
    },
    {
        "category": "질문",
        "title": "DDP 전시회 예매 현장 발권 가능한가요?",
        "content": "이번 주 금요일 오후에 가려고 하는데 온라인 예매를 깜빡했네요. 현장 발권 대기 줄 길게 서야 하는지 아시는 분 답변 부탁드려요.",
        "password": "ddp_query_1",
        "views": 2,
        "tags": "DDP,전시회,현장발권"
    },
    {
        "category": "후기",
        "title": "남산타워 케이블카 주말에 타고 온 솔직한 후기",
        "content": "어제 오후에 남산타워 다녀왔는데 케이블카 대기만 1시간 넘게 걸렸네요. 날씨가 좋을 때는 그냥 산책로 따라 걸어 올라가는 것을 강력 추천합니다.",
        "password": "namsan_pwd",
        "views": 23,
        "tags": "남산타워,방문후기,데이트"
    },
    {
        "category": "추천",
        "title": "창경궁 대온실 일몰 타임 방문 추천해 드려요",
        "content": "우리나라 최초의 서양식 온실인데, 낮에도 이쁘지만 해질녘 불 켜질 때 가시면 정말 환상적인 야경을 볼 수 있습니다. 입장료도 1,000원이라 가성비 최고예요.",
        "password": "palace_tip1",
        "views": 56,
        "tags": "창경궁,대온실,야경명소"
    },
    {
        "category": "기타",
        "title": "을지로 야장 거리 분위기 실시간 공유",
        "content": "어제 퇴근하고 동료들이랑 을지로 3가 노가리 골목 다녀왔는데 야외 테이블 감성이 정말 최고였습니다. 날씨 선선할 때 꼭 가보세요.",
        "password": "eulji_pass_77",
        "views": 19,
        "tags": "을지로,야장,노가리골목"
    },
    {
        "category": "질문",
        "title": "서울 3대 족발 중에서 어디가 제일 괜찮나요?",
        "content": "시청 오향족발, 성수 족발, 양재 영동족발 중에서 주말에 부모님 모시고 가려고 하는데 어디를 가장 추천하시는지 궁금합니다.",
        "password": "food_query_2",
        "views": 31,
        "tags": "맛집질문,가족외식,족발"
    },
    {
        "category": "추천",
        "title": "북촌 한옥마을 조용히 걷기 좋은 코스 추천",
        "content": "주민분들이 거주하시는 곳이라 소음은 주의해야 하지만, 이른 아침 안국역에서 출발해 가회동 성당을 거쳐 내려오는 코스가 고즈넉하고 가장 아름답습니다.",
        "password": "hanok_rule",
        "views": 14,
        "tags": "북촌한옥마을,산책코스,조용한길"
    },
    {
        "category": "후기",
        "title": "성수동 명품 팝업스토어 평일 오픈런 다녀왔습니다",
        "content": "평일 오전인데도 대기 번호가 벌써 100번대 뒤로 밀리더라고요. 볼거리는 많았지만 웨이팅 감안하고 가셔야 할 것 같습니다.",
        "password": "seongsu_pop",
        "views": 11,
        "tags": "성수동,팝업스토어,오픈런후기"
    },
    {
        "category": "추천",
        "title": "여의도 한강공원 자전거 피크닉 코스 추천합니다",
        "content": "마포대교 밑에서 출발해 샛강 생태공원 쪽으로 크게 돌면 사람도 적고 시원하게 자전거 타기 딱 좋습니다. 돗자리 펴고 쉬기 좋은 명당도 공유해요.",
        "password": "bike_love",
        "views": 17,
        "tags": "한강공원,자전거코스,피크닉"
    },
    {
        "category": "질문",
        "title": "광화문 광장 바닥 분수 가동 시간 정보 아시는 분?",
        "content": "이번 주말에 아이들 데리고 분수 놀이 하러 가려고 합니다. 가동 시간대 정보나 혹시 근처에 가볍게 옷 갈아입을 만한 공간이 있는지 궁금해요.",
        "password": "fountain_12",
        "views": 5,
        "tags": "광화문광장,바닥분수,육아정보"
    },
    {
        "category": "추천",
        "title": "국립중앙박물관 기획전 무료/할인 관람 꿀팁",
        "content": "매주 마지막 수요일 '문화가 있는 날'에는 기획 전시 입장료를 50%나 할인해 줍니다. 상설 전시관은 상시 무료니 꼼꼼하게 챙겨서 다녀오세요.",
        "password": "museum_pass_3",
        "views": 29,
        "tags": "박물관추천,문화가있는날,할인"
    },
    {
        "category": "후기",
        "title": "노량진 수산시장 대게 시세랑 식당 이용 솔직 후기",
        "content": "주말이라 가족들이랑 대게 먹으러 다녀왔는데 수산물 시장에서 직접 고르고 2층 식당가 연결해서 먹으니 신선함은 최고였습니다. 상차림비 정보 적어둘게요.",
        "password": "noryangjin_sea",
        "views": 22,
        "tags": "노량진수산시장,대게후기,가족식사"
    }
]

def extract_items(data):
    """
    다양한 JSON 구조(중첩 body, items 내부 구조 등)에서 
    안전하게 실제 item 리스트를 추출하는 보조 함수입니다.
    """
    try:
        response = data.get("response", {})
        body = response.get("body", {})
        items_wrapper = body.get("items", {})
        if isinstance(items_wrapper, dict):
            items = items_wrapper.get("item", [])
            if items:
                return items if isinstance(items, list) else [items]
    except Exception:
        pass

    if "items" in data and isinstance(data["items"], dict) and "item" in data["items"]:
        items = data["items"]["item"]
        return items if isinstance(items, list) else [items]
    
    if isinstance(data, list):
        return data

    for key in ["item", "items", "data", "list"]:
        if key in data:
            val = data[key]
            if isinstance(val, list):
                return val
            if isinstance(val, dict) and "item" in val:
                items = val["item"]
                return items if isinstance(items, list) else [items]

    return []

def seed_locations():
    db: Session = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)

        # ----------------------------------------------------------------
        # 1. 기존 데이터 테이블 초기화 (지우고 새로 생성)
        # ----------------------------------------------------------------
        print("데이터베이스 초기화를 시작합니다...")
        db.query(Location).delete()
        db.query(Post).delete()  # 게시글 테이블도 깨끗하게 초기화
        db.commit()

        # ----------------------------------------------------------------
        # 2. 게시글 더미 데이터 삽입
        # ----------------------------------------------------------------
        print("익명 게시판 더미 데이터 적재 중...")
        for post_data in DUMMY_POSTS:
            post = Post(
                category=post_data["category"],
                title=post_data["title"],
                content=post_data["content"],
                password=post_data["password"],
                views=post_data["views"],
                tags=post_data["tags"]
            )
            db.add(post)
        db.commit()
        print(f"-> {len(DUMMY_POSTS)}개의 게시판 더미 글이 생성되었습니다.")

        # ----------------------------------------------------------------
        # 3. 공공데이터 적재
        # ----------------------------------------------------------------
        print("공공데이터 적재를 시작합니다...")
        for file_name, category_id in CATEGORY_MAPPING.items():
            file_path = os.path.join(JSON_DIR, file_name)
            
            if not os.path.exists(file_path):
                continue
                
            print(f"{file_name} 파싱 중...")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = extract_items(data)
                
                print(f"-> {file_name}에서 {len(items)}개의 장소를 찾았습니다.")
                
                for item in items:
                    extra_keys = ["zipcode", "mlevel", "areacode", "sigungucode", "cat1", "cat2", "cat3", "cpyrhtDivCd"]
                    extra_dict = {k: item.get(k) for k in extra_keys if k in item}
                    
                    location = Location(
                        category_id=category_id,
                        title=item.get("title", "이름 없음"),
                        addr1=item.get("addr1"),
                        addr2=item.get("addr2"),
                        tel=item.get("tel"),
                        mapx=float(item.get("mapx")) if item.get("mapx") else None,
                        mapy=float(item.get("mapy")) if item.get("mapy") else None,
                        firstimage=item.get("firstimage"),
                        extra_data=extra_dict
                    )
                    db.add(location)
            
        db.commit()
        print("모든 공공데이터가 localhub.db에 성공적으로 적재되었습니다!")
        
    except Exception as e:
        db.rollback()
        print(f"데이터 적재 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_locations()