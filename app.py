#!/usr/bin/env python3
"""
AI TỰ HỌC - Web App cho Render.com
Nhận request từ iPhone, tự học và trả lời thông minh.
"""

import os
import json
import time
import re
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

# ================== CẤU HÌNH ==================
app = Flask(__name__)
CORS(app)  # Cho phép iPhone gọi API

KNOWLEDGE_FILE = "ai_brain.json"
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
]

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

    # ---------- TÌM KIẾM (dùng DuckDuckGo API chính thức) ----------
    def search_links(self, query, max_results=5):
        """Trả về list {url, title}"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                links = []
                for r in results:
                    links.append({
                        'url': r['href'],
                        'title': r['title']
                    })
                return links
        except Exception as e:
            print(f"Lỗi tìm kiếm DuckDuckGo: {e}")
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
            # Xóa thẻ rác
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()

            # Lấy text từ các thẻ chính
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
        "version": "2.0",
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
