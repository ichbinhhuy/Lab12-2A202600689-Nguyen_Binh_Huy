## 📝 Tổng Hợp Kết Quả Thực Hành (Part 1 - Part 6)

**Học viên:** Nguyễn Bình Huy  
**Mã học viên:** 2A202600689

---

### 🌐 Part 1: Localhost vs Production
*   **Anti-patterns phát hiện được:**
    *   Hardcode API Key và cấu hình trong mã nguồn.
    *   Thiếu ghi nhật ký (logging) dạng JSON có cấu trúc (chỉ dùng `print()`).
    *   Thiếu endpoint kiểm tra trạng thái `/health`.
    *   Cố định Host/Port làm cản trở quá trình container hóa và triển khai Cloud.
*   **So sánh giữa Develop & Production:**
    *   *Cấu hình:* Đã chuyển sang đọc hoàn toàn từ biến môi trường (`.env`).
    *   *Health check:* Tích hợp `/health` và `/ready`.
    *   *Logging:* Chuyển sang định dạng JSON có cấu trúc để phục vụ giám sát tập trung.
    *   *Graceful Shutdown:* Bắt tín hiệu ngắt tiến trình để hoàn tất các request hiện có.

### 🐳 Part 2: Docker Containerization & Orchestration
*   **Tối ưu hóa dung lượng (Multi-stage Build):**
    *   Image Develop (Single-stage): **~1000 MB**
    *   Image Production (Multi-stage, python:3.11-slim): **~150 MB** (Giảm **85%** dung lượng không cần thiết).
*   **Độ bảo mật:** Chạy dưới quyền user không đặc quyền (`agent`).
*   **Kiến trúc Stack (Docker Compose):**
    ```
    Client ──> Nginx (port 80) ──> Agent API (port 8000) ──> Redis (port 6379)
    ```

### ☁️ Part 3: Cloud Deployment (Day 12 Base)
*   Triển khai thành công ứng dụng cơ sở lên Railway Cloud.
*   **URL chạy thực tế:** [https://day12-2a202600689-nguyenbinhhuy-production.up.railway.app/](https://day12-2a202600689-nguyenbinhhuy-production.up.railway.app/)
*   **Tài liệu kiểm chứng:** Xem tại [DEPLOYMENT.md](DEPLOYMENT.md) hoặc thư mục [screenshots/](screenshots/).

### 🔒 Part 4 & 5: Security, Scale & Reliability
*   **Xác thực:** Yêu cầu bắt buộc header `X-API-Key` (trả về `401 Unauthorized` nếu thiếu/sai).
*   **Rate Limiter:** Giới hạn tối đa `10 req/min` trên mỗi client (sử dụng Redis, trả về `429 Too Many Requests` khi vượt ngưỡng).
*   **Cost Guard:** Quản lý ngân quỹ chạy LLM tối đa `$10/tháng/user` bằng Redis.
*   **Stateless Design:** Lịch sử hội thoại lưu tập trung ở Redis để dễ dàng scale-out ra nhiều instance song song.
*   **Graceful Shutdown:** Lắng nghe tín hiệu `SIGTERM` từ container orchestrator để dọn dẹp và kết thúc an toàn.

---

### ☕ Part 6: Lab 06 - AI Cafe Vibe Recommender (Mới)
*   **Tổng quan:** Ứng dụng gợi ý quán cafe dựa trên độ tương đồng về vibe sử dụng mô hình embedding và FastAPI + Redis + HTML/JS Frontend.
*   **Dockerization:** Multi-stage build tối ưu kích thước, cấu hình `HEALTHCHECK` kiểm tra route `/health` định kỳ mỗi 30s.
*   **Security & Stateless:** Tích hợp xác thực khóa API, giới hạn tần suất qua Redis và lưu trữ lịch sử hội thoại stateless trên Redis.
*   **Railway Cloud Deployment:**
    *   **Service Name:** `Lab12-2A202600689-Nguyen_Binh_Huy`
    *   **URL chạy thực tế:** [https://lab12-2a202600689-nguyenbinhhuy-production.up.railway.app/](https://lab12-2a202600689-nguyenbinhhuy-production.up.railway.app/)
    *   **Cấu hình Railway (`railway.toml`):** Tự động phát hiện Dockerfile, restart policy khi gặp lỗi (`ON_FAILURE`).
*   **Độ sẵn sàng (Production-ready):**
    *   Giao diện web trực quan, tải dữ liệu động và ảnh thực tế từ Unsplash.
    *   Đã vượt qua bộ kiểm thử tự động cục bộ: **8/8 test cases** của `pytest` thành công vượt mức mong đợi.
