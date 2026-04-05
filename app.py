#!/usr/bin/env python3
"""
AI TỰ HỌC - Web App cho Render.com
Bản sửa lỗi tìm kiếm – fallback DuckDuckGo HTML
"""

import os
import json
import time
import re
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

# ================== CẤU HÌNH ==================
app = Flask(__name__)
CORS(app)

KNOWLEDGE_FILE = "ai_brain.json"
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
]

# Thử import duckduckgo_search (nếu có)
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("⚠️ duckduckgo_search không có sẵn, sẽ dùng fallback HTML.")

# ================== LỚP AI ==================
class SmartAI:
    def __init__(self):
        self.brain = self.load_brain()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})

    def load_brain(self):
        if os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "topics": {},
            "stats": {"total_learned": 0, "pages_read": 0},
            "learned_urls": []
        }

    def save_brain(self):
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.brain, f, ensure_ascii=False, indent=2)

    # ---------- TÌM KIẾM (DuckDuckGo API + HTML fallback) ----------
    def search_links(self, query, max_results=5):
        """Trả về list {url, title} - hoạt động ổn định"""
        # Cách 1: Dùng duckduckgo_search nếu có
        if DDGS_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                    links = [{'url': r['href'], 'title': r['title']} for r in results]
                    if links:
                        print(f"✅ DuckDuckGo API trả về {len(links)} link")
                        return links
            except Exception as e:
                print(f"⚠️ DuckDuckGo API lỗi: {e}, chuyển sang fallback HTML")

        # Cách 2: Fallback parse DuckDuckGo Lite (dùng requests + BeautifulSoup)
        print("🔁 Đang dùng fallback DuckDuckGo Lite HTML...")
        try:
            url = f"https://lite.duckduckgo.com/lite/?q={query}"
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"❌ DuckDuckGo Lite HTTP {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, 'html.parser')
            links = []

            # Cấu trúc mới: kết quả nằm trong các dòng <td> của bảng
            rows = soup.find_all('tr')
            for row in rows:
                # Tìm cột chứa link (thường có class='result-snippet' hoặc thẻ a)
                link_cell = row.find('td', class_='result-snippet')
                if not link_cell:
                    # Thử tìm bất kỳ thẻ a nào trong row
                    link_cell = row.find('a')
                if link_cell:
                    a_tag = link_cell.find('a') if link_cell.name != 'a' else link_cell
                    if a_tag and a_tag.get('href'):
                        href = a_tag['href']
                        # Lọc link thật (bỏ qua link nội bộ duckduckgo)
                        if href.startswith('http') and 'duckduckgo.com' not in href:
                            title = a_tag.get_text(strip=True)
                            if title:
                                links.append({'url': href, 'title': title[:150]})
                                if len(links) >= max_results:
                                    break

            # Nếu vẫn không có, quét toàn bộ thẻ a trong trang
            if not links:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('http') and 'duckduckgo.com' not in href:
                        title = a.get_text(strip=True)
                        if title and len(title) > 5:
                            links.append({'url': href, 'title': title[:150]})
                            if len(links) >= max_results:
                                break

            print(f"✅ DuckDuckGo Lite fallback trả về {len(links)} link")
            return links
        except Exception as e:
            print(f"❌ Fallback HTML lỗi: {e}")
            return []

    # ---------- ĐỌC VÀ TRÍCH XUẤT CÂU ----------
    def read_and_extract(self, url, topic):
        try:
            print(f"📖 Đọc: {url[:80]}...")
            self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()

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

            print(f"   → Trích xuất {len(valid)} câu")
            return valid
        except Exception as e:
            print(f"   ❌ Lỗi đọc trang: {e}")
            return []

    # ---------- HỌC CHỦ ĐỀ ----------
    def learn_topic(self, topic):
        topic = topic.strip().lower()
        links = self.search_links(topic)
        if not links:
            return {"success": False, "message": "Không tìm thấy tài liệu nào!"}

        new_knowledge = []
        learned_urls = self.brain.get("learned_urls", [])

        for item in links:
            url = item['url']
            if url in learned_urls:
                continue

            sentences = self.read_and_extract(url, topic)
            for sent in sentences:
                existing = self.brain["topics"].get(topic, [])
                if not any(sent == old['s'] for old in existing):
                    new_knowledge.append({
                        "s": sent,
                        "src": url,
                        "t": time.time()
                    })

            learned_urls.append(url)
            time.sleep(random.uniform(1, 2))

        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = []
        self.brain["topics"][topic].extend(new_knowledge)
        self.brain["stats"]["total_learned"] = self.brain["stats"].get("total_learned", 0) + len(new_knowledge)
        self.brain["stats"]["pages_read"] = self.brain["stats"].get("pages_read", 0) + len(links)
        self.brain["learned_urls"] = learned_urls
        self.save_brain()

        return {
            "success": True,
            "topic": topic,
            "new_knowledge": len(new_knowledge),
            "total_knowledge": len(self.brain["topics"].get(topic, [])),
            "links_read": len(links)
        }

    # ---------- HỎI ĐÁP ----------
    def ask(self, question):
        q_words = set(question.lower().split())
        results = []
        for topic, items in self.brain["topics"].items():
            for item in items:
                sent = item['s'].lower()
                score = sum(2 for w in q_words if w in sent)
                if score > 0:
                    results.append((score, item['s'], topic))

        if not results:
            return {
                "answer": "🤔 Tôi chưa có kiến thức về câu hỏi này. Hãy gửi yêu cầu học chủ đề trước nhé!",
                "found": False
            }

        results.sort(key=lambda x: x[0], reverse=True)
        top3 = [f"{i+1}. {txt}" for i, (_, txt, _) in enumerate(results[:3])]
        return {
            "answer": "\n".join(top3),
            "found": True,
            "best_topic": results[0][2]
        }

    def get_stats(self):
        return {
            "total_knowledge": self.brain["stats"]["total_learned"],
            "pages_read": self.brain["stats"]["pages_read"],
            "topics_count": len(self.brain["topics"]),
            "topics": list(self.brain["topics"].keys())
        }

# ================== KHỞI TẠO AI ==================
ai = SmartAI()

# ================== API ENDPOINTS ==================
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "name": "AI Tự Học",
        "version": "2.1",
        "endpoints": {
            "POST /learn": "Học một chủ đề. Body: { 'topic': 'python' }",
            "POST /ask": "Hỏi một câu hỏi. Body: { 'question': 'python là gì?' }",
            "GET /stats": "Xem thống kê kiến thức"
        }
    })

@app.route('/learn', methods=['POST'])
def learn():
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({"error": "Thiếu 'topic' trong body"}), 400
    topic = data['topic']
    result = ai.learn_topic(topic)
    return jsonify(result)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "Thiếu 'question' trong body"}), 400
    question = data['question']
    result = ai.ask(question)
    return jsonify(result)

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify(ai.get_stats())

# ================== CHẠY SERVER ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
