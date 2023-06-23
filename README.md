# Timekeeper-Face-Server

Timekeeper Face Server

# Cài đặt

## Môi trường và công cụ

- Hệ điều hành: Windows 10, 11.
- Cài đặt IDE: Visual Studio Code.
- Cài đặt python 3 & pip.

# Khởi động mã nguồn

1. Tạo virtual environment bằng command line: py -3 -m venv venv.
   Nhằm tạo môi trường độc lập giữa các thư viện trong ứng dụng đang phát triển với các ứng dụng khác. (Đơn giản là để tránh các conflict giữa các ứng dụng, mỗi ứng dụng chỉ dùng thư viện trong môi trường của nó)
2. Kích hoạt môi trường ảo bằng command line: venv\Scripts\activate
3. Cài đặt packages cần thiết bằng command: pip install -r requirements.txt
4. Chạy chương trình: flask run
