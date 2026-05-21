import solcx
from web3 import Web3

# Tự động tải solc phiên bản mặc định nếu chưa có
try:
    solcx.install_solc("0.8.20")
except Exception:
    pass

def compile_and_deploy_contract(source_code: str, rpc_url: str):
    """
    Biên dịch và deploy contract. Trả về địa chỉ của contract.
    """
    try:
        # 1. Biên dịch
        compiled_sol = solcx.compile_source(
            source_code,
            output_values=["abi", "bin"],
            solc_version="0.8.20"
        )
        
        # Lấy contract đầu tiên tìm thấy
        contract_id, contract_interface = compiled_sol.popitem()
        bytecode = contract_interface['bin']
        abi = contract_interface['abi']
        
        # 2. Deploy
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Lấy tài khoản mặc định đang unlock (Node-0 coinbase)
        w3.eth.default_account = w3.eth.accounts[0]
        
        # Tạo object contract
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Gửi transaction
        tx_hash = Contract.constructor().transact()
        
        # Đợi transaction được mine
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            "status": "success",
            "contract_address": tx_receipt.contractAddress,
            "tx_hash": tx_receipt.transactionHash.hex(),
            "abi": abi
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
