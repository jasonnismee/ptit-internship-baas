# Khảo sát Các Nghiên cứu và Ứng dụng Blockchain-as-a-Service (BaaS)

Tài liệu này tổng hợp, phân loại và đánh giá các hệ thống công nghệ, nền tảng Blockchain-as-a-Service (BaaS) hiện có trên thị trường. Việc khảo sát này đóng vai trò quan trọng làm nền tảng lý luận để biện minh cho quyết định tự xây dựng kiến trúc BaaS Orchestrator trên Kubernetes trong dự án này.

## 1. Phân loại theo nhóm giải pháp BaaS

Hệ sinh thái Blockchain-as-a-Service hiện tại có thể được phân loại thành 3 nhóm chính dựa trên đặc điểm về quyền kiểm soát (control), môi trường triển khai (deployment environment), và tính chất mạng lưới (public/private).

### Nhóm 1: Public Node-as-a-Service (NaaS) cho Public Blockchain
- **Đại diện tiêu biểu:** Infura, Alchemy, QuickNode.
- **Tiêu chí/Đặc trưng:** Cấp quyền truy cập trực tiếp (thông qua API/RPC) vào các node của các mạng public blockchain (Ethereum, Polygon, Solana...) mà không cần khách hàng tự vận hành và duy trì các node này.

### Nhóm 2: Enterprise Cloud-based BaaS (Managed Blockchain)
- **Đại diện tiêu biểu:** Amazon Managed Blockchain (AWS), IBM Blockchain Platform, Microsoft Azure Blockchain Service (từng tồn tại).
- **Tiêu chí/Đặc trưng:** Hướng tới đối tượng Enterprise / Doanh nghiệp. Cung cấp hạ tầng để triển khai các mạng Private hoặc Consortium (Hyperledger Fabric, Ethereum Private) một cách nhanh chóng trên hạ tầng Cloud độc quyền của nhà cung cấp, với mục đích quản lý chuỗi cung ứng, tài chính, nội bộ.

### Nhóm 3: Self-managed Orchestration (Platform-agnostic)
- **Đại diện tiêu biểu:** Các kiến trúc triển khai mã nguồn mở hoặc dựa trên Cloud Native stack (như Kubernetes Helm charts cho Hyperledger / Geth), Kaleido (lai giữa managed và self-managed nhiều cloud). Điển hình chính là cách tiếp cận của dự án **BaaS Orchestrator** hiện tại.
- **Tiêu chí/Đặc trưng:** Sử dụng công cụ DevOps (K8s, GitOps, Terraform) để tự động hóa quá trình sinh node trên hạ tầng Cloud trung lập (Agnostic) hay On-premise, thay vì phụ thuộc dịch vụ quản lý (managed service) của một Cloud Provider.

---

## 2. Phân tích, đánh giá Ưu và Nhược điểm từng nhóm

### 2.1. Nhóm Public Node-as-a-Service (Infura, Alchemy)
**Khảo sát:** Các nền tảng này phục vụ chủ yếu cho các nhà phát triển dApp không muốn đối mặt với việc lưu trữ vài Terabyte dữ liệu của Public Blockchain trên máy chủ riêng biệt.
- **Ưu điểm:**
  - Tiện lợi, có thể sử dụng được ngay lập tức chỉ với 1 đường link API url.
  - Rất nhanh, hệ thống hạ tầng phía sau xử lý load balancing rất tốt.
- **Nhược điểm:**
  - **Tính phi tập trung giả tạo (Centralized choke point):** Khiến mạng blockchain bị phân mảnh và phụ thuộc. Ví dụ khi Infura sập, phần lớn hệ sinh thái Ethereum gặp lỗi liên đới.
  - **Thiếu tùy chỉnh:** Khách hàng không thể thay đổi thuật toán đồng thuận, sửa đổi file cấu hình `genesis` hoặc tự lập mạng private với node của nhóm này. Tính riêng tư cho dữ liệu doanh nghiệp không được đảm bảo.

### 2.2. Nhóm Enterprise Cloud-based BaaS (AWS Managed Blockchain, IBM)
**Khảo sát:** Là các dịch vụ khổng lồ dành cho các tập đoàn, giúp triển khai mạng riêng chỉ qua một vài nút bấm trên UI của AWS hoặc IBM.
- **Ưu điểm:**
  - Độ ổn định cực kỳ cao với SLA chuẩn doanh nghiệp.
  - Tích hợp sâu vào công cụ theo dõi, bảo mật sẵn có của hệ sinh thái (như AWS KMS, CloudWatch, IAM).
- **Nhược điểm:**
  - **Vendor Lock-in (Trói buộc nhà cung cấp):** Khi mạng lưới phát triển, việc di chuyển (migrate) node từ hệ sinh thái AWS sang Azure hay server On-premise là cực kỳ khó khăn.
  - **Chi phí cực khủng:** Phí duy trì các node dạng managed trên Cloud provider thường rất cao (tính bằng hàng chục đến hàng trăm USD/ngày cho các cấu hình enterprise).
  - Tùy chỉnh ở mức cấu trúc hạt nhân (như can thiệp cách peer node) thường bị chặn đứng bởi nhà cung cấp.

### 2.3. Nhóm Self-managed Orchestration / Cloud-Native BaaS (Hệ thống dự án đang hướng tới)
**Khảo sát:** Xây dựng hệ thống điều phối bằng Kubernetes, tự sinh và setup Docker container chứa Geth thông qua Backend (FastAPI).
- **Ưu điểm:**
  - **Giành quyền kiểm soát 100%:** Khả năng tùy chỉnh mọi cơ chế từ `genesis.json`, cơ chế PEER discovery đến Thuật toán đồng thuận (PoA/PoW), mà không bị giới hạn.
  - **Infrastructure Agnostic:** Hạ tầng Kubernetes tạo ra một lớp trừu tượng (abstraction), giúp dễ dàng bưng dự án triển khai ở bất kỳ đâu (Máy local WSL/Minikube, AWS EKS, Google GKE, hay Bare-metal) mà cấu hình/manifest không đổi. Không còn Vendor lock-in.
  - **Tiết kiệm chi phí vận hành:** Sử dụng tối ưu tài nguyên của máy chủ vật lý, phù hợp với doanh nghiệp vừa và nhỏ hoặc mục tiêu giáo dục, demo thay vì phải gánh chi phí khổng lồ của Enterprise Cloud BaaS.
- **Nhược điểm:**
  - Độ khó khởi tạo rất cao: Đòi hỏi kĩ sư (người thực hiện dự án) phải rất am hiểu phối hợp hệ sinh thái đa dạng (K8s, CI/CD, Python, Blockchain P2P network).
  - Cần tự xây dựng cơ sở hạ tầng giám sát và phục hồi (tuy nhiên dự án đã giải quyết bằng kịch bản Auto-healing và ArgoCD GitOps).

---

## 3. Tổng kết

Việc khảo sát các nền tảng Blockchain-as-a-Service hiện tại cho thấy một khoảng trống lớn:
1. Public NaaS không phù hợp với nhu cầu thiết lập mạng riêng tùy chỉnh sâu.
2. Cloud-based BaaS tuy mạnh nhưng quá tốn kém và độc quyền.

Dựa trên việc hệ thống hóa này, quyết định sử dụng **Kubernetes và FastAPI để điều phối kiến trúc Custom BaaS** trong dự án hoàn toàn giải quyết được nhược điểm của các nghiên cứu hiện tại: Đem lại sự trung lập về hạ tầng (Agnostic), giúp khách hàng chủ động 100% về cấu hình, với chi phí tối thiểu nhưng vẫn đảm bảo sức mạnh chịu tải và auto-scaling chuẩn DevOps. Mảnh ghép này hoàn thiện hoàn toàn năng lực thiết kế kiến trúc hệ thống của dự án.
