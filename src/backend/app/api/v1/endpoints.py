from fastapi import APIRouter
from pydantic import BaseModel
from app.services.k8s_service import k8s_service

router = APIRouter()

class NetworkRequest(BaseModel):
    replicas: int = 3

class VinamilkRequest(BaseModel):
    message: str

class VerifyRequest(BaseModel):
    tx_hash: str

@router.get("/nodes")
def list_blockchain_nodes():
    """API: Xem danh sách các node Blockchain"""
    return k8s_service.get_node_list()

@router.post("/peer")
def trigger_peering():
    """API: Kích hoạt quá trình kết nối mạng (Peering)"""
    return k8s_service.peer_nodes()

from datetime import datetime

# Biến tạm lưu lịch sử trên RAM (Thực tế nên lưu vào Database/Elasticsearch để fetch index từ K8s)
ledger_history = []

@router.post("/network")
def create_blockchain_network(req: NetworkRequest):
    """API: Tự động khởi tạo và triển khai cụm node Blockchain mới"""
    return k8s_service.deploy_network(req.replicas)

@router.get("/vinamilk/history")
def get_vinamilk_history():
    """API: Lấy lịch sử theo dõi chuỗi cung ứng đã lưu"""
    return {"status": "success", "data": ledger_history}

@router.post("/vinamilk/track")
def track_vinamilk_batch(req: VinamilkRequest):
    """API (Demo Thực Tế): Ghi nhật ký hành trình hộp sữa Vinamilk vào thẳng Blockchain"""
    res = k8s_service.record_supply_chain(req.message)
    if res.get("status") == "success":
        ledger_history.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": req.message,
            "tx_hash": res.get("tx_hash")
        })
    return res

@router.post("/demo/crash")
def simulate_node_crash():
    """API (Demo): Xóa ngẫu nhiên 1 Node để chứng minh Auto-Healing"""
    return k8s_service.crash_random_node()

@router.post("/demo/verify")
def verify_ledger_consensus(req: VerifyRequest):
    """API (Demo): Quét dữ liệu chéo trên toàn mạng lưới Blockchain"""
    return k8s_service.verify_transaction(req.tx_hash)