import asyncio
import json
from typing import Any, Dict, List
from core.llm_factory import LLMFactory
from core.prompt_manager import prompt_manager
from core.utils.text_processor import TextProcessor, RecursiveCharacterTextSplitter

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    工业级深度调研工具。
    采用分布式抓取与分级摘要算法，解决超长上下文和实时性挑战。
    """
    query = params.get("query")
    if not query:
        return {"status": "error", "message": "缺少调研主题 (query)。"}

    llm = LLMFactory()
    processor = TextProcessor()
    search_queries = [query] # 预设初始值，防止变量未定义错误
    
    # 1. 意图拆解
    print(f"\n{'*'*20} [Researcher: 意图拆解] {'*'*20}")
    expand_system = prompt_manager.get_prompt("tools.researcher.expansion")
    try:
        expansion_resp = llm.call_default_llm([
            {"role": "system", "content": expand_system},
            {"role": "user", "content": f"用户原始调研需求: {query}"}
        ])
        content = expansion_resp.content.strip()
        # 鲁棒的提取逻辑
        if "[" in content and "]" in content:
            json_str = content[content.find("["):content.rfind("]")+1]
            search_queries = json.loads(json_str)
            print(f"生成的搜索矩阵: {search_queries}")
        else:
            print(f"未能从响应中解析 JSON 数组，内容: {content}")
            search_queries = [query]
    except Exception as e:
        print(f"意图拆解失败，将使用原始查询。错误: {e}")
        search_queries = [query]

    # 2. 并发检索
    from tools import web_search
    print(f"\n{'*'*20} [Researcher: 并发检索] {'*'*20}")
    print(f"执行关键词: {search_queries}")
    search_tasks = [web_search.run({"query": q}) for q in search_queries]
    search_results = await asyncio.gather(*search_tasks)
    
    links = []
    for idx, res in enumerate(search_results):
        if res.get("status") == "success" and res.get("sources"):
            found = [s["link"] for s in res["sources"][:2]]
            print(f"  > 关键词 '{search_queries[idx]}' 命中 {len(found)} 个链接: {found}")
            links.extend(found)
    unique_links = list(set(links))[:5]

    if not unique_links:
        return {"status": "error", "message": "搜索引擎未返回有效结果。"}

    # 3. 分级摘要 (Map-Reduce)
    from tools import web_fetch
    print(f"\n{'*'*20} [Researcher: 并发抓取与分级摘要] {'*'*20}")
    print(f"待处理链接池: {unique_links}")
    fetch_tasks = [web_fetch.run({"url": url}) for url in unique_links]
    fetch_results = await asyncio.gather(*fetch_tasks)
    
    research_splitter = RecursiveCharacterTextSplitter(chunk_size=3500, chunk_overlap=0)
    
    brief_tasks = []
    for res in fetch_results:
        if res.get("status") == "success" and res.get("output"):
            url = res["metadata"]["url"]
            print(f"\n[分析源]: {url}")
            brief_tasks.append(processor.map_reduce_summarize(
                res["output"], 
                query, 
                llm, 
                splitter=research_splitter
            ))
    
    briefs = await asyncio.gather(*brief_tasks)
    valid_briefs = [b for b in briefs if b and "失败" not in b]

    # 4. 最终报告合成
    print(f"\n{'*'*20} [Researcher: 结果合成] {'*'*20}")
    if not valid_briefs:
        return {"status": "error", "message": "所有情报来源均无法访问。"}

    final_context = "\n\n---\n\n".join(valid_briefs)
    synthesize_system = prompt_manager.get_prompt("tools.researcher.synthesis")
    
    try:
        final_resp = llm.call_default_llm([
            {"role": "system", "content": synthesize_system},
            {"role": "user", "content": f"核心查询: {query}\n\n采集到的情报简报:\n{final_context}"}
        ], temperature=0.3)
        
        return {
            "status": "success",
            "output": final_resp.content,
            "metadata": {"sources_processed": len(valid_briefs)}
        }
    except Exception as e:
        return {"status": "error", "message": f"合成报告失败: {e}"}
