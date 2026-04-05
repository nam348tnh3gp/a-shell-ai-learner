#!/usr/bin/env python3
import json
import os
import time
import re
import random
import urllib.parse
import requests
from bs4 import BeautifulSoup

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

    # ================== TÌM KIẾM BẰNG DUCKDUCKGO LITE (FIX CẤU TRÚC MỚI) ==================
    def search_duckduckgo_lite(self, query):
        """DuckDuckGo Lite - parse theo cấu trúc HTML hiện tại (dùng table)"""
        links = []
        try:
            url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
            print(f"🦆 Đang tìm trên DuckDuckGo Lite: {query}")
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"   HTTP {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Cấu trúc mới: kết quả nằm trong <table> và mỗi dòng <tr> có link trong <a>
            rows = soup.find_all('tr')
            for row in rows:
                link_tag = row.find('a', href=True)
                if link_tag:
                    href = link_tag.get('href')
                    # Bỏ qua link quảng cáo hoặc nội bộ
                    if href and href.startswith('http') and 'duckduckgo.com' not in href:
                        title = link_tag.get_text(strip=True)
                        if title:
                            links.append({'url': href, 'title': title})
                            if len(links) >= 5:
                                break
            # Nếu không tìm thấy theo cách trên, thử tìm tất cả thẻ a có href http
            if not links:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('http') and 'duckduckgo.com' not in href:
                        title = a.get_text(strip=True)
                        if title and len(title) > 5:
                            links.append({'url': href, 'title': title})
                            if len(links) >= 5:
                                break
            print(f"   ✓ Tìm thấy {len(links)} link")
            return links
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            return []

    # ================== GOOGLE (BỎ QUA NẾU CHẶN) ==================
    def search_google(self, query):
        """Thử Google, nếu lỗi thì trả về rỗng (không fallback ở đây)"""
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=5"
            resp = self.session.get(url, timeout=12)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, 'html.parser')
            links = []
            for g in soup.select('div.g, div.tF2Cxc'):
                a = g.find('a', href=True)
                if not a:
                    continue
                href = a['href']
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
                if any(x in real_url for x in ['google.com', 'youtube.com', 'facebook.com']):
                    continue
                title_tag = g.find('h3')
                title = title_tag.get_text(strip=True) if title_tag else "No title"
                links.append({'url': real_url, 'title': title})
                if len(links) >= 3:
                    break
            return links
        except:
            return []

    # ================== LẤY LINK TỔNG HỢP ==================
    def search_links(self, query):
        print(f"🔍 Đang tìm kiếm: {query}")
        # Ưu tiên DuckDuckGo Lite vì ít bị chặn hơn
        links = self.search_duckduckgo_lite(query)
        if links:
            return links
        # Nếu DuckDuckGo không có, thử Google (hy vọng)
        print("⚠️ DuckDuckGo không có kết quả, thử Google...")
        links = self.search_google(query)
        if links:
            return links
        print("❌ Không tìm thấy link nào từ cả hai nguồn!")
        return []

    # ================== ĐỌC VÀ TRÍCH XUẤT ==================
    def read_and_extract(self, url, topic):
        try:
            print(f"📖 Đang đọc: {url[:80]}...")
            self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"   HTTP {resp.status_code}, bỏ qua")
                return []
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'meta']):
                tag.decompose()
            # Lấy text từ thẻ p, li, div, article, section
            texts = []
            for tag in soup.find_all(['p', 'li', 'div', 'article', 'section']):
                text = tag.get_text(separator=' ', strip=True)
                if text:
                    texts.append(text)
            full_text = ' '.join(texts)
            sentences = re.split(r'[.!?]+', full_text)
            topic_words = set(topic.lower().split())
            valid = []
            for sent in sentences:
                sent = sent.strip()
                if 50 < len(sent) < 500:
                    if any(w in sent.lower() for w in topic_words):
                        valid.append(sent)
                    elif len(valid) < 5:
                        valid.append(sent)
                if len(valid) >= 8:
                    break
            if not valid:
                for sent in sentences:
                    if 50 < len(sent) < 500:
                        valid.append(sent)
                        if len(valid) >= 3:
                            break
            print(f"   ✓ Trích xuất {len(valid)} câu")
            return valid
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            return []

    # ================== HỌC ==================
    def learn_topic(self, topic):
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
                print(f"⏭️ Đã học: {item['title'][:40]}...")
                continue
            sentences = self.read_and_extract(url, topic)
            for sent in sentences:
                existing = self.brain["topics"].get(topic, [])
                if not any(sent == old['s'] for old in existing):
                    new_knowledge.append({"s": sent, "src": url, "t": time.time()})
            learned_urls.append(url)
            time.sleep(random.uniform(1, 2))
        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = []
        self.brain["topics"][topic].extend(new_knowledge)
        self.brain["stats"]["total_learned"] = self.brain["stats"].get("total_learned", 0) + len(new_knowledge)
        self.brain["learned_urls"] = learned_urls
        self.save_brain()
        print(f"✅ Đã học thêm {len(new_knowledge)} kiến thức mới về '{topic}'!")

    # ================== HỎI ==================
    def ask(self, question):
        q_words = set(question.lower().split())
        results = []
        for topic, items in self.brain["topics"].items():
            for item in items:
                sent = item['s'].lower()
                score = sum(2 for w in q_words if w in sent)
                if score > 0:
                    results.append((score, item['s']))
        if not results:
            return "🤔 Não chưa có thông tin này, hãy chọn 'Học' nhé!"
        results.sort(key=lambda x: x[0], reverse=True)
        answer = "🤖 **Câu trả lời:**\n"
        for i, (_, txt) in enumerate(results[:3], 1):
            answer += f"{i}. {txt}\n"
        return answer

# ================== MAIN ==================
if __name__ == "__main__":
    ai = SmartAI()
    print("🤖 AI TỰ HỌC - BẢN SỬA LỖI TÌM KIẾM\n")
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
