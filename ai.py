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
    print("Vui lòng cài đặt thư viện: pip install requests beautifulsoup4")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

class GoogleAI:
    def __init__(self):
        self.brain = self.init_brain() 
        self.session = self.create_session()

    def init_brain(self):
        """Hàm khởi tạo bộ não (giả định)"""
        return {}

    def create_session(self):
        """Tạo session với headers giả lập trình duyệt"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
        })
        return session

    def search_google(self, query):
        """Tìm kiếm trên Google và bóc tách link chính xác"""
        if not HAS_LIBS:
            return []

        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded_query}&num=10&hl=vi"
            print(f"🔍 Đang tìm trên Google: {query}")
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200: 
                print(f"⚠️ Google trả về mã lỗi {response.status_code}. Fallback...")
                return self.search_duckduckgo_lite(query)

            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            # Quét tất cả thẻ 'a' vì Google trả về HTML lộn xộn cho bot
            for a in soup.find_all('a'):
                href = a.get('href')
                if not href:
                    continue
                
                url_clean = None
                
                # Trường hợp 1: Link bị bọc bởi redirect của Google
                if href.startswith('/url?q='):
                    raw_url = href.split('/url?q=')[1].split('&')[0]
                    url_clean = urllib.parse.unquote(raw_url)
                # Trường hợp 2: Link thẳng
                elif href.startswith('http') and 'google.com' not in href:
                    url_clean = href
                
                if url_clean:
                    # Bỏ qua các link nội bộ của Google
                    if any(domain in url_clean for domain in ['google.com', 'youtube.com/results']):
                        continue

                    # Tìm tiêu đề
                    title_tag = a.find('h3') or a.find('div')
                    title = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)
                    
                    # Thêm vào list nếu có title và chưa bị trùng
                    if title and url_clean not in [item['url'] for item in links]:
                        links.append({'url': url_clean, 'title': title})
                
                if len(links) >= 5: 
                    break
            
            if not links:
                print("⚠️ Không bóc tách được link từ HTML của Google. Fallback...")
                return self.search_duckduckgo_lite(query)
            
            print(f"✅ Tìm thấy {len(links)} link từ Google")
            return links

        except Exception as e:
            print(f"❌ Lỗi Google: {e}")
            return self.search_duckduckgo_lite(query)

    def search_duckduckgo_lite(self, query):
        """Tìm kiếm dự phòng trên DuckDuckGo Lite"""
        if not HAS_LIBS:
            return []

        try:
            url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
            print(f"🦆 Đang tìm trên DuckDuckGo Lite...")
            
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []

            for a in soup.find_all('a', class_='result-link'):
                href = a.get('href')
                if href and 'http' in href:
                    links.append({'url': href, 'title': a.get_text(strip=True)})
                if len(links) >= 5: 
                    break
                
            print(f"✅ Tìm thấy {len(links)} link từ DuckDuckGo")
            return links
        except Exception as e:
            print(f"❌ Lỗi DuckDuckGo: {e}")
            return []

# --- CHẠY THỬ NGHIỆM ---
if __name__ == "__main__":
    if HAS_LIBS:
        ai = GoogleAI()
        
        print("-" * 50)
        results = ai.search_google("Tin tức công nghệ hôm nay")
        
        for i, res in enumerate(results, 1):
            print(f"{i}. {res['title']}")
            print(f"   {res['url']}")
        print("-" * 50)
    else:
        print("Không thể chạy code vì thiếu thư viện.")
