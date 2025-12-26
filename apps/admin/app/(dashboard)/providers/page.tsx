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
    Box,
    ChevronDown,
    ChevronRight,
    Globe2,
    Key,
    Plus,
    Save,
    Search,
    Trash2,
    Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

export default function ProviderManagement() {
    const [providers, setProviders] = useState<any[]>([]);
    const [selectedProvider, setSelectedProvider] = useState<any>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    const [expandedModelIndex, setExpandedModelIndex] = useState<number | null>(
        null
    );

    const fetchProviders = async () => {
        setLoading(true);
        const { data } = await supabase
            .from("llm_providers")
            .select("*")
            .order("name");
        if (data) setProviders(data);
        if (data && data.length > 0 && !selectedProvider)
            setSelectedProvider(data[0]);
        setLoading(false);
    };

    useEffect(() => {
        fetchProviders();
    }, []);

    const getVendorName = (url: string) => {
        try {
            if (!url) return "未知厂商";
            const hostname = new URL(url).hostname;
            const parts = hostname.split(".");
            if (parts.length >= 2) {
                return parts[parts.length - 2];
            }
            return hostname;
        } catch (e) {
            return url;
        }
    };

    const filteredProviders = providers.filter((p) => {
        const vendorName = getVendorName(p.api_base);
        return (
            p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            vendorName.toLowerCase().includes(searchQuery.toLowerCase())
        );
    });

    const handleSave = async () => {
        setIsSaving(true);
        const { error } = await supabase.from("llm_providers").upsert({
            id: selectedProvider.id,
            name: selectedProvider.name,
            api_base: selectedProvider.api_base,
            api_token: selectedProvider.api_token,
            type: selectedProvider.type || "openai",
            supported_models: selectedProvider.supported_models || [],
        });

        if (!error) {
            alert("配置已保存");
            fetchProviders();
        } else {
            alert("保存失败: " + error.message);
        }
        setIsSaving(false);
    };

    const handleAddModel = () => {
        const newModels = [
            "新模型",
            ...(selectedProvider.supported_models || []),
        ];
        setSelectedProvider({
            ...selectedProvider,
            supported_models: newModels,
        });
        setExpandedModelIndex(0);
    };

    const handleUpdateModel = (index: number, value: string) => {
        const newModels = [...(selectedProvider.supported_models || [])];
        newModels[index] = value;
        setSelectedProvider({
            ...selectedProvider,
            supported_models: newModels,
        });
    };

    const handleDeleteModel = (index: number) => {
        const newModels = [...(selectedProvider.supported_models || [])];
        newModels.splice(index, 1);
        setSelectedProvider({
            ...selectedProvider,
            supported_models: newModels,
        });
        setExpandedModelIndex(null);
    };

    const handleDeleteProvider = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (!confirm("确定要删除此供应商吗？")) return;

        const { error } = await supabase
            .from("llm_providers")
            .delete()
            .eq("id", id);
        if (error) {
            alert("删除失败: " + error.message);
        } else {
            if (selectedProvider?.id === id) setSelectedProvider(null);
            fetchProviders();
        }
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
                            placeholder="搜索厂商..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-8 h-8 text-xs! bg-background/50 border-border"
                        />
                    </div>
                    <Button
                        size="icon"
                        variant="default"
                        onClick={() =>
                            setSelectedProvider({
                                name: "新建厂商",
                                api_base: "https://api.example.com/v1",
                                api_token: "",
                                type: "openai",
                                supported_models: [],
                            })
                        }
                        className="w-7 h-7 rounded-full shrink-0 shadow-sm"
                    >
                        <Plus size={12} />
                    </Button>
                </div>

                <ScrollArea className="flex-1">
                    <nav className="p-3 space-y-1">
                        {filteredProviders.map((p) => {
                            const vendorName = getVendorName(p.api_base);
                            return (
                                <div
                                    key={p.id}
                                    onClick={() => setSelectedProvider(p)}
                                    className={`w-full flex items-center justify-start py-2.5 px-4 rounded-xl gap-4 cursor-pointer transition-all group ${
                                        selectedProvider?.id === p.id
                                            ? "bg-primary/10 text-primary font-bold border border-primary/20"
                                            : "text-foreground/50 hover:bg-foreground/5 border border-transparent"
                                    }`}
                                >
                                    <div
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center text-white font-black text-xs shrink-0 uppercase ${
                                            vendorName.includes("anthropic")
                                                ? "bg-orange-500"
                                                : vendorName.includes("openai")
                                                ? "bg-green-600"
                                                : "bg-blue-500"
                                        }`}
                                    >
                                        {vendorName.charAt(0)}
                                    </div>
                                    <div className="truncate flex-1">
                                        <div
                                            className={`text-sm truncate leading-tight capitalize ${
                                                selectedProvider?.id === p.id
                                                    ? "text-primary"
                                                    : "text-foreground"
                                            }`}
                                        >
                                            {vendorName}
                                        </div>
                                        <div className="text-xs text-muted-foreground font-mono truncate">
                                            {p.name}
                                        </div>
                                    </div>
                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={(e) =>
                                            handleDeleteProvider(e, p.id)
                                        }
                                        className="ml-auto opacity-0 group-hover:opacity-100 w-7 h-7 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-all shrink-0"
                                    >
                                        <Trash2 size={12} />
                                    </Button>
                                </div>
                            );
                        })}
                    </nav>
                </ScrollArea>
            </aside>

            {/* === Right: Content === */}
            <main className="flex-1 flex flex-col min-w-0 bg-background overflow-hidden relative">
                {selectedProvider ? (
                    <>
                        <header className="h-12 border-b border-border px-4 flex items-center justify-between shrink-0 bg-background sticky top-0 z-20">
                            <div className="flex items-center gap-2">
                                <Box size={16} className="text-primary" />
                                <span className="text-[14px] font-bold text-foreground capitalize">
                                    {getVendorName(selectedProvider.api_base)}{" "}
                                    配置
                                </span>
                            </div>
                        </header>

                        <ScrollArea className="flex-1 bg-background p-6">
                            <div className="max-w-4xl mx-auto space-y-10 pb-12">
                                {/* 1. Base Config */}
                                <section className="space-y-4">
                                    <div className="flex items-center gap-2 text-foreground">
                                        <Zap
                                            size={14}
                                            className="text-primary"
                                        />
                                        <h3 className="text-xs font-bold uppercase tracking-wider">
                                            基础连接配置
                                        </h3>
                                    </div>

                                    <Card className="p-6 bg-muted/5 border-border rounded-xl space-y-6 shadow-none">
                                        <div className="grid grid-cols-12 gap-6">
                                            <div className="space-y-2 col-span-6">
                                                <Label className="text-xs font-black text-muted-foreground uppercase tracking-widest">
                                                    厂商名称
                                                </Label>
                                                <Input
                                                    value={
                                                        selectedProvider.name
                                                    }
                                                    onChange={(e) =>
                                                        setSelectedProvider({
                                                            ...selectedProvider,
                                                            name: e.target
                                                                .value,
                                                        })
                                                    }
                                                    className="bg-background text-sm h-9"
                                                    placeholder="如: OpenAI, DeepSeek"
                                                />
                                            </div>
                                            <div className="space-y-2 col-span-6">
                                                <Label className="text-xs font-black text-muted-foreground uppercase tracking-widest">
                                                    协议标准
                                                </Label>
                                                <Select
                                                    value={
                                                        selectedProvider.type
                                                    }
                                                    onValueChange={(val) =>
                                                        setSelectedProvider({
                                                            ...selectedProvider,
                                                            type: val,
                                                        })
                                                    }
                                                >
                                                    <SelectTrigger className="bg-background text-sm border-border h-9 w-full">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent className="border-border">
                                                        <SelectItem value="openai">
                                                            OpenAI
                                                        </SelectItem>
                                                        <SelectItem value="anthropic">
                                                            Anthropic
                                                        </SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="space-y-2 col-span-12">
                                                <Label className="text-xs font-black text-muted-foreground uppercase tracking-widest flex items-center gap-1.5">
                                                    <Globe2 size={10} />{" "}
                                                    接口地址 (Base URL)
                                                </Label>
                                                <Input
                                                    value={
                                                        selectedProvider.api_base
                                                    }
                                                    onChange={(e) =>
                                                        setSelectedProvider({
                                                            ...selectedProvider,
                                                            api_base:
                                                                e.target.value,
                                                        })
                                                    }
                                                    placeholder="https://api.openai.com/v1"
                                                    className="bg-background text-sm font-mono h-9"
                                                />
                                            </div>
                                            <div className="space-y-2 col-span-12">
                                                <Label className="text-xs font-black text-muted-foreground uppercase tracking-widest flex items-center gap-1.5">
                                                    <Key size={10} /> 全局 API
                                                    密钥 (Token)
                                                </Label>
                                                <Input
                                                    type="password"
                                                    value={
                                                        selectedProvider.api_token
                                                    }
                                                    onChange={(e) =>
                                                        setSelectedProvider({
                                                            ...selectedProvider,
                                                            api_token:
                                                                e.target.value,
                                                        })
                                                    }
                                                    placeholder="sk-..."
                                                    className="bg-background text-sm font-mono h-9"
                                                />
                                            </div>
                                        </div>
                                        <div className="flex justify-end">
                                            <Button
                                                onClick={handleSave}
                                                disabled={isSaving}
                                                className="text-[11px] font-bold h-8 px-6"
                                            >
                                                <Save size={12} />
                                                {isSaving
                                                    ? "保存中..."
                                                    : "保存"}
                                            </Button>
                                        </div>
                                    </Card>
                                </section>

                                {/* 2. Model List Section */}
                                <section className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 text-foreground">
                                            <Box
                                                size={14}
                                                className="text-primary"
                                            />
                                            <h3 className="text-xs font-bold uppercase tracking-wider">
                                                模型列表
                                            </h3>
                                        </div>
                                        <Button
                                            variant="link"
                                            size="sm"
                                            onClick={handleAddModel}
                                            className="text-xs h-7 font-bold no-underline! cursor-pointer"
                                        >
                                            <Plus size={12} />
                                            添加模型
                                        </Button>
                                    </div>

                                    <div className="space-y-4">
                                        {(
                                            selectedProvider.supported_models ||
                                            []
                                        ).length === 0 && (
                                            <div className="text-center py-10 border border-dashed border-border rounded-xl text-muted-foreground text-[11px] bg-muted/5">
                                                暂无模型，请点击右上角添加
                                            </div>
                                        )}

                                        {(
                                            selectedProvider.supported_models ||
                                            []
                                        ).map((model: string, idx: number) => (
                                            <Card
                                                key={idx}
                                                className={`p-6 transition-all border-border shadow-none overflow-hidden ${
                                                    expandedModelIndex === idx
                                                        ? "ring-1 ring-primary/50 bg-primary/5"
                                                        : "hover:border-primary/30"
                                                }`}
                                            >
                                                <div
                                                    onClick={() =>
                                                        setExpandedModelIndex(
                                                            expandedModelIndex ===
                                                                idx
                                                                ? null
                                                                : idx
                                                        )
                                                    }
                                                    className="flex items-center justify-between cursor-pointer select-none"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div
                                                            className={`p-1.5 rounded-md ${
                                                                expandedModelIndex ===
                                                                idx
                                                                    ? "bg-primary text-primary-foreground"
                                                                    : "bg-muted text-muted-foreground"
                                                            }`}
                                                        >
                                                            {expandedModelIndex ===
                                                            idx ? (
                                                                <ChevronDown
                                                                    size={12}
                                                                />
                                                            ) : (
                                                                <ChevronRight
                                                                    size={12}
                                                                />
                                                            )}
                                                        </div>
                                                        <span className="text-sm font-medium font-mono">
                                                            {model}
                                                        </span>
                                                    </div>
                                                    <span className="text-[10px] text-muted-foreground font-mono opacity-50">
                                                        MODEL ID
                                                    </span>
                                                </div>

                                                {expandedModelIndex === idx && (
                                                    <div className="border-t border-border pt-4 space-y-4 animate-in fade-in slide-in-from-top-1 duration-200">
                                                        <div className="space-y-2">
                                                            <Label className="text-[10px] font-bold text-muted-foreground uppercase">
                                                                模型标识 (Model
                                                                ID)
                                                            </Label>
                                                            <Input
                                                                value={model}
                                                                onChange={(e) =>
                                                                    handleUpdateModel(
                                                                        idx,
                                                                        e.target
                                                                            .value
                                                                    )
                                                                }
                                                                className="text-sm font-mono h-9 bg-background"
                                                                placeholder="例如: gpt-4o"
                                                            />
                                                            <p className="text-[10px] text-muted-foreground">
                                                                此 ID 将直接用于
                                                                API
                                                                调用，请确保与供应商文档一致。
                                                            </p>
                                                        </div>
                                                        <div className="flex justify-end gap-2">
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={(
                                                                    e
                                                                ) => {
                                                                    e.stopPropagation();
                                                                    handleDeleteModel(
                                                                        idx
                                                                    );
                                                                }}
                                                                className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 text-[11px] h-8"
                                                            >
                                                                <Trash2
                                                                    size={12}
                                                                    className="mr-1"
                                                                />{" "}
                                                                删除
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                onClick={(
                                                                    e
                                                                ) => {
                                                                    e.stopPropagation();
                                                                    handleSave();
                                                                }}
                                                                className="text-[11px] h-8"
                                                            >
                                                                <Save
                                                                    size={12}
                                                                    className="mr-1"
                                                                />{" "}
                                                                保存
                                                            </Button>
                                                        </div>
                                                    </div>
                                                )}
                                            </Card>
                                        ))}
                                    </div>
                                </section>
                            </div>
                        </ScrollArea>
                    </>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground/30 font-black uppercase tracking-[0.2em] text-sm">
                        请选择左侧厂商进行配置
                    </div>
                )}
            </main>
        </div>
    );
}
