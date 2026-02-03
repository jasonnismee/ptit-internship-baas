import json
import os
from web3 import Web3

def create_new_account():
    w3 = Web3()
    acc = w3.eth.account.create()
    
    print("-" * 30)
    print("TẠO VÍ THÀNH CÔNG!")
    print(f"Address (Địa chỉ):     {acc.address}")
    print(f"Private Key (Khóa bí mật): {acc.key.hex()}")
    print("-" * 30)
  
    os.makedirs("secrets", exist_ok=True)
    
    account_data = {
        "address": acc.address,
        "private_key": acc.key.hex()
    }
    
    with open("secrets/node1_account.json", "w") as f:
        json.dump(account_data, f, indent=4)
        
    print("-> Đã lưu thông tin ví vào file: secrets/node1_account.json")

if __name__ == "__main__":
    create_new_account()