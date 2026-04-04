#!/usr/bin/env python3
"""
AI TỰ HỌC TOÀN DIỆN - Phiên bản Full Fix
Hoạt động ổn định trên a-Shell mini
Chức năng: Học từ Google (hoặc dữ liệu mẫu), trả lời câu hỏi, tự cải thiện
"""

import json
import os
import time
import random
import re
from datetime import datetime

# Cố gắng import requests
try:
    import requests
    from urllib.parse import quote_plus
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️ Cần cài requests: pip install requests")

# File lưu trữ
KNOWLEDGE_FILE = "ai_brain_full.json"
CONFIG_FILE = "ai_config.json"

class FullAI:
    def __init__(self):
        if not HAS_REQUESTS:
            raise Exception("Chưa cài requests! Chạy: pip install requests")
        
        self.config = self.load_config()
        self.brain = self.load_brain()
        self.session = self.create_session()
        
    def create_session(self):
        """Tạo session với headers chống chặn"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return session
    
    def load_config(self):
        """Tải cấu hình"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.default_config()
        return self.default_config()
    
    def default_config(self):
        return {
            "use_internet": True,
            "auto_learn_interval": 0,
            "max_results": 5,
            "language": "vi",
            "version": "2.0"
        }
    
    def load_brain(self):
        """Tải bộ não AI"""
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.init_brain()
        return self.init_brain()
    
    def init_brain(self):
        """Khởi tạo bộ não với kiến thức nền tảng"""
        return {
            "topics": {
                "python": {
                    "learned_at": time.time(),
                    "info": [
                        {"title": "Python là ngôn ngữ lập trình bậc cao", 
                         "summary": "Được tạo bởi Guido van Rossum năm 1991. Cú pháp đơn giản, dễ đọc, dễ học."},
                        {"title": "Ứng dụng của Python", 
                         "summary": "Web development (Django/Flask), Data Science (Pandas/NumPy), AI/ML (TensorFlow/PyTorch), Automation."},
                        {"title": "Cài đặt Python", 
                         "summary": "Tải từ python.org, dùng pip để cài thư viện. Kiểm tra: python --version"}
                    ],
                    "times_learned": 1,
                    "keywords": ["ngôn ngữ", "lập trình", "code", "script", "thư viện"]
                },
                "machine learning": {
                    "learned_at": time.time(),
                    "info": [
                        {"title": "Machine Learning là gì?", 
                         "summary": "Nhánh của AI cho phép máy học từ dữ liệu mà không cần lập trình rõ ràng."},
                        {"title": "Các loại Machine Learning", 
                         "summary": "Supervised Learning (học có giám sát), Unsupervised Learning (không giám sát), Reinforcement Learning (học tăng cường)."},
                        {"title": "Thư viện ML phổ biến", 
                         "summary": "Scikit-learn, TensorFlow, PyTorch, Keras, XGBoost."}
                    ],
                    "times_learned": 1,
                    "keywords": ["học máy", "dữ liệu", "mô hình", "training", "AI"]
                },
                "artificial intelligence": {
                    "learned_at": time.time(),
                    "info": [
                        {"title": "AI là gì?", 
                         "summary": "Trí tuệ nhân tạo - mô phỏng trí thông minh con người bằng máy tính."},
                        {"title": "Các lĩnh vực của AI", 
                         "summary": "Machine Learning, Deep Learning, Natural Language Processing (NLP), Computer Vision, Robotics."},
                        {"title": "Lịch sử AI", 
                         "summary": "1950: Alan Turing đề xuất Turing Test. 1956: Thuật ngữ AI ra đời. 2010s: Bùng nổ Deep Learning."}
                    ],
                    "times_learned": 1,
                    "keywords": ["trí tuệ", "thông minh", "robot", "tự động", "neural"]
                },
                "deep learning": {
                    "learned_at": time.time(),
                    "info": [
                        {"title": "Deep Learning là gì?", 
                         "summary": "Nhánh của Machine Learning sử dụng mạng neural nhiều lớp (deep neural networks)."},
                        {"title": "Kiến trúc Deep Learning", 
                         "summary": "CNN (Computer Vision), RNN/LSTM (Sequence data), Transformer (NLP), GAN (Sinh dữ liệu)."},
                        {"title": "Framework Deep Learning", 
                         "summary": "TensorFlow (Google), PyTorch (Facebook), Keras (API cao cấp), JAX."}
                    ],
                    "times_learned": 1,
                    "keywords": ["neural network", "mạng nơ-ron", "tensorflow", "pytorch", "cnn"]
                },
                "data science": {
                    "learned_at": time.time(),
                    "info": [
                        {"title": "Data Science là gì?", 
                         "summary": "Khoa học dữ liệu - khai thác tri thức từ dữ liệu."},
                        {"title": "Quy trình Data Science", 
                         "summary": "Thu thập -> Làm sạch -> Khám phá -> Mô hình hóa -> Đánh giá -> Triển khai."},
                        {"title": "Thư viện Data Science Python", 
                         "summary": "Pandas (xử lý dữ liệu), NumPy (tính toán số), Matplotlib/Seaborn (trực quan hóa), Scikit-learn (ML)."}
                    ],
                    "times_learned": 1,
                    "keywords": ["dữ liệu", "phân tích", "thống kê", "pandas", "numpy"]
                }
            },
            "search_history": [],
            "conversations": [],
            "stats": {
                "total_learned": 15,  # 5 topics * 3 info
                "questions_answered": 0,
                "total_searches": 0,
                "last_activity": None
            }
        }
    
    def save_brain(self):
        """Lưu bộ não"""
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.brain, f, indent=2, ensure_ascii=False)
        print("💾 Đã lưu bộ não AI!")
    
    def save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def search_google(self, query):
        """Tìm kiếm Google thực tế"""
        try:
            encoded_query = quote_plus(query.encode('utf-8'))
            url = f"https://www.google.com/search?q={encoded_query}&num=10"
            
            print(f"🔍 Đang tìm kiếm: '{query}'...")
            start_time = time.time()
            
            response = self.session.get(url, timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                print(f"⚠️ Lỗi HTTP {response.status_code}")
                return self.get_mock_data(query)
            
            html = response.text
            
            # Kiểm tra bị chặn
            if 'captcha' in html.lower() or 'unusual traffic' in html.lower():
                print("⚠️ Google yêu cầu CAPTCHA, dùng dữ liệu mẫu")
                return self.get_mock_data(query)
            
            results = self.parse_html_results(html)
            
            if results:
                print(f"✅ Tìm thấy {len(results)} kết quả trong {response_time:.2f}s")
                return results
            else:
                print("⚠️ Không parse được, dùng dữ liệu mẫu")
                return self.get_mock_data(query)
                
        except requests.exceptions.Timeout:
            print("❌ Timeout! Dùng dữ liệu mẫu")
            return self.get_mock_data(query)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return self.get_mock_data(query)
    
    def parse_html_results(self, html):
        """Parse HTML kết quả Google"""
        results = []
        
        # Pattern cho kết quả tìm kiếm
        patterns = [
            # Pattern 1: class="g"
            r'<div class="g"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<div class="[^"]*(?:VwiC3b|IsZvec|aCOpRe)[^"]*"[^>]*>(.*?)</div>',
            # Pattern 2: đơn giản hơn
            r'<h3[^>]*>(.*?)</h3>\s*<div[^>]*>(.*?)</div>'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for match in matches[:5]:
                title = re.sub(r'<[^>]+>', '', match[0]).strip()
                snippet = re.sub(r'<[^>]+>', '', match[1] if len(match) > 1 else "").strip()
                
                if title and len(title) > 5:
                    results.append({
                        "title": title[:200],
                        "snippet": snippet[:300] if snippet else "Thông tin chi tiết về chủ đề này."
                    })
            
            if results:
                break
        
        return results
    
    def get_mock_data(self, query):
        """Dữ liệu mẫu mở rộng cho nhiều chủ đề"""
        mock_database = {
            "python": [
                {"title": "Python Tutorial - W3Schools", "snippet": "Python là ngôn ngữ lập trình dễ học, mạnh mẽ. Hướng dẫn từ cơ bản đến nâng cao."},
                {"title": "Python.org - Official Website", "snippet": "Trang chủ của Python. Tải Python, đọc tài liệu chính thức, tham gia cộng đồng."},
                {"title": "Python for Beginners - Real Python", "snippet": "Học Python qua các dự án thực tế. Biến, vòng lặp, hàm, class."},
                {"title": "Python Libraries for Data Science", "snippet": "Pandas, NumPy, Matplotlib, Scikit-learn - bộ công cụ mạnh mẽ cho Data Science."}
            ],
            "machine learning": [
                {"title": "Machine Learning Crash Course - Google", "snippet": "Khóa học ML miễn phí từ Google. Học về supervised, unsupervised learning."},
                {"title": "Scikit-learn Tutorial", "snippet": "Thư viện ML phổ biến nhất cho Python. Classification, Regression, Clustering."},
                {"title": "Machine Learning Algorithms Explained", "snippet": "Decision Trees, Random Forest, SVM, KNN, Neural Networks - giải thích đơn giản."}
            ],
            "ai": [
                {"title": "Artificial Intelligence - IBM", "snippet": "AI là gì? Lịch sử, ứng dụng và tương lai của trí tuệ nhân tạo."},
                {"title": "AI vs Machine Learning vs Deep Learning", "snippet": "Giải thích sự khác biệt giữa AI, ML và Deep Learning."}
            ],
            "deep learning": [
                {"title": "Deep Learning Book - Ian Goodfellow", "snippet": "Sách giáo khoa về Deep Learning. Mạng neural, backpropagation, optimization."},
                {"title": "Neural Networks Explained", "snippet": "Cấu trúc neural network: input layer, hidden layers, output layer. Activation functions."}
            ],
            "data science": [
                {"title": "Data Science for Beginners", "snippet": "Quy trình Data Science: Thu thập, làm sạch, phân tích, trực quan hóa dữ liệu."},
                {"title": "Pandas Tutorial", "snippet": "Xử lý dữ liệu với Pandas: DataFrame, Series, filtering, grouping, merging."}
            ]
        }
        
        query_lower = query.lower()
        
        # Tìm chủ đề phù hợp
        for key, results in mock_database.items():
            if key in query_lower or query_lower in key:
                print(f"📚 Dùng dữ liệu mẫu cho '{query}'")
                return results
        
        # Tạo kết quả động cho chủ đề mới
        return [
            {"title": f"Tổng quan về {query}", "snippet": f"Thông tin cơ bản về {query}. Đây là một chủ đề thú vị trong công nghệ."},
            {"title": f"Học {query} từ cơ bản", "snippet": f"Hướng dẫn chi tiết về {query} cho người mới bắt đầu."},
            {"title": f"Ứng dụng của {query}", "snippet": f"Các ứng dụng thực tế của {query} trong đời sống và công nghiệp."}
        ]
    
    def learn_topic(self, topic):
        """Học một chủ đề mới"""
        print(f"\n{'='*50}")
        print(f"📚 HỌC CHỦ ĐỀ: {topic.upper()}")
        print(f"{'='*50}")
        
        # Tìm kiếm
        results = self.search_google(topic)
        
        if not results:
            print("😔 Không có kết quả để học")
            return False
        
        # Tạo hoặc cập nhật topic
        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = {
                "learned_at": time.time(),
                "info": [],
                "times_learned": 0,
                "keywords": []
            }
        
        topic_data = self.brain["topics"][topic]
        topic_data["times_learned"] += 1
        
        # Học thông tin mới
        new_count = 0
        for result in results[:self.config["max_results"]]:
            # Kiểm tra trùng lặp
            is_duplicate = False
            for existing in topic_data["info"]:
                if existing["title"] == result["title"]:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                topic_data["info"].append({
                    "title": result["title"],
                    "summary": result.get("snippet", ""),
                    "learned_at": time.time()
                })
                new_count += 1
                
                # Trích xuất từ khóa
                words = result["title"].lower().split() + result.get("snippet", "").lower().split()
                keywords = [w for w in words if len(w) > 4 and w not in ['this', 'that', 'with', 'from', 'have', 'will']]
                for kw in keywords[:3]:
                    if kw not in topic_data["keywords"]:
                        topic_data["keywords"].append(kw)
        
        # Cập nhật thống kê
        self.brain["stats"]["total_learned"] += new_count
        self.brain["stats"]["total_searches"] += 1
        self.brain["stats"]["last_activity"] = time.time()
        
        self.brain["search_history"].append({
            "topic": topic,
            "timestamp": time.time(),
            "results_found": len(results),
            "new_learned": new_count
        })
        
        print(f"\n✅ KẾT QUẢ HỌC:")
        print(f"   - Thông tin mới: {new_count}")
        print(f"   - Tổng thông tin về '{topic}': {len(topic_data['info'])}")
        print(f"   - Từ khóa phát hiện: {', '.join(topic_data['keywords'][:5])}")
        
        self.save_brain()
        return True
    
    def ask_question(self, question):
        """Trả lời câu hỏi thông minh"""
        print(f"\n🤔 Đang suy nghĩ về: '{question}'...")
        
        question_lower = question.lower()
        
        # Tìm chủ đề liên quan nhất
        topic_scores = []
        
        for topic, data in self.brain["topics"].items():
            score = 0
            
            # Kiểm tra từ khóa trong câu hỏi
            for word in question_lower.split():
                if len(word) < 3:
                    continue
                    
                # Trong tên topic
                if word in topic.lower():
                    score += 10
                
                # Trong keywords
                for kw in data.get("keywords", []):
                    if word in kw or kw in word:
                        score += 5
                
                # Trong thông tin đã học
                for info in data["info"]:
                    if word in info["title"].lower():
                        score += 3
                    if word in info["summary"].lower():
                        score += 2
            
            if score > 0:
                topic_scores.append((topic, data, score))
        
        # Sắp xếp theo điểm
        topic_scores.sort(key=lambda x: x[2], reverse=True)
        
        if not topic_scores:
            return self.no_knowledge_response(question)
        
        # Xây dựng câu trả lời
        answer = f"📖 **Dựa trên kiến thức của tôi:**\n\n"
        
        for topic, data, score in topic_scores[:2]:
            answer += f"🔹 **Về {topic.title()}** (độ tin cậy: {min(100, int(score))}%)\n"
            
            # Lấy 2 thông tin liên quan nhất
            relevant_infos = []
            for info in data["info"]:
                relevance = 0
                for word in question_lower.split():
                    if word in info["title"].lower():
                        relevance += 2
                    if word in info["summary"].lower():
                        relevance += 1
                relevant_infos.append((relevance, info))
            
            relevant_infos.sort(key=lambda x: x[0], reverse=True)
            
            for i, (rel, info) in enumerate(relevant_infos[:2]):
                answer += f"   {i+1}. **{info['title']}**\n"
                if info['summary']:
                    answer += f"      {info['summary'][:150]}\n"
                answer += "\n"
        
        # Thêm gợi ý
        answer += f"💡 *Tôi đã học về {len(self.brain['topics'])} chủ đề. Bạn có thể hỏi thêm hoặc dạy tôi chủ đề mới!*"
        
        # Lưu lịch sử hội thoại
        self.brain["conversations"].append({
            "question": question,
            "timestamp": time.time(),
            "topics_used": [t for t, _, _ in topic_scores[:2]]
        })
        self.brain["stats"]["questions_answered"] += 1
        
        return answer
    
    def no_knowledge_response(self, question):
        """Trả lời khi chưa có kiến thức"""
        return f"""🤔 *Tôi chưa có kiến thức về '{question}'*

📚 **Bạn có thể giúp tôi học bằng cách:**
1. Chọn 'Học chủ đề mới' và nhập '{question}'
2. Hoặc dạy tôi thủ công qua menu 'Dạy AI'

💡 *Tôi sẽ ghi nhớ và trả lời tốt hơn sau khi được học!*"""
    
    def teach_manual(self):
        """Dạy AI thủ công"""
        print("\n" + "="*50)
        print("📝 DẠY AI THỦ CÔNG")
        print("="*50)
        print("Bạn có thể dạy AI bất kỳ kiến thức nào!")
        
        topic = input("\n📚 Chủ đề: ").strip()
        if not topic:
            print("❌ Chủ đề không hợp lệ!")
            return
        
        if topic not in self.brain["topics"]:
            self.brain["topics"][topic] = {
                "learned_at": time.time(),
                "info": [],
                "times_learned": 0,
                "keywords": []
            }
        
        print("\n📝 Nhập kiến thức (gõ 'done' để kết thúc):")
        facts = []
        while True:
            fact = input(f"📖 Sự thật {len(facts)+1}: ").strip()
            if fact.lower() == 'done':
                break
            if fact:
                facts.append(fact)
        
        for fact in facts:
            self.brain["topics"][topic]["info"].append({
                "title": fact[:100],
                "summary": fact,
                "learned_at": time.time()
            })
        
        self.brain["topics"][topic]["times_learned"] += 1
        self.brain["stats"]["total_learned"] += len(facts)
        
        print(f"\n✅ Đã dạy AI {len(facts)} kiến thức về '{topic}'!")
        self.save_brain()
    
    def show_statistics(self):
        """Hiển thị thống kê"""
        print("\n" + "="*50)
        print("📊 THỐNG KÊ BỘ NÃO AI")
        print("="*50)
        
        stats = self.brain["stats"]
        print(f"\n📈 TỔNG QUAN:")
        print(f"   - Tổng số thông tin: {stats['total_learned']}")
        print(f"   - Số chủ đề: {len(self.brain['topics'])}")
        print(f"   - Số câu hỏi đã trả lời: {stats['questions_answered']}")
        print(f"   - Số lần tìm kiếm: {stats['total_searches']}")
        
        print(f"\n📚 DANH SÁCH CHỦ ĐỀ:")
        for topic, data in self.brain["topics"].items():
            info_count = len(data["info"])
            print(f"   🔹 {topic.upper()}: {info_count} thông tin")
            
            # Hiển thị preview
            if data["info"]:
                preview = data["info"][-1]["title"][:50]
                print(f"      └─ Mới nhất: {preview}...")
        
        if self.brain["search_history"]:
            print(f"\n🕐 LẦN HỌC GẦN ĐÂY:")
            for history in self.brain["search_history"][-3:]:
                print(f"   - {history['topic']}: {history['new_learned']} thông tin mới")
    
    def auto_learn(self):
        """Tự động học các chủ đề phổ biến"""
        suggested_topics = [
            "python programming", "machine learning", "artificial intelligence",
            "deep learning", "data science", "neural networks", "natural language processing",
            "computer vision", "reinforcement learning", "cloud computing"
        ]
        
        # Chọn chủ đề chưa học hoặc học ít
        best_topic = None
        lowest_info = float('inf')
        
        for topic in suggested_topics:
            if topic not in self.brain["topics"]:
                best_topic = topic
                break
            else:
                info_count = len(self.brain["topics"][topic]["info"])
                if info_count < lowest_info and info_count < 5:
                    lowest_info = info_count
                    best_topic = topic
        
        if not best_topic:
            best_topic = random.choice(suggested_topics)
        
        print(f"\n🤖 AI quyết định tự học: {best_topic}")
        return self.learn_topic(best_topic)

def main():
    print("="*60)
    print("🚀 AI TỰ HỌC TOÀN DIỆN - Full Fix Edition")
    print("="*60)
    print("\n✨ TÍNH NĂNG:")
    print("   • Học từ Google (hoặc dữ liệu mẫu)")
    print("   • Trả lời câu hỏi thông minh")
    print("   • Tự động đề xuất chủ đề học")
    print("   • Dạy AI thủ công")
    print("   • Lưu trữ kiến thức vĩnh viễn")
    print("="*60)
    
    if not HAS_REQUESTS:
        print("\n❌ THIẾU THƯ VIỆN!")
        print("📦 Chạy lệnh: pip install requests")
        print("🔄 Sau đó chạy lại chương trình")
        return
    
    try:
        ai = FullAI()
    except Exception as e:
        print(f"❌ Lỗi khởi tạo: {e}")
        return
    
    print(f"\n📊 THÔNG TIN HIỆN TẠI:")
    print(f"   • Kiến thức: {ai.brain['stats']['total_learned']} thông tin")
    print(f"   • Chủ đề: {len(ai.brain['topics'])}")
    print(f"   • Đã trả lời: {ai.brain['stats']['questions_answered']} câu hỏi")
    
    while True:
        print("\n" + "-"*50)
        print("🎯 MENU CHÍNH:")
        print("   1. 🔍 Học chủ đề mới (tìm kiếm Google)")
        print("   2. 🤖 AI tự động học (đề xuất thông minh)")
        print("   3. 💬 Hỏi AI (trả lời dựa trên kiến thức)")
        print("   4. 📝 Dạy AI thủ công (tự nhập kiến thức)")
        print("   5. 📊 Xem thống kê & kiến thức")
        print("   6. 🗑️ Xóa toàn bộ kiến thức (reset)")
        print("   7. 🚪 Thoát")
        
        choice = input("\n👉 Nhập lựa chọn (1-7): ").strip()
        
        if choice == '1':
            topic = input("\n📚 Nhập chủ đề cần học: ").strip()
            if topic:
                ai.learn_topic(topic)
            else:
                print("❌ Vui lòng nhập chủ đề!")
                
        elif choice == '2':
            print("\n🤖 AI ĐANG TỰ HỌC...")
            ai.auto_learn()
            
        elif choice == '3':
            question = input("\n❓ Nhập câu hỏi của bạn: ").strip()
            if question:
                answer = ai.ask_question(question)
                print(f"\n{answer}")
            else:
                print("❌ Vui lòng nhập câu hỏi!")
                
        elif choice == '4':
            ai.teach_manual()
            
        elif choice == '5':
            ai.show_statistics()
            
        elif choice == '6':
            confirm = input("\n⚠️ Bạn có chắc muốn xóa toàn bộ kiến thức? (yes/no): ").strip()
            if confirm.lower() == 'yes':
                ai.brain = ai.init_brain()
                ai.save_brain()
                print("✅ Đã xóa và khởi tạo lại bộ não!")
            else:
                print("❌ Đã hủy!")
                
        elif choice == '7':
            print("\n👋 Tạm biệt! Đang lưu kiến thức...")
            ai.save_brain()
            ai.save_config()
            print("✅ Đã lưu! Hẹn gặp lại!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ! Vui lòng chọn 1-7")

if __name__ == "__main__":
    # Tắt warning SSL nếu cần
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass
    
    main()
