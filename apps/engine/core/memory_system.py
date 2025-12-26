from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import uuid
import time

class MemorySystem:
    """基于ChromaDB的长期记忆系统"""
    
    def __init__(self, persist_directory: str = "./chromadb_data"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                persist_directory=persist_directory
            )
        )
        self.persist_directory = persist_directory
        self.collections = {}
    
    def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
        """获取或创建集合"""
        if collection_name not in self.collections:
            self.collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"created_at": time.time()}
            )
        return self.collections[collection_name]
    
    def store_memory(self, agent_id: str, memory_content: str, metadata: Dict[str, Any] = None) -> str:
        """存储记忆"""
        collection = self.get_or_create_collection(agent_id)
        memory_id = str(uuid.uuid4())
        
        # 准备元数据
        memory_metadata = {
            "memory_id": memory_id,
            "created_at": time.time(),
            "type": metadata.get("type", "general") if metadata else "general"
        }
        
        if metadata:
            memory_metadata.update(metadata)
        
        # 存储记忆（ChromaDB会自动处理向量化）
        collection.add(
            documents=[memory_content],
            metadatas=[memory_metadata],
            ids=[memory_id]
        )
        
        return memory_id
    
    def retrieve_memories(self, agent_id: str, query: str, n_results: int = 5, filter_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        collection = self.get_or_create_collection(agent_id)
        
        # 执行相似性搜索
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_criteria
        )
        
        # 格式化结果
        memories = []
        for i in range(len(results["ids"][0])):
            memory = {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": results["distances"][0][i] if "distances" in results else None
            }
            memories.append(memory)
        
        return memories
    
    def update_memory(self, agent_id: str, memory_id: str, new_content: str, new_metadata: Dict[str, Any] = None) -> bool:
        """更新记忆"""
        try:
            collection = self.get_or_create_collection(agent_id)
            collection.update(
                ids=[memory_id],
                documents=[new_content],
                metadatas=[new_metadata]
            )
            return True
        except Exception as e:
            print(f"更新记忆失败: {e}")
            return False
    
    def delete_memory(self, agent_id: str, memory_id: str) -> bool:
        """删除记忆"""
        try:
            collection = self.get_or_create_collection(agent_id)
            collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"删除记忆失败: {e}")
            return False
    
    def get_all_memories(self, agent_id: str, filter_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """获取所有记忆"""
        collection = self.get_or_create_collection(agent_id)
        
        results = collection.get(
            where=filter_criteria
        )
        
        memories = []
        for i in range(len(results["ids"])):
            memory = {
                "id": results["ids"][i],
                "content": results["documents"][i],
                "metadata": results["metadatas"][i]
            }
            memories.append(memory)
        
        return memories
    
    def clear_memories(self, agent_id: str) -> bool:
        """清除特定Agent的所有记忆"""
        try:
            self.client.delete_collection(name=agent_id)
            if agent_id in self.collections:
                del self.collections[agent_id]
            return True
        except Exception as e:
            print(f"清除记忆失败: {e}")
            return False
    
    def get_memory_count(self, agent_id: str) -> int:
        """获取记忆数量"""
        collection = self.get_or_create_collection(agent_id)
        return collection.count()
    
    def store_agent_interaction(self, agent_id: str, interaction_type: str, content: Dict[str, Any]):
        """存储Agent交互记录"""
        # 格式化交互内容
        interaction_text = f"{interaction_type}: {content}"
        metadata = {
            "type": "interaction",
            "interaction_type": interaction_type,
            "timestamp": time.time()
        }
        
        return self.store_memory(agent_id, interaction_text, metadata)
    
    def retrieve_recent_interactions(self, agent_id: str, n: int = 10) -> List[Dict[str, Any]]:
        """检索最近的交互记录"""
        # 获取所有交互记录
        interactions = self.get_all_memories(agent_id, filter_criteria={"type": "interaction"})
        
        # 按时间排序，返回最近的n条
        interactions.sort(key=lambda x: x["metadata"]["timestamp"], reverse=True)
        return interactions[:n]
