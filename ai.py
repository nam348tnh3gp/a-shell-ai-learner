#!/usr/bin/env python3
import json
import os
import time
import re
import random
import urllib.parse
import requests
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
KNOWLEDGE_FILE = "ai_brain_google.json"
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
]

class SmartAI:
    def __init__(self):
        self.brain = self.load_brain()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})

    def load_brain(self):
        if os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"topics": {}, "stats": {"total_learned": 0}, "learned_urls": []}

    def save_brain(self):
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.brain, f, ensure_ascii=False, indent=2)

    # --- TÌM KIẾM LINK (XỬ LÝ ĐÚNG URL GOOGLE) ---
    def search_links(self, query):
        links = []
        print(f"🔍 Đang quét tìm link cho: {query}...")
        
        # Thử Google
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=5"
            resp = self.session.get(url, timeout=12)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for g in soup.select('div.g, div.tF2Cxc'):
                a = g.find('a', href=True)
                if not a:
                    continue
                href = a['href']
                # Xử lý link redirect của Google
                if href.startswith('/url?q='):
                    match = re.search(r'/url\?q=(https?://[^&]+)', href)
                    if match:
                        real_url = match.group(1)
                    else:
                        continue
                elif href.startswith('http'):
                    real_url = href
                else:
                    continue
                # Bỏ qua các trang rác
                if any(x in real_url for x in ['google.com', 'youtube.com', 'facebook.com']):
                    continue
                title_tag = g.find('h3')
                title = title_tag.get_text(strip=True) if title_tag else "Không có tiêu đề"
                links.append({'url': real_url, 'title': title})
                if len(links) >= 3:
                    break
        except Exception as e:
            print(f"   Google lỗi: {e}")

        # Fallback DuckDuckGo Lite
        if not links:
            print("⚠️ Google chặn hoặc không có kết quả, chuyển sang DuckDuckGo...")
            try:
                url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
                resp = self.session.get(url, timeout=12)
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', class_='result-link'):
                    href = a.get('href')
                    if href and href.startswith('http'):
                        links.append({'url': href, 'title': a.get_text(strip=True)})
                        if len(links) >= 3:
                            break
            except Exception as e:
                print(f"   DuckDuckGo lỗi: {e}")

        return links

    # --- ĐỌC TRANG VÀ TRÍCH XUẤT CÂU HỮU ÍCH (CẢI TIẾN) ---
    def read_and_extract(self, url, topic):
        try:
            print(f"📖 Đang đọc: {url[:80]}...")
            self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"   HTTP {resp.status_code}, bỏ qua")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Xóa các thẻ không chứa nội dung chính
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'meta']):
                tag.decompose()
            
            # Lấy text từ nhiều loại thẻ khác nhau
            texts = []
            for tag in soup.find_all(['p', 'li', 'div', 'span', 'article', 'section']):
                text = tag.get_text(separator=' ', strip=True)
                if text:
                    texts.append(text)
            
            # Gộp và tách câu
            full_text = ' '.join(texts)
            # Tách câu dựa trên dấu chấm, chấm hỏi, chấm than
            sentences = re.split(r'[.!?]+', full_text)
            
            topic_words = set(topic.lower().split())
            valid_sentences = []
            
            for sent in sentences:
                sent = sent.strip()
                # Lọc câu có độ dài hợp lý (từ 50 đến 500 ký tự)
                if len(sent) < 50 or len(sent) > 500:
                    continue
                # Nếu câu chứa từ khóa của chủ đề thì ưu tiên
                sent_lower = sent.lower()
                if any(word in sent_lower for word in topic_words):
                    valid_sentences.append(sent)
                # Nếu chưa đủ câu, vẫn lấy câu dài nhưng không chứa từ khóa (vẫn có thể hữu ích)
                elif len(valid_sentences) < 5:
                    valid_sentences.append(sent)
                if len(valid_sentences) >= 8:
                    break
            
            # Nếu không có câu nào, lấy 3 câu đầu tiên đủ dài
            if not valid_sentences:
                for sent in sentences:
                    if 50 < len(sent) < 500:
                        valid_sentences.append(sent)
                        if len(valid_sentences) >= 3:
                            break
            
            print(f"   ✓ Trích xuất được {len(valid_sentences)} câu")
            return valid_sentences
        except Exception as e:
            print(f"   ❌ Lỗi đọc trang: {e}")
            return []

    # --- HỌC CHỦ ĐỀ ---
    def learn_topic(self, topic):
        # Chuẩn hóa topic
        topic = topic.strip().lower()
        links = self.search_links(topic)
        if not links:
            print("❌ Không tìm được tài liệu nào!")
            return
        
        new_knowledge = []
        learned_urls = self.brain.get("learned_urls", [])
        
        for item in links:
            url = item['url']
            if url in learned_urls:
                print(f"⏭️ Đã học {item['title'][:40]}... bỏ qua")
                continue
            
            sentences = self.read_and_extract(url, topic)
            for sent in sentences:
                # Tránh trùng lặp trong cùng chủ đề
                existing = self.brain["topics"].get(topic, [])
                if not any(sent == old['s'] for old in existing):
                    new_knowledge.append({
                        "s": sent,
                        "src": url,
                        "t": time.time()
                    })
            
            # Đánh dấu đã đọc URL này
            learned_urls.append(url)
            time.sleep(random.uniform(1, 2))  # Tránh bị chặn
        
        # Lưu vào brain
        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = []
        self.brain["topics"][topic].extend(new_knowledge)
        self.brain["stats"]["total_learned"] = self.brain["stats"].get("total_learned", 0) + len(new_knowledge)
        self.brain["learned_urls"] = learned_urls
        
        self.save_brain()
        print(f"✅ Đã học thêm {len(new_knowledge)} kiến thức mới về '{topic}'!")

    # --- HỎI ĐÁP THÔNG MINH ---
    def ask(self, question):
        q_words = set(question.lower().split())
        results = []
        
        for topic, items in self.brain["topics"].items():
            for item in items:
                sent = item['s'].lower()
                # Tính điểm dựa trên số từ khóa xuất hiện
                score = sum(2 for w in q_words if w in sent)
                if score > 0:
                    results.append((score, item['s']))
        
        if not results:
            return "🤔 Não chưa có thông tin này, hãy chọn 'Học' nhé!"
        
        # Sắp xếp theo điểm giảm dần, lấy 3 câu hay nhất
        results.sort(key=lambda x: x[0], reverse=True)
        answer = "🤖 **Câu trả lời hay nhất:**\n"
        for i, (_, txt) in enumerate(results[:3], 1):
            answer += f"{i}. {txt}\n"
        return answer

# --- MAIN ---
if __name__ == "__main__":
    ai = SmartAI()
    print("🤖 AI TỰ HỌC - BẢN CỰC MẠNH\n")
    while True:
        print("\n1. Học | 2. Hỏi | 3. Thoát")
        chon = input("Chọn: ").strip()
        if chon == '1':
            topic = input("Chủ đề cần học: ").strip()
            if topic:
                ai.learn_topic(topic)
            else:
                print("Vui lòng nhập chủ đề!")
        elif chon == '2':
            q = input("Câu hỏi: ").strip()
            if q:
                print(ai.ask(q))
            else:
                print("Vui lòng nhập câu hỏi!")
        elif chon == '3':
            break
        else:
            print("Chọn 1, 2 hoặc 3!")
