from fastapi import APIRouter
from app.services.k8s_service import k8s_service

router = APIRouter()

@router.get("/nodes")
def list_blockchain_nodes():
    """API: Xem danh sách các node Blockchain"""
    return k8s_service.get_node_list()

@router.post("/peer")
def trigger_peering():
    """API: Kích hoạt quá trình kết nối mạng (Peering)"""
    return k8s_service.peer_nodes()