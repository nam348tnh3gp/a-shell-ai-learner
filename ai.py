#!/usr/bin/env python3
"""
AI TỰ HỌC TOÀN DIỆN - Đọc nội dung từ link
Tìm kiếm Google -> Lấy link -> Truy cập link -> Đọc nội dung -> Học
"""

import json
import os
import time
import random
import re
from datetime import datetime

try:
    import requests
    from urllib.parse import quote_plus, urljoin, urlparse
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️ Cần cài: pip install requests beautifulsoup4")

KNOWLEDGE_FILE = "ai_brain_deep.json"

class DeepAI:
    def __init__(self):
        if not HAS_BS4:
            raise Exception("Chưa cài thư viện! Chạy: pip install requests beautifulsoup4")
        
        self.brain = self.load_brain()
        self.session = self.create_session()
        
    def create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        return session
    
    def load_brain(self):
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.init_brain()
        return self.init_brain()
    
    def init_brain(self):
        return {
            "topics": {},
            "learned_links": [],
            "stats": {
                "total_learned": 0,
                "pages_visited": 0,
                "total_searches": 0
            }
        }
    
    def save_brain(self):
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.brain, f, indent=2, ensure_ascii=False)
        print("💾 Đã lưu kiến thức!")
    
    def search_google(self, query, num_results=3):
        """Tìm kiếm Google và lấy danh sách link"""
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"
            
            print(f"🔍 Tìm kiếm: '{query}'...")
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"⚠️ Lỗi HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            # Tìm tất cả link trong kết quả tìm kiếm
            for result in soup.find_all('a'):
                href = result.get('href', '')
                # Link Google có dạng /url?q=...
                if '/url?q=' in href and 'http' in href:
                    # Trích xuất URL thực
                    match = re.search(r'/url\?q=(https?://[^&]+)', href)
                    if match:
                        real_url = match.group(1)
                        # Lấy title từ thẻ h3 gần đó
                        title_tag = result.find_previous('h3')
                        title = title_tag.get_text() if title_tag else "Không có tiêu đề"
                        
                        # Bỏ qua các link không mong muốn
                        if not any(x in real_url for x in ['google.com/setprefs', 'accounts.google', 'support.google']):
                            links.append({
                                'url': real_url,
                                'title': title[:150]
                            })
            
            # Lấy link đầu tiên (thường là kết quả chính)
            links = links[:num_results]
            print(f"✅ Tìm thấy {len(links)} link")
            
            for link in links:
                print(f"   📎 {link['title'][:50]}...")
                print(f"      {link['url'][:80]}...")
            
            return links
            
        except Exception as e:
            print(f"❌ Lỗi tìm kiếm: {e}")
            return []
    
    def read_page_content(self, url, topic):
        """Đọc nội dung từ một URL"""
        try:
            print(f"\n📖 Đang đọc: {url[:80]}...")
            
            response = self.session.get(url, timeout=20)
            
            if response.status_code != 200:
                print(f"   ⚠️ Không thể đọc: HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Xóa các thẻ không cần thiết
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            # Lấy nội dung chính
            content = ""
            
            # Ưu tiên các thẻ chứa nội dung chính
            main_tags = soup.find_all(['article', 'main', 'div', 'section'], 
                                       class_=re.compile(r'(content|post|article|entry|main|body)', re.I))
            
            if main_tags:
                for tag in main_tags[:2]:
                    text = tag.get_text(separator=' ', strip=True)
                    if len(text) > len(content):
                        content = text
            else:
                # Fallback: lấy body
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
            
            # Làm sạch nội dung
            content = re.sub(r'\s+', ' ', content)
            content = content[:3000]  # Giới hạn 3000 ký tự
            
            # Trích xuất đoạn liên quan đến topic
            sentences = re.split(r'[.!?]+', content)
            relevant_sentences = []
            
            topic_words = set(topic.lower().split())
            for sentence in sentences:
                sentence_lower = sentence.lower()
                # Kiểm tra câu có chứa từ khóa không
                if any(word in sentence_lower for word in topic_words):
                    sentence = sentence.strip()
                    if len(sentence) > 50 and len(sentence) < 500:
                        relevant_sentences.append(sentence)
            
            if not relevant_sentences:
                # Lấy các câu đầu tiên nếu không tìm thấy
                for sentence in sentences[:5]:
                    sentence = sentence.strip()
                    if len(sentence) > 50:
                        relevant_sentences.append(sentence)
            
            print(f"   ✅ Đã đọc {len(content)} ký tự, trích xuất {len(relevant_sentences)} câu liên quan")
            
            return {
                'title': soup.title.get_text()[:200] if soup.title else "Không có tiêu đề",
                'content': content[:2000],
                'sentences': relevant_sentences[:10],
                'url': url,
                'read_at': time.time()
            }
            
        except Exception as e:
            print(f"   ❌ Lỗi đọc trang: {e}")
            return None
    
    def learn_from_page(self, page_data, topic):
        """Học từ nội dung trang đã đọc"""
        if not page_data:
            return 0
        
        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = {
                "learned_at": time.time(),
                "sources": [],
                "knowledge": [],
                "times_learned": 0
            }
        
        topic_data = self.brain["topics"][topic]
        topic_data["times_learned"] += 1
        
        # Tránh học lại cùng một link
        if page_data['url'] in self.brain["learned_links"]:
            print(f"   ⏭️ Đã học link này rồi, bỏ qua")
            return 0
        
        self.brain["learned_links"].append(page_data['url'])
        
        # Lưu nguồn
        topic_data["sources"].append({
            'url': page_data['url'],
            'title': page_data['title'],
            'read_at': page_data['read_at']
        })
        
        # Học từ các câu
        new_count = 0
        for sentence in page_data['sentences']:
            # Kiểm tra trùng lặp
            is_duplicate = False
            for existing in topic_data["knowledge"]:
                if existing['sentence'] == sentence:
                    is_duplicate = True
                    break
            
            if not is_duplicate and len(sentence) > 30:
                topic_data["knowledge"].append({
                    'sentence': sentence,
                    'source': page_data['url'],
                    'learned_at': time.time()
                })
                new_count += 1
        
        self.brain["stats"]["total_learned"] += new_count
        self.brain["stats"]["pages_visited"] += 1
        
        print(f"   📚 Học được {new_count} kiến thức mới từ trang này")
        
        return new_count
    
    def learn_topic_deep(self, topic):
        """Học sâu một chủ đề: tìm kiếm -> đọc link -> học"""
        print(f"\n{'='*60}")
        print(f"🎓 HỌC SÂU CHỦ ĐỀ: {topic.upper()}")
        print(f"{'='*60}")
        
        # Bước 1: Tìm kiếm Google lấy link
        links = self.search_google(topic, num_results=3)
        
        if not links:
            print("⚠️ Không tìm thấy link nào, dùng dữ liệu mẫu")
            return self.use_mock_data(topic)
        
        # Bước 2: Đọc từng link
        total_learned = 0
        for i, link in enumerate(links, 1):
            print(f"\n--- Đọc link {i}/{len(links)} ---")
            
            # Đọc nội dung
            page_data = self.read_page_content(link['url'], topic)
            
            # Học từ nội dung
            learned = self.learn_from_page(page_data, topic)
            total_learned += learned
            
            # Chờ một chút để tránh bị chặn
            time.sleep(1)
        
        # Bước 3: Tổng kết
        self.brain["stats"]["total_searches"] += 1
        self.save_brain()
        
        print(f"\n{'='*60}")
        print(f"✅ KẾT QUẢ HỌC TẬP:")
        print(f"   - Chủ đề: {topic}")
        print(f"   - Số link đã đọc: {len(links)}")
        print(f"   - Kiến thức mới: {total_learned}")
        print(f"   - Tổng kiến thức về '{topic}': {len(self.brain['topics'].get(topic, {}).get('knowledge', []))}")
        print(f"{'='*60}")
        
        return total_learned > 0
    
    def use_mock_data(self, topic):
        """Dùng dữ liệu mẫu khi không thể truy cập internet"""
        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = {
                "learned_at": time.time(),
                "sources": [],
                "knowledge": [],
                "times_learned": 0
            }
        
        topic_data = self.brain["topics"][topic]
        
        mock_knowledge = {
            "python": [
                "Python là ngôn ngữ lập trình bậc cao, được tạo bởi Guido van Rossum.",
                "Python có cú pháp đơn giản, dễ đọc, phù hợp cho người mới học.",
                "Python được dùng nhiều trong AI, Machine Learning, Data Science.",
                "Các thư viện Python phổ biến: NumPy, Pandas, TensorFlow, PyTorch."
            ],
            "machine learning": [
                "Machine Learning là nhánh của AI cho phép máy học từ dữ liệu.",
                "Có 3 loại học chính: Supervised, Unsupervised, Reinforcement Learning.",
                "Scikit-learn là thư viện ML phổ biến nhất cho Python."
            ],
            "ai": [
                "AI (Artificial Intelligence) là trí tuệ nhân tạo.",
                "AI bao gồm Machine Learning, Deep Learning, NLP, Computer Vision."
            ]
        }
        
        topic_lower = topic.lower()
        knowledge_list = []
        
        for key, items in mock_knowledge.items():
            if key in topic_lower or topic_lower in key:
                knowledge_list = items
                break
        
        if not knowledge_list:
            knowledge_list = [
                f"{topic} là một chủ đề quan trọng trong công nghệ thông tin.",
                f"Học {topic} giúp phát triển kỹ năng lập trình và tư duy logic.",
                f"Có nhiều tài liệu và khóa học trực tuyến về {topic}."
            ]
        
        new_count = 0
        for knowledge in knowledge_list:
            is_duplicate = False
            for existing in topic_data["knowledge"]:
                if existing['sentence'] == knowledge:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                topic_data["knowledge"].append({
                    'sentence': knowledge,
                    'source': 'mock_data',
                    'learned_at': time.time()
                })
                new_count += 1
        
        self.brain["stats"]["total_learned"] += new_count
        self.save_brain()
        
        print(f"📚 Đã học {new_count} kiến thức mẫu về '{topic}'")
        return new_count > 0
    
    def ask(self, question):
        """Trả lời câu hỏi dựa trên kiến thức đã học"""
        print(f"\n🤔 Suy nghĩ về: '{question}'...")
        
        question_lower = question.lower()
        
        # Tìm chủ đề liên quan
        best_topic = None
        best_score = 0
        best_knowledge = []
        
        for topic, data in self.brain["topics"].items():
            score = 0
            relevant_knowledge = []
            
            for knowledge in data["knowledge"]:
                sentence = knowledge['sentence'].lower()
                # Tính điểm liên quan
                for word in question_lower.split():
                    if len(word) < 3:
                        continue
                    if word in sentence:
                        score += 2
                    if word in topic.lower():
                        score += 3
                
                if score > 0:
                    relevant_knowledge.append(knowledge)
            
            if score > best_score:
                best_score = score
                best_topic = topic
                best_knowledge = relevant_knowledge
        
        if not best_topic or best_score < 2:
            return f"🤔 Tôi chưa có kiến thức về '{question}'. Hãy chọn 'Học sâu chủ đề' để tôi tìm hiểu!"
        
        # Xây dựng câu trả lời
        answer = f"📖 **Về {best_topic.title()}:**\n\n"
        
        for i, knowledge in enumerate(best_knowledge[:5], 1):
            answer += f"{i}. {knowledge['sentence']}\n\n"
        
        answer += f"💡 *Tôi đã học từ {len(self.brain['topics'][best_topic]['sources'])} nguồn khác nhau.*"
        
        return answer
    
    def show_knowledge(self):
        """Hiển thị kiến thức đã học"""
        print("\n" + "="*60)
        print("📚 KHO KIẾN THỨC CỦA AI")
        print("="*60)
        
        if not self.brain["topics"]:
            print("\nChưa có kiến thức nào! Hãy chọn 'Học sâu chủ đề'")
            return
        
        for topic, data in self.brain["topics"].items():
            print(f"\n🔹 {topic.upper()}")
            print(f"   📝 Số kiến thức: {len(data['knowledge'])}")
            print(f"   🔗 Số nguồn: {len(data['sources'])}")
            print(f"   🔄 Số lần học: {data['times_learned']}")
            
            if data["knowledge"]:
                print(f"\n   📖 Kiến thức đã học:")
                for i, k in enumerate(data["knowledge"][:3], 1):
                    preview = k['sentence'][:100] + "..." if len(k['sentence']) > 100 else k['sentence']
                    print(f"      {i}. {preview}")
    
    def auto_learn_suggestions(self):
        """Đề xuất chủ đề để học"""
        suggestions = [
            "python programming", "machine learning", "artificial intelligence",
            "deep learning", "data science", "neural networks",
            "natural language processing", "computer vision"
        ]
        
        for topic in suggestions:
            if topic not in self.brain["topics"] or len(self.brain["topics"][topic]["knowledge"]) < 5:
                return topic
        
        return random.choice(suggestions)

def main():
    print("="*60)
    print("🤖 AI TỰ HỌC - ĐỌC NỘI DUNG TỪ LINK")
    print("="*60)
    print("\nCách hoạt động:")
    print("1. Tìm kiếm Google → Lấy link kết quả")
    print("2. Truy cập vào từng link")
    print("3. Đọc và trích xuất nội dung")
    print("4. Học và ghi nhớ kiến thức")
    print("="*60)
    
    if not HAS_BS4:
        print("\n❌ THIẾU THƯ VIỆN!")
        print("📦 Chạy lệnh: pip install requests beautifulsoup4")
        return
    
    try:
        ai = DeepAI()
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return
    
    print(f"\n📊 Thống kê hiện tại:")
    print(f"   - Kiến thức: {ai.brain['stats']['total_learned']}")
    print(f"   - Trang đã đọc: {ai.brain['stats']['pages_visited']}")
    print(f"   - Chủ đề: {len(ai.brain['topics'])}")
    
    while True:
        print("\n" + "-*"*30)
        print("\n🎯 MENU:")
        print("   1. 🔍 Học sâu chủ đề (tìm + đọc link)")
        print("   2. 🤖 AI tự đề xuất và học")
        print("   3. 💬 Hỏi AI")
        print("   4. 📊 Xem kiến thức")
        print("   5. 🚪 Thoát")
        
        choice = input("\n👉 Chọn (1-5): ").strip()
        
        if choice == '1':
            topic = input("\n📚 Nhập chủ đề: ").strip()
            if topic:
                ai.learn_topic_deep(topic)
            else:
                print("❌ Vui lòng nhập chủ đề!")
                
        elif choice == '2':
            topic = ai.auto_learn_suggestions()
            print(f"\n🤖 AI đề xuất học: {topic}")
            ai.learn_topic_deep(topic)
            
        elif choice == '3':
            question = input("\n❓ Câu hỏi: ").strip()
            if question:
                answer = ai.ask(question)
                print(f"\n{answer}")
            else:
                print("❌ Vui lòng nhập câu hỏi!")
                
        elif choice == '4':
            ai.show_knowledge()
            
        elif choice == '5':
            print("\n👋 Tạm biệt! Đang lưu...")
            ai.save_brain()
            print("✅ Đã lưu!")
            break
        else:
            print("❌ Chọn không hợp lệ!")

if __name__ == "__main__":
    main()
