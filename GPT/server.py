import socket
import os
import multiprocessing
import hashlib
import signal
import sys

LOG_FILE = "server.log"

def log_message(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{message}\n")

def calculate_checksum(file_path):
    with open(file_path, "rb") as f:
        file_data = f.read()
    return hashlib.md5(file_data).hexdigest()

def split_into_chunks(file_path, num_chunks):
    file_size = os.path.getsize(file_path)
    chunk_size = file_size // num_chunks
    chunks = []

    with open(file_path, "rb") as f:
        for _ in range(num_chunks - 1):
            chunks.append(f.read(chunk_size))
        chunks.append(f.read())  # Chunk cuối cùng chứa phần còn lại
    return chunks

def sendChunk(connection, chunk, retries=3):
    temp = 0
    length = len(chunk)
    while temp < length and retries > 0:
        try:
            end = min(temp + 1024, length)
            connection.sendall(chunk[temp:end])
            temp = end
        except Exception as e:
            retries -= 1
            log_message(f"[WARN] Error sending chunk: {e}. Retries left: {retries}")
            if retries == 0:
                log_message(f"[ERROR] Failed to send chunk after multiple retries.")
                raise e

def handle_client(connections, file_name):
    try:
        checksum = calculate_checksum("Server/" + file_name)
        connections[0].sendall(checksum.encode())

        file_size = os.path.getsize("Server/" + file_name)
        chunks = split_into_chunks("Server/" + file_name, len(connections))

        with multiprocessing.Pool(processes=len(connections)) as pool:
            pool.starmap(sendChunk, [(conn, chunk) for conn, chunk in zip(connections, chunks)])
            log_message(f"Sent chunks of {file_name}.")
    except Exception as e:
        log_message(f"Error handling client: {e}")
    finally:
        for conn in connections:
            conn.close()

def start_server(host, port, file_list_path):
    def signal_handler(sig, frame):
        print("\n[INFO] Server shutting down safely...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[INFO] Server listening on {host}:{port}\n")

    while True:
        client_connections = []
        for _ in range(4):
            conn, addr = server.accept()
            client_connections.append(conn)
        print(f"[INFO] Connected to {addr}")

        try:
            with open(file_list_path, "r", encoding="utf-8") as f:
                file_list = f.read()
            file_size = len(file_list)
            client_connections[0].sendall(str(file_size).encode())
            client_connections[0].sendall(file_list.encode())

            process = multiprocessing.Process(target=handle_client, args=(client_connections, file_list.strip().split("\n")[0],))
            process.start()
        except FileNotFoundError:
            log_message(f"[ERROR] {file_list_path} not found.")
            break

if __name__ == "__main__":
    start_server("192.168.58.220", 65432, "Server/fileList.txt")
