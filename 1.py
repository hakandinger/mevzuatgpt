

from dotenv import load_dotenv
import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings



def main():
    load_dotenv()
    st.set_page_config(page_title="PDF Dosyasını Yükle")
    st.header("PDF Dosyasını Yükle")

    #print(os.getenv())

    #pdf="C:\Users\421942\mevzuatgpt\1.5.7245.pdf"
    pdf=""
    if pdf is not None:
        pdf_reader = PdfReader(pdf)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        text_splitter = CharacterTextSplitter(
            separator ="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,

        )

        chunks = text_splitter.split_text(text)

        embeddings = OpenAIEmbeddings()
        #st.write(chunks)
        knowledge_base = FAISS.from_texts(chunks, embeddings)

        user_question = st.text_input()
        if user_question:
            docs = knowledge_base.similarity_search(user_question)
            #st.write(docs)
         




