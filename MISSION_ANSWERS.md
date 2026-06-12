# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcode API Key trong mã nguồn:** Khóa `OPENAI_API_KEY` được đặt trực tiếp trong mã nguồn. Việc này gây rủi ro bảo mật nghiêm trọng nếu mã nguồn được tải lên kho lưu trữ mã nguồn như Github.
2. **Thiếu quản lý cấu hình (Config Management):** Các biến trạng thái như `DEBUG = True` và đường dẫn Database được lập trình cứng (hardcode). Điều này gây khó khăn khi cần chuyển đổi giữa các môi trường khác nhau.
3. **Ghi nhật ký (Log) không an toàn:** Ứng dụng sử dụng hàm `print()` thay vì thư viện `logging` tiêu chuẩn. Việc này không chỉ thiếu kiểm soát mà còn làm rò rỉ khóa `OPENAI_API_KEY` ra màn hình lệnh (console).
4. **Thiếu điểm kiểm tra trạng thái (Health Check):** Hệ thống thiếu các API (`/health`) để hệ thống quản lý bên ngoài có thể theo dõi tình trạng hoạt động hoặc trạng thái lỗi của ứng dụng.
5. **Cố định cấu hình mạng (Port/Host):** Thiết lập `host="localhost"` và `port=8000` làm ứng dụng không thể giao tiếp với bên ngoài môi trường container và không tương thích với các dịch vụ Cloud (thường yêu cầu gán Port động).

### Exercise 1.3: Comparison table
| Feature | Basic (Develop) | Advanced (Production) | Tại sao quan trọng? |
|---------|---------|------------|----------------|
| Cấu hình (Config) | Lập trình cứng trong mã nguồn | Đọc từ Biến môi trường (Environment Variables) | Bảo mật dữ liệu nhạy cảm và dễ dàng thiết lập theo từng môi trường. |
| Kiểm tra trạng thái (Health check) | Không hỗ trợ | Có endpoint `/health` và `/ready` | Giúp hệ thống quản lý (như Docker/Kubernetes) nhận biết tình trạng ứng dụng để tự động phục hồi khi gặp lỗi. |
| Ghi nhật ký (Logging) | Sử dụng lệnh `print()` | Dùng thư viện `logging` (Định dạng JSON) | Dễ dàng quản lý, phân tích lỗi trong tương lai và tránh lộ dữ liệu nhạy cảm. |
| Tắt ứng dụng (Shutdown) | Dừng đột ngột (Ngắt tiến trình) | Dừng có quy trình (Graceful Shutdown) | Đảm bảo các tiến trình và yêu cầu đang xử lý dở dang được hoàn thành trước khi tắt máy chủ. |
| Cấu hình Port | Cố định `localhost:8000` | Đọc biến môi trường `PORT` và host `0.0.0.0` | Đảm bảo Container có thể kết nối với môi trường mạng bên ngoài và nhận Port tự động từ dịch vụ Cloud. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** Sử dụng `python:3.11` (Bản đầy đủ, dung lượng lớn).
2. **Working directory:** Thay đổi thư mục làm việc mặc định thành `/app`.
3. **Tại sao COPY requirements.txt trước?** Nhằm tối ưu hóa bộ nhớ đệm (Cache) của Docker. Do danh sách thư viện ít thay đổi hơn mã nguồn, việc sao chép riêng tệp này giúp Docker không cần cài đặt lại toàn bộ thư viện khi mã nguồn ứng dụng thay đổi.
4. **CMD vs ENTRYPOINT khác nhau thế nào?** `ENTRYPOINT` xác định lệnh gốc sẽ luôn được chạy, trong khi `CMD` cung cấp các tham số mặc định cho `ENTRYPOINT`. Lệnh `CMD ["python", "app.py"]` quy định tệp tin sẽ được thực thi khi vùng chứa (container) bắt đầu hoạt động.

### Exercise 2.3: Image size comparison
*(Dựa trên kết quả thực thi lệnh docker build)*
- Môi trường Develop (Single-stage, python:3.11): ~1000 MB
- Môi trường Production (Multi-stage, python:3.11-slim): ~150 MB
- Mức độ thay đổi (Difference): Dung lượng giảm khoảng 85%. Phương pháp Multi-stage giúp loại bỏ các công cụ hỗ trợ xây dựng (build tools) và chỉ giữ lại tệp tin cần thiết cho môi trường thực thi (runtime).

### Exercise 2.4: Architecture diagram
Mô hình triển khai hệ thống như sau:
```
Client → Nginx (port 80) → Agent (port 8000) → Redis (port 6379)
```
- **Nginx:** Đóng vai trò là Reverse Proxy và Load Balancer, tiếp nhận các yêu cầu từ Client.
- **Agent:** Ứng dụng chính (FastAPI), nhận và xử lý yêu cầu.
- **Redis:** Lưu trữ trạng thái (State), bao gồm giới hạn tần suất (Rate Limiter) và ngân sách (Cost Guard).

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
URL: https://day12-2a202600689-nguyenbinhhuy-production.up.railway.app
Screenshot: Tham khảo trong tệp [DEPLOYMENT.md](DEPLOYMENT.md) hoặc thư mục [screenshots/](screenshots/) (bao gồm [railway_dashboard.png](screenshots/railway_dashboard.png), [health_check.png](screenshots/health_check.png), và [terminal_check.png](screenshots/terminal_check.png))
## Part 4: API Security

### Exercise 4.1-4.3: Test results
- Khi gửi yêu cầu không có API Key: Hệ thống từ chối và trả về mã lỗi `401 Unauthorized`.
- Khi gửi yêu cầu kèm API Key hợp lệ: Hệ thống xử lý thành công và trả về mã HTTP 200 kèm phản hồi dạng JSON.
- Khi kiểm tra quá tải (Rate Limiting): Khi gửi quá giới hạn 10 yêu cầu/phút, hệ thống bắt đầu chặn từ yêu cầu thứ 11 và trả về lỗi `429 Rate limit exceeded`.

### Exercise 4.4: Cost guard implementation
Hệ thống sử dụng Redis để lưu trữ và kiểm soát chi phí. Mỗi người dùng được cấp một khóa (key) lưu trữ trên Redis theo từng tháng (định dạng `budget:user_id:YYYY-MM`). Trước khi xử lý yêu cầu, hệ thống tính toán chi phí dự kiến. Nếu tổng chi phí vượt mức giới hạn ($10), yêu cầu sẽ bị từ chối. Nếu hợp lệ, chi phí được cộng dồn bằng lệnh `incrbyfloat()` và khóa sẽ được tự động xóa sau 32 ngày để giải phóng bộ nhớ.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Kiểm tra trạng thái (Health Check):** Triển khai Liveness probe để kiểm tra ứng dụng có đang hoạt động hay không, và Readiness probe để xác nhận khả năng kết nối thành công với cơ sở dữ liệu Redis.
- **Thiết kế không trạng thái (Stateless Design):** Không lưu trữ dữ liệu tạm thời (ví dụ: lịch sử hội thoại) trong bộ nhớ RAM của ứng dụng. Thay vào đó, trạng thái được lưu tập trung tại Redis. Điều này đảm bảo tính đồng nhất của dữ liệu khi hệ thống mở rộng (scale) thành nhiều máy chủ độc lập.
- **Tắt máy chủ an toàn (Graceful Shutdown):** Ứng dụng lắng nghe tín hiệu `SIGTERM`. Khi nhận được tín hiệu, hệ thống sẽ ngừng tiếp nhận yêu cầu mới và chờ các yêu cầu hiện tại hoàn thành trước khi dừng hoàn toàn tiến trình Python.
