#!/usr/bin/env python3
"""
AI Tự Học Google - Phiên bản hoạt động thực tế
Dùng requests và BeautifulSoup để parse kết quả tìm kiếm
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
import re

# File lưu trữ
KNOWLEDGE_FILE = "ai_knowledge.json"

class GoogleLearnerAI:
    def __init__(self):
        self.knowledge = self.load_knowledge()
        # User-Agent xoay vòng để tránh bị chặn
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        ]
        
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
            "search_history": [],
            "total_searches": 0,
            "last_search": None
        }
    
    def save_knowledge(self):
        with open(KNOWLEDGE_FILE, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
        print("💾 Đã lưu kiến thức!")
    
    def search_google(self, query):
        """Tìm kiếm Google và parse kết quả thực tế"""
        try:
            # URL tìm kiếm
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=5"
            
            # Chọn User-Agent ngẫu nhiên
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            print(f"🔍 Đang tìm: '{query}'...")
            start = time.time()
            
            # Gửi request
            response = requests.get(search_url, headers=headers, timeout=15)
            response_time = time.time() - start
            
            if response.status_code != 200:
                print(f"⚠️ Google trả về mã {response.status_code}")
                return [], False
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm kết quả tìm kiếm (cập nhật selector mới nhất)
            results = []
            
            # Cách 1: Tìm theo class phổ biến của Google
            search_results = soup.find_all('div', class_=re.compile('g'))
            
            if not search_results:
                # Cách 2: Tìm theo h3
                search_results = soup.find_all('div', recursive=True)
            
            for result in search_results[:5]:
                # Tìm tiêu đề
                title_tag = result.find('h3')
                if not title_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                # Tìm đoạn mô tả
                snippet = ""
                snippet_div = result.find('div', class_=re.compile('VwiC3b|IsZvec|aCOpRe'))
                if snippet_div:
                    snippet = snippet_div.get_text(strip=True)
                
                # Tìm link
                link_tag = result.find('a')
                link = link_tag.get('href') if link_tag else ""
                
                results.append({
                    "title": title[:200],
                    "snippet": snippet[:300] if snippet else "Không có mô tả",
                    "link": link[:100]
                })
            
            if results:
                print(f"✅ Tìm thấy {len(results)} kết quả trong {response_time:.2f}s")
                # In preview kết quả đầu tiên
                print(f"📄 VD: {results[0]['title'][:50]}...")
            else:
                print(f"⚠️ Không tìm thấy kết quả nào (có thể Google chặn bot)")
            
            return results, len(results) > 0
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi mạng: {e}")
            return [], False
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return [], False
    
    def learn_from_search(self, query, results):
        """Học từ kết quả tìm kiếm"""
        if not results:
            print("😔 Không có kết quả để học")
            return 0
        
        topic = query.lower().strip()
        
        if topic not in self.knowledge["topics"]:
            self.knowledge["topics"][topic] = {
                "learned_at": time.time(),
                "searches": 0,
                "information": [],
                "key_concepts": set()
            }
        
        topic_data = self.knowledge["topics"][topic]
        topic_data["searches"] += 1
        
        new_info_count = 0
        for result in results:
            info = {
                "title": result["title"],
                "summary": result["snippet"],
                "learned_at": time.time()
            }
            
            # Tránh trùng lặp
            if not any(existing["title"] == result["title"] for existing in topic_data["information"]):
                topic_data["information"].append(info)
                new_info_count += 1
                
                # Trích xuất từ khóa quan trọng
                words = result["title"].lower().split() + result["snippet"].lower().split()
                important = [w for w in words if len(w) > 5 and w not in ['there', 'their', 'about', 'would']]
                for word in important[:3]:
                    topic_data["key_concepts"].add(word)
        
        # Convert set thành list để lưu JSON
        topic_data["key_concepts"] = list(topic_data["key_concepts"])
        
        # Cập nhật lịch sử
        self.knowledge["search_history"].append({
            "query": topic,
            "timestamp": time.time(),
            "results_found": len(results)
        })
        self.knowledge["total_searches"] += 1
        self.knowledge["last_search"] = topic
        
        print(f"📚 Đã học {new_info_count} thông tin mới về '{topic}'!")
        print(f"💡 Tổng số kiến thức về chủ đề này: {len(topic_data['information'])}")
        
        return new_info_count
    
    def ask_question(self, question):
        """Trả lời câu hỏi dựa trên kiến thức đã học"""
        question_lower = question.lower()
        
        # Tìm chủ đề liên quan nhất
        best_match = None
        best_score = 0
        
        for topic, data in self.knowledge["topics"].items():
            # Tính điểm liên quan
            score = 0
            words_in_question = question_lower.split()
            for word in words_in_question:
                if word in topic or topic in word:
                    score += 3
                for concept in data.get("key_concepts", []):
                    if word in concept or concept in word:
                        score += 1
            
            if score > best_score and score > 0:
                best_score = score
                best_match = (topic, data)
        
        if not best_match:
            return f"🤔 Tôi chưa có kiến thức về '{question}'. Hãy gõ 'học {question}' để tôi tìm hiểu!"
        
        topic, data = best_match
        info_list = data["information"]
        
        if not info_list:
            return f"📖 Tôi đã tìm hiểu về '{topic}' nhưng chưa có thông tin chi tiết."
        
        # Tạo câu trả lời
        answer = f"📖 **Về {topic.title()}:**\n\n"
        
        # Lấy 2 thông tin hay nhất
        for i, info in enumerate(info_list[:2], 1):
            answer += f"{i}. **{info['title']}**\n"
            if info['summary']:
                answer += f"   {info['summary'][:200]}\n"
            answer += "\n"
        
        # Thêm từ khóa quan trọng
        if data.get("key_concepts"):
            concepts = ", ".join(data["key_concepts"][:5])
            answer += f"🔑 Từ khóa quan trọng: {concepts}\n"
        
        return answer
    
    def auto_learn(self, num_rounds=3):
        """Tự động học các chủ đề phổ biến"""
        default_topics = [
            "python programming basics",
            "machine learning introduction",
            "artificial intelligence explained",
            "deep learning tutorial",
            "data science for beginners",
            "neural networks explained",
            "natural language processing",
            "computer vision basics"
        ]
        
        # Chọn chủ đề chưa học hoặc học ít
        topics_to_learn = []
        for topic in default_topics:
            if topic not in self.knowledge["topics"] or len(self.knowledge["topics"][topic]["information"]) < 2:
                topics_to_learn.append(topic)
        
        if not topics_to_learn:
            topics_to_learn = random.sample(default_topics, min(num_rounds, len(default_topics)))
        
        learned = 0
        for topic in topics_to_learn[:num_rounds]:
            print(f"\n🤖 Tự học: {topic}")
            results, success = self.search_google(topic)
            if success:
                learned += self.learn_from_search(topic, results)
                self.save_knowledge()
                time.sleep(2)  # Tránh bị chặn
            else:
                print(f"⚠️ Bỏ qua {topic} do lỗi kết nối")
        
        return learned

def main():
    print("🚀 GOOGLE LEARNER AI - Phiên bản hoạt động")
    print("="*50)
    
    ai = GoogleLearnerAI()
    
    print(f"\n📊 Thống kê:")
    print(f"   - Đã tìm kiếm: {ai.knowledge['total_searches']} lần")
    print(f"   - Chủ đề đã học: {len(ai.knowledge['topics'])}")
    
    while True:
        print("\n" + "-"*40)
        print("1. 🤖 AI tự học")
        print("2. 💬 Hỏi AI (dùng kiến thức đã học)")
        print("3. 🔍 Học chủ đề mới")
        print("4. 📊 Xem kiến thức đã có")
        print("5. 🚪 Thoát")
        
        choice = input("\nChọn (1-5): ").strip()
        
        if choice == '1':
            print("\n🤖 Bắt đầu tự học...")
            learned = ai.auto_learn(2)
            print(f"\n✅ Đã học {learned} thông tin mới!")
            
        elif choice == '2':
            question = input("\n❓ Câu hỏi của bạn: ").strip()
            if question:
                answer = ai.ask_question(question)
                print(f"\n🤖 {answer}")
            else:
                print("Vui lòng nhập câu hỏi!")
                
        elif choice == '3':
            topic = input("\n📚 Nhập chủ đề muốn học: ").strip()
            if topic:
                print(f"\nĐang học về '{topic}'...")
                results, success = ai.search_google(topic)
                if success:
                    ai.learn_from_search(topic, results)
                    ai.save_knowledge()
                    print("\n✅ Học xong! Bạn có thể hỏi AI về chủ đề này.")
                else:
                    print("❌ Không thể học chủ đề này lúc này.")
            else:
                print("Vui lòng nhập chủ đề!")
                
        elif choice == '4':
            print("\n📚 KIẾN THỨC ĐÃ HỌC:")
            if not ai.knowledge["topics"]:
                print("   Chưa có kiến thức nào. Hãy chọn 'Tự học' hoặc 'Học chủ đề mới'!")
            else:
                for topic, data in ai.knowledge["topics"].items():
                    info_count = len(data["information"])
                    print(f"\n📖 {topic.title()}:")
                    print(f"   - Số thông tin: {info_count}")
                    if data["information"]:
                        print(f"   - Gần đây: {data['information'][-1]['title'][:60]}...")
                        
        elif choice == '5':
            print("\n👋 Tạm biệt! Đã lưu kiến thức!")
            ai.save_knowledge()
            break
        else:
            print("Chọn không hợp lệ!")

if __name__ == "__main__":
    main()
