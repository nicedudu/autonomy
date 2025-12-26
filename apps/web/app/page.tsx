"use client";

import {
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    ChevronsLeft,
    ChevronUp,
    Languages,
    Layout,
    Plus,
    Square,
    User,
    Users,
} from "lucide-react";
import { useEffect, useState } from "react";

// 导入共享全量 shadcn 组件
import { Badge } from "@autonomy/ui/components/badge";
import { Button } from "@autonomy/ui/components/button";
import { Card, CardContent } from "@autonomy/ui/components/card";
import { ModeToggle } from "@autonomy/ui/components/mode-toggle";
import { ScrollArea } from "@autonomy/ui/components/scroll-area";
import { Separator } from "@autonomy/ui/components/separator";
import { Textarea } from "@autonomy/ui/components/textarea";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@autonomy/ui/components/tooltip";

interface Event {
    type: string;
    data: any;
    timestamp: string;
}

export default function DashboardFinalThemeSynced() {
    const [events, setEvents] = useState<Event[]>([]);
    const [inputCommand, setInputCommand] = useState("");
    const [agentList, setAgentList] = useState<any[]>([]);

    useEffect(() => {
        fetch("http://localhost:8000/api/agents")
            .then((res) => res.json())
            .then((data) => setAgentList(data))
            .catch(() => {
                setAgentList([
                    {
                        id: "ceo",
                        name: "Mike",
                        avatar: "🐼",
                        role: "团队领导者",
                    },
                    {
                        id: "cpo",
                        name: "Alice",
                        avatar: "🔍",
                        role: "选品专家",
                    },
                    { id: "scm", name: "Bob", avatar: "📦", role: "供应链官" },
                    { id: "cmo", name: "Carol", avatar: "📢", role: "营销官" },
                ]);
            });

        const ws = new WebSocket("ws://localhost:8000/ws/ops");
        ws.onmessage = (event) => {
            const newEvent = JSON.parse(event.data);
            setEvents((prev) => [...prev.slice(-50), newEvent]);
        };
        return () => ws.close();
    }, []);

    const latestAction = events
        .slice()
        .reverse()
        .find((e) => e.type === "agent_action");

    return (
        <TooltipProvider>
            <div className="flex h-screen bg-background text-foreground font-sans overflow-hidden">
                {/* === Left: Intelligence Stream (Using Sidebar Tokens) === */}
                <aside className="w-[380px] flex flex-col shrink-0 bg-sidebar border-r border-sidebar-border h-full">
                    <header className="h-14 border-b border-sidebar-border flex items-center px-6 bg-sidebar shrink-0">
                        <span className="text-[11px] font-black uppercase tracking-widest text-sidebar-foreground/40">
                            Intelligence Stream
                        </span>
                    </header>

                    <ScrollArea className="flex-1">
                        <div className="px-6 py-8 space-y-8">
                            {/* Core Context */}
                            <div className="flex gap-4">
                                <div className="w-10 h-10 rounded-full bg-primary/10 text-primary shrink-0 flex items-center justify-center text-2xl border border-primary/20 shadow-sm">
                                    🐼
                                </div>
                                <div className="space-y-3 w-full">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-bold text-foreground uppercase tracking-tight">
                                            Mike
                                        </span>
                                        <Badge
                                            variant="outline"
                                            className="text-xs font-black py-0 h-4 border-sidebar-border text-sidebar-foreground/40 rounded-sm uppercase"
                                        >
                                            Leader
                                        </Badge>
                                    </div>

                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="h-7 text-[10px] gap-1.5 px-3 bg-background border-sidebar-border text-sidebar-foreground/60 rounded-full hover:bg-sidebar-accent transition-colors shadow-none"
                                    >
                                        <CheckCircle2
                                            size={12}
                                            className="text-green-500"
                                        />
                                        <span className="font-bold">
                                            Process initialized
                                        </span>
                                        <ChevronDown
                                            size={10}
                                            className="text-sidebar-foreground/30"
                                        />
                                    </Button>

                                    <Card className="border-none bg-background/50 shadow-none rounded-2xl rounded-tl-none ring-1 ring-sidebar-border">
                                        <CardContent className="p-4 text-[14px] text-foreground/80 leading-relaxed">
                                            系统已就绪。你可以通过下方的指令框对整个智能体矩阵下达战略指令。
                                        </CardContent>
                                    </Card>
                                </div>
                            </div>

                            {/* Action Events */}
                            {events.map((event, idx) => (
                                <div
                                    key={idx}
                                    className="flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-500"
                                >
                                    <div className="w-10 h-10 rounded-full bg-primary/10 text-primary shrink-0 flex items-center justify-center text-2xl border border-primary/20">
                                        🤖
                                    </div>
                                    <div className="flex-1 space-y-3 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm font-bold text-foreground capitalize">
                                                {event.data.agent_type ||
                                                    event.type}
                                            </span>
                                            <span className="text-[10px] text-foreground/30 font-medium">
                                                {new Date().toLocaleTimeString(
                                                    [],
                                                    {
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    }
                                                )}
                                            </span>
                                        </div>

                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="h-7 text-[10px] gap-1.5 px-3 bg-background border-sidebar-border text-sidebar-foreground/60 rounded-full shadow-none"
                                        >
                                            <CheckCircle2
                                                size={12}
                                                className="text-primary"
                                            />
                                            <span className="font-bold">
                                                Step executed
                                            </span>
                                            <ChevronDown size={10} />
                                        </Button>

                                        <Card className="border-none bg-background/50 shadow-none rounded-2xl rounded-tl-none ring-1 ring-sidebar-border">
                                            <CardContent className="p-4 text-[14px] text-foreground/80 leading-relaxed whitespace-pre-wrap break-words">
                                                {typeof event.data === "string"
                                                    ? event.data
                                                    : event.data.thought ||
                                                      JSON.stringify(
                                                          event.data
                                                      )}
                                            </CardContent>
                                        </Card>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </ScrollArea>

                    {/* Input Section */}
                    <div className="px-6 pb-8 pt-4 bg-sidebar shrink-0 border-t border-sidebar-border/50">
                        <Card className="border-sidebar-border rounded-3xl p-3 focus-within:ring-2 focus-within:ring-primary/20 transition-all bg-background shadow-sm overflow-hidden ring-1 ring-sidebar-border">
                            <Textarea
                                value={inputCommand}
                                onChange={(e) =>
                                    setInputCommand(e.target.value)
                                }
                                className="w-full border-none shadow-none focus-visible:ring-0 text-[14px] px-2 py-1 min-h-[45px] max-h-[120px] bg-transparent placeholder:text-foreground/20 resize-none font-sans"
                                placeholder="下达公司级战略指令..."
                                rows={1}
                            />
                            <div className="flex items-center justify-between mt-2 pt-2 border-t border-sidebar-border/20">
                                <div className="flex items-center gap-0.5">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-sidebar-foreground/40 hover:bg-sidebar-accent rounded-lg"
                                    >
                                        <Plus size={18} />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-sidebar-foreground/40 hover:bg-sidebar-accent rounded-lg"
                                    >
                                        <Users size={18} />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-sidebar-foreground/40 hover:bg-sidebar-accent rounded-lg"
                                    >
                                        <User size={18} />
                                    </Button>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2 pr-1">
                                        <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                                        <span className="text-[10px] text-sidebar-foreground/40 font-bold uppercase tracking-tighter">
                                            Engine Active
                                        </span>
                                    </div>
                                    <Button
                                        size="icon"
                                        className="h-9 w-9 bg-primary text-primary-foreground hover:opacity-90 active:scale-95 transition-all rounded-xl shadow-lg shadow-primary/20 border-none"
                                    >
                                        <Square size={12} fill="currentColor" />
                                    </Button>
                                </div>
                            </div>
                        </Card>
                    </div>
                </aside>

                {/* === Right Workspace === */}
                <main className="flex-1 flex flex-col min-w-0 bg-background relative p-6 h-full">
                    {/* Main Header */}
                    <header className="h-14 flex items-center justify-between px-4 mb-4 shrink-0">
                        <div className="flex items-center gap-3 text-sm text-foreground/40 font-medium">
                            <span className="hover:text-foreground cursor-pointer transition-colors uppercase text-[11px] font-black tracking-widest">
                                Autonomy
                            </span>
                            <ChevronRight
                                size={14}
                                className="text-foreground/20"
                            />
                            <span className="text-foreground font-black italic tracking-tight text-sm uppercase">
                                Global Operations
                            </span>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2 px-2">
                                <ModeToggle />
                            </div>
                            <Card className="flex items-center bg-card border-border rounded-full px-2 py-1.5 gap-2 shadow-sm h-10">
                                {agentList.map((agent) => (
                                    <Tooltip key={agent.id}>
                                        <TooltipTrigger asChild>
                                            <Button
                                                variant="ghost"
                                                className="w-7 h-7 rounded-full p-0 flex items-center justify-center text-sm hover:scale-110 transition-all border border-transparent hover:border-border"
                                            >
                                                {agent.avatar}
                                            </Button>
                                        </TooltipTrigger>
                                        <TooltipContent
                                            side="bottom"
                                            className="bg-popover text-popover-foreground border-border text-[11px] py-2 px-3 font-bold rounded-xl shadow-2xl"
                                        >
                                            <div className="flex items-center gap-2">
                                                <span>{agent.name}</span>
                                                <Badge
                                                    variant="secondary"
                                                    className="bg-primary/10 text-primary border-none h-4 px-1 text-xs font-black uppercase"
                                                >
                                                    Role: {agent.role}
                                                </Badge>
                                            </div>
                                        </TooltipContent>
                                    </Tooltip>
                                ))}
                            </Card>
                            <Button className="h-10 text-[11px] font-black px-6 rounded-full uppercase tracking-widest bg-primary text-primary-foreground hover:opacity-90 transition-all shadow-lg shadow-primary/10 border-none">
                                Share
                            </Button>
                        </div>
                    </header>

                    {/* Follow Screen Canvas */}
                    <div className="flex-1 bg-card rounded-[2.5rem] border-[2.5px] border-primary relative overflow-hidden flex flex-col shadow-2xl shadow-primary/5 group min-h-0">
                        {/* Tag */}
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-[10px] font-black px-6 py-2 rounded-b-3xl z-30 flex items-center gap-3 shadow-lg transform group-hover:translate-y-0.5 transition-transform">
                            <div className="w-1.5 h-1.5 rounded-full bg-primary-foreground animate-pulse"></div>
                            <span className="tracking-tight uppercase">
                                跟随智能体的屏幕
                            </span>
                            <Separator
                                orientation="vertical"
                                className="h-3 bg-primary-foreground/20"
                            />
                            <span className="bg-primary-foreground/20 px-2 py-0.5 rounded-lg hover:bg-primary-foreground/40 cursor-pointer transition-colors text-xs">
                                EXIT
                            </span>
                        </div>

                        {/* Content Area */}
                        <ScrollArea className="flex-1 bg-card">
                            <div className="p-16">
                                {latestAction ? (
                                    <div className="max-w-4xl mx-auto animate-in fade-in zoom-in-95 duration-700">
                                        <Card className="border-border rounded-[3rem] p-12 shadow-none bg-background/50 border-b-[10px] border-b-border/50">
                                            <CardContent className="p-0">
                                                <div className="flex items-center gap-8 mb-12">
                                                    <div className="w-24 h-24 bg-primary/5 rounded-[3.5rem] flex items-center justify-center text-5xl border border-primary/10 shadow-inner">
                                                        {latestAction.data
                                                            .agent_type ===
                                                        "cpo"
                                                            ? "🔍"
                                                            : "🤖"}
                                                    </div>
                                                    <div className="space-y-1">
                                                        <h2 className="text-4xl font-black text-foreground tracking-tighter uppercase italic leading-none">
                                                            {latestAction.data
                                                                .agent_type ||
                                                                "Agent"}
                                                        </h2>
                                                        <p className="text-primary font-bold tracking-widest text-sm uppercase mt-1">
                                                            is executing
                                                            mission...
                                                        </p>
                                                        <div className="flex items-center gap-3 mt-4">
                                                            <Badge className="px-3 py-1 bg-foreground text-background text-[10px] font-black rounded-full tracking-widest uppercase">
                                                                NODE ACTIVE
                                                            </Badge>
                                                            <span className="text-[11px] text-foreground/40 font-mono opacity-60">
                                                                ID: #0xAF22-2025
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <Card className="bg-secondary/50 border-border rounded-[2rem] p-10 shadow-inner relative overflow-hidden ring-1 ring-border">
                                                    <div className="flex gap-2 text-primary/40 mb-6 font-black italic text-[11px] tracking-[0.2em]">
                                                        <span>{">"}</span>
                                                        <span>
                                                            CORE_NEURAL_LINK_ACTIVE
                                                        </span>
                                                    </div>
                                                    <div className="relative z-10 break-words text-foreground font-mono text-[15px] leading-relaxed opacity-95">
                                                        {typeof latestAction.data ===
                                                        "string"
                                                            ? latestAction.data
                                                            : latestAction.data
                                                                  .thought ||
                                                              JSON.stringify(
                                                                  latestAction.data,
                                                                  null,
                                                                  2
                                                              )}
                                                        <span className="inline-block w-3 h-6 bg-primary/80 ml-3 animate-pulse align-middle"></span>
                                                    </div>
                                                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[100px] rounded-full pointer-events-none"></div>
                                                </Card>
                                            </CardContent>
                                        </Card>
                                    </div>
                                ) : (
                                    <div className="h-[60vh] flex flex-col items-center justify-center text-foreground/10">
                                        <div className="w-32 h-32 bg-card rounded-[3.5rem] flex items-center justify-center border border-border relative shadow-inner">
                                            <Languages
                                                size={48}
                                                className="opacity-50"
                                            />
                                            <div className="absolute inset-0 border-[2px] border-dashed border-border rounded-[3.5rem] animate-[spin_40s_linear_infinite]"></div>
                                        </div>
                                        <span className="mt-8 text-[11px] font-black text-foreground/30 uppercase tracking-[0.5em] ml-2">
                                            Awaiting Neural Link
                                        </span>
                                    </div>
                                )}
                            </div>
                        </ScrollArea>

                        {/* App Switcher */}
                        <Card className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-popover/90 backdrop-blur-md border border-border rounded-full px-6 py-3 flex items-center gap-5 z-40 shadow-2xl">
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-muted-foreground hover:text-foreground"
                            >
                                <ChevronsLeft size={20} />
                            </Button>
                            <Separator
                                orientation="vertical"
                                className="h-6 bg-border"
                            />
                            <Button
                                variant="ghost"
                                className="flex items-center gap-3 px-4 py-2 rounded-full transition-all group hover:bg-accent"
                            >
                                <Layout
                                    size={18}
                                    className="text-muted-foreground group-hover:text-primary transition-colors"
                                />
                                <span className="text-sm font-black text-foreground tracking-tight group-hover:text-primary transition-colors uppercase">
                                    应用查看器
                                </span>
                                <ChevronUp
                                    size={16}
                                    className="text-muted-foreground"
                                />
                            </Button>
                        </Card>
                    </div>
                </main>
            </div>
        </TooltipProvider>
    );
}
