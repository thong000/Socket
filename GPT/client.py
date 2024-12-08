import socket
import os
import hashlib
import time
import signal
import sys
from math import floor

LOG_FILE = "client.log"
PROGRESS_LOG = "progress.log"
INPUT_FILE = "Client/input.txt"
MAX_FILE_RETRIES = 3

def log_message(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{message}\n")

def save_progress(file_name, part, offset, total_size):
    with open(PROGRESS_LOG, "a") as log:
        log.write(f"{file_name},{part},{offset},{total_size}\n")

def load_progress():
    progress = {}
    try:
        with open(PROGRESS_LOG, "r") as log:
            for line in log:
                file_name, part, offset, total_size = line.strip().split(",")
                if file_name not in progress:
                    progress[file_name] = {}
                progress[file_name][int(part)] = (int(offset), int(total_size))
    except FileNotFoundError:
        pass
    return progress

def calculate_checksum(file_path):
    with open(file_path, "rb") as f:
        file_data = f.read()
    return hashlib.md5(file_data).hexdigest()

def recvByte(connection, size):
    data = connection.recv(size)
    if len(data) == 0:
        raise ConnectionError("Connection lost or no data received.")
    return data

def receiveChunk(connection, chunk_size, part, file_name, retries=3):
    receiver = b""
    temp = 0

    while temp < chunk_size and retries > 0:
        try:
            last = temp + 1024
            if last < chunk_size:
                receiver += recvByte(connection, 1024)
            else:
                receiver += recvByte(connection, chunk_size - temp)
            temp += 1024
            print(f"[INFO] Downloading {file_name} part {part}: {floor(temp / chunk_size * 100.0)}%")
        except Exception as e:
            retries -= 1
            print(f"[WARN] Error downloading part {part}: {e}. Retries left: {retries}")
            if retries == 0:
                print(f"[ERROR] Failed to download part {part} after retries.")
                return None
            continue

    save_progress(file_name, part, temp, chunk_size)
    return receiver

def authenticate_with_server(conn, token="securetoken123"):
    conn.sendall(token.encode())
    response = conn.recv(1024).decode()
    if response == "AUTH_SUCCESS":
        print("[INFO] Authentication successful.")
        return True
    else:
        print("[ERROR] Authentication failed.")
        return False

def download_file(file_name):
    HOST = "192.168.58.220"
    PORT = 65432

    try:
        receiver_sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(4)]
        for sock in receiver_sockets:
            sock.connect((HOST, PORT))
            if not authenticate_with_server(sock):
                raise Exception("Authentication failed.")

        # Gửi tên file đến server
        receiver_sockets[0].sendall(str(len(file_name)).encode())
        receiver_sockets[0].sendall(file_name.encode())

        # Nhận checksum từ server
        checksum = receiver_sockets[0].recv(1024).decode()
        if not checksum:
            raise Exception("Failed to receive checksum from server.")

        # Nhận kích thước file từ server
        file_size = int(receiver_sockets[0].recv(1024).decode())
        chunk_size = file_size // 4

        receiver = []
        for i, sock in enumerate(receiver_sockets):
            chunk = receiveChunk(sock, chunk_size if i < 3 else file_size - 3 * chunk_size, i + 1, file_name)
            if chunk:
                receiver.append(chunk)

        # Ghép các chunk và lưu file
        with open(f"Client/{file_name}", "wb") as f:
            for chunk in receiver:
                f.write(chunk)

        # Xác minh checksum
        if calculate_checksum(f"Client/{file_name}") == checksum:
            print(f"[INFO] File {file_name} downloaded successfully and verified!")
        else:
            print(f"[ERROR] File {file_name} verification failed!")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        for sock in receiver_sockets:
            sock.close()

def monitor_input_file(file_path, interval=5):
    seen_files = set()
    while True:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_files = set(f.read().splitlines())
            new_files = current_files - seen_files
            for file_name in new_files:
                print(f"[INFO] Detected new file to download: {file_name}")
                download_file_with_retry(file_name)
            seen_files.update(new_files)
        except FileNotFoundError:
            print(f"[WARN] File {file_path} not found. Retrying in {interval} seconds.")
        time.sleep(interval)

def download_file_with_retry(file_name):
    for attempt in range(MAX_FILE_RETRIES):
        try:
            download_file(file_name)
            print(f"[INFO] Successfully downloaded {file_name}")
            return
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1}/{MAX_FILE_RETRIES} failed: {e}")
            if attempt < MAX_FILE_RETRIES - 1:
                print("[INFO] Retrying...")
                time.sleep(2)
            else:
                print(f"[ERROR] Failed to download {file_name} after {MAX_FILE_RETRIES} attempts.")
                break

def main():
    print("[INFO] Monitoring input file...")
    monitor_input_file(INPUT_FILE)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    main()
