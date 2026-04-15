from fastapi import APIRouter
from pydantic import BaseModel
from app.services.k8s_service import k8s_service

router = APIRouter()

class NetworkRequest(BaseModel):
    replicas: int = 3

@router.get("/nodes")
def list_blockchain_nodes():
    """API: Xem danh sách các node Blockchain"""
    return k8s_service.get_node_list()

@router.post("/peer")
def trigger_peering():
    """API: Kích hoạt quá trình kết nối mạng (Peering)"""
    return k8s_service.peer_nodes()

@router.post("/network")
def create_blockchain_network(req: NetworkRequest):
    """API: Tự động khởi tạo và triển khai cụm node Blockchain mới"""
    return k8s_service.deploy_network(req.replicas)