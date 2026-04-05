#!/usr/bin/env python3
"""
AI TỰ HỌC - Google Search + DuckDuckGo Fallback
Fix lỗi bị chặn, tự động chuyển sang công cụ tìm kiếm dự phòng
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

# Danh sách User-Agent để luân phiên
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
]

class GoogleAI:
    def __init__(self):
        if not HAS_LIBS:
            raise Exception("Chưa cài thư viện! Chạy: pip install requests beautifulsoup4")
        
        self.brain = self.load_brain()
        self.session = self.create_session()
        
    def create_session(self):
        session = requests.Session()
        # Chọn User-Agent ngẫu nhiên
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        # Thêm cookie giả lập (quan trọng để qua mặt Google)
        session.cookies.set('CONSENT', 'YES+cb', domain='.google.com')
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
    
    def search_duckduckgo(self, query):
        """Tìm kiếm bằng DuckDuckGo (ít bị chặn hơn)"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            print(f"🦆 Tìm DuckDuckGo: '{query}'")
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            # DuckDuckGo HTML: kết quả nằm trong class="result__a" hoặc "result__url"
            for result in soup.find_all('a', class_='result__a'):
                title = result.get_text(strip=True)
                href = result.get('href')
                if href and href.startswith('/l/?uddg='):
                    # Giải mã URL thực
                    match = re.search(r'/l/\?uddg=(https?://[^&]+)', href)
                    if match:
                        real_url = urllib.parse.unquote(match.group(1))
                        if real_url and not any(x in real_url for x in ['duckduckgo.com']):
                            links.append({'url': real_url, 'title': title[:150]})
                            if len(links) >= 3:
                                break
            
            # Fallback: tìm tất cả link có chữ "result"
            if not links:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('/l/?uddg='):
                        match = re.search(r'/l/\?uddg=(https?://[^&]+)', href)
                        if match:
                            real_url = urllib.parse.unquote(match.group(1))
                            title = a.get_text(strip=True)
                            if title and len(title) > 5:
                                links.append({'url': real_url, 'title': title[:150]})
                                if len(links) >= 3:
                                    break
            
            print(f"✅ DuckDuckGo tìm thấy {len(links)} link")
            return links
        except Exception as e:
            print(f"❌ Lỗi DuckDuckGo: {e}")
            return []
    
    def search_google(self, query):
        """Tìm kiếm Google - có xử lý chặn và luân phiên User-Agent"""
        max_tries = 2
        for attempt in range(max_tries):
            try:
                # Đổi User-Agent mỗi lần thử
                self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
                encoded_query = urllib.parse.quote(query)
                url = f"https://www.google.com/search?q={encoded_query}&num=5&hl=en&gl=us"
                
                print(f"🔍 Tìm Google (lần {attempt+1}): '{query}'")
                response = self.session.get(url, timeout=20)
                
                if response.status_code != 200:
                    print(f"⚠️ HTTP {response.status_code}")
                    continue
                
                html = response.text
                
                # Kiểm tra bị chặn
                if 'captcha' in html.lower() or 'unusual traffic' in html.lower() or 'Our systems have detected' in html:
                    print("⚠️ Google chặn request, thử lại với User-Agent khác...")
                    time.sleep(2)
                    continue
                
                links = []
                soup = BeautifulSoup(html, 'html.parser')
                
                # Cách 1: Tìm div class="g" hoặc "tF2Cxc"
                for result in soup.find_all(['div'], class_=lambda c: c and ('g' in c or 'tF2Cxc' in c)):
                    title_tag = result.find('h3')
                    if not title_tag:
                        continue
                    title = title_tag.get_text(strip=True)
                    link_tag = result.find('a', href=True)
                    if not link_tag:
                        continue
                    href = link_tag['href']
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
                    
                    if any(x in real_url for x in ['google.com', 'youtube.com', 'facebook.com', 'twitter.com']):
                        continue
                    
                    links.append({'url': real_url, 'title': title[:150]})
                    if len(links) >= 3:
                        break
                
                # Cách 2: fallback
                if not links:
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if '/url?q=' in href:
                            match = re.search(r'/url\?q=(https?://[^&]+)', href)
                            if match:
                                real_url = match.group(1)
                                title = a.get_text(strip=True)
                                if not title or len(title) < 5:
                                    parent = a.find_parent()
                                    if parent:
                                        h3 = parent.find('h3')
                                        if h3:
                                            title = h3.get_text(strip=True)
                                if title and len(title) > 5 and not any(x in real_url for x in ['google.com', 'youtube.com']):
                                    links.append({'url': real_url, 'title': title[:150]})
                                    if len(links) >= 3:
                                        break
                
                if links:
                    print(f"✅ Google tìm thấy {len(links)} link")
                    return links
                else:
                    print("⚠️ Google không trả về link nào, thử lại...")
                    continue
                
            except requests.exceptions.Timeout:
                print("❌ Timeout khi tìm Google")
                continue
            except Exception as e:
                print(f"❌ Lỗi Google: {e}")
                continue
        
        # Hết lần thử, fallback sang DuckDuckGo
        print("🔄 Google thất bại, chuyển sang DuckDuckGo...")
        return self.search_duckduckgo(query)
    
    def read_page(self, url, topic):
        """Đọc nội dung trang web"""
        try:
            print(f"\n📖 Đọc: {url[:70]}...")
            # Đổi User-Agent trước khi đọc trang
            self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"   ⚠️ HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Xóa thẻ không cần thiết
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'meta', 'link', 'iframe']):
                tag.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            text = text[:5000]
            
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
        """Học chủ đề từ Google (hoặc DuckDuckGo nếu Google lỗi)"""
        print(f"\n{'='*60}")
        print(f"🎓 HỌC TỪ GOOGLE: {topic.upper()}")
        print(f"{'='*60}")
        
        links = self.search_google(topic)  # đã có fallback DuckDuckGo bên trong
        
        if not links:
            print("\n⚠️ Không tìm thấy link từ cả Google và DuckDuckGo, dùng dữ liệu mẫu")
            return self.use_mock(topic)
        
        total = 0
        for i, link in enumerate(links, 1):
            print(f"\n--- Link {i}/{len(links)} ---")
            page = self.read_page(link['url'], topic)
            learned = self.learn_from_page(page, topic)
            total += learned
            time.sleep(random.uniform(1.5, 3.0))
        
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
        """Dữ liệu mẫu (giữ nguyên như cũ)"""
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
        """Trả lời câu hỏi (giữ nguyên)"""
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
        """Hiển thị thống kê (giữ nguyên)"""
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
        suggestions = ["python programming", "machine learning", "artificial intelligence", 
                      "deep learning", "data science", "neural networks", "computer vision"]
        for topic in suggestions:
            if topic not in self.brain["topics"] or len(self.brain["topics"][topic]["knowledge"]) < 3:
                return topic
        return random.choice(suggestions)

def main():
    print("="*60)
    print("🤖 AI TỰ HỌC - GOOGLE + DUCKDUCKGO")
    print("="*60)
    print("\n✨ Tính năng:")
    print("   • Tìm kiếm Google (tự động fallback DuckDuckGo nếu bị chặn)")
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
