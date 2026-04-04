#!/usr/bin/env python3
"""
AI Tự Học Nâng Cao - Truy cập tri thức Google
Chạy trên a-Shell mini với khả năng tìm kiếm và học có chọn lọc
"""

import urllib.request
import urllib.parse
import json
import os
import re
import time
import random
from html.parser import HTMLParser

# File lưu trữ kiến thức
KNOWLEDGE_FILE = "ai_knowledge.json"
MEMORY_FILE = "ai_memory.json"

class MLStripper(HTMLParser):
    """Loại bỏ thẻ HTML để lấy text thuần"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, d):
        self.text.append(d)
    
    def get_data(self):
        return ''.join(self.text)

def strip_html(html):
    """Chuyển HTML thành text thuần"""
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class KnowledgeAI:
    def __init__(self):
        self.knowledge = self.load_knowledge()
        self.memory = self.load_memory()
        self.learning_rate = 0.1
        
    def load_knowledge(self):
        """Tải kho kiến thức đã học"""
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {"facts": {}, "topics": {}, "total_learned": 0}
        return {"facts": {}, "topics": {}, "total_learned": 0}
    
    def load_memory(self):
        """Tải bộ nhớ học tập"""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {"searches": 0, "learned_concepts": []}
        return {"searches": 0, "learned_concepts": []}
    
    def save_all(self):
        """Lưu toàn bộ kiến thức"""
        with open(KNOWLEDGE_FILE, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.memory, f, indent=2)
        print("💾 Đã lưu kiến thức vào bộ nhớ dài hạn!")
    
    def search_google(self, query):
        """Tìm kiếm Google và trả về kết quả"""
        try:
            # Mã hóa query
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            # Thêm User-Agent để tránh bị chặn cơ bản
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            
            print(f"🔍 Đang tìm kiếm: '{query}'...")
            start_time = time.time()
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                response_time = time.time() - start_time
                
                # Trích xuất tiêu đề và đoạn trích từ kết quả tìm kiếm
                results = self.extract_search_results(html)
                
                print(f"✅ Tìm thấy {len(results)} kết quả trong {response_time:.2f}s")
                return results, True
                
        except Exception as e:
            print(f"❌ Lỗi tìm kiếm: {e}")
            return [], False
    
    def extract_search_results(self, html):
        """Trích xuất tiêu đề và mô tả từ HTML kết quả Google"""
        results = []
        
        # Pattern đơn giản để lấy kết quả tìm kiếm
        title_pattern = r'<h3[^>]*>(.*?)</h3>'
        snippet_pattern = r'<div[^>]*class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</div>'
        
        titles = re.findall(title_pattern, html, re.DOTALL)
        snippets = re.findall(snippet_pattern, html, re.DOTALL)
        
        # Lấy 5 kết quả đầu tiên
        for i in range(min(5, len(titles))):
            title = strip_html(titles[i])[:200]
            snippet = strip_html(snippets[i])[:300] if i < len(snippets) else ""
            
            if title and len(title) > 5:
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "relevance": 1.0 - (i * 0.1)  # Kết quả đầu tiên có độ liên quan cao nhất
                })
        
        return results
    
    def learn_from_results(self, query, results):
        """Học kiến thức từ kết quả tìm kiếm"""
        if not results:
            print("😔 Không có kiến thức mới để học")
            return 0
        
        learned_count = 0
        
        for result in results:
            # Trích xuất từ khóa quan trọng
            words = result['title'].lower().split() + result['snippet'].lower().split()
            important_words = [w for w in words if len(w) > 4 and w not in ['this', 'that', 'with', 'from']]
            
            # Lưu vào kho kiến thức
            topic = query.lower().replace(' ', '_')
            
            if topic not in self.knowledge['topics']:
                self.knowledge['topics'][topic] = {
                    'learned_at': time.time(),
                    'key_points': [],
                    'relevance_score': 0
                }
            
            # Thêm điểm chính (không trùng lặp)
            key_point = result['title'][:150]
            if key_point not in self.knowledge['topics'][topic]['key_points']:
                self.knowledge['topics'][topic]['key_points'].append(key_point)
                self.knowledge['topics'][topic]['relevance_score'] += result['relevance']
                learned_count += 1
            
            # Lưu các sự kiện quan trọng
            for word in important_words[:5]:
                if word not in self.knowledge['facts']:
                    self.knowledge['facts'][word] = {
                        'count': 0,
                        'contexts': []
                    }
                self.knowledge['facts'][word]['count'] += 1
                if len(self.knowledge['facts'][word]['contexts']) < 3:
                    self.knowledge['facts'][word]['contexts'].append(result['snippet'][:100])
        
        self.knowledge['total_learned'] += learned_count
        print(f"📚 Đã học {learned_count} kiến thức mới về '{query}'!")
        return learned_count
    
    def ask_ai(self, question):
        """AI tự trả lời dựa trên kiến thức đã học"""
        question_lower = question.lower()
        
        # Tìm chủ đề liên quan
        related_topics = []
        for topic, data in self.knowledge['topics'].items():
            if any(word in question_lower for word in topic.split('_')):
                related_topics.append((topic, data))
        
        if not related_topics:
            return "🤔 Tôi chưa có kiến thức về chủ đề này. Hãy để tôi tìm kiếm và học!"
        
        # Tổng hợp câu trả lời
        answer = f"📖 Dựa trên kiến thức đã học:\n\n"
        for topic, data in related_topics[:2]:
            answer += f"**Về {topic.replace('_', ' ')}:**\n"
            for point in data['key_points'][:2]:
                answer += f"• {point}\n"
            answer += f"(Độ tin cậy: {data['relevance_score']:.1f})\n\n"
        
        return answer
    
    def self_improve(self):
        """Tự cải thiện bằng cách đặt câu hỏi và tìm câu trả lời"""
        
        # Danh sách câu hỏi mẫu để AI tự học
        questions_to_ask = [
            "What is artificial intelligence",
            "How does machine learning work",
            "Python programming basics",
            "What is iOS development",
            "Internet of things explained",
            "Cloud computing benefits",
            "Data science for beginners",
            "Cybersecurity best practices"
        ]
        
        # Chọn câu hỏi chưa học nhiều
        best_question = None
        lowest_score = float('inf')
        
        for q in questions_to_ask:
            topic_key = q.lower().replace(' ', '_')
            score = self.knowledge['topics'].get(topic_key, {}).get('relevance_score', 0)
            if score < lowest_score:
                lowest_score = score
                best_question = q
        
        if not best_question:
            best_question = random.choice(questions_to_ask)
        
        print(f"\n🤔 AI tự hỏi: 'Hãy cho tôi biết về {best_question}'")
        time.sleep(1)
        
        # Tìm kiếm và học
        results, success = self.search_google(best_question)
        if success and results:
            self.learn_from_results(best_question, results)
            return True
        return False
    
    def chat_mode(self):
        """Chế độ trò chuyện - AI có thể trả lời câu hỏi"""
        print("\n" + "="*50)
        print("💬 CHẾ ĐỘ TRÒ CHUYỆN VỚI AI")
        print("AI có thể trả lời dựa trên kiến thức đã học từ Google")
        print("Gõ 'học <chủ đề>' để AI tìm hiểu thêm")
        print("Gõ 'thoát' để kết thúc")
        print("="*50)
        
        while True:
            user_input = input("\n🧑 Bạn: ").strip()
            
            if user_input.lower() == 'thoát':
                break
            
            if user_input.lower().startswith('học '):
                topic = user_input[4:].strip()
                print(f"📚 Đang học về '{topic}'...")
                results, success = self.search_google(topic)
                if success:
                    self.learn_from_results(topic, results)
                    self.save_all()
                continue
            
            # AI trả lời câu hỏi
            answer = self.ask_ai(user_input)
            print(f"\n🤖 AI: {answer}")
            
            # Nếu AI chưa biết, tự động tìm hiểu
            if "chưa có kiến thức" in answer:
                print("🔍 AI đang tự tìm hiểu để trả lời bạn...")
                results, success = self.search_google(user_input)
                if success:
                    self.learn_from_results(user_input, results)
                    self.save_all()
                    # Trả lời lại sau khi học
                    print(f"\n🤖 AI (sau khi học): {self.ask_ai(user_input)}")

def main():
    print("🚀 KHỞI ĐỘNG AI TRI THỨC - Phiên bản Google Learner")
    print("="*50)
    print("AI này có khả năng:")
    print("1. Tìm kiếm và học từ Google")
    print("2. Ghi nhớ kiến thức lâu dài")
    print("3. Tự đặt câu hỏi để mở rộng hiểu biết")
    print("4. Trả lời câu hỏi dựa trên kiến thức đã học")
    print("="*50)
    
    ai = KnowledgeAI()
    
    print(f"\n📊 THỐNG KÊ HIỆN TẠI:")
    print(f"   - Kiến thức đã học: {ai.knowledge['total_learned']} mẩu tin")
    print(f"   - Chủ đề đã nắm: {len(ai.knowledge['topics'])}")
    print(f"   - Sự kiện đã ghi nhớ: {len(ai.knowledge['facts'])}")
    
    try:
        while True:
            print("\n" + "-"*40)
            print("Chọn chế độ:")
            print("1. 🤖 AI tự học (tự đặt câu hỏi)")
            print("2. 💬 Trò chuyện với AI")
            print("3. 📊 Xem thống kê kiến thức")
            print("4. 🚪 Thoát")
            
            choice = input("\n👉 Chọn (1-4): ").strip()
            
            if choice == '1':
                print("\n🔄 AI bắt đầu chu kỳ tự học...")
                for i in range(3):  # Tự học 3 chủ đề
                    print(f"\n--- Lần học {i+1} ---")
                    if ai.self_improve():
                        ai.save_all()
                    time.sleep(2)
                    
            elif choice == '2':
                ai.chat_mode()
                
            elif choice == '3':
                print("\n📊 KIẾN THỨC AI ĐÃ TÍCH LŨY:")
                print(f"   Tổng số mẩu tin: {ai.knowledge['total_learned']}")
                print(f"   Số chủ đề: {len(ai.knowledge['topics'])}")
                print("\n📚 Các chủ đề đã học:")
                for topic, data in list(ai.knowledge['topics'].items())[:10]:
                    points = len(data['key_points'])
                    print(f"   • {topic.replace('_', ' ')}: {points} điểm chính")
                    
            elif choice == '4':
                print("\n👋 Tạm biệt! Đã lưu toàn bộ kiến thức!")
                ai.save_all()
                break
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Dừng bởi người dùng. Đang lưu kiến thức...")
        ai.save_all()

if __name__ == "__main__":
    main()
