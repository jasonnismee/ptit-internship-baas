import subprocess
import re
import time

def run_kubectl_command(pod_name, js_command):
    cmd = [
        "kubectl", "exec", "-it", pod_name, "-c", "geth", "--",
        "geth", "attach", "--exec", js_command, "/data/geth.ipc"
    ]

    result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
    return result

def get_enode(pod_name):
    raw_output = run_kubectl_command(pod_name, "admin.nodeInfo.enode")
    match = re.search(r'enode://([a-f0-9]+)@([0-9\.]+):([0-9]+)', raw_output)
    
    if match:
        return match.group(0)
    else:
        raise Exception(f"Không tìm thấy enode: {raw_output}")

def main():
    print("--- BẮT ĐẦU PEERING (STANDARD VERSION) ---")
 
    print("Đang lấy địa chỉ Node-0...")
    try:
        admin_enode = get_enode("node-0")
        print(f"Node-0 Enode: {admin_enode}")
    except Exception as e:
        print(f"Lỗi lấy Node-0: {e}")
        return

    # 2. Peering
    print("Đang kết nối các node...")
    target_nodes = ["node-1", "node-2"]
    
    for node in target_nodes:
        print(f"{node} -> Node-0...")
        js_cmd = f"admin.addPeer('{admin_enode}')"
        
        try:
            result = run_kubectl_command(node, js_cmd)
            clean_result = result.replace('"', '').strip()
            
            if clean_result == "true":
                print(f"Thành công!")
            else:
                print(f"Phản hồi: {clean_result}")
        except Exception as e:
            print(f"Lỗi: {e}")

    print("--- HOÀN TẤT ---")
    print("Đợi 5s đồng bộ mạng lưới...")
    time.sleep(5)

if __name__ == "__main__":
    main()