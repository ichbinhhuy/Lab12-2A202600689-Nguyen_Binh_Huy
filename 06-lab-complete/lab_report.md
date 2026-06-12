# Báo cáo triển khai dự án: AI Cafe Vibe Recommender

**Tên học viên**: Nguyễn Bình Huy
**Mã học viên**: 2A202600689

Báo cáo chi tiết về quá trình tối ưu hóa mã nguồn, đóng gói Docker và triển khai lên môi trường đám mây Railway cho dự án **Coffeeholic**.

---

## 1. Tổng quan dự án & Kiến trúc hệ thống
Dự án là một ứng dụng gợi ý quán cafe dựa trên độ tương đồng về vibe (không gian, môi trường) sử dụng các mô hình embedding.

*   **Backend:** FastAPI (Python 3.11), cung cấp các API xử lý logic gợi ý, phản hồi và quản lý dữ liệu quán cafe.
*   **Database/Cache:** Redis (Docker container / Railway Redis database), sử dụng làm bộ lưu trữ dữ liệu phiên và quản lý giới hạn tần suất yêu cầu (Rate Limiter).
*   **Frontend:** Giao diện Web tương tác viết bằng HTML/CSS (Tailwind CDN) và Vanilla JS, được host trực tiếp từ server FastAPI ở root path `/`.
*   **Mô hình Deploy:** Đóng gói bằng Docker và triển khai trực tiếp lên đám mây **Railway**.

---

## 2. Cấu hình Docker & Tối ưu hóa (Production-ready)
Ứng dụng đã được đóng gói tối ưu để chạy mượt mà trong môi trường Docker:

*   **Multi-stage Build (Dockerfile):**
    *   **Stage 1 (Builder):** Sử dụng `python:3.11-slim` để cài đặt các dependency cần thiết (gcc, libpq-dev) và tải các gói thư viện vào `/root/.local`.
    *   **Stage 2 (Runtime):** Chỉ sao chép các thư mục chạy (`app`, `data`, `frontend`, `index.html`) và các thư viện cần thiết từ Stage 1. Môi trường chạy không chứa các công cụ build dư thừa giúp giảm kích thước image tối đa (< 500 MB).
*   **Bảo mật & Phân quyền:**
    *   Không chạy dưới quyền `root`. Image tạo riêng một user hệ thống tên là `agent` và nhóm `agent` để chạy ứng dụng (`USER agent`).
    *   Toàn bộ thư mục ứng dụng `/app` được bàn giao quyền sở hữu cho user này (`chown -R agent:agent /app`).
*   **Kiểm tra sức khỏe (Health Check):**
    *   Tích hợp sẵn chỉ thị `HEALTHCHECK` trong Dockerfile để tự động kiểm tra trạng thái sống của container định kỳ mỗi 30 giây qua route `/health`.
*   **Docker Compose (Local Dev):**
    *   Tạo file `docker-compose.yml` định nghĩa 2 dịch vụ chạy song song: `agent` (Web server trên cổng `8000`) và `redis` (Redis database v7-alpine).
    *   Dịch vụ `agent` phụ thuộc vào trạng thái `healthy` của dịch vụ `redis` (`depends_on` với `service_healthy`).

---

## 3. Triển khai đám mây (Railway Cloud)
Dự án đã được triển khai thành công lên nền tảng đám mây **Railway**:

*   **Thông tin Deployment:**
    *   **Dự án Railway:** `adaptable-spirit`
    *   **Service Name:** `Lab12-2A202600689-Nguyen_Binh_Huy`
    *   **Đường dẫn Public URL:** [https://lab12-2a202600689-nguyenbinhhuy-production.up.railway.app/](https://lab12-2a202600689-nguyenbinhhuy-production.up.railway.app/)
*   **Cấu hình Railway (`railway.toml`):**
    *   Chỉ định sử dụng `DOCKERFILE` làm builder.
    *   Cấu hình `healthcheckPath = "/health"` với thời gian timeout là 60 giây.
    *   Cài đặt chính sách khởi động lại khi gặp lỗi: `restartPolicyType = "ON_FAILURE"` (tối đa 3 lần thử lại).
*   **Các biến môi trường được thiết lập:**
    *   `ENVIRONMENT=production`
    *   `DEBUG=false`
    *   `AGENT_API_KEY=my-secret-key-123`
    *   `REDIS_URL` (Liên kết nội bộ với database Redis được tạo trực tiếp trên Railway)
    *   `PORT` (Cấp phát động từ Railway)

---

## 4. Kết quả kiểm tra tính năng & Độ sẵn sàng

### Các tính năng đã được xác minh:
1.  **Giao diện người dùng Web (HTML/JS):** Hoạt động mượt mà, tải dữ liệu động từ backend và hiển thị ảnh thực tế chất lượng cao từ Unsplash (thay thế cho các URL dummy ban đầu).
2.  **Liveness & Readiness Endpoint:**
    *   `GET /health` -> Trả về trạng thái `"ok"` kèm thời gian chạy (uptime).
    *   `GET /ready` -> Trả về `{"ready":true}` sau khi ping kiểm tra kết nối với Redis thành công.
3.  **Xác thực API Key:** Yêu cầu header `X-API-Key` khi thực hiện các yêu cầu nhạy cảm đến backend, trả về lỗi `401 Unauthorized` nếu khóa không hợp lệ.
4.  **Giới hạn tần suất yêu cầu (Rate Limiter):** Tích hợp thông qua Redis, giới hạn tối đa 10 yêu cầu/phút trên mỗi client. Yêu cầu thứ 11 trong vòng 1 phút sẽ ngay lập tức nhận phản hồi lỗi `429 Too Many Requests`.
5.  **Cost Guard & Graceful Shutdown:** Hỗ trợ kiểm soát ngân sách chạy API và bắt các tín hiệu ngắt `SIGTERM` để tắt máy chủ một cách an toàn mà không làm mất dữ liệu phiên.
6.  **Bộ kiểm thử tự động (Unit Tests):** Chạy `pytest` cục bộ vượt qua **8/8 test cases** thành công trong vòng 0.21 giây.

---

## 5. Kết luận
Dự án đã được tối ưu hóa hoàn thiện theo đúng chuẩn quy trình phát triển phần mềm hiện đại (12-Factor App): tách biệt cấu hình khỏi mã nguồn, bảo mật thông tin nhạy cảm, thiết lập hệ thống log có cấu trúc dạng JSON, và tự động hóa toàn bộ quy trình đóng gói/triển khai lên Cloud bằng Docker. Hệ thống hiện đang chạy cực kỳ ổn định và sẵn sàng bàn giao.
