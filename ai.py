#!/usr/bin/env python3
import json, os, time, re, random, urllib.parse
import requests
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
KNOWLEDGE_FILE = "ai_brain_google.json"
USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...']

class SmartAI:
    def __init__(self):
        self.brain = self.load_brain()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})

    def load_brain(self):
        if os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        return {"topics": {}, "stats": {"total_learned": 0}}

    # --- FIX LỖI LẤY LINK (GOOGLE + DUCKDUCKGO) ---
    def search_links(self, query):
        links = []
        print(f"🔍 Đang quét tìm link cho: {query}...")
        
        # Thử Google trước
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=vi"
            resp = self.session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Selector 'div.g' là chuẩn nhất cho Google hiện tại
            for g in soup.select('div.g'):
                link = g.find('a', href=True)
                title = g.find('h3')
                if link and title:
                    href = link['href']
                    if 'http' in href and 'google.com' not in href:
                        links.append({'url': href, 'title': title.get_text()})
                if len(links) >= 3: break
        except: pass

        # Nếu Google chặn, fallback sang DuckDuckGo Lite (Rất lỳ, ít khi chặn)
        if not links:
            print("⚠️ Google chặn, chuyển sang DuckDuckGo...")
            try:
                url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
                resp = self.session.get(url, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', class_='result-link'):
                    links.append({'url': a['href'], 'title': a.get_text()})
                    if len(links) >= 3: break
            except: pass
        
        return links

    # --- ĐỌC VÀ CHỌN LỌC CÂU HAY (TRÁNH RÁC) ---
    def learn_topic(self, topic):
        links = self.search_links(topic)
        if not links: return print("❌ Không tìm được tài liệu nào!")

        new_knowledge = []
        for item in links:
            print(f"📖 Đang đọc: {item['title'][:50]}...")
            try:
                resp = self.session.get(item['url'], timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Lấy text trong các thẻ p, li (chứa nội dung chính)
                paragraphs = [p.get_text().strip() for p in soup.find_all(['p', 'li'])]
                
                for text in paragraphs:
                    # Chỉ lấy câu có độ dài vừa phải và chứa từ khóa chủ đề
                    if 40 < len(text) < 300 and any(w in text.lower() for w in topic.lower().split()):
                        new_knowledge.append({
                            "s": text, 
                            "src": item['url'],
                            "t": time.time()
                        })
            except: continue
        
        # Lưu vào não
        if topic not in self.brain["topics"]: self.brain["topics"][topic] = []
        self.brain["topics"][topic].extend(new_knowledge)
        self.brain["stats"]["total_learned"] += len(new_knowledge)
        
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.brain, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã học thêm {len(new_knowledge)} kiến thức mới!")

    # --- HỎI ĐÁP THÔNG MINH (TRẢ LỜI ĐÚNG TRỌNG TÂM) ---
    def ask(self, question):
        results = []
        q_words = question.lower().split()
        
        for topic, sentences in self.brain["topics"].items():
            for item in sentences:
                score = sum(2 for word in q_words if word in item['s'].lower())
                if score > 0:
                    results.append((score, item['s']))
        
        # Sắp xếp câu trả lời theo điểm số từ cao xuống thấp
        results.sort(key=lambda x: x[0], reverse=True)
        
        if not results: return "🤔 Não chưa có thông tin này, hãy chọn 'Học' nhé!"
        
        output = "🤖 Câu trả lời tốt nhất cho bạn:\n"
        for i, (score, txt) in enumerate(results[:3], 1):
            output += f"{i}. {txt}\n"
        return output

# --- HÀM MAIN ĐƠN GIẢN ---
if __name__ == "__main__":
    ai = SmartAI()
    while True:
        print("\n1. Học | 2. Hỏi | 3. Thoát")
        c = input("Chọn: ")
        if c == '1':
            t = input("Chủ đề cần học: ")
            ai.learn_topic(t)
        elif c == '2':
            q = input("Câu hỏi: ")
            print(ai.ask(q))
        elif c == '3': break
