"use client";

import { ModeToggle } from "@autonomy/ui/components/mode-toggle";
import { Globe2, Settings, Users } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();

    const menuItems = [
        { name: "智能体", href: "/agents", icon: Users },
        { name: "模型配置", href: "/providers", icon: Globe2 },
    ];

    return (
        <div className="flex h-screen bg-background text-foreground font-sans overflow-hidden selection:bg-primary/30 relative">
            {/* Background Decor */}
            <div
                className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05] pointer-events-none"
                style={{
                    backgroundImage:
                        "radial-gradient(circle, currentColor 1px, transparent 1px)",
                    backgroundSize: "32px 32px",
                }}
            ></div>

            {/* Primary Sidebar */}
            <aside className="w-[220px] flex flex-col bg-sidebar border-r border-sidebar-border/40 shrink-0 relative z-50">
                <div className="p-4 pt-6 flex-1 overflow-y-auto scrollbar-hide">
                    <div className="flex items-center gap-2 mb-8 px-4">
                        <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-black text-xl">
                            A
                        </div>
                        <span className="font-black tracking-tighter text-foreground text-sm">
                            Autonomy
                        </span>
                    </div>

                    <nav className="space-y-1.5">
                        {menuItems.map((item) => {
                            const isActive =
                                pathname === item.href ||
                                pathname.startsWith(item.href + "/");
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`flex items-center justify-between text-xs px-4 py-4 rounded-xl font-semibold transition-all ${
                                        isActive
                                            ? "bg-primary/10 text-primary ring-1 ring-primary/20 "
                                            : "text-sidebar-foreground/50 hover:bg-sidebar-accent hover:text-foreground"
                                    }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <item.icon
                                            size={16}
                                            className={
                                                isActive
                                                    ? "text-primary"
                                                    : "text-sidebar-foreground/30"
                                            }
                                        />
                                        {item.name}
                                    </div>
                                </Link>
                            );
                        })}
                    </nav>
                </div>

                {/* Footer Area */}
                <div className="p-4 flex flex-col gap-1 border-t border-sidebar-border/50 bg-sidebar relative z-60">
                    <div className="flex items-center justify-end px-3 h-10 mb-1 relative">
                        <div className="relative z-70">
                            <ModeToggle />
                        </div>
                    </div>
                    <button className="flex items-center gap-3 px-4 py-2.5 w-full text-sm text-sidebar-foreground/40 hover:text-foreground rounded-xl hover:bg-sidebar-accent font-semibold transition-all group">
                        <Settings
                            size={16}
                            className="group-hover:rotate-90 transition-transform duration-500"
                        />
                        系统配置
                    </button>
                </div>
            </aside>

            <main className="flex-1 overflow-hidden relative z-0">
                {children}
            </main>
        </div>
    );
}
