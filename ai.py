#!/usr/bin/env python3
"""
AI Tự Học - Dùng DuckDuckGo (không bị chặn)
Chạy tốt trên a-Shell mini
"""

import urllib.request
import urllib.parse
import json
import os
import time
import random
import re

KNOWLEDGE_FILE = "ai_knowledge_ddg.json"

class DuckDuckGoAI:
    def __init__(self):
        self.knowledge = self.load_knowledge()
        
    def load_knowledge(self):
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.init_knowledge()
        return self.init_knowledge()
    
    def init_knowledge(self):
        return {
            "topics": {},
            "total_learned": 0,
            "last_learned": None
        }
    
    def save_knowledge(self):
        with open(KNOWLEDGE_FILE, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
        print("💾 Đã lưu kiến thức!")
    
    def search_duckduckgo(self, query):
        """Tìm kiếm trên DuckDuckGo API (miễn phí, không chặn)"""
        try:
            # Dùng DuckDuckGo Lite (phiên bản nhẹ, dễ parse)
            encoded_query = urllib.parse.quote(query)
            url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"🔍 Đang tìm: '{query}'...")
            start_time = time.time()
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                response_time = time.time() - start_time
                
                # Parse HTML của DuckDuckGo Lite
                results = self.parse_ddg_results(html)
                
                if results:
                    print(f"✅ Tìm thấy {len(results)} kết quả trong {response_time:.2f}s")
                    # Hiển thị kết quả đầu tiên
                    print(f"📄 Ví dụ: {results[0]['title'][:60]}...")
                else:
                    print(f"⚠️ Không tìm thấy kết quả cho '{query}'")
                
                return results, len(results) > 0
                
        except urllib.error.URLError as e:
            print(f"❌ Lỗi mạng: {e.reason}")
            return [], False
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return [], False
    
    def parse_ddg_results(self, html):
        """Parse kết quả từ DuckDuckGo Lite"""
        results = []
        
        # Tìm các dòng kết quả trong bảng của DDG Lite
        lines = html.split('\n')
        
        current_result = {}
        in_result = False
        
        for i, line in enumerate(lines):
            # Kết quả thường nằm trong thẻ <tr> với class="result-snippet"
            if '<tr class="result-snippet">' in line:
                in_result = True
                current_result = {}
            elif in_result and '<a rel="nofollow"' in line:
                # Lấy tiêu đề
                title_match = re.search(r'>([^<]+)</a>', line)
                if title_match:
                    current_result['title'] = title_match.group(1).strip()
            elif in_result and '<td class="result-snippet">' in line:
                # Lấy mô tả
                snippet_match = re.search(r'<td class="result-snippet">(.*?)</td>', line)
                if snippet_match:
                    snippet = snippet_match.group(1)
                    # Loại bỏ thẻ HTML
                    snippet = re.sub(r'<[^>]+>', '', snippet)
                    current_result['snippet'] = snippet.strip()
                    results.append(current_result)
                    in_result = False
            
            # Giới hạn 5 kết quả
            if len(results) >= 5:
                break
        
        # Nếu cách trên không hoạt động, thử cách đơn giản hơn
        if not results:
            # Tìm tất cả các dòng có chứa kết quả
            result_blocks = re.findall(r'<a rel="nofollow"[^>]*>([^<]+)</a>.*?<td class="result-snippet">(.*?)</td>', html, re.DOTALL)
            for title, snippet in result_blocks[:5]:
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                results.append({
                    'title': title.strip(),
                    'snippet': snippet[:300]
                })
        
        return results
    
    def learn_topic(self, topic):
        """Học một chủ đề mới"""
        print(f"\n📚 Đang học về: {topic}")
        
        # Tìm kiếm
        results, success = self.search_duckduckgo(topic)
        
        if not success or not results:
            print("😔 Không thể học chủ đề này lúc này")
            return False
        
        # Lưu kiến thức
        if topic not in self.knowledge["topics"]:
            self.knowledge["topics"][topic] = {
                "learned_at": time.time(),
                "information": [],
                "times_learned": 0
            }
        
        topic_data = self.knowledge["topics"][topic]
        topic_data["times_learned"] += 1
        
        new_count = 0
        for result in results:
            # Kiểm tra trùng lặp
            is_new = True
            for existing in topic_data["information"]:
                if existing["title"] == result["title"]:
                    is_new = False
                    break
            
            if is_new:
                topic_data["information"].append({
                    "title": result["title"][:200],
                    "summary": result.get("snippet", "")[:300],
                    "learned_at": time.time()
                })
                new_count += 1
        
        self.knowledge["total_learned"] += new_count
        self.knowledge["last_learned"] = topic
        
        print(f"✅ Đã học {new_count} thông tin mới về '{topic}'!")
        print(f"📊 Tổng số thông tin về chủ đề này: {len(topic_data['information'])}")
        
        self.save_knowledge()
        return True
    
    def ask(self, question):
        """Trả lời câu hỏi dựa trên kiến thức"""
        question_lower = question.lower()
        
        # Tìm chủ đề liên quan nhất
        best_topic = None
        best_score = 0
        best_data = None
        
        for topic, data in self.knowledge["topics"].items():
            score = 0
            # Từ khóa trong câu hỏi
            for word in question_lower.split():
                if word in topic.lower():
                    score += 5
                for info in data["information"]:
                    if word in info["title"].lower():
                        score += 2
                    if word in info["summary"].lower():
                        score += 1
            
            if score > best_score and score > 0:
                best_score = score
                best_topic = topic
                best_data = data
        
        if not best_topic:
            return f"🤔 Tôi chưa học về '{question}'. Hãy chọn 'Học chủ đề mới' để tôi tìm hiểu!"
        
        # Tạo câu trả lời
        answer = f"📖 **Về {best_topic.title()}:**\n\n"
        
        for i, info in enumerate(best_data["information"][:3], 1):
            answer += f"{i}. **{info['title']}**\n"
            if info['summary']:
                summary = info['summary'][:150]
                answer += f"   {summary}...\n"
            answer += "\n"
        
        answer += f"💡 Tôi đã học về chủ đề này {best_data['times_learned']} lần, với {len(best_data['information'])} thông tin."
        
        return answer
    
    def show_knowledge(self):
        """Hiển thị tất cả kiến thức"""
        if not self.knowledge["topics"]:
            print("\n📚 Chưa có kiến thức nào. Hãy chọn 'Học chủ đề mới'!")
            return
        
        print("\n" + "="*50)
        print("📚 KHO KIẾN THỨC ĐÃ HỌC")
        print("="*50)
        
        for topic, data in self.knowledge["topics"].items():
            print(f"\n🔹 {topic.upper()}")
            print(f"   📝 Số thông tin: {len(data['information'])}")
            print(f"   🔄 Số lần học: {data['times_learned']}")
            if data["information"]:
                print(f"   📖 Gần đây: {data['information'][-1]['title'][:60]}...")
        
        print(f"\n📊 Tổng số: {self.knowledge['total_learned']} thông tin")
    
    def auto_learn_suggestions(self):
        """Tự đề xuất chủ đề để học"""
        suggestions = [
            "python programming",
            "machine learning basics",
            "artificial intelligence",
            "data science",
            "neural networks",
            "deep learning tutorial",
            "natural language processing",
            "computer vision",
            "reinforcement learning",
            "python libraries for data science"
        ]
        
        # Chọn chủ đề chưa học hoặc học ít
        for topic in suggestions:
            if topic not in self.knowledge["topics"] or len(self.knowledge["topics"][topic]["information"]) < 2:
                return topic
        
        return random.choice(suggestions)

def main():
    print("🚀 DUCKDUCKGO AI LEARNER - Học từ Internet")
    print("="*50)
    print("✨ Dùng DuckDuckGo (không bị chặn như Google)")
    print("="*50)
    
    ai = DuckDuckGoAI()
    
    print(f"\n📊 Thống kê hiện tại:")
    print(f"   - Đã học: {ai.knowledge['total_learned']} thông tin")
    print(f"   - Chủ đề: {len(ai.knowledge['topics'])}")
    
    while True:
        print("\n" + "-"*40)
        print("1. 🤖 AI tự học (chọn chủ đề thông minh)")
        print("2. 📚 Học chủ đề mới (nhập tên)")
        print("3. 💬 Hỏi AI (dùng kiến thức đã học)")
        print("4. 📊 Xem kho kiến thức")
        print("5. 🚪 Thoát")
        
        choice = input("\n👉 Chọn (1-5): ").strip()
        
        if choice == '1':
            topic = ai.auto_learn_suggestions()
            print(f"\n🤖 AI quyết định học: {topic}")
            ai.learn_topic(topic)
            
        elif choice == '2':
            topic = input("\n📚 Nhập chủ đề muốn học: ").strip()
            if topic:
                ai.learn_topic(topic)
            else:
                print("Vui lòng nhập chủ đề!")
                
        elif choice == '3':
            question = input("\n❓ Câu hỏi của bạn: ").strip()
            if question:
                answer = ai.ask(question)
                print(f"\n🤖 {answer}")
            else:
                print("Vui lòng nhập câu hỏi!")
                
        elif choice == '4':
            ai.show_knowledge()
            
        elif choice == '5':
            print("\n👋 Tạm biệt! Đã lưu tất cả kiến thức.")
            ai.save_knowledge()
            break
        else:
            print("❌ Chọn không hợp lệ!")

if __name__ == "__main__":
    main()
