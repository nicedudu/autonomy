"use client";

import { supabase } from "@/lib/supabase";
import { Button } from "@autonomy/ui/components/button";
import { Card } from "@autonomy/ui/components/card";
import { Input } from "@autonomy/ui/components/input";
import { Label } from "@autonomy/ui/components/label";
import { ScrollArea } from "@autonomy/ui/components/scroll-area";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@autonomy/ui/components/select";
import { Textarea } from "@autonomy/ui/components/textarea";
import { Code2, Save, Search, Terminal, Zap } from "lucide-react";
import { useEffect, useState } from "react";

export default function AdminAgentsThemeAligned() {
    const [agents, setAgents] = useState<any[]>([]);
    const [providers, setProviders] = useState<any[]>([]);
    const [allPrompts, setAllPrompts] = useState<any[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        const { data: agentsData } = await supabase
            .from("agents")
            .select("*")
            .order("agent_id");
        const { data: promptsData } = await supabase
            .from("prompt_library")
            .select("*");
        const { data: providersData } = await supabase
            .from("llm_providers")
            .select("*");

        if (agentsData) setAgents(agentsData);
        if (promptsData) setAllPrompts(promptsData);
        if (providersData) setProviders(providersData);

        if (agentsData && agentsData.length > 0 && !selectedAgent) {
            setSelectedAgent(agentsData[0]);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchData();
    }, []);

    const currentProvider = providers.find(
        (p) => p.name.toLowerCase() === selectedAgent?.provider?.toLowerCase()
    );
    const availableModels = Array.isArray(currentProvider?.supported_models)
        ? currentProvider.supported_models
        : [];

    const agentPrefix = selectedAgent?.agent_id.split("_")[0];
    let currentUserPrompt = allPrompts.find((p) =>
        p.slug.startsWith(agentPrefix)
    );

    const handleSave = async () => {
        setIsSaving(true);
        const { error: agentError } = await supabase
            .from("agents")
            .update({
                provider: selectedAgent.provider,
                model: selectedAgent.model,
                system_prompt: selectedAgent.system_prompt,
            })
            .eq("agent_id", selectedAgent.agent_id);

        if (currentUserPrompt) {
            await supabase.from("prompt_library").upsert(
                {
                    slug: currentUserPrompt.slug || `${agentPrefix}_task`,
                    name:
                        currentUserPrompt.name ||
                        `${selectedAgent.name} 任务指令`,
                    template: currentUserPrompt.template,
                },
                { onConflict: "slug" }
            );
        }

        if (!agentError) {
            alert("配置已保存");
            fetchData();
        } else {
            alert("保存失败: " + agentError.message);
        }
        setIsSaving(false);
    };

    const handleDeleteAgent = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (!confirm("确定要删除此智能体吗？")) return;
        const { error } = await supabase
            .from("agents")
            .delete()
            .eq("agent_id", id);
        if (!error) {
            if (selectedAgent?.agent_id === id) setSelectedAgent(null);
            fetchData();
        }
    };

    const updatePromptLocal = (val: string) => {
        const newPrompts = [...allPrompts];
        const idx = newPrompts.findIndex((p) => p.slug.startsWith(agentPrefix));
        if (idx !== -1) newPrompts[idx].template = val;
        else newPrompts.push({ slug: `${agentPrefix}_task`, template: val });
        setAllPrompts(newPrompts);
    };

    return (
        <div className="h-full flex bg-background font-sans overflow-hidden">
            {/* === Left: Sidebar === */}
            <aside className="w-64 border-r border-border flex flex-col bg-muted/20 shrink-0">
                <div className="h-12 p-3 border-b border-border bg-sidebar/20 flex items-center gap-2">
                    <div className="relative flex-1">
                        <Search
                            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-foreground/30"
                            size={13}
                        />
                        <Input
                            placeholder="搜索智能体..."
                            className="w-full pl-8 h-8 text-xs! bg-background/50 border-border shadow-none"
                        />
                    </div>
                </div>

                <ScrollArea className="flex-1">
                    <nav className="p-3 space-y-1">
                        {agents.map((agent) => (
                            <div
                                key={agent.agent_id}
                                onClick={() => setSelectedAgent(agent)}
                                className={`w-full flex items-center justify-start py-2.5 px-4 rounded-xl gap-4 cursor-pointer transition-all group ${
                                    selectedAgent?.agent_id === agent.agent_id
                                        ? "bg-primary/10 text-primary font-bold border border-primary/20"
                                        : "text-foreground/50 hover:bg-foreground/5 border border-transparent"
                                }`}
                            >
                                <div
                                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg shrink-0 ${
                                        selectedAgent?.agent_id ===
                                        agent.agent_id
                                            ? "bg-primary/20"
                                            : "bg-muted"
                                    }`}
                                >
                                    {agent.avatar}
                                </div>
                                <div className="truncate flex-1">
                                    <div
                                        className={`text-sm truncate leading-tight ${
                                            selectedAgent?.agent_id ===
                                            agent.agent_id
                                                ? "text-primary"
                                                : "text-foreground"
                                        }`}
                                    >
                                        {agent.name}
                                    </div>
                                    <div className="text-xs text-muted-foreground font-mono uppercase tracking-tighter truncate mt-0.5">
                                        {agent.role}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </nav>
                </ScrollArea>
            </aside>

            {/* === Right: Content === */}
            <main className="flex-1 flex flex-col min-w-0 bg-background relative">
                {selectedAgent ? (
                    <>
                        <header className="h-12 border-b border-border px-4 flex items-center justify-between shrink-0 bg-background sticky top-0 z-20">
                            <div className="flex items-center gap-2">
                                <div className="text-primary text-lg">
                                    {selectedAgent.avatar}
                                </div>
                                <span className="text-[14px] font-bold text-foreground">
                                    {selectedAgent.name}
                                </span>
                            </div>
                        </header>

                        <ScrollArea className="flex-1 bg-background p-6 h-full overflow-auto">
                            <div className="max-w-4xl mx-auto space-y-10 pb-12">
                                {/* 1. LLM Config */}
                                <section className="space-y-4">
                                    <div className="flex items-center gap-2 text-foreground">
                                        <Zap
                                            size={14}
                                            className="text-primary"
                                        />
                                        <h3 className="text-xs font-bold uppercase tracking-wider">
                                            LLM 核心配置
                                        </h3>
                                    </div>

                                    <Card className="p-4 bg-muted/10 border-border rounded-xl space-y-6 shadow-none">
                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-2">
                                                <Label className="text-xs font-black text-muted-foreground uppercase tracking-widest">
                                                    模型选择
                                                </Label>
                                                <Select
                                                    value={selectedAgent.model}
                                                    onValueChange={(val) =>
                                                        setSelectedAgent({
                                                            ...selectedAgent,
                                                            model: val,
                                                        })
                                                    }
                                                >
                                                    <SelectTrigger className="w-full bg-background border-border h-9 text-sm shadow-none">
                                                        <SelectValue placeholder="选择模型" />
                                                    </SelectTrigger>
                                                    <SelectContent className="border-border">
                                                        {availableModels.length >
                                                        0 ? (
                                                            availableModels.map(
                                                                (m: string) => (
                                                                    <SelectItem
                                                                        key={m}
                                                                        value={
                                                                            m
                                                                        }
                                                                        className="text-sm font-mono"
                                                                    >
                                                                        {m}
                                                                    </SelectItem>
                                                                )
                                                            )
                                                        ) : (
                                                            <SelectItem
                                                                value={
                                                                    selectedAgent.model
                                                                }
                                                                className="text-sm font-mono"
                                                            >
                                                                {
                                                                    selectedAgent.model
                                                                }
                                                            </SelectItem>
                                                        )}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="space-y-2">
                                                <Label className="text-xs font-black text-muted-foreground uppercase tracking-widest">
                                                    API 类型
                                                </Label>
                                                <div className="w-full bg-background/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground/70 flex items-center gap-2 h-9">
                                                    {currentProvider?.type ||
                                                        "openai"}{" "}
                                                    协议
                                                </div>
                                            </div>
                                        </div>
                                    </Card>
                                </section>

                                {/* 2. System Prompt */}
                                <section className="space-y-4">
                                    <div className="flex items-center gap-2 text-foreground">
                                        <Terminal
                                            size={14}
                                            className="text-primary"
                                        />
                                        <h3 className="text-xs font-bold uppercase tracking-wider">
                                            系统提示词 (System Prompt)
                                        </h3>
                                    </div>
                                    <Textarea
                                        value={selectedAgent.system_prompt}
                                        onChange={(e) =>
                                            setSelectedAgent({
                                                ...selectedAgent,
                                                system_prompt: e.target.value,
                                            })
                                        }
                                        className="w-full h-48 bg-background border-border rounded-xl p-4 text-sm leading-relaxed font-mono shadow-none"
                                        placeholder="在此确立智能体的身份协议与行为准则..."
                                    />
                                </section>

                                {/* 3. User Prompt */}
                                <section className="space-y-4">
                                    <div className="flex items-center gap-2 text-foreground">
                                        <Code2
                                            size={14}
                                            className="text-primary"
                                        />
                                        <h3 className="text-xs font-bold uppercase tracking-wider">
                                            用户提示词 (User Prompt)
                                        </h3>
                                    </div>
                                    <Textarea
                                        value={
                                            currentUserPrompt?.template || ""
                                        }
                                        onChange={(e) =>
                                            updatePromptLocal(e.target.value)
                                        }
                                        className="w-full h-96 bg-background border-border rounded-xl p-4 text-sm leading-relaxed font-mono shadow-none"
                                        placeholder="在此定义具体的执行任务与操作流程..."
                                    />
                                </section>

                                <div className="flex justify-end">
                                    <Button
                                        onClick={handleSave}
                                        disabled={isSaving}
                                        className="text-sm px-8 h-10 font-bold shadow-lg shadow-primary/20"
                                    >
                                        <Save size={16} />
                                        {isSaving ? "保存中..." : "保存"}
                                    </Button>
                                </div>
                            </div>
                        </ScrollArea>
                    </>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground/30 font-black uppercase tracking-[0.2em] text-sm">
                        请选择左侧智能体进行配置
                    </div>
                )}
            </main>
        </div>
    );
}
