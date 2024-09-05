from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_milvus import Milvus
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from typing import List


class JokeVectorStore:
    db: Milvus

    def __init__(self) -> None:
        self.db = self._get_db()

    def search(self, query: str) -> List[Document]:
        return self.db.similarity_search(query, top_k=5)

    def create_index(self):
        pdf_loader = PyPDFLoader("./data/kids_joke_book.pdf")
        documents = pdf_loader.load_and_split(
            text_splitter=RecursiveCharacterTextSplitter(
                chunk_size=500, chunk_overlap=0
            )
        )
        self.db.add_documents(documents)

    def _get_db(self) -> Milvus:
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        return Milvus(
            embedding_function=embeddings,
            connection_args={"uri": "./vectorstore.db"},
            # drop_old=True,
            auto_id=True,
        )
