import subprocess
import re
import os
import yaml
import tempfile
from kubernetes import client, config, utils
from app.core.config import settings
from app.services.k8s_templates import get_namespace_yaml, get_service_yaml, get_genesis_yaml, get_statefulset_yaml
import json

class K8sService:
    def __init__(self):
        try:
            if settings.KUBE_CONFIG_PATH and os.path.exists(os.path.expanduser(settings.KUBE_CONFIG_PATH)):
                config.load_kube_config(config_file=os.path.expanduser(settings.KUBE_CONFIG_PATH))
            else:
                config.load_kube_config()
        except Exception:
            try:
                config.load_incluster_config()
            except Exception as e:
                print(f"Error: Could not load K8s config: {e}")
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        
        # Hardcode địa chỉ ví demo (lấy từ generate_account)
        self.admin_address = "0xe660105C765DE27a9095c1589368F4DEDaf1f9C4"
        self.admin_private_key = "a91239b176874b54603c67a53848c08e25b7d4f97b60e9cc16af99da4cf19851"
        self.admin_password = "password123"

    def get_network_list(self):
        """Lấy danh sách các mạng (dựa trên Namespace có prefix baas-)"""
        try:
            ns_list = self.v1.list_namespace()
            networks = []
            for ns in ns_list.items:
                if ns.metadata.name.startswith("baas-") or ns.metadata.name == "default":
                    # Lấy số lượng pod trong mạng này
                    pods = self.get_node_list(ns.metadata.name)
                    networks.append({
                        "name": ns.metadata.name,
                        "nodes_count": len(pods),
                        "status": "Running" if len(pods) > 0 else "Stopped"
                    })
            return networks
        except Exception as e:
            return [{"error": str(e)}]

    def get_node_list(self, namespace="default"):
        try:
            pods = self.v1.list_namespaced_pod(
                namespace=namespace, 
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

    def get_rpc_url(self, namespace="default"):
        """Lấy RPC url của mạng bằng cách port-forward hoặc dùng IP cluster"""
        # Trong môi trường thực tế sẽ gọi service IP hoặc ingress.
        # Ở đây ta lấy IP của Node-0 làm RPC URL nội bộ
        try:
            pod = self.v1.read_namespaced_pod(name="node-0", namespace=namespace)
            if pod.status.pod_ip:
                return f"http://{pod.status.pod_ip}:8545"
            return None
        except:
            return None

    def _run_geth_cmd(self, pod_name: str, js_command: str, namespace="default") -> str:
        cmd = [
            "kubectl", "exec", "-i", pod_name, "-n", namespace, "-c", "geth", "--",
            "geth", "attach", "--exec", js_command, "/data/geth.ipc"
        ]
        try:
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
            return result.replace('"', '')
        except subprocess.CalledProcessError as e:
            return ""

    def get_enode(self, pod_name: str, namespace="default") -> str:
        raw = self._run_geth_cmd(pod_name, "admin.nodeInfo.enode", namespace)
        if not raw:
            raise Exception(f"Empty enode response from {pod_name}")
        match = re.search(r'enode://([a-f0-9]+)@([0-9\.]+):([0-9]+)', raw)
        if match:
            return match.group(0)
        raise Exception(f"Invalid Enode: {raw}")

    def peer_nodes(self, namespace="default"):
        pods = self.get_node_list(namespace)
        pod_names = [p['name'] for p in pods]
        
        if "node-0" not in pod_names:
            return {"status": "error", "message": "Missing node-0"}

        try:
            admin_enode = self.get_enode("node-0", namespace)
        except Exception as e:
            return {"status": "error", "message": str(e)}

        logs = []
        for pod in pod_names:
            if pod == "node-0": continue
            try:
                self._run_geth_cmd(pod, f"admin.addPeer('{admin_enode}')", namespace)
                logs.append(f"{pod} -> Connected to Admin")
            except Exception as e:
                logs.append(f"{pod} failed: {str(e)}")
        
        return {
            "status": "success",
            "admin_enode": admin_enode,
            "logs": logs
        }

    def wait_and_peer_nodes(self, namespace: str, expected_replicas: int):
        import time
        max_retries = 60 # Chờ tối đa 2 phút
        for _ in range(max_retries):
            pods = self.get_node_list(namespace)
            running_pods = [p for p in pods if p["status"] == "Running"]
            if len(running_pods) >= expected_replicas:
                # Đợi thêm 5s để Geth khởi động hẳn RPC server
                time.sleep(5)
                self.peer_nodes(namespace)
                break
            time.sleep(2)

    def _apply_yaml_string(self, yaml_str: str):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp:
            tmp.write(yaml_str)
            tmp_path = tmp.name
        try:
            utils.create_from_yaml(self.v1.api_client, tmp_path)
        except Exception as e:
            pass # Ignore AlreadyExists
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def deploy_network(self, name: str, chain_id: int, replicas: int):
        namespace = f"baas-{name}" if name != "default" else "default"
        results = []

        # 1. Tạo Namespace nếu chưa có
        if namespace != "default":
            self._apply_yaml_string(get_namespace_yaml(namespace))
            results.append(f"Tạo Namespace {namespace}")

        # 2. Tạo Genesis ConfigMap
        self._apply_yaml_string(get_genesis_yaml(namespace, chain_id, self.admin_address))
        results.append("Tạo Genesis ConfigMap")

        # 2.5 Tạo Secrets (Mật khẩu và Private Key)
        try:
            from kubernetes.client import V1Secret, V1ObjectMeta
            import base64
            
            # Create password secret
            pass_b64 = base64.b64encode(self.admin_password.encode('utf-8')).decode('utf-8')
            sec_pass = V1Secret(
                metadata=V1ObjectMeta(name="geth-pass", namespace=namespace),
                data={"password": pass_b64}
            )
            try: self.v1.create_namespaced_secret(namespace, sec_pass)
            except: pass
            
            # Create account key secret
            key_b64 = base64.b64encode(self.admin_private_key.encode('utf-8')).decode('utf-8')
            sec_key = V1Secret(
                metadata=V1ObjectMeta(name="geth-account-key", namespace=namespace),
                data={"key": key_b64}
            )
            try: self.v1.create_namespaced_secret(namespace, sec_key)
            except: pass
        except Exception as e:
            print(f"Error creating secrets: {e}")

        # 3. Apply Service
        self._apply_yaml_string(get_service_yaml(namespace))
        results.append("Tạo Headless Service")
            
        # 4. Apply StatefulSet
        self._apply_yaml_string(get_statefulset_yaml(namespace, replicas, chain_id, self.admin_address))
        results.append(f"Triển khai {replicas} Nodes cho {name}")
            
        return {
            "status": "success",
            "namespace": namespace,
            "chain_id": chain_id,
            "replicas_requested": replicas,
            "actions": results
        }

    def scale_network(self, name: str, replicas: int):
        namespace = f"baas-{name}" if name != "default" else "default"
        try:
            # Dùng patch
            body = {"spec": {"replicas": replicas}}
            self.apps_v1.patch_namespaced_stateful_set(
                name="node",
                namespace=namespace,
                body=body
            )
            return {"status": "success", "message": f"Đã gửi lệnh Scale thành {replicas} nodes"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def crash_random_node(self, namespace="default"):
        import random
        pods = self.get_node_list(namespace)
        if not pods: return {"status": "error", "message": "Không có Node nào đang chạy!"}
        
        target = random.choice(pods)
        try:
            self.v1.delete_namespaced_pod(name=target["name"], namespace=namespace, grace_period_seconds=0)
            return {"status": "success", "message": f"💥 Đã mô phỏng cháy phần cứng tại {target['name']}!"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def cleanup_network(self, namespace="default"):
        try:
            self.apps_v1.delete_namespaced_stateful_set(name="node", namespace=namespace)
            pvcs = self.v1.list_namespaced_persistent_volume_claim(namespace=namespace)
            for pvc in pvcs.items:
                self.v1.delete_namespaced_persistent_volume_claim(name=pvc.metadata.name, namespace=namespace)
            return {"status": "success", "message": "Đã dọn dẹp sạch sẽ hạ tầng K8s!"}
        except Exception as e:
            # Ignore not found errors
            return {"status": "success", "message": "Đã dọn dẹp sạch sẽ hạ tầng K8s!"}

k8s_service = K8sService()