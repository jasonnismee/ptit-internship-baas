# Hướng dẫn chi tiết dự án Blockchain-as-a-Service (BaaS) Orchestrator 2.0

## Các tính năng cốt lõi

1. **Khởi tạo Mạng Blockchain "1 Click" (Multi-tenancy):**
   Tạo ra vô số mạng lưới Private Blockchain độc lập chỉ bằng việc nhập Tên mạng và Số Node. K8s sẽ tự động sinh mã và cấp phát tài nguyên riêng biệt.
2. **Trực quan hóa Mạng lưới (Network Topology):**
   Biểu đồ mạng nhện tương tác vật lý. Các Node xuất hiện dưới dạng các thực thể phát sáng (Cam: Đang khởi tạo, Xanh: Đang chạy). Các đường tia laser biểu thị kết nối Mesh giữa các máy chủ.
3. **Mở rộng tài nguyên (Dynamic Scaling) & Auto-Mesh:**
   Tăng giảm sức mạnh mạng lưới chỉ với 1 nút bấm. Hệ thống chạy ngầm Background Task để tự động kết nối mạng lưới (Auto-Peer) sau khi scale mà không làm đứt gãy hệ thống.
4. **Giám sát Thời gian thực (Real-time Live Metrics):**
   API tự động hỏi thăm các Node Blockchain mỗi 4 giây để lấy các chỉ số trực tiếp như: Chiều cao Khối (Block Height), Tốc độ Giao dịch (TPS), và Số lượng Peer.
5. **Cảnh báo (Threat Alerts) & Terminal Ảo:**
   Màn hình console ma trận chạy chữ liên tục, hút dòng Log thực tế từ dưới lõi Kubernetes đưa lên giao diện. Cùng với đó là hệ thống dò lỗi tự động thông báo khi có Node sập mạng.
6. **Enterprise Observability (Grafana):**
   Tích hợp sâu Prometheus và Grafana để thu thập thông số tài nguyên (RAM, CPU) ở cấp độ Phần cứng máy chủ.

---

## Phần 1: Khởi tạo Dữ liệu Cốt lõi (Chỉ làm 1 lần)

Hệ thống cần 1 tài khoản ví Admin (Private Key & Password) lưu trong Kubernetes Secret để dùng chung cho việc khởi tạo các mạng.

1. Bật môi trường ảo và cài thư viện Backend:
   ```bash
   cd ~/code/ptit-internship-baas
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Chạy script tạo tài khoản:
   ```bash
   python3 src/scripts/generate_account.py
   ```
   *(Script sẽ in ra Private Key và Address)*
3. Lưu Mật khẩu và Private Key vào Kubernetes:
   ```bash
   echo -n "123456" > password.txt
   kubectl create secret generic geth-pass --from-file=password=password.txt
   
   echo -n "<BỎ_0x_PRIVATE_KEY_CỦA_BẠN>" > key.txt
   kubectl create secret generic geth-account-key --from-file=key=key.txt
   ```
4. Cấp quyền cho Backend điều khiển Kubernetes:
   ```bash
   kubectl apply -f infrastructure/k8s/rbac.yaml
   ```

---

## Phần 2: Khởi động Hệ thống Giám sát Phần cứng (Grafana)

Chạy 3 lệnh sau để bật Prometheus và Grafana (Mở tab Terminal mới):
```bash
# 1. Khởi động Prometheus (Tạo sẵn Namespace monitoring)
kubectl apply -f infrastructure/monitoring/prometheus.yaml

# 2. Áp dụng bảng điều khiển (Dashboard) mẫu
kubectl apply -f infrastructure/monitoring/grafana-dashboards.yaml

# 3. Khởi động Grafana
kubectl apply -f infrastructure/monitoring/grafana.yaml
```

**Mở cổng (Port-forward) để truy cập Grafana:**
Do đang chạy K8s nội bộ (Local), bạn cần mở cổng ra ngoài. Hãy chạy lệnh sau và **để nguyên tab Terminal này chạy ngầm (không được tắt)**:
```bash
kubectl port-forward svc/grafana-service 30001:3000 -n monitoring
```
*Lưu ý: Tài khoản đăng nhập mặc định của Grafana trên giao diện là `admin`/`admin`.*

---

## Phần 3: Khởi động Hệ sinh thái BaaS (Backend & Frontend)

**1. Khởi động Backend (Core Orchestrator):**
Mở một Terminal mới:
```bash
cd ~/code/ptit-internship-baas
source venv/bin/activate
cd src/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**2. Khởi động Giao diện Quản trị (Cybernetic Dashboard):**
Mở một Terminal mới. Vì giao diện bản 2.0 có chứa công nghệ vẽ không gian 2D, bạn cần cài đặt nó trước khi chạy:
```bash
cd ~/code/ptit-internship-baas/src/frontend
npm install
npm install react-force-graph-2d
npm run dev
```

**XONG!** Bây giờ bạn chỉ cần truy cập `http://localhost:3000`, toàn bộ đài chỉ huy không gian mạng sẽ hiện ra trước mắt bạn!
