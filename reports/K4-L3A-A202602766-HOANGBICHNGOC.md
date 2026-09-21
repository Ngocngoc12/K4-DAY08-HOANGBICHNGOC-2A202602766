# Báo cáo đóng góp cá nhân

## Thông tin

- Họ và tên: HOANG BICH NGOC
- Mã học viên: 2A202602766
- Nhóm: Credit Retrieval
- Repository/nhánh: K4-DAY08-VuHieuThien-2A202602867/HOANGBICHNGOC

## Phần việc đã làm

| Module / Kết quả | Việc tôi trực tiếp làm | File / Commit / PR | Trạng thái |
|------------------|------------------------|-------------------|------------|
| Chọn chủ đề & thu thập dữ liệu | Chọn đề tài "Dịch vụ đại học" (học phí, đăng ký học phần, thư viện), copy data từ DAY07 sang DAY08 | data/landing/legal/ | Xong |
| Task 3: Chuyển Markdown | Viết code chuyển tài liệu legal (copy markdown có sẵn) | src/task3_convert_markdown.py | Xong |
| Task 4: Chunking, embedding, indexing | Viết load_documents, chunk_documents (RecursiveChunker tự viết tránh lỗi OpenBLAS), embed_texts (OpenAI), index_to_vectorstore | src/task4_chunking_indexing.py | Xong |
| Task 5: Tìm kiếm ngữ nghĩa | Dense search với ChromaDB cosine similarity, dùng OpenAI embeddings | src/task5_semantic_search.py | Xong |
| Task 6: Tìm kiếm từ khóa | BM25 lexical search dùng BM25L | src/task6_lexical_search.py | Xong |
| Task 7: Reranking | RRF fusion theo công thức sum(1/(k+rank)), k=60 | src/task7_reranking.py | Xong |
| Task 8: PageIndex | Vectorless search PageIndex với error handling tránh crash | src/task8_pageindex_vectorless.py | Xong |
| Task 9: Retrieval pipeline | retrieve() với hybrid + RRF + fallback (so sánh dense cosine score với threshold) | src/task9_retrieval_pipeline.py | Xong |
| Task 10: Generation | generate_with_citation() dùng OpenAI o4-mini, format citation đúng số chunk | src/task10_generation.py | Xong |
| app.py | Streamlit UI: chat message, hiển thị sources/retrieval_method/score, URL validation, citation validation, session state | app.py | Xong |
| Golden dataset | Tạo 18 cặp Q&A từ legal corpus | group_project/evaluation/golden_dataset.json | Xong |
| Evaluation script | A/B so sánh dense-only vs hybrid+RRF với 4 metrics | scripts/evaluate.py | Xong |
| Evaluation report | Điền kết quả đánh giá thực tế (OpenAI embeddings + o4-mini), debug pipeline cho 3 worst performers | group_project/evaluation/RESULT.md | Xong |

## Các quyết định kỹ thuật quan trọng

**1. Dùng OpenAI text-embedding-3-small (1536-dim) cho embeddings**  
Lý do: BAAI/bge-m3 và sentence-transformers đều gây lỗi OpenBLAS memory allocation trên máy local (không GPU). OpenAI API trả embeddings chất lượng cao, dense scores lên tới 0.7-0.8 cho query in-domain.  
Đánh đổi: Tốn tiền API call nhưng ổn định và tốt cho tiếng Việt.

**2. Dùng OpenAI o4-mini cho LLM generation**  
Lý do: o4-mini hỗ trợ tiếng Việt tốt, trả lời ngắn gọn, trích dẫn chính xác. Lưu ý o4-mini yêu cầu `max_completion_tokens` và mặc định `temperature=1` — đã xử lý trong `_call_llm()`.  
Đánh đổi: o4-mini đôi khi trả lời dài hơn gpt-4o-mini nhưng phù hợp task này.

**3. Dùng BM25L thay vì BM25Okapi**  
Lý do: BM25Okapi trả score 0 cho mọi query, khiến RRF không chạy được. BM25L trả điểm dương đúng.  
Đánh đổi: Công thức điểm khác nhưng vẫn đảm bảo thứ hạng hợp lý cho RRF.

**4. SCORE_THRESHOLD = 0.3**  
Lý do: Calibrated với real OpenAI embeddings: in-domain ~0.55-0.80, out-of-domain ~0.1-0.3. Threshold này phân biệt tốt.  
Đánh đổi: Có thể điều chỉnh để tối ưu recall/precision tùy corpus.

**5. Custom RecursiveChunker thay vì langchain_text_splitters**  
Lý do: langchain_text_splitters gây lỗi OpenBLAS khi import. Custom chunker với separators ["\n\n", "\n", ". ", " ", ""] chạy ổn định, chunk kém tinh vi hơn nhưng đủ dùng.

## Kiểm thử và kết quả

- `pytest tests/test_contracts.py -v` → 15/15 PASSED
- `pytest tests/test_acceptance.py -v` → 5/5 PASSED
- `pytest tests/ -v` → 20/20 PASSED
- Embedding test: `text-embedding-3-small` → vector 1536-dim, dense scores ~0.7-0.8
- Semantic search: `semantic_search('hoc phi', top_k=3)` → 3 chunks với score thực ~0.7-0.8
- Retrieval: `retrieve('hoc phi', top_k=3)` → hybrid RRF kết quả
- Generation: `generate_with_citation('Hoc phi la bao nhieu?', top_k=3)` → trả lời chi tiết có citation
- Embedding pipeline: 1953 chunks indexed vào ChromaDB
- Evaluation: A/B 18 golden cases, Config B (hybrid+RRF) tốt hơn Config A (dense-only) ở tất cả 4 metrics (+0.147 average)

## Hạn chế

- PageIndex chưa cấu hình API key (có error handling để fallback gracefully)
- Provider `sentence-transformers` local chưa dùng được do OpenBLAS (OpenAI provider chạy tốt)
- URL/citation validation trong UI đang hiển thị trạng thái hợp lệ/missing/invalid của URL và trích dẫn
- Debug pipeline cho 3 worst performers: Case 1 (dense truy xuất sai tài liệu), Case 2 (out-of-domain query), Case 3 (dense nhầm faculty/student doc)

Nếu có thêm thời gian: Thêm HyDE hoặc query expansion để cải thiện retrieval cho numeric facts.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: HOANG BICH NGOC 