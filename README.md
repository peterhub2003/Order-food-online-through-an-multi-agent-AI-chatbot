🍜 Thang Food Assistant - Multi-Agent AI Chatbot

📖 Giới thiệu

Thang Food Assistant là một hệ thống chatbot đặt món ăn thông minh thế hệ mới, được xây dựng dựa trên kiến trúc Multi-Agent (Đa tác tử). Khác với các chatbot truyền thống dựa trên kịch bản cứng, hệ thống này sử dụng LLM (Large Language Model) chạy cục bộ (Local Inference) để suy luận, lập kế hoạch và thực hiện các tác vụ phức tạp.

Hệ thống bao gồm 4 thành phần chính hoạt động phối hợp:

- ChatUI (Frontend): Giao diện chat hiện đại, hỗ trợ xác thực người dùng.

- Multi-Agent System: Bộ não trung tâm sử dụng LangGraph (Orchestrator, Tool Agent, Synthesis Agent).

- MCP Server: Chuẩn hóa giao tiếp công cụ (Model Context Protocol).

- Backend Service: Hệ thống quản lý nhà hàng (Menu, Đơn hàng, User) viết bằng FastAPI.

Tính năng nổi bật

🤖 Local LLM: Chạy hoàn toàn offline với Ollama (Llama 3, Qwen 2.5, GPT-OSS...), đảm bảo quyền riêng tư dữ liệu.

🧠 Reasoning & Planning: Tự động lập kế hoạch đa bước để xử lý yêu cầu (Hỏi giá -> Tìm ID -> Tạo đơn -> Thêm món -> Tính tiền).

🛠️ Tool Use chính xác: Sử dụng công cụ để tra cứu DB và tính toán tiền nong chính xác tuyệt đối, không bị ảo giác (hallucination).

🔄 Quản lý ngữ cảnh: Ghi nhớ thông tin khách hàng và giỏ hàng trong suốt phiên hội thoại.

⚙️ Yêu cầu hệ thống (Prerequisites)

Để chạy trơn tru hệ thống (đặc biệt là mô hình LLM 20B+), máy tính của bạn cần đáp ứng:

- Docker & Docker Compose: Đã cài đặt.
- Git: Đã cài đặt.
- Phần cứng (Khuyến nghị):
  - RAM: Tối thiểu 16GB.
  - GPU: NVIDIA GPU với tối thiểu 16GB VRAM (Nếu chạy mode GPU).

Nếu chỉ dùng CPU, tốc độ phản hồi sẽ chậm hơn đáng kể.

🚀 Hướng dẫn Cài đặt & Sử dụng

Làm theo các bước sau để khởi chạy hệ thống:

Bước 1: Tải mã nguồn

``` bash
git clone https://github.com/peterhub2003/Order-food-online-through-an-multi-agent-AI-chatbot.git
cd Order-food-online-through-an-multi-agent-AI-chatbot
``` 

Bước 2: Khởi chạy hạ tầng Docker

Tùy thuộc vào phần cứng của bạn, hãy chọn lệnh phù hợp:

👉 Lựa chọn A: Nếu bạn có NVIDIA GPU (Khuyến nghị)
Sử dụng file cấu hình hỗ trợ GPU để tối ưu hiệu suất Ollama:

``` bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```


👉 Lựa chọn B: Nếu bạn chỉ dùng CPU
Sử dụng cấu hình mặc định:

``` bash
docker compose -f docker-compose.yml up -d --build
```


Bước 3: Tải và chạy Mô hình AI (Ollama)

Chúng tôi cung cấp script tự động để pull và chạy model. Mặc định hệ thống sử dụng mô hình gpt-oss:20b (hoặc model tùy chỉnh được định nghĩa trong script).

Chạy với model mặc định:

``` bash
chmod +x run_ollama_gpt_oss.sh
./run_ollama_gpt_oss.sh
```


Hoặc chạy với model khác (Ví dụ: llama3):

``` bash
./run_ollama_gpt_oss.sh llama3
```


Lưu ý: Quá trình này có thể mất vài phút tùy thuộc vào tốc độ mạng để tải model về.

Bước 4: Khởi tạo dữ liệu mẫu (Seed Database)

Để chatbot có dữ liệu về Menu (Cơm Tấm, Phở...), User và các thiết lập ban đầu, hãy chạy lệnh seed:

``` bash
docker compose exec backend python -m app.seed
```


Bước 5: Trải nghiệm

Mở trình duyệt web và truy cập vào địa chỉ:

👉 http://localhost:3000

- Đăng ký tài khoản mới (Register).

- Đăng nhập (Login).

- Bắt đầu chat đặt món (Ví dụ: "Cho tôi 2 phần Cơm Tấm về 12 Lê Duẩn").


