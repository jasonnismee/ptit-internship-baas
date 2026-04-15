import subprocess
import re
import os
from kubernetes import client, config
from app.core.config import settings

class K8sService:
    def __init__(self):
        # Kiểm tra cấu hình K8s
        try:
            # Nếu KUBE_CONFIG_PATH có giá trị, ưu tiên dùng đường dẫn đó
            if settings.KUBE_CONFIG_PATH and os.path.exists(os.path.expanduser(settings.KUBE_CONFIG_PATH)):
                config.load_kube_config(config_file=os.path.expanduser(settings.KUBE_CONFIG_PATH))
                print(f"Loaded K8s config from {settings.KUBE_CONFIG_PATH}")
            else:
                # Nếu trống hoặc không tìm thấy file, tự động tìm ~/.kube/config (Dùng cho Local)
                config.load_kube_config()
                print("Loaded default K8s config (~/.kube/config)")
        except Exception as e:
            # Fallback dùng cho môi trường Production (khi chạy bên trong cluster)
            try:
                config.load_incluster_config()
                print("Loaded In-Cluster K8s config")
            except Exception:
                print(f"Error: Could not load K8s config: {e}")
        
        self.v1 = client.CoreV1Api()

    def get_node_list(self):
        """Lấy danh sách các Pod Blockchain đang chạy"""
        try:
            pods = self.v1.list_namespaced_pod(
                namespace="default", 
                label_selector="app=geth"
            )
            
            results = []
            for pod in pods.items:
                results.append({
                    "name": pod.metadata.name,
                    "ip": pod.status.pod_ip,
                    "status": pod.status.phase,
                    "start_time": str(pod.status.start_time)
                })
            return results
        except Exception as e:
            print(f"Error fetching pod list: {e}")
            return []

    def _run_geth_cmd(self, pod_name: str, js_command: str) -> str:
        """Hàm nội bộ để chạy lệnh Geth attach"""
        # Bỏ flag -t (terminal) để tránh lỗi khi chạy từ background process/FastAPI
        cmd = [
            "kubectl", "exec", "-i", pod_name, "-c", "geth", "--",
            "geth", "attach", "--exec", js_command, "/data/geth.ipc"
        ]
        try:
            # Chạy lệnh và lọc bỏ log rác
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
            return result.replace('"', '')
        except subprocess.CalledProcessError as e:
            print(f"Subprocess error on {pod_name}: {e}")
            return ""

    def get_enode(self, pod_name: str) -> str:
        """Lấy Enode URL chuẩn của một Pod"""
        raw = self._run_geth_cmd(pod_name, "admin.nodeInfo.enode")
        if not raw:
            raise Exception(f"Empty enode response from {pod_name}")
            
        # Regex lọc Enode 
        match = re.search(r'enode://([a-f0-9]+)@([0-9\.]+):([0-9]+)', raw)
        if match:
            return match.group(0)
        raise Exception(f"Invalid Enode: {raw}")

    def peer_nodes(self):
        """Logic kết nối mạng lưới (Peering)"""
        # 1. Lấy danh sách pod
        pods = self.get_node_list()
        pod_names = [p['name'] for p in pods]
        
        if "node-0" not in pod_names:
            return {"status": "error", "message": "Missing node-0"}

        # 2. Lấy Enode của Admin (Node-0)
        try:
            admin_enode = self.get_enode("node-0")
        except Exception as e:
            return {"status": "error", "message": str(e)}

        logs = []
        # 3. Gửi lệnh kết bạn
        for pod in pod_names:
            if pod == "node-0": continue
            
            try:
                self._run_geth_cmd(pod, f"admin.addPeer('{admin_enode}')")
                logs.append(f"{pod} -> Connected to Admin")
            except Exception as e:
                logs.append(f"{pod} failed: {str(e)}")
        
        return {
            "status": "success",
            "admin_enode": admin_enode,
            "logs": logs
        }

    def deploy_network(self, replicas: int = 3):
        """Khởi tạo mạng lưới Blockchain động (BaaS) với YAML và tự động cấu hình replicas"""
        from kubernetes import utils
        import tempfile
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        k8s_dir = os.path.join(base_dir, "infrastructure", "k8s")
        service_path = os.path.join(k8s_dir, "service.yaml")
        statefulset_path = os.path.join(k8s_dir, "statefulset.yaml")
        
        results = []
        
        # 1. Apply Service
        try:
            utils.create_from_yaml(self.v1.api_client, service_path)
            results.append("Đã tạo Headless Service")
        except Exception as e:
            results.append(f"Service info (có thể đã tồn tại): {str(e)}")
            
        # 2. Đọc YAML StatefulSet cũ, sửa chữ `replicas` và apply
        try:
            with open(statefulset_path, "r") as f:
                content = f.read()
                
            # Thay đổi tham số "replicas: 3" (hoặc số khác) thành tham số mới
            content = re.sub(r'replicas:\s*\d+', f'replicas: {replicas}', content)
            
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
                
            utils.create_from_yaml(self.v1.api_client, tmp_path)
            os.remove(tmp_path)
            results.append(f"Đã triển khai hệ thống Geth với {replicas} Nodes")
        except Exception as e:
            results.append(f"StatefulSet error: {str(e)}")
            
        return {
            "status": "success",
            "replicas_requested": replicas,
            "actions": results
        }

k8s_service = K8sService()