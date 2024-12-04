
# So sanh file tai ve voi file goc co giong nhau khong

serverFile="Server/a.jpg"
clientFile="Client/a.jpg"

with open(serverFile, "rb") as file_a, open(clientFile, "rb") as file_b:
    if file_a.read() == file_b.read():
        print("2 file giong nhau")
    else:
        xor_result = int.from_bytes(file_a.read()) ^ int.from_bytes(file_b.read())
        if xor_result == 0:
            print("2 file giong nhau")
        else:
            print("2 file khac nhau")