import socket
import os
import time
from cgi import print_directory


def fileData(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        return content
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None

def fileDataFrom(file_path, size):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        if size==0:
            return content[0:]
        else:
            return content[size:]

    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None
def split_string(input_string, delimiter):
    # Sử dụng phương thức split() để chia chuỗi theo ký tự phân cách
    result = input_string.split(delimiter)
    return result

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
    num = int(data.decode())
    return num

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


def isChange(fileName,oldSize):
    curSize=getFileSize(fileName)
    if curSize==None:
        return False
    return curSize!=oldSize



HOST = "127.0.0.1"  # IP adress server
PORT = 65432        # port is used by the server

client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (HOST, PORT)
print("Client connect to server with port: " + str(PORT))
client1.connect(server_address)
client2.connect(server_address)
client3.connect(server_address)
client4.connect(server_address)


def receive_file(host, port):
    # Tạo socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        print("Đã kết nối tới server.")

        # Nhận tên file
        filename = s.recv(1024).decode()
        s.sendall(b"ACK")  # Gửi phản hồi

        # Nhận kích thước file
        filesize = int(s.recv(1024).decode())
        s.sendall(b"ACK")  # Gửi phản hồi

        # Nhận dữ liệu file
        received = 0
        with open(f"received_{filename}", "wb") as f:
            while received < filesize:
                chunk = s.recv(1024)
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)

        print(f"Đã nhận file {filename} ({filesize} bytes).")



def findIndex(arr,num):
    for i in range(len(arr)):
        if arr[i]==num:
            return i
    return -1

try:

        size = socketRecvNumber(client1, 1024)
        fileList=socketRecvString(client1, size)
        print("Danh sach cac file co the download la:\n")
        print(fileList)

        start_time = time.time()
        oldSize=getFileSize("Client/input.txt")
        newSize=0

        while True:
            if isChange("Client/input.txt", oldSize):

                newSize=getFileSize("Client/input.txt")
                changeSize=newSize-oldSize


                split=split_string(fileDataFrom("Client/input.txt", oldSize), '\n')

                for i in range(len(split)):

                    if split[i] != "":

                        socketSendNumber(len(split[i]), client1) # Gui do dai ten file
                        socketSendString(split[i], client1) # Gui ten file

                        # Nhận kích thước file
                        filesize = int(client1.recv(1024).decode())
                        chunkSize=filesize//4
                        client1.sendall(b"ACK")  # Gửi phản hồi


                        Des="Client/"+split[i]

                        receiver=[]  # Noi dung tung chunk
                        oder=[]  # Thu tu cac chunk

                        receiver.append(client1.recv(chunkSize))
                        oder.append(int(client1.recv(1024).decode()))
                        receiver.append(client2.recv(chunkSize))
                        oder.append(int(client2.recv(1024).decode()))
                        receiver.append(client3.recv(chunkSize))
                        oder.append(int(client3.recv(1024).decode()))
                        receiver.append(client4.recv(filesize-3*chunkSize))
                        oder.append(int(client4.recv(1024).decode()))


                        with open("Client/"+split[i],"wb") as f:
                            for i in range(4):
                                f.write(receiver[findIndex(oder,i)])



                oldSize=newSize
            else:
                oldSize=getFileSize("Client/input.txt")
            time.sleep(2)


except KeyboardInterrupt:
    client1.close()
finally:
    client1.close()

