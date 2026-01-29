# Internship Project: Blockchain-as-a-Service (BaaS) Orchestrator

**Sinh viên:** Trịnh Đặng Huy Hoàng
**Mã SV:** B23DCCN345
**GVHD:** ThS. Nguyễn Xuân Đức
**Học phần:** Thực tập cơ sở - INT13147

## 1. Giới thiệu
Dự án xây dựng nền tảng tự động hóa triển khai mạng lưới Private Blockchain trên Kubernetes.
Mục tiêu: Cung cấp giải pháp "One-click deployment" cho hạ tầng Blockchain.

## 2. Công nghệ sử dụng
- **Core:** Kubernetes (K3s/Minikube), Docker.
- **Blockchain:** Geth (Ethereum Private) hoặc Hyperledger Besu.
- **Backend:** Python (FastAPI) để điều phối.
- **DevOps:** GitHub Actions, ArgoCD (GitOps).

## 3. Cấu trúc Source Code
- `/src`: Mã nguồn backend và smart contracts.
- `/infrastructure`: Các file cấu hình K8s (Manifests, Helm Charts).
- `/docs`: Tài liệu báo cáo và nhật ký thực tập.