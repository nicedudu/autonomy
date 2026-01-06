import asyncio
from typing import Any, List, Optional


class TextSplitter:
    """文本分割逻辑的基类。"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 0):
        """
        初始化分割器。
        :param chunk_size: 每个分块的最大字符数。
        :param chunk_overlap: 分块间的重叠字符数，基类默认设为 0。
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """执行文本分割的抽象方法。"""
        raise NotImplementedError


class CharacterTextSplitter(TextSplitter):
    """简单的按字符数硬分割，支持重叠。"""

    def split_text(self, text: str) -> List[str]:
        """根据固定字符数和重叠度切分文本。"""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        return chunks


class RecursiveCharacterTextSplitter(TextSplitter):
    """
    标准递归字符分割器。
    通过一组分隔符（段落、换行、句号等）递归切分，以尽量保持语义完整性。
    """

    def __init__(self, separators: Optional[List[str]] = None, **kwargs):
        """
        初始化递归分割器。
        :param separators: 用于切分的分隔符列表，按优先级排序。
        """
        super().__init__(**kwargs)
        self.separators = separators or [
            "\n\n", "\n", "。 ", "！ ", "？ ", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """执行递归切分逻辑。"""
        final_chunks = []

        # 确定当前层级的首选分隔符
        separator = self.separators[-1]
        for s in self.separators:
            if s == "":
                separator = s
                break
            if s in text:
                separator = s
                break

        # 执行切分
        if separator != "":
            splits = text.split(separator)
        else:
            splits = list(text)

        # 递归组装
        current_doc = []
        total_len = 0

        for s in splits:
            _len = len(s)
            if total_len + _len + (len(separator) if current_doc else 0) <= self.chunk_size:
                current_doc.append(s)
                total_len += _len + (len(separator) if current_doc else 0)
            else:
                if current_doc:
                    doc_content = separator.join(current_doc)
                    if len(doc_content) > self.chunk_size:
                        # 即使使用当前分隔符依然超限，则进入更深层递归
                        final_chunks.extend(self._recurse_split(doc_content))
                    else:
                        final_chunks.append(doc_content)

                    # 处理重叠逻辑：保留末尾符合 overlap 长度的元素
                    overlap_doc = []
                    overlap_len = 0
                    for item in reversed(current_doc):
                        if overlap_len + len(item) <= self.chunk_overlap:
                            overlap_doc.insert(0, item)
                            overlap_len += len(item)
                        else:
                            break
                    current_doc = overlap_doc
                    total_len = overlap_len

                current_doc.append(s)
                total_len += _len

        if current_doc:
            final_chunks.append(separator.join(current_doc))

        return final_chunks

    def _recurse_split(self, text: str) -> List[str]:
        """内部辅助方法：针对超长分块进行更深层级的递归切分。"""
        inner_splitter = RecursiveCharacterTextSplitter(
            separators=self.separators[self.separators.index(
                self.separators[0])+1:] if len(self.separators) > 1 else [""],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        return inner_splitter.split_text(text)


class TextProcessor:
    """
    文本处理核心入口。
    提供分块、摘要等高级文本操作。
    """

    def __init__(self):
        # 注意：此处为 TextProcessor 的默认配置，维持一定的重叠度以保证摘要上下文连贯
        self.default_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=200)

    async def map_reduce_summarize(self, text: str, query: str, llm: Any, splitter: Optional[TextSplitter] = None) -> str:
        """
        通过分级摘要（Map-Reduce 模式）处理长文本。
        """
        active_splitter = splitter or self.default_splitter
        chunks = active_splitter.split_text(text)

        print(f"  [TextProcessor] 文本长度: {len(text)}, 分块数量: {len(chunks)}")

        if len(chunks) == 1:
            return await self._summarize_chunk(chunks[0], query, llm)

        # 并发执行 Map 阶段
        print(
            f"  [TextProcessor] 正在发起 {min(len(chunks), 5)} 个分块的并发摘要 (Map)...")
        tasks = [self._summarize_chunk(c, query, llm) for c in chunks[:5]]
        intermediate = await asyncio.gather(*tasks)

        valid_intermediates = [i for i in intermediate if i]
        print(
            f"  [TextProcessor] Map 阶段完成，成功产出 {len(valid_intermediates)} 份中间摘要。")

        # 执行 Reduce 阶段
        print("  [TextProcessor] 正在执行摘要聚合 (Reduce)...")
        combined = "\n\n".join(valid_intermediates)

        from prompts.utils import REDUCE_SUMMARIZE_TPL
        prompt = []
        for msg in REDUCE_SUMMARIZE_TPL:
            prompt.append({
                "role": msg["role"],
                "content": msg["content"].format(combined_text=combined, query=query)
            })

        try:
            resp = llm.call_default_llm(prompt, temperature=0)
            return resp.content
        except Exception as e:
            print(f"  [TextProcessor] Reduce 失败: {e}")
            return f"合成摘要失败: {e}"

    @staticmethod
    async def _summarize_chunk(chunk: str, query: str, llm: Any) -> str:
        """提取单个文本块中与查询相关的关键数据点和事实。"""
        from prompts.utils import MAP_SUMMARIZE_TPL
        prompt = []
        for msg in MAP_SUMMARIZE_TPL:
            prompt.append({
                "role": msg["role"],
                "content": msg["content"].format(chunk=chunk, query=query)
            })

        try:
            resp = llm.call_default_llm(prompt, temperature=0)
            content = resp.content.strip()
            if content:
                # 打印摘要预览
                print(f"\n      [Map 摘要产出]:\n      {content[:300]}...")
            return content
        except Exception as e:
            print(f"      [Map 摘要失败]: {e}")
            return ""
