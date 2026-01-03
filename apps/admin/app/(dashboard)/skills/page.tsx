"use client";

import { Card } from "@autonomy/ui/components/card";
import { ScrollArea } from "@autonomy/ui/components/scroll-area";
import { Badge } from "@autonomy/ui/components/badge";
import { Box, Code2, Terminal, Hammer } from "lucide-react";
import { useEffect, useState } from "react";

export default function AdminSkills() {
    const [skills, setSkills] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSkills = async () => {
            try {
                const res = await fetch("http://localhost:8000/api/skills");
                const data = await res.json();
                setSkills(data);
            } catch (err) {
                console.error("Fetch skills error:", err);
            }
            setLoading(false);
        };
        fetchSkills();
    }, []);

    return (
        <div className="h-full flex flex-col bg-background font-sans overflow-hidden">
            <header className="h-12 border-b border-border/40 px-6 flex items-center justify-between shrink-0 bg-background/50 backdrop-blur-md sticky top-0 z-20">
                <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center text-primary shadow-sm">
                        <Hammer size={16} />
                    </div>
                    <h1 className="text-sm font-bold tracking-tight text-foreground uppercase tracking-widest">
                        技能注册中心 (Skill Registry)
                    </h1>
                </div>
                <Badge variant="outline" className="text-[10px] font-mono opacity-50 uppercase tracking-[0.2em] border-border">
                    {skills.length} Loaded
                </Badge>
            </header>

            <ScrollArea className="flex-1 p-8 bg-muted/5">
                <div className="max-w-6xl mx-auto space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {skills.map((skill) => (
                            <Card key={skill.id} className="p-6 bg-card border-border/60 hover:border-primary/40 transition-all group relative overflow-hidden shadow-none rounded-2xl animate-in fade-in slide-in-from-bottom-2 duration-500">
                                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                    <Code2 size={64} />
                                </div>
                                
                                <div className="space-y-4 relative z-10">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                                            <Terminal size={20} />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-foreground text-sm tracking-tight group-hover:text-primary transition-colors">
                                                {skill.name}
                                            </h3>
                                            <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest mt-0.5">
                                                ID: {skill.id}
                                            </p>
                                        </div>
                                    </div>

                                    <p className="text-xs text-muted-foreground/80 leading-relaxed font-medium line-clamp-3 min-h-[3em]">
                                        {skill.description}
                                    </p>

                                    <div className="pt-2 flex flex-wrap gap-2">
                                        {Object.keys(skill.parameters || {}).map(param => (
                                            <Badge key={param} variant="secondary" className="text-[9px] font-mono px-2 py-0 h-5 bg-muted/50 border-none text-muted-foreground">
                                                {param}
                                            </Badge>
                                        ))}
                                    </div>

                                    <div className="pt-4 border-t border-border/40 flex items-center justify-between">
                                        <div className="flex items-center gap-2 text-primary/60">
                                            <Box size={12} />
                                            <span className="text-[10px] font-bold uppercase tracking-tighter">
                                                Implementation
                                            </span>
                                        </div>
                                        <span className="text-[10px] font-mono text-muted-foreground/40 italic">
                                            {skill.implementation}
                                        </span>
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                </div>
            </ScrollArea>
        </div>
    );
}
