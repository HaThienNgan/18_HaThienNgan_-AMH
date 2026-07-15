# ACSIncome Business Rule Gap

## Đánh giá khoảng cách giữa khai phá quan hệ phụ thuộc từ dữ liệu và quy tắc nghiệp vụ

Dự án nghiên cứu đánh giá khoảng cách giữa các quan hệ phụ thuộc được tự động khai phá từ dữ liệu và các quy tắc nghiệp vụ được xác định dựa trên tri thức chuyên môn trên bộ dữ liệu **ACSIncome**.

Notebook sử dụng quy trình thực nghiệm gồm:

- Tách tập huấn luyện và tập kiểm tra theo `state × income_label`.
- Chỉ khai phá các quan hệ phụ thuộc trên tập huấn luyện nhằm hạn chế rò rỉ dữ liệu.
- Xây dựng bộ kiểm tra từ các mapping học được trên tập huấn luyện.
- Tiêm lỗi ở cấp dòng dữ liệu để đánh giá khả năng phát hiện vi phạm.
- Thực hiện kiểm thử với nhiều random seed và báo cáo kết quả trung bình cùng độ lệch chuẩn.
- Sử dụng bootstrap cho chỉ số Dependency Distribution Shift (DDS).
- Thực hiện đánh giá leave-one-state-out để kiểm tra khả năng khái quát giữa các bang.

## Mục tiêu nghiên cứu

Nghiên cứu hướng đến việc làm rõ rằng một quan hệ phụ thuộc mạnh về mặt thống kê không nhất thiết đồng nghĩa với một quy tắc nghiệp vụ hợp lệ. Ngược lại, một số quy tắc nghiệp vụ quan trọng có thể được hình thành từ codebook, metadata hoặc tri thức chuyên gia và không thể được phát hiện chỉ bằng phương pháp khai phá dữ liệu.

Dự án phân biệt hai nhóm quy tắc:

1. **Data-driven dependencies:** các quan hệ được máy tự động phát hiện từ dữ liệu.
2. **Domain business rules:** các quy tắc kiểm tra được xây dựng từ codebook và logic nghiệp vụ mô phỏng.

## Phương pháp đánh giá

Các phương pháp và chỉ số chính gồm:

- Exact Functional Dependency
- QStrength
- Theil’s U
- Mutual Information
- Cramér’s V
- Precision@K
- Recall@K
- Business Rule Recovery
- Non-Prescribed Dependency Rate
- Dependency Distribution Shift (DDS)

## Lưu ý về phạm vi

Bộ quy tắc nghiệp vụ trong nghiên cứu là **rule catalog mô phỏng**, được sử dụng như một benchmark có kiểm soát để đánh giá mức độ phù hợp giữa dependency mining và tri thức nghiệp vụ. Đây không phải là bộ quy tắc chính thức của ACS và nghiên cứu không nhằm thay thế vai trò của chuyên gia nghiệp vụ.

## File chính

- `ACSIncome_BusinessRule_V3_1_FIXED.ipynb`: notebook thực nghiệm phiên bản V3.1.

## Công nghệ sử dụng

- Python
- Jupyter Notebook / Google Colab
- pandas
- NumPy
- SciPy
- scikit-learn
- Matplotlib
- Seaborn

## Mô tả ngắn

Notebook nghiên cứu đánh giá khoảng cách giữa các quan hệ phụ thuộc được khai phá từ dữ liệu và các quy tắc nghiệp vụ theo chuyên môn trên bộ dữ liệu ACSIncome, sử dụng phương pháp tách tập huấn luyện–kiểm tra, kiểm thử với nhiều seed ngẫu nhiên, bootstrap DDS và đánh giá leave-one-state-out.
