# PTIT BaaS Orchestrator
> **Blockchain-as-a-Service** — Nền tảng tự động hóa triển khai mạng Private Blockchain trên Kubernetes

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-kind-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Ethereum](https://img.shields.io/badge/Geth-v1.13.5-3C3C3D?style=for-the-badge&logo=ethereum&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## Thông tin Dự án

| Thông tin | Chi tiết |
|---|---|
| **Sinh viên** | Trịnh Đặng Huy Hoàng |
| **Mã sinh viên** | B23DCCN345 |
| **Giảng viên hướng dẫn** | ThS. Nguyễn Xuân Đức |
| **Học phần** | Thực tập cơ sở — INT13147 |
| **Phiên bản hệ thống** | v1.5.0 |

---

## Giới thiệu

**PTIT BaaS Orchestrator** là một nền tảng **Cloud Infrastructure** cung cấp giải pháp *"One-click deployment"* để tự động hóa hoàn toàn việc triển khai và quản lý mạng lưới **Private Blockchain (Geth/Ethereum)** trên hạ tầng **Kubernetes**.

Dự án giải quyết khoảng trống lớn trong hệ sinh thái BaaS hiện tại:
- **Public NaaS** (Infura, Alchemy): Không hỗ trợ mạng private, gây Vendor Lock-in với public chain.
- **Enterprise Cloud BaaS** (AWS, IBM): Tốn kém hàng chục–hàng trăm USD/ngày, bị trói buộc vào một Cloud Provider.
- **Self-managed BaaS (Dự án này)**: Toàn quyền kiểm soát, triển khai mọi nơi (Local/Cloud/Bare-metal), chi phí tối thiểu.

---

## Tính năng cốt lõi

| # | Tính năng | Mô tả |
|---|---|---|
| 1 | **One-click Network Deploy** | Tạo mạng Blockchain private độc lập chỉ bằng API call — Kubernetes tự động cấp phát tài nguyên |
| 2 | **Dynamic Scaling + Auto-Mesh** | Tăng/giảm số node realtime, Background Task tự động kết nối P2P (auto-peer) sau khi scale |
| 3 | **Network Topology Visualization** | Đồ thị mạng nhện tương tác, hiển thị trạng thái node và kết nối Mesh theo thời gian thực |
| 4 | **Live Metrics Dashboard** | Thu thập Block Height, TPS, Peer Count trực tiếp từ Geth node mỗi 4 giây |
| 5 | **Auto-Healing Demo** | Mô phỏng kịch bản node sập — Kubernetes tự khôi phục, hệ thống tiếp tục đồng thuận |
| 6 | **Smart Contract Deployment** | Biên dịch & deploy Solidity contract lên mạng private qua API |
| 7 | **Vinamilk Supply Chain Demo** | Use-case doanh nghiệp: Truy xuất nguồn gốc sản phẩm với cơ chế đồng thuận tối thiểu 4 node |
| 8 | **Enterprise Observability** | Tích hợp Prometheus + Grafana giám sát tài nguyên phần cứng (RAM, CPU) |
| 9 | **CI Validation** | GitHub Actions tự động build & kiểm tra Docker image khi push lên nhánh `main` |

---

##  Kiến trúc Hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER / CLIENT                              │
│           Next.js Dashboard  │  REST API Client                 │
└─────────────────┬────────────────────────────────────────────── ┘
                  │ HTTP (port 3000 / port 8000)
┌─────────────────▼────────────────────────────────────────────── ┐
│                  BACKEND — FastAPI (Python 3.10)                │
│   /api/v1/network/create   →  K8s Orchestration Service         │
│   /api/v1/network/scale    →  StatefulSet Patch                 │
│   /api/v1/peer             →  Auto P2P Mesh                     │
│   /api/v1/vinamilk/*       →  Supply Chain Business Logic       │
└─────────────────┬────────────────────────────────────────────── ┘
                  │ kubernetes-client (Python SDK)
┌─────────────────▼────────────────────────────────────────────── ┐
│              KUBERNETES CLUSTER (kind — Kubernetes in Docker)   │
│                                                                 │
│  Namespace: baas-<name>                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  node-0  │  │  node-1  │  │  node-2  │  │  node-N  │         │
│  │  (Geth)  │◄─┤  (Geth)  │◄─┤  (Geth)  │  │  (Geth)  │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
│       │ ConfigMap: genesis.json                                 │
│       │ Secret: geth-pass, geth-account-key                     │
│       │ PVC: 1Gi/node                                           │
└─────────────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────────── ┐
│              MONITORING — Prometheus + Grafana                  │
│              CI         — GitHub Actions (build validation)     │
│              GitOps     — ArgoCD manifest (infrastructure/k8s/) │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
```
User gửi POST /api/v1/network/create
  → FastAPI sinh genesis.json, Service, StatefulSet YAML
  → Apply lên Kubernetes Cluster
  → K8s pull image ethereum/client-go:v1.13.5
  → InitContainers: khởi tạo genesis, import account
  → Geth nodes khởi động, mine block
  → Background Task: chờ pods Running → auto-peer
  → Mạng Blockchain hoạt động đầy đủ 
```

---

## Cấu trúc Source Code

```
ptit-internship-baas/
├── src/
│   ├── backend/                    # Core Backend (FastAPI)
│   │   ├── app/
│   │   │   ├── main.py             # Entry point, CORS, Router
│   │   │   ├── api/v1/
│   │   │   │   └── endpoints.py    # Tất cả API Endpoints
│   │   │   ├── core/
│   │   │   │   └── config.py       # Cấu hình qua .env (Pydantic Settings)
│   │   │   ├── services/
│   │   │   │   ├── k8s_service.py  # Kubernetes Orchestration Logic
│   │   │   │   ├── k8s_templates.py # Sinh YAML Manifests động
│   │   │   │   └── contract_service.py # Biên dịch & Deploy Smart Contract
│   │   │   └── static/
│   │   │       └── index.html      # Glassmorphism Dashboard (Fallback)
│   │   └── .env                    # Biến môi trường Backend
│   ├── frontend/                   # Next.js 14 Dashboard
│   │   ├── src/
│   │   │   └── app/                # App Router
│   │   ├── package.json
│   │   └── tailwind.config.ts
│   ├── smart-contracts/
│   │   └── VinamilkTracker.sol     # Solidity Contract (Truy xuất chuỗi cung ứng)
│   └── scripts/
│       ├── generate_account.py     # Tạo cặp Private Key / Address
│       ├── peer_nodes.py           # Script kết nối P2P thủ công
│       └── check_health.py         # Kiểm tra sức khỏe cluster
├── infrastructure/
│   ├── genesis.json                # Genesis Block configuration
│   ├── k8s/
│   │   ├── statefulset.yaml        # StatefulSet định nghĩa Geth nodes
│   │   ├── service.yaml            # Headless Service (P2P Discovery)
│   │   ├── backend.yaml            # Deployment + Service cho Backend
│   │   ├── rbac.yaml               # RBAC quyền điều khiển K8s cho Backend
│   │   └── argocd-app.yaml         # ArgoCD GitOps Application
│   └── monitoring/
│       ├── prometheus.yaml         # Prometheus scrape config
│       ├── grafana.yaml            # Grafana deployment
│       └── grafana-dashboards.yaml # Dashboard provisioning
├── Dockerfile                      # Build image cho Backend
├── requirements.txt                # Python dependencies
├── tutorial.md                     # Hướng dẫn khởi động hệ thống
└── README.md                       # Tài liệu này
```

---

## Hướng dẫn Khởi động Nhanh

### Yêu cầu hệ thống

- **OS:** WSL2 (Ubuntu 22.04) hoặc Linux
- **Runtime:** Docker Desktop (với WSL2 backend), Python 3.10+, Node.js 18+
- **Kubernetes:** [`kind`](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- **Tools:** `kubectl`, `kind`, `git`

> **Tạo cluster kind nhanh:**
> ```bash
> kind create cluster --name baas
> kubectl cluster-info --context kind-baas
> ```

### Bước 1 — Cài đặt môi trường Python

```bash
cd ~/code/ptit-internship-baas
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Bước 2 — Khởi tạo tài khoản Admin (Chỉ làm 1 lần)

```bash
# Tạo cặp Private Key / Address
python3 src/scripts/generate_account.py

# Lưu vào Kubernetes Secrets
echo -n "password123" > password.txt
kubectl create secret generic geth-pass --from-file=password=password.txt

echo -n "<PRIVATE_KEY_KHÔNG_CÓ_0x>" > key.txt
kubectl create secret generic geth-account-key --from-file=key=key.txt

# Cấp quyền RBAC cho Backend
kubectl apply -f infrastructure/k8s/rbac.yaml
```

### Bước 3 — Khởi động Backend

```bash
cd src/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> API Docs tự động: `http://localhost:8000/api/v1/openapi.json`  
> Swagger UI: `http://localhost:8000/docs`

### Bước 4 — Khởi động Frontend

```bash
cd src/frontend
npm install
npm run dev
```

> Dashboard: `http://localhost:3000`

### Bước 5 — (Tùy chọn) Bật Monitoring Stack

```bash
kubectl apply -f infrastructure/monitoring/prometheus.yaml
kubectl apply -f infrastructure/monitoring/grafana.yaml
kubectl apply -f infrastructure/monitoring/grafana-dashboards.yaml
# Truy cập Grafana (admin/admin)
kubectl port-forward svc/grafana-service 30001:3000 -n monitoring
```

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/networks` | Danh sách các mạng Blockchain đang chạy |
| `GET` | `/nodes?namespace=<name>` | Danh sách node trong một mạng |
| `POST` | `/network/create` | Tạo mạng Blockchain mới (deploy lên K8s) |
| `POST` | `/network/scale` | Scale số lượng node (1–8) |
| `POST` | `/peer?namespace=<name>` | Kết nối P2P thủ công |
| `GET` | `/network/topology` | Dữ liệu đồ thị mạng (nodes + links) |
| `GET` | `/network/metrics` | Metrics thời gian thực (Block Height, TPS, Peers) |
| `GET` | `/network/logs` | Logs thực tế từ Kubernetes pod |
| `POST` | `/demo/crash` | Mô phỏng node sập (Auto-Healing demo) |
| `POST` | `/network/cleanup` | Xóa toàn bộ hạ tầng K8s của mạng |
| `POST` | `/vinamilk/transaction` | Tạo giao dịch chuỗi cung ứng Vinamilk |
| `GET` | `/vinamilk/state` | Trạng thái kho hàng và danh sách giao dịch |

---

## Smart Contract — VinamilkTracker

```solidity
// Truy xuất nguồn gốc sản phẩm sữa Vinamilk trên Private Blockchain
contract VinamilkTracker {
    enum Status { AtFarm, AtFactory, InTransit, AtRetailer, Sold }
    
    function registerBatch(string memory _batchId, string memory _farm) public;
    function updateStatus(string memory _batchId, Status _newStatus, string memory _location) public;
    function getBatchInfo(string memory _batchId) public view returns (...);
}
```

**Use-case:** Minh họa cơ chế đồng thuận — giao dịch chỉ `CONFIRMED` khi có **≥ 4 node** đang hoạt động, mô phỏng đúng hành vi Byzantine Fault Tolerance.

---

## Tech Stack

| Layer | Công nghệ |
|---|---|
| **Backend** | Python 3.10, FastAPI 0.109, Uvicorn |
| **Blockchain** | Go-Ethereum (Geth) v1.13.5, Solidity 0.8.20 |
| **Kubernetes (local)** | kind (Kubernetes in Docker) |
| **Orchestration** | Kubernetes StatefulSet, RBAC, ConfigMap, Secret, PVC |
| **Frontend** | Next.js 14, TypeScript, TailwindCSS, react-force-graph-2d |
| **Monitoring** | Prometheus, Grafana |
| **CI** | GitHub Actions (build validation) |
| **GitOps (chuẩn bị)** | ArgoCD manifest (`infrastructure/k8s/argocd-app.yaml`) |
| **Container** | Docker (python:3.10-slim base image) |
| **Libraries** | kubernetes-client, web3.py, py-solc-x, pydantic-settings |

---

## Tài liệu liên quan

- [`tutorial.md`](tutorial.md) — Hướng dẫn khởi động chi tiết từng bước
- [`RESEARCH.md`](RESEARCH.md) — Khảo sát và phân tích các giải pháp BaaS trên thị trường
- [`PROGRESS.md`](PROGRESS.md) — Nhật ký tiến độ thực tập
- [`docs.md`](docs.md) — Tài liệu kỹ thuật chi tiết kiến trúc hệ thống

---

<div align="center">

**Học viện Công nghệ Bưu chính Viễn thông (PTIT)**  
*Khoa Công nghệ Thông tin*

</div>