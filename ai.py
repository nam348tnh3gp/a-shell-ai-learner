#!/usr/bin/env python3
"""
AI TỰ HỌC GOOGLE - Bản fix encoding
Chạy được trên a-Shell mini với encoding chuẩn
"""

import json
import os
import time
import random

# Cố gắng import requests, nếu không có thì hướng dẫn cài
try:
    import requests
    from urllib.parse import quote_plus
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️ Cần cài requests: pip install requests")

KNOWLEDGE_FILE = "ai_knowledge_fixed.json"

class GoogleAIFixed:
    def __init__(self):
        if not HAS_REQUESTS:
            raise Exception("Chưa cài requests! Chạy: pip install requests")
        
        self.knowledge = self.load_knowledge()
        self.session = requests.Session()
        # Headers giống trình duyệt thật
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def load_knowledge(self):
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.init_knowledge()
        return self.init_knowledge()
    
    def init_knowledge(self):
        return {
            "topics": {},
            "search_history": [],
            "total_learned": 0
        }
    
    def save_knowledge(self):
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
        print("💾 Đã lưu kiến thức!")
    
    def search_google(self, query):
        """Tìm kiếm Google với encoding đúng"""
        try:
            # Encode query đúng cách cho URL
            encoded_query = quote_plus(query.encode('utf-8'))
            url = f"https://www.google.com/search?q={encoded_query}&hl=vi"
            
            print(f"🔍 Đang tìm: '{query}'")
            print(f"📎 URL: {url[:80]}...")
            
            start_time = time.time()
            
            # Gửi request với timeout
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response_time = time.time() - start_time
            
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"⚠️ Google trả về mã {response.status_code}")
                return self.mock_search(query)  # Fallback to mock data
            
            # Kiểm tra nếu bị chặn
            html = response.text
            if 'captcha' in html.lower() or 'unusual traffic' in html.lower():
                print("⚠️ Google đã chặn (CAPTCHA). Dùng dữ liệu mẫu...")
                return self.mock_search(query)
            
            # Parse kết quả đơn giản
            results = self.parse_google_results(html)
            
            if results:
                print(f"✅ Tìm thấy {len(results)} kết quả trong {response_time:.2f}s")
                for i, r in enumerate(results[:2], 1):
                    print(f"   {i}. {r['title'][:50]}...")
                return results, True
            else:
                print("⚠️ Không parse được kết quả, dùng dữ liệu mẫu")
                return self.mock_search(query), True
                
        except requests.exceptions.SSLError as e:
            print(f"❌ Lỗi SSL: {e}")
            print("🔄 Thử lại với verify=False...")
            try:
                response = self.session.get(url, timeout=15, verify=False)
                if response.status_code == 200:
                    return self.mock_search(query), True
            except:
                pass
            return self.mock_search(query), True
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return self.mock_search(query), True
    
    def parse_google_results(self, html):
        """Parse kết quả Google đơn giản"""
        results = []
        
        # Tìm các block kết quả
        import re
        
        # Pattern tìm title và snippet
        title_pattern = r'<h3[^>]*>(.*?)</h3>'
        snippet_pattern = r'<div[^>]*class="[^"]*(?:VwiC3b|IsZvec|aCOpRe)[^"]*"[^>]*>(.*?)</div>'
        
        titles = re.findall(title_pattern, html, re.DOTALL)
        snippets = re.findall(snippet_pattern, html, re.DOTALL)
        
        # Loại bỏ HTML tags
        def clean_html(text):
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'&[a-z]+;', '', text)
            return text.strip()
        
        for i in range(min(5, len(titles))):
            title = clean_html(titles[i])
            snippet = clean_html(snippets[i]) if i < len(snippets) else ""
            
            if title and len(title) > 5:
                results.append({
                    "title": title[:200],
                    "snippet": snippet[:300]
                })
        
        return results
    
    def mock_search(self, query):
        """Dữ liệu mẫu khi không thể kết nối Google"""
        mock_data = {
            "python": [
                {"title": "Python Tutorial - W3Schools", "snippet": "Python là ngôn ngữ lập trình dễ học, mạnh mẽ."},
                {"title": "Python.org - Official Website", "snippet": "Trang chủ của Python, tải về và tài liệu chính thức."},
                {"title": "Python for Beginners", "snippet": "Học Python cơ bản đến nâng cao."}
            ],
            "machine learning": [
                {"title": "Machine Learning Crash Course - Google", "snippet": "Khóa học ML miễn phí từ Google."},
                {"title": "Scikit-learn Tutorial", "snippet": "Thư viện ML phổ biến cho Python."}
            ],
            "artificial intelligence": [
                {"title": "What is AI? - IBM", "snippet": "Trí tuệ nhân tạo là gì và ứng dụng."},
                {"title": "AI Tutorial for Beginners", "snippet": "Học AI từ cơ bản."}
            ]
        }
        
        # Tìm kiếm trong mock data
        query_lower = query.lower()
        for key, results in mock_data.items():
            if key in query_lower or query_lower in key:
                print(f"📚 Dùng dữ liệu mẫu cho '{query}'")
                return results
        
        # Mock data mặc định
        default_results = [
            {"title": f"Kết quả tìm kiếm cho '{query}'", "snippet": f"Đây là thông tin mẫu về {query}. Khi có internet, AI sẽ tìm kiếm thực tế."},
            {"title": f"Học {query} cơ bản", "snippet": f"Hướng dẫn chi tiết về {query} cho người mới bắt đầu."},
            {"title": f"{query} - Tài liệu tham khảo", "snippet": f"Tổng hợp kiến thức về {query}."}
        ]
        
        return default_results
    
    def learn_topic(self, topic):
        """Học một chủ đề"""
        print(f"\n📚 Đang học: {topic}")
        
        results, success = self.search_google(topic)
        
        if not results:
            print("😔 Không có kết quả")
            return False
        
        if topic not in self.knowledge["topics"]:
            self.knowledge["topics"][topic] = {
                "learned_at": time.time(),
                "info": [],
                "times": 0
            }
        
        topic_data = self.knowledge["topics"][topic]
        topic_data["times"] += 1
        
        new_count = 0
        for result in results[:3]:
            # Kiểm tra trùng
            is_new = True
            for existing in topic_data["info"]:
                if existing["title"] == result["title"]:
                    is_new = False
                    break
            
            if is_new:
                topic_data["info"].append({
                    "title": result["title"],
                    "summary": result.get("snippet", "")[:200]
                })
                new_count += 1
        
        self.knowledge["total_learned"] += new_count
        self.knowledge["search_history"].append({
            "topic": topic,
            "time": time.time(),
            "results": len(results)
        })
        
        print(f"✅ Học xong! {new_count} thông tin mới")
        self.save_knowledge()
        return True
    
    def ask(self, question):
        """Trả lời câu hỏi"""
        question_lower = question.lower()
        
        # Tìm chủ đề liên quan
        best_match = None
        best_score = 0
        
        for topic, data in self.knowledge["topics"].items():
            score = 0
            for word in question_lower.split():
                if word in topic.lower():
                    score += 5
                for info in data["info"]:
                    if word in info["title"].lower():
                        score += 2
                    if word in info["summary"].lower():
                        score += 1
            
            if score > best_score and score > 0:
                best_score = score
                best_match = (topic, data)
        
        if not best_match:
            return f"🤔 Tôi chưa học về '{question}'. Hãy chọn 'Học chủ đề mới'!"
        
        topic, data = best_match
        answer = f"📖 **Về {topic.title()}:**\n\n"
        
        for i, info in enumerate(data["info"][:3], 1):
            answer += f"{i}. {info['title']}\n"
            if info['summary']:
                answer += f"   {info['summary'][:150]}\n"
            answer += "\n"
        
        return answer

def main():
    print("🚀 GOOGLE AI - Bản fix encoding")
    print("="*50)
    
    if not HAS_REQUESTS:
        print("\n❌ Thiếu thư viện requests!")
        print("📦 Chạy lệnh: pip install requests")
        print("🔄 Sau đó chạy lại chương trình")
        return
    
    ai = GoogleAIFixed()
    
    print(f"\n📊 Thống kê:")
    print(f"   - Đã học: {ai.knowledge['total_learned']} thông tin")
    print(f"   - Chủ đề: {len(ai.knowledge['topics'])}")
    
    while True:
        print("\n" + "-"*40)
        print("1. 🔍 Học chủ đề mới (tìm kiếm Google)")
        print("2. 💬 Hỏi AI")
        print("3. 📊 Xem kiến thức")
        print("4. 🚪 Thoát")
        
        choice = input("\n👉 Chọn (1-4): ").strip()
        
        if choice == '1':
            topic = input("\n📚 Nhập chủ đề (VD: python, AI, machine learning): ").strip()
            if topic:
                ai.learn_topic(topic)
            else:
                print("Vui lòng nhập chủ đề!")
                
        elif choice == '2':
            question = input("\n❓ Câu hỏi: ").strip()
            if question:
                answer = ai.ask(question)
                print(f"\n🤖 {answer}")
            else:
                print("Vui lòng nhập câu hỏi!")
                
        elif choice == '3':
            print("\n📚 KHO KIẾN THỨC:")
            if not ai.knowledge["topics"]:
                print("   Chưa có kiến thức. Hãy chọn 'Học chủ đề mới'!")
            else:
                for topic, data in ai.knowledge["topics"].items():
                    print(f"\n🔹 {topic.upper()}: {len(data['info'])} thông tin")
                    for info in data["info"][:2]:
                        print(f"   - {info['title'][:60]}")
                        
        elif choice == '4':
            print("\n👋 Tạm biệt!")
            ai.save_knowledge()
            break
        else:
            print("Chọn không hợp lệ!")

if __name__ == "__main__":
    # Tắt warning SSL nếu cần
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main()
