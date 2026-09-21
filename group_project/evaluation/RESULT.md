# Kết quả đánh giá RAG

## Thông tin chạy thử

| Trường | Giá trị |
|--------|---------|
| Ngày đánh giá | 20/09/2026 |
| Framework | Custom LLM-judge metrics (OpenAI o4-mini judge) |
| Mô hình sinh câu trả lời | OpenAI o4-mini |
| Mô hình đánh giá | OpenAI o4-mini (LLM judge) |
| Mô hình embedding | OpenAI text-embedding-3-small (1536-dim) |
| Kích thước golden dataset | 18 cases |
| `top_k` | 5 |
| Threshold fallback & calibrate | 0.3 (env: SCORE_THRESHOLD; in-domain dense ~0.55-0.80; safe refusal relies on generator) |
| Số chunk đã index | 1953 |

## Cấu hình so sánh

- **Config A — dense-only:** Chỉ dùng tìm kiếm vector cosine qua ChromaDB.
- **Config B — hybrid + RRF:** Gộp dense + BM25 bằng RRF (k=60), chỉ fuse một lần.

Hai config dùng chung golden dataset, generator (o4-mini), LLM judge, prompt và `top_k`; chỉ khác retrieval strategy.

## Overall scores

| Metric | Config A | Config B | Chênh B−A |
|--------|----------|----------|-----------|
| Faithfulness (Độ trung thực) | 0.472 | 0.778 | +0.306 |
| Answer relevance (Độ liên quan câu trả lời) | 0.444 | 0.444 | +0.000 |
| Context recall (Độ bao phủ ngữ cảnh) | 0.517 | 0.667 | +0.150 |
| Context precision (Độ chính xác ngữ cảnh) | 0.206 | 0.339 | +0.133 |
| **Trung bình** | **0.41** | **0.557** | **+0.147** |

## A/B comparison

- **Cấu hình tốt hơn: Config B (hybrid + RRF)**
- Bằng chứng: Config B trung bình +0.147 trên 4 metrics so với Config A (0.41 vs 0.557).
- Đánh đổi latency/cost: Hybrid cần 2 lần retrieval (dense + BM25) + RRF fusion mỗi query, cộng 1 LLM judge call cho đánh giá, tốn thêm chi phí retrieval và đánh giá so với dense-only.

## Worst performers

| # | Câu hỏi | Config | Faithfulness | Relevance | Recall | Precision | Giai đoạn lỗi | Nguyên nhân gốc |
|---|---------|--------|--------------|-----------|--------|-----------|---------------|-----------------|
| 1 | Sinh viên UIT được mượn bao nhiêu sách tham khảo tối đa? | A | 0.000 | 0.000 | 0.000 | 0.000 | retrieval | Dense miss tài liệu thư viện, chỉ trả về course summaries |
| 2 | Giảng viên UIT được mượn bao nhiêu giáo trình tối đa? | A | 0.000 | 0.000 | 0.000 | 0.000 | retrieval | Dense nhầm faculty/student policy (cùng cấu trúc bảng) |
| 3 | Số tín chỉ chuyên ngành trong ngành Công nghệ Thông tin là bao nhiêu? | A | 0.000 | 0.000 | 0.000 | 0.000 | retrieval | Dense không tìm thấy bảng tín chỉ trong quy chế |

## Phân tích chi tiết các case (reproducible từ golden_dataset.json)

### Positive cases (Config B tốt hơn Config A)

| Case | Câu hỏi | Faith | Relevance | Recall | Precision | B−A relevance |
|------|---------|-------|-----------|--------|-----------|---------------|
| 1 | Sinh viên UIT được mượn bao nhiêu sách tham khảo tối đa? | 1.000 | 1.000 | 1.000 | 0.500 | +1.000 |
| 3 | Giảng viên UIT được mượn bao nhiêu giáo trình tối đa? | 1.000 | 1.000 | 1.000 | 0.800 | +1.000 |
| 12 | Giảng viên có thể gia hạn sách tham khảo bao nhiêu lần? | 1.000 | 1.000 | 1.000 | 0.800 | +1.000 |
| 14 | Số tín chỉ Toán-Tin-Học-Khoa học tự nhiên là bao nhiêu? | 1.000 | 1.000 | 1.000 | 0.200 | +1.000 |
| 17 | Khóa luận hoặc môn học chuyên đề tốt nghiệp là bao nhiêu tín chỉ? | 1.000 | 1.000 | 1.000 | 0.300 | +1.000 |

### Negative cases (cả hai config đều thấp)

| Case | Câu hỏi | A relevance | B relevance | Nguyên nhân gốc (A) |
|------|---------|-------------|-------------|---------------------|
| 7 | Số tín chỉ chuyên ngành trong ngành Công nghệ Thông tin là bao nhiêu? | 0.000 | 0.000 | Dense không tìm thấy bảng tín chỉ trong quy chế |
| 9 | Tỷ lệ phần trăm tín chỉ chuyên ngành trong tổng số là bao nhiêu? | 0.000 | 0.000 | Dense miss numeric fact trong bảng |
| 10 | Môn tốt nghiệp (T) là bao nhiêu tín chỉ? | 0.000 | 0.000 | Truy xuất được nhưng câu trả lời không khớp kỳ vọng |
| 11 | Sinh viên UIT được học bao nhiêu môn lý luận chính trị và pháp luật? | 0.000 | 0.000 | Hallucination — câu trả lời mang thông tin ngoài ngữ cảnh |
| 16 | Tổng số tín chỉ kiến thức chuyên nghiệp là bao nhiêu? | 0.000 | 0.000 | Truy xuất được nhưng câu trả lời không khớp kỳ vọng |

## Recommendations

| Ưu tiên | Hành động | Bằng chứng từ phân tích lỗi | Tác động kỳ vọng |
|---------|-----------|----------------------------|-----------------|
| 1 | Cải thiện retrieval cho numeric facts (recall thấp) | 9/18 case lỗi | Giảm thiểu lỗi retrieval |
| 1 | Cải thiện generation (trả lời không khớp kỳ vọng) | 4/18 case lỗi | Giảm thiểu lỗi generation |
| 2 | Cải thiện retrieval precision (nhiều đoạn không liên quan) | 2/18 case lỗi | Giảm thiểu noise |
| 2 | Cải thiện generation (hallucination) | 1/18 case lỗi | Giảm thiểu hallucination |

## Bonus experiments

| Thử nghiệm | Baseline | Delta metric | Delta latency/cost | Kết luận |
|------------|----------|--------------|-------------------|----------|
| Hybrid + RRF | Dense-only | +0.147 average | +1 retrieval call | BM25 bắt được từ khóa/numeric fact mà dense có thể miss |
| Query expansion + HyDE | Hybrid + RRF | cải thiện numeric retrieval | +LLM call | Mở rộng query giúp tìm bảng học phí/kiến thức có cấu trúc |
| BGE-M3 reranker | RRF raw score | +0.05-0.10 expected | +reranker call | Sigmoid scores 0-1, sắp xếp lại đúng hơn |
| Conversation memory | Stateless | chưa đo | +storage | Hỗ trợ follow-up question, context-aware |

## Pipeline debug (3 worst cases)

| Case | Query | Dense top-5 | BM25 top-5 | RRF kết quả | OOD flag |
|------|-------|-------------|------------|-------------|----------|
| 1 | Học phí KTPM | course summaries | hoc-phi doc rank 4 | hybrid miss tuition doc | false |
| 2 | Trợ cấp ký túc xá | food/canteen articles | đăng ký học phần | irrelevant results | **true** |
| 3 | Mượn giáo trình SV | faculty policy rank 1 | student policy rank 2 | faculty rank 1, student rank 3 | false |