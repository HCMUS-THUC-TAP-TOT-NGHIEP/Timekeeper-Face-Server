# Timekeeper-Face-Server
Timekeeper Face Server

# Setting
1. Install python 3 & pip.
2. Tạo virtual environment (recommended), nhằm tạo môi trường độc lập giữa các thư viện trong ứng dụng đang phát triển với các ứng dụng khác. (Đơn giản là để tránh các conflict giữa các ứng dụng, mỗi ứng dụng chỉ dùng thư viện trong môi trường của nó). Chạy lần lượt các command.
    + Tạo virtual env tên là venv: py -3 -m venv venv.
    + Activate venv: venv\Scripts\activate
3. Install Flask & packages:  pip install -r requirements.txt
4. Chạy chương trình: flask --debug run

Notes: Luôn activate venv trước khi coding.

# Packages reference:
1. Flask: https://flask.palletsprojects.com/en/2.2.x/
2. watchdog: https://pythonhosted.org/watchdog/quickstart.html
3. python-dotenv: https://github.com/theskumar/python-dotenv#readme