"""Single-page Streamlit interface for the labor-code assistant."""

import streamlit as st

from app import analyze_question, format_answer


st.set_page_config(page_title="Código do Trabalho", page_icon="⚖️")
st.title("Assistente do Código do Trabalho")
st.caption(
    "Respostas informativas baseadas nos artigos recuperados do Código do "
    "Trabalho português. Não substitui aconselhamento jurídico."
)

with st.form("question-form"):
    question = st.text_area(
        "Escreva a sua pergunta",
        placeholder="Ex.: A empresa pode exigir um teste de gravidez a uma candidata?",
    )
    submitted = st.form_submit_button("Consultar")

if submitted:
    if not question.strip():
        st.warning("Escreva uma pergunta antes de consultar.")
    else:
        with st.spinner("A consultar os artigos relevantes..."):
            result, articles = analyze_question(question.strip())
        st.markdown(format_answer(result))
        if articles:
            with st.expander("Artigos consultados"):
                for article in articles:
                    st.markdown(f"**Artigo {article['number']} — {article['title']}**")
                    st.write(article["text"])
