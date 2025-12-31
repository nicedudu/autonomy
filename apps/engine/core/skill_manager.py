import yaml
import os
import importlib.util
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class SkillManifest(BaseModel):
    skill_id: str
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    required: List[str] = []
    implementation: str # 对应的 py 文件路径

class SkillManager:
    """
    Nexus V4 技能管理器
    负责 Skills 的发现、动态加载与工具化转换。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillManager, cls).__new__(cls)
            cls._instance.skills: Dict[str, SkillManifest] = {}
            cls._instance.registry_dir = "agents/skills"
        return cls._instance

    def discover_skills(self):
        """扫描技能目录，加载元数据"""
        if not os.path.exists(self.registry_dir):
            os.makedirs(self.registry_dir)
            return

        for filename in os.listdir(self.registry_dir):
            if filename.endswith(".yaml"):
                path = os.path.join(self.registry_dir, filename)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        data = yaml.safe_load(f)
                        manifest = SkillManifest(**data)
                        self.skills[manifest.skill_id] = manifest
                        print(f"[SkillManager] 发现并注册技能: {manifest.name} ({manifest.skill_id})")
                    except Exception as e:
                        print(f"[SkillManager] 加载技能失败 {filename}: {e}")

    def get_skill_instruction(self, skill_ids: List[str]) -> str:
        """生成供 LLM 阅读的技能说明文档"""
        instructions = []
        for sid in skill_ids:
            skill = self.skills.get(sid)
            if skill:
                instr = f"- {skill.name} ({skill.skill_id}): {skill.description}\n"
                instr += f"  参数要求: {skill.parameters}"
                instructions.append(instr)
        
        if not instructions:
            return ""
        return "\n[可用专业技能列表]:\n" + "\n".join(instructions)

    def run_skill(self, skill_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行特定技能 (Nexus V4 真实执行引擎)
        """
        skill = self.skills.get(skill_id)
        if not skill:
            return {"success": False, "error": f"未找到技能: {skill_id}"}
        
        implementation_path = skill.implementation
        # 转换相对路径为绝对路径或正确的模块路径
        # 假设 implementation 是 "tools/market_scraper.py"
        try:
            # 动态加载模块
            module_name = f"skills.impl.{skill_id}"
            file_path = os.path.join(os.getcwd(), "apps/engine", implementation_path)
            
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 约定：所有技能必须实现异步或同步的 run(params) 函数
            if hasattr(module, "run"):
                print(f"[SkillManager] 执行技能 {skill_id}...")
                result = module.run(params)
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": f"技能模块 {skill_id} 缺失 run 函数接口"}
                
        except Exception as e:
            print(f"[SkillManager] 技能执行崩溃: {e}")
            return {"success": False, "error": str(e)}

skill_manager = SkillManager()
