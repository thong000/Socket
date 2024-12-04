import socket
import os
import multiprocessing


def fileData(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        return content
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None

def fileDataFrom(file_path,index):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        return content[index]
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None


def getFileSize(file_path):
    try:
        file_size = os.path.getsize(file_path)  # Lấy kích thước tệp tính theo byte
        return file_size
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None


def socketSendNumber(num,soc):
    soc.sendall(str(num).encode())

def socketSendString(string,soc):
    soc.sendall(bytes(string, "utf8"))

def socketRecvNumber(soc,size):
        data = soc.recv(size)
        number = int(data.decode())
        return number

def socketRecvString(soc,size):
        data = soc.recv(size)
        return data.decode()

def writeStringToFile(file_path, content):
        try:
            # Mở tệp ở chế độ ghi ('w'). Nếu tệp đã tồn tại, nó sẽ bị ghi đè.
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(content)  # Ghi chuỗi vào tệp
            print(f"Đã ghi nội dung vào tệp {file_path}")
        except Exception as e:
            print(f"Lỗi khi ghi tệp: {e}")


def send_file(filename,connection):
    # Tạo socket
        with connection[0]:
            # Gửi tên file
            connection[0].sendall(filename.encode())
            connection[0].recv(1024)  # Chờ ACK từ client

            # Gửi kích thước file
            filesize = os.path.getsize("Server/"+filename)
            connection[0].sendall(str(filesize).encode())
            connection[0].recv(1024)  # Chờ ACK từ client

            # Gửi dữ liệu file
            with open("Server/"+filename, "rb") as f:
                while chunk := f.read(1024):  # Đọc từng chunk 1024 byte
                    connection[0].sendall(chunk)
            print("Đã gửi file.")


        f.close()


def handle_client(connection):


    while True:

            fileSize = int(connection[0].recv(1024).decode())
            print("Da nhan size\n")
            fileName=socketRecvString(connection[0],fileSize)
            print("Da nhan ten file\n")
            print(fileName)
            print(fileName)
            send_file(fileName,connection)




def start_server(host, port,file):
    """
    Khởi động server sử dụng multiprocessing.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[INFO] Server listening on {host}:{port}")

    while True:

        client_socket=[]
        for i in range(4):
            coon, addr = server.accept()
            client_socket.append(coon)

        socketSendNumber(getFileSize(file), client_socket[0])
        socketSendString(fileData(file), client_socket[0])

        print("Da mo tien trinh\n")

        process = multiprocessing.Process(target=handle_client, args=(client_socket,))
        process.start()
        print(f"[INFO] Active processes: {len(multiprocessing.active_children())}")




if __name__ == "__main__":
    start_server("192.168.58.76", 65432,"../../../../../../../../../../DoAn/TCP/Server/fileList.txt")
