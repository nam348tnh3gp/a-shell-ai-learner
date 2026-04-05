import json
import os
import time
import random
import urllib.parse
import requests
from bs4 import BeautifulSoup

# Giả lập danh sách User-Agent
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
]

class GoogleAI:
    def __init__(self, brain_file="brain.json"):
        self.brain_file = brain_file
        self.brain = self.load_brain()
        self.session = self.create_session()

    def create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8',
        })
        return session

    # --- HỆ THỐNG GHI NHỚ ---
    def load_brain(self):
        if os.path.exists(self.brain_file):
            with open(self.brain_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_brain(self):
        with open(self.brain_file, 'w', encoding='utf-8') as f:
            json.dump(self.brain, f, ensure_ascii=False, indent=4)

    def learn(self, query, content):
        """Lưu kiến thức mới vào bộ nhớ"""
        self.brain[query.lower()] = {
            "content": content[:500] + "...", # Lưu tóm tắt 500 ký tự
            "timestamp": time.ctime()
        }
        self.save_brain()

    # --- KHẢ NĂNG ĐỌC ---
    def get_page_content(self, url):
        """Truy cập vào link để đọc nội dung văn bản"""
        try:
            res = self.session.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # Lấy các đoạn văn bản trong thẻ p
            paragraphs = soup.find_all('p')
            text = " ".join([p.get_text() for p in paragraphs[:5]]) # Lấy 5 đoạn đầu
            return text.strip() if text else "Không thể đọc nội dung chi tiết."
        except:
            return "Lỗi khi truy cập trang web."

    # --- HỆ THỐNG TÌM KIẾM (GOOGLE & DUCKDUCKGO) ---
    def search_online(self, query):
        """Tìm kiếm link từ Google (hoặc DDG)"""
        links = []
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=vi"
            res = self.session.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if '/url?q=' in href:
                    clean_url = href.split('/url?q=')[1].split('&')[0]
                    clean_url = urllib.parse.unquote(clean_url)
                    if 'google.com' not in clean_url:
                        title = a.find('h3').get_text() if a.find('h3') else "No Title"
                        links.append({'url': clean_url, 'title': title})
                if len(links) >= 3: break
        except:
            pass
        return links

    # --- XỬ LÝ TƯƠNG TÁC CHÍNH ---
    def chat(self, user_input):
        user_input_low = user_input.lower()

        # 1. Kiểm tra xem đã học chưa
        if user_input_low in self.brain:
            print(f"🤖 AI (Bộ nhớ): Tôi đã học điều này vào {self.brain[user_input_low]['timestamp']}:")
            return self.brain[user_input_low]['content']

        # 2. Nếu chưa biết, đi tìm kiếm
        print(f"🤖 AI: Kiến thức này mới quá, đợi tôi tí để lên mạng học...")
        results = self.search_online(user_input)

        if not results:
            return "🤖 AI: Xin lỗi, tôi không tìm thấy thông tin này trên mạng."

        # 3. Đọc link đầu tiên tìm được để "học"
        first_link = results[0]['url']
        print(f"📖 AI: Đang đọc tại {first_link}...")
        knowledge = self.get_page_content(first_link)

        # 4. Lưu vào bộ nhớ
        if len(knowledge) > 20:
            self.learn(user_input, knowledge)
            return f"🤖 AI (Mới học): {knowledge}"
        else:
            return "🤖 AI: Tôi thấy link nhưng không đọc được nội dung chi tiết."

# --- CHƯƠNG TRÌNH CHÍNH ---
if __name__ == "__main__":
    ai = GoogleAI()
    print("=== AI TỰ HỌC ĐÃ SẴN SÀNG (Gõ 'exit' để thoát) ===")
    
    while True:
        query = input("\n👤 Bạn hỏi: ")
        if query.lower() in ['exit', 'thoát', 'quit']:
            break
            
        if query.strip() == "xem kiến thức":
            print(f"📚 Bộ nhớ hiện tại: {json.dumps(ai.brain, indent=2, ensure_ascii=False)}")
            continue

        response = ai.chat(query)
        print(response)
