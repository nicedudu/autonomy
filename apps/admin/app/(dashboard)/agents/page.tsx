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
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@autonomy/ui/components/tooltip";
import { Save, Search, Settings, Zap } from "lucide-react";
import { useEffect, useState } from "react";

export default function AdminAgentsThemeAligned() {
    const [agents, setAgents] = useState<any[]>([]);
    const [providers, setProviders] = useState<any[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<any>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [generalConfig, setGeneralConfig] = useState({
        provider_id: "",
        model: "",
        core_system_prompt: "",
    });

    const fetchData = async () => {
        setLoading(true);
        try {
            // 1. 获取本地引擎数据 (增加鲁棒性)
            let engineAgents: any[] = [];
            try {
                // 使用 127.0.0.1 提高连接稳定性
                const agentsRes = await fetch(
                    "http://127.0.0.1:8000/api/agents",
                    {
                        signal: AbortSignal.timeout(3000), // 3秒超时，防止无限挂起
                    }
                );
                if (agentsRes.ok) {
                    engineAgents = await agentsRes.json();
                }
            } catch (engineErr) {
                console.warn(
                    "本地引擎 API 离线，将仅显示数据库数据:",
                    engineErr
                );
            }

            // 2. 获取 Supabase 云端数据 (调度配置)
            const [providersRes, settingsRes, dbAgentsRes] = await Promise.all([
                supabase.from("llm_providers").select("*"),
                supabase.from("system_settings").select("*").single(),
                supabase.from("agents").select("*"),
            ]);

            // 3. 深度数据合并
            const dbAgents = dbAgentsRes.data || [];

            // 以 Engine 的身份定义为基准，合并数据库的调度配置
            const mergedAgents = engineAgents.map((engineAgent) => {
                const dbConfig = dbAgents.find(
                    (da) => da.identifier === engineAgent.identifier
                );
                return {
                    ...engineAgent,
                    provider_id: dbConfig?.provider_id || "",
                    model: dbConfig?.model || "",
                    temperature: dbConfig?.temperature || 0.7,
                    extra_params: dbConfig?.extra_params || {},
                };
            });

            if (mergedAgents.length > 0) {
                setAgents(mergedAgents);
            } else if (dbAgents.length > 0) {
                // 降级方案：如果 Engine 离线，至少显示数据库里的配置
                setAgents(dbAgents);
            }

            if (providersRes.data) setProviders(providersRes.data);
            if (settingsRes.data) {
                setGeneralConfig({
                    provider_id: settingsRes.data.default_provider_id,
                    model: settingsRes.data.default_model,
                    core_system_prompt:
                        settingsRes.data.core_system_prompt || "",
                });
            }

            // 自动选择第一个 Agent
            if (engineAgents.length > 0 && !selectedAgent) {
                setSelectedAgent(engineAgents[0]);
            }
        } catch (err) {
            console.error("Admin 全局加载失败:", err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchData();
    }, []);

    const filteredAgents = agents.filter(
        (agent) =>
            agent.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            agent.role?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const currentProvider = providers.find(
        (p) => p.id === selectedAgent?.provider_id
    );
    const availableModels = Array.isArray(currentProvider?.supported_models)
        ? currentProvider.supported_models
        : [];

    const generalProvider = providers.find(
        (p) => p.id === generalConfig.provider_id
    );
    const generalAvailableModels = Array.isArray(
        generalProvider?.supported_models
    )
        ? generalProvider.supported_models
        : [];

    const handleSave = async () => {
        setIsSaving(true);
        let error;

        if (selectedAgent === "general_config") {
            const { error: settingsError } = await supabase
                .from("system_settings")
                .update({
                    default_provider_id: generalConfig.provider_id,
                    default_model: generalConfig.model,
                    updated_at: new Date().toISOString(),
                })
                .eq("id", 1);
            error = settingsError;
        } else {
            const { error: agentError } = await supabase
                .from("agents")
                .update({
                    provider_id: selectedAgent.provider_id,
                    model: selectedAgent.model,
                })
                .eq("identifier", selectedAgent.identifier);
            error = agentError;
        }

        if (!error) {
            alert("调度配置已保存");
            fetchData();
        } else {
            alert("保存失败: " + error.message);
        }
        setIsSaving(false);
    };

    return (
        <div className="h-full flex bg-background font-sans overflow-hidden">
            {/* === Left: Sidebar === */}
            <aside className="w-64 border-r border-border/40 flex flex-col bg-muted/20 shrink-0">
                <div className="h-12 p-3 border-b border-border/40 bg-sidebar/20 flex items-center gap-2">
                    <div className="relative flex-1">
                        <Search
                            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-foreground/30"
                            size={13}
                        />
                        <Input
                            placeholder="搜索智能体..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-8 h-8 text-xs! bg-background/50 border-border shadow-none"
                        />
                    </div>
                </div>

                <ScrollArea className="flex-1">
                    <nav className="p-3 space-y-1">
                        {filteredAgents.map((agent) => (
                            <div
                                key={agent.identifier}
                                onClick={() => setSelectedAgent(agent)}
                                className={`w-full flex items-center justify-start py-2.5 px-4 rounded-xl gap-4 cursor-pointer transition-all group ${
                                    selectedAgent?.identifier ===
                                    agent.identifier
                                        ? "bg-primary/10 text-primary font-bold border border-primary/20"
                                        : "text-foreground/50 hover:bg-foreground/5 border border-transparent"
                                }`}
                            >
                                <div
                                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg shrink-0 overflow-hidden ${
                                        selectedAgent?.identifier ===
                                        agent.identifier
                                            ? "bg-primary/20"
                                            : "bg-muted"
                                    }`}
                                >
                                    <img
                                        src={agent.avatar}
                                        alt={agent.name}
                                        className="w-full h-full object-cover"
                                    />
                                </div>
                                <div className="truncate flex-1">
                                    <div
                                        className={`text-sm truncate leading-tight ${
                                            selectedAgent?.identifier ===
                                            agent.identifier
                                                ? "text-primary"
                                                : "text-foreground"
                                        }`}
                                    >
                                        {agent.name}
                                    </div>
                                    <div className="text-xs text-muted-foreground font-mono tracking-tighter truncate mt-0.5">
                                        {agent.role}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </nav>
                </ScrollArea>

                <div className="p-4 bg-transparent flex justify-end">
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() =>
                                        setSelectedAgent("general_config")
                                    }
                                    className={`h-9 w-9 rounded-xl transition-all shadow-none ${
                                        selectedAgent === "general_config"
                                            ? "bg-primary/10 text-primary border border-primary/20 hover:bg-primary/10 hover:text-primary"
                                            : "text-foreground hover:bg-foreground/5 hover:text-foreground"
                                    }`}
                                >
                                    <Settings
                                        size={16}
                                        className={
                                            selectedAgent === "general_config"
                                                ? "text-primary"
                                                : "text-muted-foreground"
                                        }
                                    />
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent
                                side="right"
                                className="flex flex-row items-center gap-2.5 py-1.5 px-3"
                            >
                                <span className="font-bold text-xs">默认</span>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>
            </aside>

            {/* === Right: Content === */}
            <main className="flex-1 flex flex-col min-w-0 bg-background relative overflow-hidden">
                {selectedAgent === "general_config" ? (
                    <div className="flex-1 flex flex-col min-h-0">
                        <header className="h-12 border-b border-border/40 px-4 flex items-center justify-between shrink-0 bg-background sticky top-0 z-20">
                            <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-md overflow-hidden flex items-center justify-center bg-primary/10">
                                    <Settings
                                        size={14}
                                        className="text-primary"
                                    />
                                </div>
                                <span className="text-[14px] font-bold text-foreground">
                                    默认
                                </span>
                            </div>
                        </header>
                        <ScrollArea className="h-full">
                            <div className="max-w-4xl mx-auto space-y-10 p-6 pb-12">
                                <section className="space-y-4">
                                    <div className="flex items-center gap-2 text-foreground">
                                        <Zap
                                            size={14}
                                            className="text-primary"
                                        />
                                        <h3 className="text-xs font-bold">
                                            模型调度
                                        </h3>
                                    </div>

                                    <Card className="p-4 bg-muted/10 border-border rounded-xl space-y-6 shadow-none">
                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-2">
                                                <Label className="text-xs font-black text-muted-foreground">
                                                    供应商
                                                </Label>
                                                <Select
                                                    value={
                                                        generalConfig.provider_id
                                                    }
                                                    onValueChange={(val) => {
                                                        const p =
                                                            providers.find(
                                                                (prov) =>
                                                                    prov.id ===
                                                                    val
                                                            );
                                                        setGeneralConfig({
                                                            ...generalConfig,
                                                            provider_id: val,
                                                            model:
                                                                p
                                                                    ?.supported_models?.[0] ||
                                                                "",
                                                        });
                                                    }}
                                                >
                                                    <SelectTrigger className="w-full bg-background border-border h-9 text-sm shadow-none">
                                                        <SelectValue placeholder="选择供应商" />
                                                    </SelectTrigger>
                                                    <SelectContent className="border-border">
                                                        {providers.map((p) => (
                                                            <SelectItem
                                                                key={p.id}
                                                                value={p.id}
                                                            >
                                                                {p.name}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="space-y-2">
                                                <Label className="text-xs font-black text-muted-foreground">
                                                    模型
                                                </Label>
                                                <Select
                                                    value={generalConfig.model}
                                                    onValueChange={(val) =>
                                                        setGeneralConfig({
                                                            ...generalConfig,
                                                            model: val,
                                                        })
                                                    }
                                                >
                                                    <SelectTrigger className="w-full bg-background border-border h-9 text-sm shadow-none">
                                                        <SelectValue placeholder="选择模型" />
                                                    </SelectTrigger>
                                                    <SelectContent className="border-border">
                                                        {generalAvailableModels.map(
                                                            (m: string) => (
                                                                <SelectItem
                                                                    key={m}
                                                                    value={m}
                                                                >
                                                                    {m}
                                                                </SelectItem>
                                                            )
                                                        )}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    </Card>
                                </section>

                                <div className="flex justify-end">
                                    <Button
                                        onClick={handleSave}
                                        disabled={isSaving}
                                        className="text-xs px-6 h-9 font-bold shadow-lg shadow-primary/20"
                                    >
                                        <Save size={14} />
                                        {isSaving ? "保存中..." : "保存"}
                                    </Button>
                                </div>
                            </div>
                        </ScrollArea>
                    </div>
                ) : selectedAgent ? (
                    <div className="flex-1 flex flex-col min-h-0">
                        <header className="h-12 border-b border-border/40 px-4 flex items-center justify-between shrink-0 bg-background sticky top-0 z-20">
                            <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-md overflow-hidden flex items-center justify-center bg-primary/10">
                                    <img
                                        src={selectedAgent.avatar}
                                        alt={selectedAgent.name}
                                        className="w-full h-full object-cover"
                                    />
                                </div>
                                <span className="text-[14px] font-bold text-foreground">
                                    {selectedAgent.name}
                                </span>
                            </div>
                        </header>

                        <ScrollArea className="h-full">
                            <div className="max-w-4xl mx-auto space-y-10 p-6">
                                <section className="space-y-4">
                                    <div className="flex items-center gap-2 text-foreground">
                                        <Zap
                                            size={14}
                                            className="text-primary"
                                        />
                                        <h3 className="text-xs font-bold">
                                            LLM
                                        </h3>
                                    </div>

                                    <Card className="p-4 bg-muted/10 border-border rounded-xl space-y-6 shadow-none">
                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-2">
                                                <Label className="text-xs font-black text-muted-foreground">
                                                    供应商
                                                </Label>
                                                <Select
                                                    value={
                                                        selectedAgent.provider_id ||
                                                        generalConfig.provider_id
                                                    }
                                                    onValueChange={(val) =>
                                                        setSelectedAgent({
                                                            ...selectedAgent,
                                                            provider_id: val,
                                                        })
                                                    }
                                                >
                                                    <SelectTrigger className="w-full bg-background border-border h-9 text-sm shadow-none">
                                                        <SelectValue placeholder="选择供应商" />
                                                    </SelectTrigger>
                                                    <SelectContent className="border-border">
                                                        {providers.map((p) => (
                                                            <SelectItem
                                                                key={p.id}
                                                                value={p.id}
                                                            >
                                                                {p.name}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="space-y-2">
                                                <Label className="text-xs font-black text-muted-foreground">
                                                    模型
                                                </Label>
                                                <Select
                                                    value={
                                                        selectedAgent.model ||
                                                        generalConfig.model
                                                    }
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
                                                        {(availableModels.length >
                                                        0
                                                            ? availableModels
                                                            : generalAvailableModels
                                                        ).map((m: string) => (
                                                            <SelectItem
                                                                key={m}
                                                                value={m}
                                                            >
                                                                {m}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    </Card>
                                </section>

                                <div className="flex justify-end">
                                    <Button
                                        onClick={handleSave}
                                        disabled={isSaving}
                                        className="text-xs px-6 h-9 font-bold shadow-lg shadow-primary/20"
                                    >
                                        <Save size={14} />
                                        {isSaving ? "保存中..." : "保存"}
                                    </Button>
                                </div>
                            </div>
                        </ScrollArea>
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground/30 font-black uppercase tracking-[0.2em] text-sm">
                        请选择左侧智能体进行配置
                    </div>
                )}
            </main>
        </div>
    );
}
