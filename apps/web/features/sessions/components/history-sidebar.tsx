"use client";

import { Button } from "@autonomy/ui/components/button";
import { ModeToggle } from "@autonomy/ui/components/mode-toggle";
import { ScrollArea } from "@autonomy/ui/components/scroll-area";
import { MessageSquare, PanelLeft, Plus, Trash2 } from "lucide-react";

interface Session {
    id: string;
    title: string;
    created_at: string;
}

interface HistorySidebarProps {
    isSidebarOpen: boolean;
    setIsSidebarOpen: (open: boolean) => void;
    sessions: Session[];
    currentSessionId: string | null;
    onNewChat: () => void;
    onSelectSession: (session: Session) => void;
    onDeleteSession: (sessionId: string) => void;
}

export function HistorySidebar({
    isSidebarOpen,
    setIsSidebarOpen,
    sessions,
    currentSessionId,
    onNewChat,
    onSelectSession,
    onDeleteSession,
}: HistorySidebarProps) {
    return (
        <aside
            className={`flex flex-col z-50 shrink-0 transition-all duration-300 ease-in-out bg-sidebar relative overflow-hidden ${
                isSidebarOpen
                    ? "w-[240px] border-r border-sidebar-border/40"
                    : "w-0"
            }`}
        >
            <div className="w-[240px] flex flex-col h-full">
                <header className="h-12 flex items-center justify-between px-4 shrink-0">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-black text-xl">
                            A
                        </div>
                        <span className="font-black text-sm">Autonomy</span>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setIsSidebarOpen(false)}
                        className="h-8 w-8"
                    >
                        <PanelLeft size={16} />
                    </Button>
                </header>
                <div className="p-4 flex-1 flex flex-col overflow-hidden">
                    <Button
                        onClick={onNewChat}
                        className="w-full justify-start gap-3 bg-primary/10 text-primary rounded-xl h-11 text-xs font-bold transition-all hover:text-background dark:hover:text-foreground"
                    >
                        <Plus size={18} />
                        开启新会话
                    </Button>
                    <ScrollArea className="flex-1 mt-4 w-full">
                        <div className="space-y-1.5 w-full">
                            <div className="px-4 py-2 text-[10px] font-black text-sidebar-foreground/30 uppercase tracking-[0.2em] mb-1">
                                最近会话
                            </div>

                            {sessions.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-[240px] text-muted-foreground/20 select-none">
                                    <MessageSquare
                                        size={48}
                                        strokeWidth={1}
                                        className="mb-3"
                                    />
                                    <p className="text-xs font-medium tracking-widest">
                                        暂无会话
                                    </p>
                                </div>
                            ) : (
                                sessions.map((session) => (
                                    <div
                                        key={session.id}
                                        className="group relative flex items-center w-full"
                                    >
                                        <button
                                            onClick={() =>
                                                onSelectSession(session)
                                            }
                                            className={`w-full text-left p-3.5 rounded-xl flex items-center gap-3 transition-all ${
                                                currentSessionId === session.id
                                                    ? "bg-primary/10 text-primary"
                                                    : "text-muted-foreground/60 hover:bg-muted/50"
                                            }`}
                                        >
                                            <MessageSquare
                                                size={14}
                                                className="shrink-0"
                                            />
                                            <div className="truncate flex-1 text-xs font-semibold w-0 ellipsis">
                                                {session.title}
                                            </div>
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onDeleteSession(session.id);
                                            }}
                                            className="absolute right-2 p-1.5 rounded-md text-muted-foreground/40 hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100 transition-all bg-sidebar/40 backdrop-blur-sm"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </ScrollArea>
                </div>

                {/* Sidebar Footer */}
                <div className="p-4 border-t border-sidebar-border/40 bg-sidebar/50">
                    <div className="flex items-center justify-end px-3">
                        <ModeToggle />
                    </div>
                </div>
            </div>
        </aside>
    );
}
