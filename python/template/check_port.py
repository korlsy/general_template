import socket

# D:\py_venv>Scripts\activate
# python C:\dev\eclipse-workspace\general_templates\python\template\check_port.py
def check_port(ip, port, timeout=3):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception as e:
        return False

# 예시 사용
if check_port("127.0.0.1", 5433):
    print("접속 가능")
else:
    print("방화벽 차단 or 서비스 미동작")
