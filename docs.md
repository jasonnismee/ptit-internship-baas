# Tài liệu Kỹ thuật — PTIT BaaS Orchestrator v1.5.0

> Tài liệu kỹ thuật chi tiết mô tả kiến trúc, thiết kế, và hoạt động nội bộ của hệ thống **Blockchain-as-a-Service Orchestrator** xây dựng trong khuôn khổ thực tập cơ sở INT13147.

---

## 1. Tổng quan Kiến trúc (Architecture Overview)

### 1.1. Mô hình phân lớp

Hệ thống được thiết kế theo kiến trúc **3 lớp tách biệt** (Separation of Concerns):

```
┌──────────────────────────────────┐
│  PRESENTATION LAYER              │
│  Next.js 14 (TypeScript)         │
│  Dashboard + react-force-graph   │
└────────────▬───────────────────┘
             │ REST API (HTTP/JSON)
┌────────────▼───────────────────┘
│  APPLICATION LAYER               │
│  FastAPI v0.109 (Python 3.10)    │
│  K8sService · ContractService    │
└────────────▬───────────────────┘
             │ kubernetes-client SDK
┌────────────▼───────────────────┘
│  INFRASTRUCTURE LAYER            │
│  kind cluster (local)            │
│  Kubernetes StatefulSet, RBAC    │
│  Go-Ethereum (Geth) v1.13.5      │
│  Prometheus + Grafana            │
└──────────────────────────────────┘
```

### 1.2. Luồng dữ liệu (Data Flow)

```
[1] Người dùng gửi POST /api/v1/network/create
      body: { name: "mychain", chain_id: 12345, replicas: 3 }

[2] FastAPI (K8sService.deploy_network) sinh YAML động:
      - Namespace: baas-mychain
      - ConfigMap: genesis.json (chain_id, admin_address, PoA config)
      - Secret: geth-pass, geth-account-key
      - Headless Service: geth-headless (DNS-based discovery)
      - StatefulSet: 3 replicas (node-0, node-1, node-2)

[3] Kubernetes xử lý:
      InitContainer[init-genesis]  → geth init /config/genesis.json
      InitContainer[import-account] → geth account import /etc/secret/key
      MainContainer[geth]          → geth --mine --http --nodiscover

[4] Background Task (wait_and_peer_nodes):
      Chờ tất cả pods đạt trạng thái Running
      → Lấy enode của node-0 qua `kubectl exec geth attach`
      → Gọi admin.addPeer(enode) trên tất cả node còn lại
      → Mạng P2P Mesh được thiết lập

[5] Kết quả: Mạng Blockchain Private hoạt động độc lập
```

---

## 2. Chi tiết Các Module Backend

### 2.1. `K8sService` — Dịch vụ Điều phối Kubernetes

**File:** `src/backend/app/services/k8s_service.py`

Lớp trung tâm của hệ thống, sử dụng `kubernetes-client` Python SDK để tương tác với Kubernetes API Server.

#### Khởi tạo (Constructor)
- Ưu tiên load kubeconfig từ đường dẫn trong `.env` (`KUBE_CONFIG_PATH`)
- Fallback sang `in-cluster config` nếu đang chạy trong Pod
- Khởi tạo `CoreV1Api` và `AppsV1Api` client

#### Các phương thức chính

| Phương thức | Mô tả |
|---|---|
| `deploy_network(name, chain_id, replicas)` | Sinh và apply toàn bộ K8s manifests cho một mạng mới |
| `scale_network(name, replicas)` | Patch `spec.replicas` của StatefulSet (giới hạn 1–8) |
| `peer_nodes(namespace)` | Lấy enode của node-0, gọi `admin.addPeer()` trên các node còn lại |
| `wait_and_peer_nodes(namespace, expected)` | Background task: polling đến khi đủ pods Running rồi auto-peer |
| `crash_random_node(namespace)` | Xóa ngẫu nhiên 1 pod để demo Auto-Healing của K8s |
| `cleanup_network(namespace)` | Xóa StatefulSet và tất cả PVCs |
| `get_network_list()` | Liệt kê namespaces với prefix `baas-` |
| `get_node_list(namespace)` | Liệt kê pods có label `app=geth` |
| `get_network_metrics()` | Truy vấn `eth.blockNumber` và `net.peerCount` qua Geth IPC |

#### Cơ chế Peering (Auto-Mesh)
```python
# 1. Lấy enode của node-0 qua kubectl exec
enode = kubectl exec node-0 -- geth attach --exec "admin.nodeInfo.enode" /data/geth.ipc

# 2. Kết nối tất cả node còn lại tới node-0
for pod in [node-1, node-2, ...]:
    kubectl exec pod -- geth attach --exec f"admin.addPeer('{enode}')" /data/geth.ipc
```

---

### 2.2. `k8s_templates` — Sinh YAML Manifests Động

**File:** `src/backend/app/services/k8s_templates.py`

Module tạo ra YAML manifests dưới dạng chuỗi Python (string templates), được inject các tham số tùy chỉnh:

- **`get_namespace_yaml(namespace)`** — Tạo K8s Namespace
- **`get_genesis_yaml(namespace, chain_id, admin_address)`** — Tạo ConfigMap chứa `genesis.json` với:
  - `chainId` tùy chỉnh (tránh conflict giữa các mạng)
  - `extraData` chứa địa chỉ ví Admin (cấu hình PoA Clique Consensus)
  - Phân bổ 100 ETH ban đầu cho ví Admin
- **`get_service_yaml(namespace)`** — Headless Service (`ClusterIP: None`) cho DNS-based discovery
- **`get_statefulset_yaml(namespace, replicas, chain_id, admin_address)`** — StatefulSet với:
  - InitContainer `init-genesis`: chạy `geth init genesis.json`
  - InitContainer `import-account`: import private key từ K8s Secret
  - MainContainer `geth`: khởi động node với HTTP RPC, Mining, NAT config
  - PVC template: 1Gi storage per node

---

### 2.3. `ContractService` — Biên dịch & Deploy Smart Contract

**File:** `src/backend/app/services/contract_service.py`

```python
def compile_and_deploy_contract(source_code: str, rpc_url: str):
    # 1. Biên dịch Solidity qua py-solc-x (solc v0.8.20)
    compiled = solcx.compile_source(source_code, output_values=["abi", "bin"])
    
    # 2. Kết nối tới RPC node qua web3.py
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # 3. Deploy contract và chờ transaction receipt
    tx_hash = Contract.constructor().transact()
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return { "contract_address": receipt.contractAddress, "abi": abi }
```

---

### 2.4. API Endpoints

**File:** `src/backend/app/api/v1/endpoints.py`

#### Network Management APIs

```
POST /api/v1/network/create
Body: { "name": "mychain", "chain_id": 12345, "replicas": 3 }
→ Triển khai cụm K8s mới, kích hoạt background auto-peer

POST /api/v1/network/scale
Body: { "name": "mychain", "replicas": 5 }
→ Patch StatefulSet replicas (clamp 1–8), kích hoạt background auto-peer

GET  /api/v1/networks
→ Danh sách namespace với prefix baas-

GET  /api/v1/nodes?namespace=baas-mychain
→ Danh sách pods (name, ip, status, start_time)

GET  /api/v1/network/topology?namespace=baas-mychain
→ { nodes: [{id, group, status, ip}], links: [{source, target}] }

GET  /api/v1/network/metrics?namespace=baas-mychain
→ { blockHeight, peers, tps }

GET  /api/v1/network/logs?namespace=baas-mychain
→ { logs: ["line1", "line2", ...] }  (tail 15 dòng từ pod đầu tiên)

POST /api/v1/peer?namespace=baas-mychain
→ Kết nối P2P thủ công

POST /api/v1/demo/crash?namespace=baas-mychain
→ Xóa ngẫu nhiên 1 pod, demo Auto-Healing

POST /api/v1/network/cleanup?namespace=baas-mychain
→ Xóa StatefulSet + PVCs + reset Vinamilk state
```

#### Vinamilk Supply Chain APIs

```
POST /api/v1/vinamilk/transaction
Body: { "station": "farm", "amount": 1000 }
→ Tạo giao dịch chuỗi cung ứng
  station values: "farm" | "factory" | "transport"
  Giao dịch chỉ CONFIRMED khi active_nodes >= 4

GET  /api/v1/vinamilk/state?namespace=baas-mychain
→ {
    inventory: { farm, factory, transport, warehouse },
    transactions: [...],
    active_nodes: N,
    min_consensus: 4,
    total_nodes: N
  }
```

---

## 3. Smart Contract — VinamilkTracker

**File:** `src/smart-contracts/VinamilkTracker.sol`

### Thiết kế Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VinamilkTracker {
    enum Status { AtFarm, AtFactory, InTransit, AtRetailer, Sold }

    struct MilkBatch {
        string batchId;
        string farmLocation;
        Status currentStatus;
        uint256 timestamp;
        address registeredBy;
    }

    mapping(string => MilkBatch) public batches;
    string[] public batchList;

    event StatusUpdated(string batchId, Status status, string location, uint256 time);

    function registerBatch(string memory _batchId, string memory _farm) public;
    function updateStatus(string memory _batchId, Status _newStatus, string memory _location) public;
    function getBatchInfo(string memory _batchId) public view returns (...);
}
```

### Cơ chế Đồng thuận Demo (Business Logic)

Hệ thống mô phỏng đồng thuận ở tầng Backend:

| Điều kiện | Trạng thái Giao dịch |
|---|---|
| `active_nodes >= 4` | `CONFIRMED` — Đủ quorum đồng thuận |
| `active_nodes < 4` | `PENDING` — Chờ đủ node |
| Node sập, còn < 4 nodes | Giao dịch mới bị PENDING, giao dịch cũ giữ nguyên |
| Node được K8s phục hồi, >= 4 | Tất cả PENDING → tự động CONFIRMED |

---

## 4. Hạ tầng Kubernetes

### 4.1. StatefulSet — Node Blockchain

**File:** `infrastructure/k8s/statefulset.yaml`

| Thành phần | Chi tiết |
|---|---|
| Image | `ethereum/client-go:v1.13.5` |
| Init Container 1 | `init-genesis`: `geth init /config/genesis.json` (idempotent) |
| Init Container 2 | `import-account`: Import private key từ K8s Secret |
| Main Container | `geth --mine --http --nodiscover --allow-insecure-unlock` |
| Storage | PVC 1Gi/node (ReadWriteOnce) |
| Ports | 8545 (HTTP RPC), 30303 (P2P) |
| Network ID | 12345 (có thể thay đổi qua `chain_id`) |

**NAT Configuration:** Mỗi pod lấy IP động của chính mình qua `hostname -i` và cấu hình `--nat extip:$POD_IP` để đảm bảo enode advertisement chính xác trong K8s network.

### 4.2. Headless Service

```yaml
clusterIP: None   # Headless — DNS-based discovery
selector:
  app: geth
ports:
  - port: 8545    # RPC
  - port: 30303   # P2P
```

DNS Pattern: `node-0.geth-headless.<namespace>.svc.cluster.local`

### 4.3. RBAC

**File:** `infrastructure/k8s/rbac.yaml`

Backend cần quyền quản trị để điều phối Kubernetes:

```yaml
# ServiceAccount: baas-backend-sa
# ClusterRole: Quyền CRUD trên pods, statefulsets, services, namespaces, pvcs, secrets, configmaps
# ClusterRoleBinding: Gắn ClusterRole vào ServiceAccount
```

### 4.4. GitOps với ArgoCD

**File:** `infrastructure/k8s/argocd-app.yaml`

```yaml
source:
  repoURL: 'https://github.com/hhoan/ptit-internship-baas.git'
  path: infrastructure/k8s    # Theo dõi toàn bộ thư mục này
syncPolicy:
  automated:
    prune: true      # Xóa tài nguyên không còn trong Git
    selfHeal: true   # Tự đồng bộ nếu ai đó sửa trực tiếp trên cluster
```

---

## 5. Cấu hình Hệ thống

### 5.1. Backend `.env`

**File:** `src/backend/.env`

```env
PROJECT_NAME="BaaS Orchestrator"
KUBE_CONFIG_PATH="~/.kube/config"
```

### 5.2. Cấu hình Pydantic Settings

**File:** `src/backend/app/core/config.py`

```python
class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    KUBE_CONFIG_PATH: str
    
    class Config:
        env_file = ".env"
```

### 5.3. CORS

Backend cho phép tất cả origin (`allow_origins=["*"]`) để Frontend tại port 3000 có thể gọi API tại port 8000 trong môi trường development.

---

## 6. CI/CD Pipeline

### GitHub Actions

**File:** `.github/workflows/ci.yml`

Pipeline được cấu hình để chạy mỗi khi push lên nhánh `main` (trong phạm vi `src/backend/`, `Dockerfile`, `requirements.txt`):

1. **Trigger:** Push lên `main`
2. **Build:** `docker build` từ `Dockerfile` — kiểm tra image build thành công
3. **Validate only:** `push: false` — **không push lên Docker Hub**, chỉ xác nhận image có thể build được

```yaml
# .github/workflows/ci.yml
- name: Build Docker Image (CI Validation)
  uses: docker/build-push-action@v4
  with:
    context: .
    push: false      # Chỉ build, không push
    tags: test-backend:latest
```

> **Ghi chú:** Đây là bước CI cơ bản (≤ validation). Việc push image và deploy lên cluster hiện đang được thực hiện thủ công.

### GitOps với ArgoCD (Mô hình chuẩn bị sẵn)

**File:** `infrastructure/k8s/argocd-app.yaml`

Manifest ArgoCD đã được viết sẵn với cấu hình GitOps đầy đủ:

```yaml
source:
  repoURL: 'https://github.com/hhoan/ptit-internship-baas.git'
  path: infrastructure/k8s
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

Khi cần kích hoạt (sau khi cài ArgoCD lên cluster):
```bash
kubectl apply -f infrastructure/k8s/argocd-app.yaml
```

---

## 7. Monitoring Stack

### Prometheus

**File:** `infrastructure/monitoring/prometheus.yaml`

Thu thập metrics từ:
- Kubernetes node exporter (RAM, CPU, Disk I/O)
- Geth node metrics (nếu bật `--metrics`)

### Grafana

**File:** `infrastructure/monitoring/grafana.yaml`

- Deployment trên namespace `monitoring`
- Port-forward: `kubectl port-forward svc/grafana-service 30001:3000 -n monitoring`
- Credentials mặc định: `admin/admin`

---

## 8. Scripts Tiện ích

### `generate_account.py`

Tạo cặp `Private Key` và `Ethereum Address` dùng làm tài khoản Admin cho tất cả mạng blockchain trong hệ thống.

```bash
python3 src/scripts/generate_account.py
# Output:
# Private Key: a91239b...
# Address:     0xe66010...
```

### `peer_nodes.py`

Script kết nối P2P thủ công, hữu ích để debug khi background auto-peer thất bại.

### `check_health.py`

Kiểm tra sức khỏe cluster: trạng thái pods, kết nối API server.

---

## 9. Phân tích Kỹ thuật — Điểm nổi bật

### 9.1. Infrastructure Agnostic

Kubernetes tạo lớp trừu tượng giúp hệ thống chạy mà không cần thay đổi code trên:
- `WSL2 + kind` (môi trường development hiện tại)
- `AWS EKS` / `Google GKE` / `Azure AKS`
- `K3s` trên bare-metal server

### 9.2. Multi-tenancy

Mỗi mạng blockchain có Namespace K8s riêng biệt (`baas-<name>`), hoàn toàn cách ly tài nguyên:
- Không chia sẻ volume, network, secret
- Có thể chạy nhiều mạng song song với chain_id khác nhau

### 9.3. Auto-Healing

StatefulSet đảm bảo số replicas luôn đúng với `spec.replicas`. Khi 1 node sập:
- Kubernetes phát hiện pod `Failed` → tự tạo pod mới
- Pod mới chạy InitContainers → đồng bộ lại blockchain data từ peers
- Mạng tiếp tục hoạt động nếu còn đủ node đồng thuận

### 9.4. Background Task Pattern

API `create` và `scale` sử dụng FastAPI `BackgroundTasks` để không chặn response:
```python
@router.post("/network/create")
def create(req, background_tasks: BackgroundTasks):
    result = k8s_service.deploy_network(...)
    background_tasks.add_task(k8s_service.wait_and_peer_nodes, namespace, replicas)
    return result  # Trả về ngay, peering chạy ngầm
```

---

## 10. Giới hạn Hiện tại & Hướng Phát triển

### Giới hạn

| Vấn đề | Mô tả |
|---|---|
| Admin key hardcoded | Private key Admin được nhúng cứng trong `k8s_service.py` — cần chuyển sang K8s Secret hoàn toàn |
| TPS giả lập | Giá trị TPS trong `/metrics` là random, chưa đo thực tế từ Geth mempool |
| Single namespace RPC | `get_rpc_url` chỉ hỗ trợ lấy IP node-0, chưa có Ingress/LoadBalancer |
| Max replicas = 8 | Giới hạn cứng trong code, cần cấu hình hóa |

### Hướng Phát triển

- [ ] Tích hợp Hyperledger Besu thay thế / song song Geth
- [ ] Hỗ trợ PoS (Proof of Stake) consensus
- [ ] Helm Chart để deploy hệ thống lên production cluster
- [ ] Multi-user authentication với JWT
- [ ] Tích hợp Grafana dashboard tự động cho từng mạng
- [ ] WebSocket API cho realtime log streaming

---

*Tài liệu này được viết bởi **Trịnh Đặng Huy Hoàng** (B23DCCN345) — PTIT, 2026.*
