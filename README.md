NLP Scheduler – Ứng dụng quản lý lịch trình bằng tiếng Việt
Dự án xây dựng một hệ thống quản lý sự kiện cá nhân kết hợp mô-đun NLP tiếng Việt, cho phép người dùng tạo sự kiện bằng câu lệnh tự nhiên như:
“họp nhóm lúc 7h tối mai ở quán cà phê, nhắc trước 10 phút”
Hệ thống tự động phân tích thời gian, địa điểm, nội dung sự kiện, thời gian nhắc nhở và lưu vào cơ sở dữ liệu SQLite.

Yêu cầu
Python 3.11 trở lên
Pip (trong Python)
Virtual environment (khuyến nghị)

Cài môi trường ảo
py -3.11 -m venv vevn

kích hoạt môi trường ảo
source venv/bin/activate

cài đặt thư viện
pip install -r requirements.txt


Cấu trúc dự án
/nlp
    preprocess.py
    entity_extractor.py
    event_extractor.py
    time_parser.py
    semantic_extractor.py

/storage
    storage.py             # CRUD + SQLite

/templates
    base.html
    index.html
    events.html
    edit_event.html
    search_advanced.html
    _table_macros.html

/static
    style.css
    alarm.mp3

main.py                    # Flask app
events.db                  # Database (tự tạo khi chạy lần đầu)

Chạy ứng dụng 
python main.py

Mở trình duyệt-> truy cập 
http://localhost:5000

