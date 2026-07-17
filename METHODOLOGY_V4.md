# Thiết kế nghiên cứu V4

## 1. Mục tiêu phát triển

Phiên bản V4 tách rõ hai câu hỏi vốn đang bị trộn trong notebook đầu tiên:

1. Một hệ thống khai phá dependency có tìm lại và dùng được các quy tắc đã biết trong một benchmark có kiểm soát hay không?
2. Trên các biến ACS gốc, dependency nào đủ ổn định để trở thành **ứng viên** cho chuyên gia thẩm định?

Kết quả của câu hỏi thứ hai không tự động trở thành quy tắc nghiệp vụ. Một dependency mạnh chỉ cho biết khả năng dự đoán hoặc đồng biến trong dữ liệu quan sát; nó chưa chứng minh tính hợp lệ nghiệp vụ, quan hệ nhân quả hay khả năng áp dụng ngoài phạm vi mẫu.

## 2. Câu hỏi nghiên cứu đề xuất

- **RQ1 — Recovery:** Các thước đo Exact FD, QStrength, Theil’s U, NMI và Cramér’s V tìm lại rule benchmark ở mức nào?
- **RQ2 — Detection:** Rule được học từ train phát hiện từng loại lỗi dữ liệu trên test với precision, recall, F1 và coverage ra sao?
- **RQ3 — Stability:** Dependency giữa các biến ACS gốc có ổn định qua bootstrap, bang và tập kiểm tra hay không?
- **RQ4 — Drift:** DDS có phân biệt thay đổi cấu trúc dependency với dao động do lấy mẫu hay không?

## 3. Hai tầng bằng chứng

### Tầng A — Controlled benchmark

Sáu biến `age_group`, `education_group`, `working_hours_group`, `fulltime_status`, `marital_group` và `income_group` được sinh bằng công thức do người nghiên cứu thiết kế. Vì vậy:

- Có thể dùng chúng để kiểm thử khả năng recovery và phát hiện lỗi.
- Không được dùng kết quả “tìm lại 6/6 rule” để kết luận hệ thống đã khám phá được rule nghiệp vụ thực tế.
- Cần báo cáo thêm negative control bằng cách hoán vị biến đích; metric đúng phải giảm rõ rệt.

### Tầng B — Raw-variable candidate discovery

Chỉ dùng các biến ACS gốc. Mỗi dependency được đánh giá qua:

- tần suất lọt top-K trên nhiều bootstrap;
- trung vị và độ lệch chuẩn Theil’s U;
- chặn cardinality và support để hạn chế dependency giả do LHS gần duy nhất;
- permutation test;
- Benjamini–Hochberg FDR trên danh sách ứng viên;
- kiểm tra khả năng khái quát theo bang và trên test.

Đầu ra của tầng này là danh sách `candidate`, không phải `business_rule`.

## 4. Các sửa đổi bắt buộc so với V3.1

| Vấn đề | Ảnh hưởng | Cách sửa ở V4 |
|---|---|---|
| MI dùng log tự nhiên nhưng entropy dùng log cơ số 2 | Theil’s U hoàn hảo chỉ đạt khoảng 0,693 | Dùng cùng log tự nhiên, kiểm thử `U=1` |
| QStrength không đạt 1 với FD hoàn hảo | Khó so sánh giữa RHS có cardinality khác nhau | Chuẩn hóa phần đa dạng dư về [0,1] |
| DDS tính cả đường chéo | Pha loãng mức drift | Chỉ lấy trung bình ngoài đường chéo |
| Clean và noisy dùng mẫu khác nhau | DDS chứa cả nhiễu lấy mẫu | So sánh ghép cặp cùng vị trí dòng |
| State LOO vẫn đưa `state` vào ma trận | Drift cao một cách cơ học | Luôn loại cột phân nhóm khỏi ma trận |
| Rule benchmark được sinh từ chính công thức đánh giá | Nguy cơ lập luận vòng tròn | Tách controlled benchmark và raw candidate discovery |
| Chỉ báo cáo mean/std với rất ít seed | Bất định chưa rõ | Tăng số lần lặp, báo percentile CI hoặc permutation p-value |

## 5. Tiêu chí giữ một dependency ứng viên

Ngưỡng dưới đây là cấu hình thực nghiệm, không phải chuẩn phổ quát:

- `selection_frequency >= 0.80` qua tối thiểu 30 bootstrap;
- `avg_lhs_support >= 20`;
- `rhs_cardinality <= 30`;
- permutation `q-value < 0.05`;
- Theil’s U không giảm mạnh trên test;
- không chỉ xuất hiện ở duy nhất một bang nếu mục tiêu là rule dùng chung.

Mọi ứng viên vượt ngưỡng vẫn phải được đối chiếu codebook và phỏng vấn chuyên gia trước khi đưa vào rule catalog.

## 6. Diễn giải kết quả

- **Exact FD/score cao:** bằng chứng về tính đều đặn trong mẫu, không phải bằng chứng nhân quả.
- **Selection frequency cao:** kết quả ít nhạy với lấy mẫu, nhưng vẫn có thể phản ánh thiên lệch hệ thống của dữ liệu.
- **Permutation q-value thấp:** quan hệ khó giải thích chỉ bằng hoán vị ngẫu nhiên trong mẫu, nhưng chưa chứng minh giá trị nghiệp vụ.
- **DDS vượt ngưỡng sạch:** cấu trúc dependency đã thay đổi đáng kể; DDS không chỉ ra dòng sai và không thay thế row-level validator.
- **State LOO khác biệt:** cần xem như bằng chứng về tính không đồng nhất theo bối cảnh, không mặc định là lỗi dữ liệu.

## 7. Threats to validity cần ghi trong luận văn

- Rule catalog ở tầng A là mô phỏng.
- ACSIncome là benchmark dựa trên dữ liệu điều tra Hoa Kỳ, không đại diện trực tiếp cho một quy trình nghiệp vụ Việt Nam.
- Dependency metrics nhạy với cardinality, cỡ mẫu và cách rời rạc hóa.
- Synthetic error injection có thể đơn giản hơn lỗi ngoài thực tế.
- Nhiều phép thử làm tăng false discovery nếu không kiểm soát FDR.
- Khác biệt theo bang có thể là heterogeneity hợp lệ, không phải data-quality incident.

## 8. Đóng góp phù hợp với đề tài ThS HTTT

Đóng góp nên được trình bày là một **khung hỗ trợ quản trị chất lượng dữ liệu kết hợp tri thức chuyên gia và dependency mining**, gồm:

1. discovery trên train;
2. stability/permutation screening;
3. expert approval và versioned rule catalog;
4. row-level validation;
5. structural drift monitoring;
6. audit trail cho quyết định thêm, sửa hoặc loại rule.

Khung này có giá trị HTTT rõ hơn một notebook chỉ xếp hạng tương quan, vì nó gắn khai phá dữ liệu với quy trình ra quyết định, kiểm soát thay đổi và trách nhiệm thẩm định.
