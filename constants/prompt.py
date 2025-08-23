from langchain_core.prompts import ChatPromptTemplate

LLM_EDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Bạn là bộ sắp xếp ranh giới chunk cho RAG. "
            "Luật BẮT BUỘC: KHÔNG ĐƯỢC THÊM THÔNG TIN MỚI. "
            "Chỉ được dùng lại, ghép, rút gọn các từ/cụm từ CÓ TRONG CỬA SỔ đưa vào. "
            "Nếu không thể viết lại một câu vì thiếu dữ kiện, ghi null.",
        ),
        (
            "human",
            "Cửa sổ ranh giới giữa A và B (mỗi bên tối đa 5 câu):\n\n"
            "A(tail):\n{a_tail}\n\nB(head):\n{b_head}\n\n"
            "Yêu cầu:\n"
            "1) Quyết định số câu chuyển từ A→B (0..5) và B→A (0..5).\n"
            "2) Nếu câu CUỐI của A bị cắt, viết lại câu đó CHỈ dùng từ trong cửa sổ; nếu không cần, để null.\n"
            "3) Nếu câu ĐẦU của B bị cắt, viết lại câu đó CHỈ dùng từ trong cửa sổ; nếu không cần, để null.\n\n"
            "Trả về JSON đúng schema:\n"
            '{{"move_a_to_b": <int 0..5>, "move_b_to_a": <int 0..5>, '
            '"rewrite_a_last": <string|null>, "rewrite_b_first": <string|null>}}',
        ),
    ]
)
