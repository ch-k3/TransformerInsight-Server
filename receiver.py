import socket
import threading
from data_processor import parse_and_process  # 后续定义

def handle_client(conn, addr):
    while True:
        try:
            data = conn.recv(1024)
            if not  break
            parse_and_process(data)  # 调用处理函数
        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break
    conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 8888))  # 监听所有网卡，端口 8888
    server.listen(20)
    print("Server listening on port 8888...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    main()