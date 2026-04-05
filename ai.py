import json
import os
import time
import random
import urllib.parse
import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
]

class GoogleAI:
    def __init__(self, brain_file="brain_data.json"):
        self.brain_file = brain_file
        self.brain = self.load_brain()
        self.session = self.create_session()

    def create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8',
        })
        return session

    def load_brain(self):
        if os.path.exists(self.brain_file):
            try:
                with open(self.brain_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def save_brain(self):
        with open(self.brain_file, 'w', encoding='utf-8') as f:
            json.dump(self.brain, f, ensure_ascii=False, indent=4)

    def get_page_content(self, url):
        """Đọc và làm sạch nội dung từ trang web"""
        try:
            res = self.session.get(url, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Xóa các thành phần rác
            for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                script_or_style.decompose()

            # Lấy các thẻ chứa nội dung quan trọng
            content_tags = soup.find_all(['p', 'article', 'h1', 'h2'])
            text = "\n".join([t.get_text().strip() for t in content_tags if len(t.get_text().strip()) > 20])
            
            return text[:1000].strip() if text else None
        except:
            return None

    def search_google(self, query):
        """Tìm kiếm link chất lượng từ Google"""
        links = []
        try:
            # Thêm 'là gì' để Google trả về kết quả định nghĩa tốt hơn
            search_query = f"{query} là gì" if len(query.split()) < 3 else query
            url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&hl=vi"
            
            res = self.session.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')

            for a in soup.find_all('a'):
                href = a.get('href', '')
                # Bóc tách link từ redirect của Google
                if '/url?q=' in href:
                    link = href.split('/url?q=')[1].split('&')[0]
                    link = urllib.parse.unquote(link)
                    if 'google.com' not in link and link.startswith('http'):
                        links.append(link)
                if len(links) >= 3: break
        except Exception as e:
            print(f"Lỗi tìm kiếm: {e}")
        return links

    def chat(self, user_input):
        user_input = user_input.strip()
        tag = user_input.lower()

        # 1. Kiểm tra bộ nhớ
        if tag in self.brain:
            info = self.brain[tag]
            return f"🤖 AI (Đã học ngày {info['date']}):\n{info['content']}"

        # 2. Tìm kiếm online
        print(f"🔍 Đang học về: {user_input}...")
        urls = self.search_google(user_input)
        
        if not urls:
            return "❌ Tôi không tìm thấy tài liệu nào phù hợp trên mạng."

        # 3. Thử đọc từng link cho đến khi có nội dung
        for url in urls:
            print(f"📖 Đang đọc: {url}")
            content = self.get_page_content(url)
            if content and len(content) > 100:
                # Lưu vào bộ não
                self.brain[tag] = {
                    "content": content,
                    "source": url,
                    "date": time.strftime("%d/%m/%Y %H:%M")
                }
                self.save_brain()
                return f"✅ Tôi đã học xong!\n📝 Nội dung: {content[:300]}..."
        
        return "⚠️ Tôi đã thấy các trang web nhưng nội dung quá khó đọc hoặc bị chặn."

# --- CHẠY ---
if __name__ == "__main__":
    bot = GoogleAI()
    print("🤖 Chào bạn! Tôi là AI tự học. Bạn muốn tôi tìm hiểu về điều gì?")
    while True:
        u = input("\n👤 Bạn: ")
        if u.lower() in ['exit', 'quit', 'thoát']: break
        if u.lower() == "brain":
            print(f"🧠 Số lượng từ khóa đã học: {len(bot.brain)}")
            continue
        print(bot.chat(u))
