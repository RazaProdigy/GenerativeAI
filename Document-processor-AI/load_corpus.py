# file to load the data to vector store (one time run)
from vector_store import add_documents
from langchain_community.document_loaders.parsers.pdf import PyPDFParser
from langchain_core.documents.base import Blob
from langchain_text_splitters import RecursiveCharacterTextSplitter

blob = Blob.from_path("agentic_ai_demo.pdf")
parser = PyPDFParser()
documents = parser.lazy_parse(blob)

docs = []
for doc in documents:
    docs.append(doc)
print(docs)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=40)
chunks = text_splitter.split_documents(docs)

for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk.page_content}...")
    print("-"*100)
# add the documents
add_documents([chunk.page_content for chunk in chunks])

print("Documents added to vector store")





