"""
知识检索服务
"""
from typing import List, Dict, Optional, Any
import uuid
import asyncio
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from config import settings

try:
    import chromadb
    from chromadb.config import Settings
except Exception:
    chromadb = None
    Settings = None


class KnowledgeRetriever:
    """知识检索器类"""
    
    def __init__(self):
        self.available = chromadb is not None
        self.client = None
        self.embeddings = None
        self.knowledge_collection = None
        self.product_collection = None
        if self.available:
            self.client = chromadb.Client(Settings(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                anonymized_telemetry=False
            ))
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            self.knowledge_collection = self._get_or_create_collection("knowledge_base")
            self.product_collection = self._get_or_create_collection("product_catalog")
    
    def _get_or_create_collection(self, name: str):
        """获取或创建集合"""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"description": f"{name} collection"}
            )
    
    async def retrieve(
        self,
        query: str,
        collection_name: str = "knowledge_base",
        top_k: int = 3,
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """检索相关文档"""
        if not self.available or not self.embeddings:
            return []
        # 选择集合
        collection = (
            self.knowledge_collection 
            if collection_name == "knowledge_base" 
            else self.product_collection
        )
        
        # 生成查询向量（在线程池中执行同步方法）
        loop = asyncio.get_event_loop()
        query_embedding = await loop.run_in_executor(
            None, self.embeddings.embed_query, query
        )
        
        # 执行检索
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )
        
        # 转换为Document对象
        documents = []
        if results and results['documents']:
            for i, doc_text in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                metadata['relevance_score'] = 1 - results['distances'][0][i] if results['distances'] else 0
                
                documents.append(Document(
                    page_content=doc_text,
                    metadata=metadata
                ))
        
        return documents
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str = "knowledge_base"
    ) -> List[str]:
        """添加文档到知识库"""
        if not self.available or not self.embeddings:
            return []
        collection = (
            self.knowledge_collection 
            if collection_name == "knowledge_base" 
            else self.product_collection
        )
        
        doc_ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            doc_id = doc.get("id", str(uuid.uuid4()))
            doc_ids.append(doc_id)
            texts.append(doc["content"])
            metadatas.append(doc.get("metadata", {}))
        
        # 生成嵌入向量（在线程池中执行同步方法）
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.embeddings.embed_documents, texts
        )
        
        # 添加到集合
        collection.add(
            ids=doc_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        return doc_ids
    
    async def delete_document(
        self,
        document_id: str,
        collection_name: str = "knowledge_base"
    ):
        """删除文档"""
        if not self.available:
            return
        collection = (
            self.knowledge_collection 
            if collection_name == "knowledge_base" 
            else self.product_collection
        )
        
        collection.delete(ids=[document_id])
    
    async def update_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict] = None,
        collection_name: str = "knowledge_base"
    ):
        """更新文档"""
        if not self.available or not self.embeddings:
            return
        collection = (
            self.knowledge_collection 
            if collection_name == "knowledge_base" 
            else self.product_collection
        )
        
        # 生成新的嵌入向量
        embedding = self.embeddings.embed_query(content)
        
        # 更新文档
        collection.update(
            ids=[document_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata] if metadata else None
        )
    
    async def search_by_metadata(
        self,
        filter_metadata: Dict,
        collection_name: str = "knowledge_base",
        limit: int = 10
    ) -> List[Document]:
        """根据元数据搜索文档"""
        if not self.available:
            return []
        collection = (
            self.knowledge_collection 
            if collection_name == "knowledge_base" 
            else self.product_collection
        )
        
        results = collection.get(
            where=filter_metadata,
            limit=limit
        )
        
        documents = []
        if results and results['documents']:
            for i, doc_text in enumerate(results['documents']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                documents.append(Document(
                    page_content=doc_text,
                    metadata=metadata
                ))
        
        return documents
    
    def get_collection_stats(self, collection_name: str = "knowledge_base") -> Dict:
        """获取集合统计信息"""
        if not self.available:
            return {"name": collection_name, "count": 0, "metadata": {}}
        collection = (
            self.knowledge_collection 
            if collection_name == "knowledge_base" 
            else self.product_collection
        )
        
        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata
        }


# 全局知识检索器实例
knowledge_retriever = KnowledgeRetriever()
