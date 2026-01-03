import os
import yaml
from typing import Dict, Generic, Type, TypeVar
from pydantic import BaseModel
from core.schema.models import AgentManifest, SkillManifest

T = TypeVar("T", bound=BaseModel)

class Registry(Generic[T]):
    """Resource registry for YAML-based dynamic discovery."""
    
    def __init__(self, resource_type: Type[T], directory: str):
        self._resource_type = resource_type
        self._directory = directory
        self._storage: Dict[str, T] = {}

    def discover(self):
        """Scans directory and loads resource manifests."""
        if not os.path.exists(self._directory):
            return

        for root, _, files in os.walk(self._directory):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    path = os.path.join(root, file)
                    self._load_resource(path)

    def _load_resource(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                resource = self._resource_type(**data)
                
                # Apply database overrides for agents
                if isinstance(resource, AgentManifest):
                    resource = self._apply_database_override(resource)
                
                # Determine resource ID (agent_id or skill_id)
                resource_id = getattr(resource, "agent_id", None) or getattr(resource, "skill_id", None)
                if resource_id:
                    self._storage[resource_id] = resource
            except Exception as e:
                raise RuntimeError(f"FATAL: Failed to load manifest at {path}. Error: {str(e)}")

    def _apply_database_override(self, manifest: AgentManifest) -> AgentManifest:
        """Synchronizes agent configuration from database."""
        from core.supabase_manager import SupabaseManager
        db = SupabaseManager()
        db_config = db.get_agent_config(manifest.agent_id)
        
        if not db_config:
            raise RuntimeError(f"CRITICAL: Agent '{manifest.agent_id}' missing in database.")

        # Sync critical operational fields
        manifest.name = db_config.get("name", manifest.name)
        manifest.role = db_config.get("role", manifest.role)
        manifest.model = db_config.get("model")
        manifest.provider_id = db_config.get("provider_id")
            
        return manifest

    def get(self, resource_id: str) -> T:
        return self._storage.get(resource_id)

    def all(self) -> Dict[str, T]:
        return self._storage

class DiscoveryService:
    """Centralized discovery service for agents and skills."""
    
    def __init__(self):
        self.agents = Registry(AgentManifest, "agents/registry")
        self.skills = Registry(SkillManifest, "agents/skills")

    def initialize(self):
        self.agents.discover()
        self.skills.discover()

discovery_service = DiscoveryService()
