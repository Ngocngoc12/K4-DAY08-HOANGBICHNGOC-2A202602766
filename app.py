import re
import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation
from src.bonus_integration import enhanced_chat


load_dotenv()


st.set_page_config(
    page_title="RAG Chatbot — Dịch vụ đại học (Enhanced)",
    page_icon="🎓",
    layout="wide",
)

URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")


def validate_url(url: str | None) -> tuple[bool, str]:
    if url is None:
        return False, "Chưa có URL"
    if not isinstance(url, str) or not url.strip():
        return False, "URL rỗng"
    if URL_PATTERN.match(url.strip()):
        return True, "✓ Hợp lệ"
    return False, f"✗ Không hợp lệ: {url}"


def validate_citations(answer: str, sources: list[dict]) -> tuple[bool, list[int], list[int]]:
    cited = sorted(set(int(m) for m in re.findall(r"\[(\d+)\]", answer)))
    available = list(range(1, len(sources) + 1))
    missing = [c for c in cited if c not in available]
    return (len(missing) == 0 and len(cited) > 0, cited, missing)


def render_source(source: dict, index: int) -> None:
    metadata = source["metadata"]
    source_name = metadata.get("source", "unknown")
    source_title = metadata.get("title", "unknown")
    url = metadata.get("url")
    is_valid_url, url_status = validate_url(url)
    retrieval_method = source.get("retrieval_method", "unknown")
    score = source.get("score", 0)

    st.markdown(
        f"[{index}] **{source_title}** ({retrieval_method}, "
        f"score: {score:.3f}) — {source_name}"
    )
    if url and is_valid_url:
        st.markdown(f"🔗 [{url}]({url})")
    elif not is_valid_url and url:
        st.caption(f"⚠️ {url_status}")


# Initialize session
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_session"


with st.sidebar:
    st.title("RAG Chatbot Enhanced")
    st.caption("Chatbot với HyDE, BGE-M3 Reranker, Memory State")
    
    top_k = st.slider("Số chunks", 3, 10, 5)
    
    # Feature toggles
    st.divider()
    st.subheader("⚡ Bonus Features")
    use_expansion = st.checkbox("Query Expansion / HyDE", value=True, help="Mở rộng câu hỏi để tìm kiếm tốt hơn")
    use_reranker = st.checkbox("BGE-M3 Reranker v2", value=True, help="Rerank kết quả bằng BGE-M3")
    use_memory = st.checkbox("Conversation Memory", value=True, help="Nhớ ngữ cảnh hội thoại")
    
    st.divider()
    if st.button("Xóa lịch sử & Memory"):
        st.session_state.messages = []
        # Clear memory
        try:
            from src.memory_manager import get_memory_manager
            get_memory_manager().delete_session(st.session_state.session_id)
        except Exception:
            pass
        st.rerun()
    
    # Show session info
    st.caption(f"Session: {st.session_state.session_id}")


st.title("RAG Chatbot — Dịch vụ đại học (Enhanced)")
st.caption("Học phí, học bổng, đăng ký học phần, mượn sách thư viện... với HyDE + BGE-M3 + Memory")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander(f"📚 {len(message['sources'])} nguồn tham khảo"):
                for i, source in enumerate(message["sources"], 1):
                    render_source(source, i)
                citations_valid, _, _ = validate_citations(
                    message["content"], message["sources"]
                )
                if citations_valid:
                    st.success("✅ Trích dẫn hợp lệ — tất cả đều đối chiếu được với nguồn")
                else:
                    st.warning("⚠️ Kiểm tra trích dẫn — có tham chiếu không rõ nguồn")

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm và trả lời..."):
            try:
                # Use enhanced chat with all bonus features
                result = enhanced_chat(
                    query=query,
                    top_k=top_k,
                    session_id=st.session_state.session_id
                )
                answer = result["answer"]
                sources = result["sources"]
                retrieval_source = result["retrieval_source"]
            except Exception as e:
                error_msg = str(e)
                if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                    answer = "❌ Lỗi: API key OpenAI không hợp lệ hoặc thiếu. Vui lòng kiểm tra file .env."
                elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    answer = "❌ Lỗi: Đã vượt quá hạn mức API. Vui lòng thử lại sau hoặc kiểm tra quota."
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    answer = "❌ Lỗi kết nối mạng. Vui lòng kiểm tra internet và thử lại."
                elif "model" in error_msg.lower():
                    answer = "❌ Lỗi: Model không khả dụng. Vui lòng thử lại sau."
                else:
                    answer = f"❌ Lỗi không mong muốn: {error_msg}"
                sources = []
                retrieval_source = "error"

        st.markdown(answer)

        if sources:
            with st.expander(f"📚 {len(sources)} nguồn tham khảo (retrieval: {retrieval_source})"):
                for i, source in enumerate(sources, 1):
                    render_source(source, i)

                citations_valid, cited, missing = validate_citations(answer, sources)
                if citations_valid:
                    st.success(
                        f"✅ Trích dẫn hợp lệ — [{', '.join(str(c) for c in cited)}] đối chiếu được với nguồn"
                    )
                elif missing:
                    st.warning(
                        f"⚠️ Trích dẫn [{', '.join(str(m) for m in missing)}] không tìm thấy trong nguồn"
                    )
                else:
                    st.info("ℹ️ Không có trích dẫn trong câu trả lời")

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })