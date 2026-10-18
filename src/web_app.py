"""Single-page Streamlit interface for the labor-code assistant."""

import streamlit as st

from app import analyze_question, format_answer_with_sources


st.set_page_config(page_title="Labour Code | Código do Trabalho", page_icon="⚖️")
interface_language = st.radio(
    "Interface language / Idioma da interface",
    options=["Português", "English"],
    horizontal=True,
    key="interface_language",
)
english = interface_language == "English"

if english:
    st.title("Portuguese Labour Code Assistant")
    st.caption(
        "Informational answers based on retrieved articles from the Portuguese "
        "Labour Code. This is not legal advice."
    )
    question_label = "Ask your question"
    question_placeholder = "E.g. Can an employer require a pregnancy test from a job applicant?"
    submit_label = "Ask"
    empty_warning = "Enter a question before submitting."
    spinner_label = "Preparing your question and retrieving relevant articles..."
    sources_label = "Sources consulted"
    source_notice = (
        "Source excerpts are translated for convenience. The official legal text "
        "is in Portuguese."
    )
else:
    st.title("Assistente do Código do Trabalho")
    st.caption(
        "Respostas informativas baseadas nos artigos recuperados do Código do "
        "Trabalho português. Não substitui aconselhamento jurídico."
    )
    question_label = "Escreva a sua pergunta"
    question_placeholder = (
        "Ex.: A empresa pode exigir um teste de gravidez a uma candidata?"
    )
    submit_label = "Consultar"
    empty_warning = "Escreva uma pergunta antes de consultar."
    spinner_label = "A preparar a pergunta e a consultar os artigos relevantes..."
    sources_label = "Artigos consultados"
    source_notice = (
        "Os excertos traduzidos são apresentados apenas para facilitar a leitura. "
        "O texto legal oficial está em português."
    )

with st.form("question-form"):
    question = st.text_area(
        question_label,
        placeholder=question_placeholder,
    )
    submitted = st.form_submit_button(submit_label)

if submitted:
    if not question.strip():
        st.warning(empty_warning)
    else:
        with st.spinner(spinner_label):
            result, articles = analyze_question(question.strip())
        formatted_answer, display_sources = format_answer_with_sources(
            result,
            articles,
            question.strip(),
            "en" if english else "pt",
        )
        st.markdown(formatted_answer)
        if articles:
            with st.expander(sources_label):
                st.caption(source_notice)
                for article in display_sources:
                    article_label = "Article" if english else "Artigo"
                    st.markdown(
                        f"**{article_label} {article['number']} — {article['title']}**"
                    )
                    st.write(article["text"])
