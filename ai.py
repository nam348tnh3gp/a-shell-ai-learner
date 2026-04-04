#!/usr/bin/env python3
"""
AI Tự Học trên a-Shell mini
Chạy trên iOS, kết nối google.com để tự cải thiện chiến lược kết nối
"""

import urllib.request
import time
import json
import os
import random
from datetime import datetime

# File để lưu trữ "bộ nhớ" của AI
MEMORY_FILE = "ai_memory.json"

class SimpleAI:
    def __init__(self):
        self.memory = self.load_memory()
        self.learning_rate = 0.1  # Tốc độ học
        self.last_state = None
        self.last_action = None
        
    def load_memory(self):
        """Tải bộ nhớ từ file (kiến thức đã học)"""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.init_memory()
        else:
            return self.init_memory()
    
    def init_memory(self):
        """Khởi tạo bộ nhớ ban đầu"""
        return {
            "q_table": {},      # Bảng Q-Learning lưu giá trị của từng cặp (trạng thái, hành động)
            "total_attempts": 0,
            "successful_connects": 0
        }
    
    def save_memory(self):
        """Lưu bộ nhớ để dùng cho lần sau"""
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.memory, f, indent=2)
        print("💾 Đã lưu kiến thức vào bộ nhớ!")
    
    def get_state(self, response_time):
        """Chuyển đổi thời gian phản hồi thành trạng thái (discretization)"""
        if response_time < 0.5:
            return "very_fast"
        elif response_time < 1.0:
            return "fast"
        elif response_time < 2.0:
            return "normal"
        elif response_time < 5.0:
            return "slow"
        else:
            return "very_slow"
    
    def choose_action(self, state):
        """
        Chọn hành động dựa trên trạng thái hiện tại
        Sử dụng epsilon-greedy: thăm dò (explore) vs khai thác (exploit)
        """
        actions = ["wait_short", "wait_long", "retry_immediate"]
        
        # Epsilon: 20% thời gian sẽ thử nghiệm hành động mới
        if random.random() < 0.2:
            action = random.choice(actions)
            print(f"🤔 Đang thử nghiệm hành động mới: {action}")
            return action
        
        # 80% còn lại: chọn hành động tốt nhất dựa trên kinh nghiệm
        q_key = f"{state}"
        if q_key not in self.memory["q_table"]:
            self.memory["q_table"][q_key] = {a: 0.0 for a in actions}
        
        q_values = self.memory["q_table"][q_key]
        best_action = max(q_values, key=q_values.get)
        print(f"🎯 Dựa trên kinh nghiệm, chọn: {best_action}")
        return best_action
    
    def update_q_value(self, state, action, reward):
        """Cập nhật giá trị Q dựa trên phần thưởng nhận được"""
        q_key = f"{state}"
        
        if q_key not in self.memory["q_table"]:
            self.memory["q_table"][q_key] = {}
        
        old_value = self.memory["q_table"][q_key].get(action, 0)
        
        # Công thức Q-Learning đơn giản
        new_value = old_value + self.learning_rate * (reward - old_value)
        self.memory["q_table"][q_key][action] = new_value
        
        print(f"📊 Cập nhật: {action} từ {old_value:.2f} → {new_value:.2f}")
    
    def connect_to_google(self):
        """Kết nối đến google.com và đo thời gian phản hồi"""
        try:
            start_time = time.time()
            # Sử dụng urllib (có sẵn trong Python của a-Shell mini)
            with urllib.request.urlopen('https://www.google.com', timeout=10) as response:
                end_time = time.time()
                response_time = end_time - start_time
                status = response.getcode()
                
                if status == 200:
                    print(f"✅ Kết nối thành công! Thời gian: {response_time:.2f} giây")
                    return response_time, True
                else:
                    print(f"⚠️ Kết nối được nhưng status: {status}")
                    return response_time, False
                    
        except urllib.error.URLError as e:
            print(f"❌ Lỗi kết nối: {e.reason}")
            return 10.0, False
        except Exception as e:
            print(f"❌ Lỗi không xác định: {e}")
            return 10.0, False
    
    def calculate_reward(self, response_time, success):
        """Tính điểm thưởng dựa trên kết quả"""
        if not success:
            return -5.0  # Phạt nặng nếu không kết nối được
        
        # Thưởng dựa trên tốc độ: càng nhanh càng nhiều điểm
        if response_time < 0.5:
            return 10.0
        elif response_time < 1.0:
            return 7.0
        elif response_time < 2.0:
            return 5.0
        elif response_time < 5.0:
            return 2.0
        else:
            return 0.0
    
    def execute_action(self, action):
        """Thực thi hành động đã chọn"""
        if action == "wait_short":
            print("⏳ Chờ 1 giây...")
            time.sleep(1)
        elif action == "wait_long":
            print("⏳ Chờ 3 giây...")
            time.sleep(3)
        elif action == "retry_immediate":
            print("🔄 Thử lại ngay lập tức")
            # Không chờ, kết nối lại ngay
        
        # Kết nối đến Google
        return self.connect_to_google()
    
    def learn_cycle(self):
        """Một chu kỳ học hoàn chỉnh"""
        print("\n" + "="*50)
        print(f"🧠 Chu kỳ học #{self.memory['total_attempts'] + 1}")
        print("="*50)
        
        # Bước 1: Kết nối thử để biết trạng thái hiện tại
        print("🌐 Đang kiểm tra kết nối mạng...")
        response_time, success = self.connect_to_google()
        current_state = self.get_state(response_time)
        print(f"📡 Trạng thái mạng hiện tại: {current_state}")
        
        # Bước 2: Chọn hành động dựa trên trạng thái
        action = self.choose_action(current_state)
        
        # Bước 3: Thực thi hành động và nhận kết quả
        new_response_time, new_success = self.execute_action(action)
        
        # Bước 4: Tính phần thưởng
        reward = self.calculate_reward(new_response_time, new_success)
        print(f"🎁 Phần thưởng nhận được: {reward:.2f}")
        
        # Bước 5: Cập nhật kiến thức
        self.update_q_value(current_state, action, reward)
        
        # Bước 6: Cập nhật thống kê
        self.memory["total_attempts"] += 1
        if new_success:
            self.memory["successful_connects"] += 1
        
        success_rate = (self.memory["successful_connects"] / self.memory["total_attempts"]) * 100
        print(f"📈 Tỷ lệ thành công: {success_rate:.1f}%")
        
        # Lưu bộ nhớ sau mỗi chu kỳ
        self.save_memory()
        
        return success_rate

def main():
    print("🚀 Khởi động AI Tự Học trên a-Shell mini")
    print("-" * 40)
    print("AI này sẽ tự cải thiện bằng cách kết nối với Google.com")
    print("Sau mỗi lần, AI ghi nhớ và đưa ra quyết định tốt hơn!")
    print("-" * 40)
    
    ai = SimpleAI()
    
    print(f"\n📚 KIẾN THỨC HIỆN TẠI:")
    print(f"   - Tổng số lần học: {ai.memory['total_attempts']}")
    print(f"   - Số lần thành công: {ai.memory['successful_connects']}")
    
    try:
        while True:
            # Học 1 chu kỳ
            rate = ai.learn_cycle()
            
            # Hỏi người dùng có muốn tiếp tục không
            print("\n" + "-" * 40)
            choice = input("🔄 Tiếp tục học? (y/n): ").lower()
            if choice != 'y':
                print("\n👋 Tạm biệt! AI đã ghi nhớ những gì đã học!")
                break
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Dừng bởi người dùng. Đã lưu tiến trình!")
        ai.save_memory()

if __name__ == "__main__":
    main()
