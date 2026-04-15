### Note 2/2
1. Mục đích tạo file generate_account.py
-> Tạo ra 1 cặp PRIVATE KEY và ADDRESS cho ADMIN

2. Mục đích tạo file genesis.json
-> "Hiến pháp"
-> Nó quy định các thông số khởi đầu. Tất cả các Node muốn tham gia mạng đều phải có file này giống hệt nhau.

3. Mục đích tạo file service.yaml
-> Tạo ra một danh bạ điện thoại nội bộ trong Kubernetes để các Node có thể tìm thấy nhau.

4. Mục đích tạo file statefulset.yaml
-> Bản vẽ thiết kế để Kubernetes xây dựng Node Blockchain.

### Note 8/2
src/backend/
├── app/
│   ├── __init__.py
│   ├── main.py            # Cửa chính của ứng dụng
│   ├── api/               # Chứa các API endpoints
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py
│   ├── core/              # Cấu hình hệ thống (Config, Security)
│   │   ├── __init__.py
│   │   └── config.py
│   └── services/          # Logic nghiệp vụ (Gọi K8s, Tương tác Blockchain)
│       ├── __init__.py
│       └── k8s_service.py
├── tests/
└── .env                   # File chứa biến môi trường (Password, v.v.)

### Note 25/2
## Kiến trúc "Blockchain-as-a-Service" là gì?

# Mô hình hoạt động
1. Khách hàng == User --> Muốn gọi 1 món ăn
2. Phục vụ == Python/FastAPI --> Nhận order từ khách
                             --> Check order hợp lệ hay không?
                             --> Chuyển xuống bếp (nơi xử lý)
3. Bếp trưởng == Kubernetes --> Nhận lệnh từ phục vụ
                            --> Điều phối các công cụ
4. Công cụ == Docker/Geth --> Nồi niêu để nấu ra món ăn (Node Blockchain)
5. Dây chuyền == ArgoCD/GitOps --> Đảm bảo công thức nấu ăn luôn latest

# Data Flow
1. User gửi request --> API
2. FastAPI nhận request --> Tạo các file cấu hình .yaml
3. FastAPI đẩy các file cấu hình vào Cluster
4. Cluster tự động tải Docker Image của Geth về và dựng pods
5. Các nodes này tự tìm tới nhau và sync dữ liệu
