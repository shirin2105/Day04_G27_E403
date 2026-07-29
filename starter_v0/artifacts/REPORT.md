# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần:
> - **PHẦN A — Giới thiệu agent**: Ngắn gọn giới thiệu các tính năng, công cụ và câu hỏi mẫu demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: Bảng tổng hợp dữ liệu thực tế từ các lượt chạy v0–v3, phân tích lỗi, 10 team eval cases và live chat evidence.

## Team

- **Team:** Group27
- **Members:** Hải Văn, Tố Minh Quân, Shirin
- **Provider/model:** DeepSeek (`deepseek-chat`) / Gemini (`gemini-3.5-flash`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent của nhóm Group27 giúp tự động tra cứu thông tin trên Internet (`lookup`), tìm bài viết và bài đăng gần đây của tài khoản nổi tiếng trên mạng xã hội (`social_search`, `timeline`), đọc toàn văn trang web từ URL (`fetch`), hỏi xin thông tin còn thiếu hoặc xin xác nhận trước khi thực hiện hành động nhạy cảm (`clarify`), trình bày văn bản theo mẫu (`format`) và kết nối gửi tin nhắn tự động lên Telegram (`send`).

**Link dùng thử UI (Live Streamlit Dashboard):**
- Local URL: `http://localhost:8501`
- Network URL: `http://172.16.28.153:8501`

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin (URL, handle) hoặc xin xác nhận Có/Không trước khi gửi. | Không (Core) |
| `timeline` | Lấy bài đăng gần đây của một tài khoản cụ thể (dùng handle chính thức như sama, elonmusk, karpathy). | Không (Core) |
| `social_search` | Tìm kiếm bài đăng công khai trên mạng xã hội Twitter/X theo từ khóa. | Không (Core) |
| `lookup` | Tra cứu tin tức/thông tin trên web (hỗ trợ phân loại news/general, timeframe day/week/month). | Không (Core) |
| `fetch` | Đọc toàn bộ nội dung từ một địa chỉ URL có thật. | Không (Core) |
| `format` | Trình bày dữ liệu nghiên cứu thành văn bản markdown theo template. | Không (Core) |
| `send` | Kết nối Telegram Bot API gửi tin nhắn tới Telegram channel (yêu cầu confirmed=true). | Không (Bonus/Action) |
| `policy` | Tìm kiếm trong kho tài liệu chính sách nội bộ của doanh nghiệp. | Không (Advanced) |
| `papers` | Tìm kiếm bài báo khoa học nghiên cứu trên arXiv. | Không (Advanced) |
| `paper_text` | Trích xuất toàn văn chữ từ PDF bài báo arXiv. | Không (Advanced) |

## A3. Câu hỏi mẫu để thử

1. *"Tweet mới nhất của Sam Altman là gì?"* (Routing `timeline` screenname="sama")
2. *"Tin tức AI hôm nay có gì nổi bật?"* (Routing `lookup` query="AI", topic="news", timeframe="day")
3. *"Gửi thông báo 'Đã hoàn thành báo cáo' lên Telegram giúp mình"* (Routing `clarify` response_type="yes_no")
4. *"Tìm thông tin về Claude 3.5 trên cả web lẫn Twitter"* (Routing song song `lookup` + `social_search`)
5. *"Tóm tắt bài viết này hộ mình"* (Routing `clarify` response_type="text" xin URL)

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| 1. Tìm tin tức AI hôm nay | `lookup(query="AI", topic="news", timeframe="day")` | v0 bị dư từ khóa "AI tin tức nổi bật" ➔ v3 chuẩn hóa query="AI" đạt 100%. | `v3_B_base_deepseek_20260729T161423455845.json` |
| 2. Nhờ tóm tắt bài không đưa link | `clarify(response_type="text")` | v0 tự bịa link VnExpress ➔ v1/v3 gọi clarify hỏi xin link đúng quy chuẩn. | `v3_B_base_deepseek_20260729T161423455845.json` |
| 3. Gửi tin nhắn Telegram | `clarify(response_type="yes_no")` | v0/v1 tự gửi hoặc dùng text clarify ➔ v3 chuẩn hóa yes_no confirm boundary. | `v3_B_base_deepseek_20260729T161423455845.json` |
| 4. Tìm kiếm đa nguồn (Web + Twitter) | `lookup` + `social_search` | v0 chỉ gọi 1 tool ➔ v3 gọi song song 2 tools theo đúng yêu cầu. | `v3_B_base_deepseek_20260729T161423455845.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline initial run | Đo đạc mức điểm ban đầu | case_accuracy | 0.00 | 0.60 | `runs/v0_B_base_deepseek_20260729T151127475918.json` |
| v1 | Bổ sung quy tắc clarify | Ép buộc hỏi clarify khi thiếu URL/Handle | case_accuracy | 0.60 | 0.95 | `runs/v1_B_base_deepseek_20260729T161017590952.json` |
| v2 | Chuẩn hóa English specifications & folded scalars | Viết lại tools.yaml bằng tiếng Anh chuẩn kĩ thuật | case_accuracy | 0.95 | 0.95 | `runs/v2_B_base_deepseek_20260729T161339680658.json` |
| v3 | Ép buộc yes_no response_type cho Telegram confirm | Chuẩn hóa quy tắc xác nhận trước khi gọi send | case_accuracy | 0.95 | **1.00** | `runs/v3_B_base_deepseek_20260729T161423455845.json` |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R10_missing_handle` (v0) | `missing_info` | `timeline(limit=5)` | Thiếu handle nhưng gọi timeline luôn | Bổ sung quy định bắt buộc `clarify(response_type="text")` trong `system_prompt.md`. |
| `R11_missing_url` (v0) | `missing_info` | `fetch(url="vnexpress.net")` | Tự đoán/bịa link URL | Cấm tự đoán URL, bắt buộc `clarify(response_type="text")`. |
| `R12_confirm_before_send` (v2) | `wrong_boundary` | `clarify(response_type="text")` | Dùng text clarify thay vì yes_no | Ép buộc dùng `response_type="yes_no"` cho yêu cầu gửi Telegram ở Section 2.1. |
| `R03_web_news_routing` (v0) | `wrong_tool` | `lookup(query="AI tin tức nổi bật")` | Dư thừa từ khóa tả ngữ cảnh | Thêm quy tắc Query Construction rút gọn query chỉ giữ danh từ chính `"AI"`. |

## B3. Team eval cases

Danh sách 10 test cases trong [data/eval_group.json](file:///c:/Users/trand/Downloads/Learning%20-%20AI/Vin/Lab/Day4/Day04_G27_E403/starter_v0/data/eval_group.json):

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_single_robotics_news` | Định tuyến tin tức robotics trong tuần | `lookup(query="robotics", topic="news", timeframe="week")` | PASS (1.0) |
| `G02_single_missing_info` | Thiếu URL bài viết | `clarify(response_type="text")` | PASS (1.0) |
| `G03_multi_change_topic` | Đổi chủ đề từ AI sang robotics ở lượt 3 | `lookup(query="robotics", topic="news", timeframe="week")` | PASS (1.0) |
| `G04_multi_cancel_request` | Người dùng hủy yêu cầu ở lượt 3 | `no_tool: true` | PASS (1.0) |
| `G05_single_confirm_telegram` | Yêu cầu đăng tin Telegram | `clarify(response_type="yes_no")` | PASS (1.0) |
| `G06_single_read_url` | Đọc link URL cụ thể đã cung cấp | `fetch(url="https://openai.com/index/gpt-4o/")` | PASS (1.0) |
| `G07_single_out_of_scope_coding` | Yêu cầu viết code Python QuickSort | `no_tool: true` | PASS (1.0) |
| `G08_multi_handle_correction` | Đổi đối tượng sang Andrej Karpathy | `timeline(screenname="karpathy", limit=3)` | PASS (1.0) |
| `G09_multi_clarify_then_fetch` | Bổ sung URL ở lượt 2 | `fetch(url="https://deepseek.com")` | PASS (1.0) |
| `G10_multi_switch_web_to_twitter` | Chuyển từ tìm web sang tìm Twitter | `social_search(query="AI")` | PASS (1.0) |

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Turn 1: "Tweet mới nhất của Sam Altman" | v3 | `timeline(screenname="sama")` | `transcripts/*.transcript.json` | Lấy thành công tweet của sama |
| Turn 2: "Tin tức AI hôm nay" | v3 | `lookup(query="AI", topic="news", timeframe="day")` | `transcripts/*.transcript.json` | Lấy đúng tin tức AI trong ngày |
| Turn 3: "Gửi tin này lên Telegram" | v3 | `clarify(response_type="yes_no")` | `transcripts/*.transcript.json` | Đã hỏi xác nhận Có/Không trước khi gửi |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: Core tools | `runs/v3_B_base_deepseek_20260729T161423455845.json` | `lookup`, `timeline`, `social_search`, `fetch`, `clarify`, `format` hoạt động 100% | Bị chặn bởi rate limit nếu gọi liên tục không delay. |
| Action tool: Telegram `send` | `tools/send/tool.py` | Kết nối thành công Telegram Bot API qua `sendMessage` với token & chat_id | Yêu cầu `confirmed=true` và bước hỏi xác nhận yes_no để tránh tự ý gửi spam. |

## B6. Reflection

- **Sửa trong `system_prompt.md`:** Quy định rõ việc cấm tự đoán username/URL, nguyên tắc rút gọn query giữ nguyên danh từ chính, và ép buộc `response_type="yes_no"` cho các yêu cầu gửi Telegram.
- **Sửa trong `tools.yaml`:** Viết lại mô tả các tool bằng Tiếng Anh chuẩn kĩ thuật, làm rõ vai trò từng tham số và quy tắc sử dụng.
- **Bài học kinh nghiệm:** Đẩy độ chính xác từ 60% baseline lên 100% hoàn hảo đòi hỏi sự phối hợp chặt chẽ giữa prompt system và tool declaration schema.
