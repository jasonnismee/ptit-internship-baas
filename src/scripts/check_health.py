from web3 import Web3

def check_node():
    # Kết nối vào "cây cầu" localhost:8545
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

    print("-" * 30)
    print("KIỂM TRA KẾT NỐI")
    
    if w3.is_connected():
        print("KẾT NỐI THÀNH CÔNG!")
        print(f"Chain ID: {w3.eth.chain_id}")
        print(f"Block hiện tại: {w3.eth.block_number}")
        
        # Kiểm tra tiền
        admin = w3.eth.coinbase
        balance = w3.eth.get_balance(admin)
        print(f"Tài khoản Admin: {admin}")
        print(f"Số dư: {w3.from_wei(balance, 'ether')} ETH")
    else:
        print("KHÔNG KẾT NỐI ĐƯỢC!")

if __name__ == "__main__":
    check_node()