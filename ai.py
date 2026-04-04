#!/usr/bin/env python3
"""
AI TỰ HỌC - Google Search với encode đúng
Fix lỗi encode URL và parse kết quả Google
"""

import json
import os
import time
import re
import random
import urllib.parse

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False
    print("⚠️ Cần cài: pip install requests beautifulsoup4")

KNOWLEDGE_FILE = "ai_brain_google.json"

class GoogleAI:
    def __init__(self):
        if not HAS_LIBS:
            raise Exception("Chưa cài thư viện! Chạy: pip install requests beautifulsoup4")
        
        self.brain = self.load_brain()
        self.session = self.create_session()
        
    def create_session(self):
        session = requests.Session()
        # Headers giống trình duyệt thật
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
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
            "learned_urls": [],
            "stats": {
                "total_learned": 0,
                "pages_read": 0,
                "searches": 0
            }
        }
    
    def save_brain(self):
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.brain, f, indent=2, ensure_ascii=False)
        print("💾 Đã lưu!")
    
    def search_google(self, query):
        """Tìm kiếm Google - FIX encode"""
        try:
            # CÁCH 1: Dùng encode đơn giản
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded_query}&num=5"
            
            print(f"🔍 Tìm Google: '{query}'")
            print(f"📎 URL: {url[:100]}...")
            
            # Gửi request với timeout
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"⚠️ HTTP {response.status_code}")
                return []
            
            html = response.text
            
            # Kiểm tra bị chặn
            if 'captcha' in html.lower() or 'unusual traffic' in html.lower():
                print("⚠️ Google chặn request, thử lại sau...")
                return []
            
            links = []
            soup = BeautifulSoup(html, 'html.parser')
            
            # Cách 1: Tìm tất cả thẻ a
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # Tìm link kết quả tìm kiếm
                if '/url?q=' in href and 'http' in href:
                    # Trích xuất URL thực
                    match = re.search(r'/url\?q=(https?://[^&]+)', href)
                    if match:
                        real_url = match.group(1)
                        
                        # Lấy tiêu đề từ thẻ h3 hoặc chính thẻ a
                        title = a.get_text(strip=True)
                        if not title or len(title) < 5:
                            # Tìm h3 gần đó
                            h3 = a.find_previous('h3')
                            if h3:
                                title = h3.get_text(strip=True)
                        
                        # Lọc link hợp lệ
                        if title and len(title) > 5:
                            if not any(x in real_url for x in ['google.com', 'youtube.com', 'facebook.com']):
                                links.append({
                                    'url': real_url,
                                    'title': title[:150]
                                })
            
            # Cách 2: Tìm bằng class="g"
            if not links:
                for result in soup.find_all('div', class_='g'):
                    title_tag = result.find('h3')
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        link_tag = result.find('a')
                        if link_tag and link_tag.get('href'):
                            href = link_tag['href']
                            if '/url?q=' in href:
                                match = re.search(r'/url\?q=(https?://[^&]+)', href)
                                if match:
                                    links.append({
                                        'url': match.group(1),
                                        'title': title[:150]
                                    })
            
            # Giới hạn 3 kết quả đầu
            links = links[:3]
            
            print(f"✅ Tìm thấy {len(links)} link")
            for link in links:
                print(f"   📎 {link['title'][:60]}...")
            
            return links
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return []
    
    def read_page(self, url, topic):
        """Đọc nội dung trang web"""
        try:
            print(f"\n📖 Đọc: {url[:70]}...")
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"   ⚠️ HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Xóa thẻ không cần thiết
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'meta', 'link', 'iframe']):
                tag.decompose()
            
            # Lấy nội dung text
            text = soup.get_text(separator=' ', strip=True)
            
            # Làm sạch
            text = re.sub(r'\s+', ' ', text)
            text = text[:5000]
            
            # Trích xuất câu liên quan
            sentences = re.split(r'[.!?]+', text)
            relevant = []
            
            topic_words = topic.lower().split()
            for sent in sentences:
                sent = sent.strip()
                if len(sent) < 40 or len(sent) > 500:
                    continue
                
                sent_lower = sent.lower()
                if any(word in sent_lower for word in topic_words[:3]):
                    relevant.append(sent)
                
                if len(relevant) >= 8:
                    break
            
            if not relevant and sentences:
                for sent in sentences[:5]:
                    sent = sent.strip()
                    if 40 < len(sent) < 500:
                        relevant.append(sent)
            
            title = soup.title.string if soup.title else url[:50]
            
            print(f"   ✅ Đọc {len(text)} ký tự, lấy {len(relevant)} câu")
            
            return {
                'title': title[:150],
                'url': url,
                'sentences': relevant,
                'read_at': time.time()
            }
            
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            return None
    
    def learn_from_page(self, page_data, topic):
        """Học từ nội dung trang"""
        if not page_data or not page_data['sentences']:
            return 0
        
        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = {
                "learned_at": time.time(),
                "sources": [],
                "knowledge": [],
                "times": 0
            }
        
        topic_data = self.brain["topics"][topic]
        topic_data["times"] += 1
        
        if page_data['url'] in self.brain["learned_urls"]:
            print(f"   ⏭️ Đã học URL này")
            return 0
        
        self.brain["learned_urls"].append(page_data['url'])
        
        topic_data["sources"].append({
            'url': page_data['url'],
            'title': page_data['title'],
            'read_at': page_data['read_at']
        })
        
        new_count = 0
        for sentence in page_data['sentences']:
            is_dup = False
            for existing in topic_data["knowledge"]:
                if existing['sentence'] == sentence:
                    is_dup = True
                    break
            
            if not is_dup and len(sentence) > 30:
                topic_data["knowledge"].append({
                    'sentence': sentence,
                    'source': page_data['url'],
                    'learned_at': time.time()
                })
                new_count += 1
        
        self.brain["stats"]["total_learned"] += new_count
        self.brain["stats"]["pages_read"] += 1
        
        print(f"   📚 Học {new_count} kiến thức mới")
        return new_count
    
    def learn_topic(self, topic):
        """Học chủ đề từ Google"""
        print(f"\n{'='*60}")
        print(f"🎓 HỌC TỪ GOOGLE: {topic.upper()}")
        print(f"{'='*60}")
        
        # Tìm kiếm
        links = self.search_google(topic)
        
        if not links:
            print("\n⚠️ Không tìm thấy link, dùng dữ liệu mẫu")
            return self.use_mock(topic)
        
        # Đọc từng link
        total = 0
        for i, link in enumerate(links, 1):
            print(f"\n--- Link {i}/{len(links)} ---")
            page = self.read_page(link['url'], topic)
            learned = self.learn_from_page(page, topic)
            total += learned
            time.sleep(1.5)  # Tránh bị chặn
        
        self.brain["stats"]["searches"] += 1
        self.save_brain()
        
        print(f"\n{'='*60}")
        print(f"✅ KẾT QUẢ:")
        print(f"   - Link đã đọc: {len(links)}")
        print(f"   - Kiến thức mới: {total}")
        info_count = len(self.brain['topics'].get(topic, {}).get('knowledge', []))
        print(f"   - Tổng kiến thức: {info_count}")
        print(f"{'='*60}")
        
        return total > 0
    
    def use_mock(self, topic):
        """Dữ liệu mẫu phong phú"""
        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = {
                "learned_at": time.time(),
                "sources": [],
                "knowledge": [],
                "times": 0
            }
        
        topic_data = self.brain["topics"][topic]
        
        mock_db = {
            "python": [
                "Python là ngôn ngữ lập trình bậc cao, được tạo bởi Guido van Rossum năm 1991.",
                "Python có cú pháp đơn giản, dễ đọc, phù hợp cho người mới bắt đầu học lập trình.",
                "Python được sử dụng rộng rãi trong AI, Machine Learning, Data Science, Web Development.",
                "Các thư viện Python phổ biến: NumPy, Pandas, TensorFlow, PyTorch, Django, Flask.",
                "Python chạy trên nhiều nền tảng: Windows, macOS, Linux, iOS, Android."
            ],
            "machine learning": [
                "Machine Learning là nhánh của AI cho phép máy học từ dữ liệu mà không cần lập trình rõ ràng.",
                "Có 3 loại Machine Learning: Supervised Learning, Unsupervised Learning, Reinforcement Learning.",
                "Scikit-learn là thư viện Machine Learning phổ biến nhất cho Python.",
                "Machine Learning được ứng dụng trong nhận diện ảnh, xử lý ngôn ngữ tự nhiên, dự đoán."
            ],
            "artificial intelligence": [
                "AI (Artificial Intelligence) là trí tuệ nhân tạo, mô phỏng trí thông minh con người.",
                "AI bao gồm nhiều lĩnh vực: Machine Learning, Deep Learning, NLP, Computer Vision, Robotics.",
                "Alan Turing là cha đẻ của AI với Turing Test năm 1950."
            ],
            "deep learning": [
                "Deep Learning là nhánh của Machine Learning sử dụng mạng neural nhiều lớp.",
                "Deep Learning đạt thành tựu lớn trong nhận diện ảnh, xử lý ngôn ngữ tự nhiên.",
                "Các framework Deep Learning phổ biến: TensorFlow, PyTorch, Keras."
            ],
            "data science": [
                "Data Science là lĩnh vực khai thác tri thức từ dữ liệu.",
                "Data Science kết hợp thống kê, toán học, lập trình và kiến thức chuyên ngành.",
                "Quy trình Data Science: Thu thập -> Làm sạch -> Phân tích -> Mô hình -> Triển khai."
            ]
        }
        
        topic_lower = topic.lower()
        knowledge_list = []
        
        for key, items in mock_db.items():
            if key in topic_lower or topic_lower in key:
                knowledge_list = items
                break
        
        if not knowledge_list:
            knowledge_list = [
                f"{topic} là một chủ đề quan trọng trong công nghệ thông tin.",
                f"Học {topic} giúp phát triển tư duy logic và kỹ năng lập trình.",
                f"Có nhiều tài liệu và khóa học trực tuyến miễn phí về {topic}.",
                f"{topic} được ứng dụng rộng rãi trong nhiều lĩnh vực."
            ]
        
        new_count = 0
        for knowledge in knowledge_list:
            is_dup = False
            for existing in topic_data["knowledge"]:
                if existing['sentence'] == knowledge:
                    is_dup = True
                    break
            
            if not is_dup:
                topic_data["knowledge"].append({
                    'sentence': knowledge,
                    'source': 'mock_data',
                    'learned_at': time.time()
                })
                new_count += 1
        
        self.brain["stats"]["total_learned"] += new_count
        self.save_brain()
        
        print(f"📚 Học {new_count} kiến thức mẫu về '{topic}'")
        return new_count > 0
    
    def ask(self, question):
        """Trả lời câu hỏi"""
        print(f"\n🤔 Suy nghĩ...")
        
        question_lower = question.lower()
        
        best_topic = None
        best_score = 0
        best_knowledge = []
        
        for topic, data in self.brain["topics"].items():
            score = 0
            relevant = []
            
            for knowledge in data["knowledge"]:
                sentence = knowledge['sentence'].lower()
                for word in question_lower.split():
                    if len(word) < 3:
                        continue
                    if word in sentence:
                        score += 2
                        relevant.append(knowledge)
                    if word in topic.lower():
                        score += 3
            
            if score > best_score:
                best_score = score
                best_topic = topic
                best_knowledge = relevant[:5]
        
        if not best_topic or best_score < 2:
            return f"🤔 Tôi chưa có kiến thức về '{question}'. Hãy chọn 'Học chủ đề' để tôi tìm hiểu!"
        
        answer = f"📖 **Về {best_topic.title()}:**\n\n"
        for i, k in enumerate(best_knowledge[:5], 1):
            answer += f"{i}. {k['sentence']}\n\n"
        
        return answer
    
    def show_stats(self):
        """Hiển thị thống kê"""
        print("\n" + "="*50)
        print("📊 THỐNG KÊ")
        print("="*50)
        
        print(f"\n📈 Tổng quan:")
        print(f"   - Kiến thức: {self.brain['stats']['total_learned']}")
        print(f"   - Trang đã đọc: {self.brain['stats']['pages_read']}")
        print(f"   - Chủ đề: {len(self.brain['topics'])}")
        
        print(f"\n📚 Chủ đề đã học:")
        for topic, data in self.brain["topics"].items():
            print(f"   🔹 {topic[:30]}: {len(data['knowledge'])} kiến thức")
            if data['sources']:
                print(f"      📖 Từ {len(data['sources'])} nguồn")
    
    def suggest_topic(self):
        """Đề xuất chủ đề"""
        suggestions = ["python programming", "machine learning", "artificial intelligence", 
                      "deep learning", "data science", "neural networks", "computer vision"]
        
        for topic in suggestions:
            if topic not in self.brain["topics"] or len(self.brain["topics"][topic]["knowledge"]) < 3:
                return topic
        return random.choice(suggestions)

def main():
    print("="*60)
    print("🤖 AI TỰ HỌC - GOOGLE SEARCH")
    print("="*60)
    print("\n✨ Tính năng:")
    print("   • Tìm kiếm Google thực tế")
    print("   • Đọc nội dung từ link kết quả")
    print("   • Học và ghi nhớ kiến thức")
    print("="*60)
    
    if not HAS_LIBS:
        print("\n❌ Cài thư viện: pip install requests beautifulsoup4")
        return
    
    try:
        ai = GoogleAI()
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return
    
    print(f"\n📊 Hiện tại: {ai.brain['stats']['total_learned']} kiến thức, {len(ai.brain['topics'])} chủ đề")
    
    while True:
        print("\n" + "-"*40)
        print("🎯 MENU:")
        print("   1. 🔍 Học chủ đề mới (Google)")
        print("   2. 🤖 AI tự đề xuất và học")
        print("   3. 💬 Hỏi AI")
        print("   4. 📊 Xem kiến thức")
        print("   5. 🚪 Thoát")
        
        choice = input("\n👉 Chọn (1-5): ").strip()
        
        if choice == '1':
            topic = input("📚 Nhập chủ đề (VD: python, machine learning): ").strip()
            if topic:
                ai.learn_topic(topic)
            else:
                print("❌ Nhập chủ đề!")
                
        elif choice == '2':
            topic = ai.suggest_topic()
            print(f"\n🤖 AI chọn học: {topic}")
            ai.learn_topic(topic)
            
        elif choice == '3':
            question = input("❓ Câu hỏi: ").strip()
            if question:
                answer = ai.ask(question)
                print(f"\n{answer}")
            else:
                print("❌ Nhập câu hỏi!")
                
        elif choice == '4':
            ai.show_stats()
            
        elif choice == '5':
            print("\n👋 Tạm biệt!")
            ai.save_brain()
            break
        else:
            print("❌ Chọn 1-5!")

if __name__ == "__main__":
    main()
