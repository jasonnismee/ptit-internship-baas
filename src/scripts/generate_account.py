import json
import os
import re
from web3 import Web3

def update_genesis_json(address):
    genesis_path = "infrastructure/genesis.json"
    if not os.path.exists(genesis_path):
        print(f"Không tìm thấy {genesis_path}")
        return

    with open(genesis_path, "r") as f:
        data = json.load(f)

    # Cập nhật extradata (32 bytes zero + 20 bytes address + 65 bytes zero)
    clean_address = address.replace("0x", "")
    extradata = "0x" + "0" * 64 + clean_address + "0" * 130
    data["extradata"] = extradata

    # Cập nhật alloc
    if "alloc" in data:
        # Lấy key cũ ra
        old_keys = list(data["alloc"].keys())
        for old_key in old_keys:
            balance = data["alloc"][old_key]
            del data["alloc"][old_key]
            data["alloc"][address] = balance
    else:
        data["alloc"] = {address: {"balance": "1000000000000000000000"}}

    with open(genesis_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"-> Đã cập nhật địa chỉ ví mới vào {genesis_path}")


def update_statefulset_yaml(address):
    yaml_path = "infrastructure/k8s/statefulset.yaml"
    if not os.path.exists(yaml_path):
        print(f"Không tìm thấy {yaml_path}")
        return

    with open(yaml_path, "r") as f:
        content = f.read()

    # Cập nhật etherbase
    content = re.sub(r'--miner\.etherbase\s+0x[a-fA-F0-9]+', f'--miner.etherbase {address}', content)
    # Cập nhật unlock
    content = re.sub(r'--unlock\s+0x[a-fA-F0-9]+', f'--unlock {address}', content)

    with open(yaml_path, "w") as f:
        f.write(content)
    print(f"-> Đã cập nhật địa chỉ ví mới vào {yaml_path}")


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

    # Cập nhật các file cấu hình
    update_genesis_json(acc.address)
    update_statefulset_yaml(acc.address)

if __name__ == "__main__":
    create_new_account()