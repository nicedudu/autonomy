"use client";

import { Badge } from "@autonomy/ui/components/badge";
import { AtSign, Lightbulb, Terminal } from "lucide-react";
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ChartData = {
    chartType?: string;
    title?: string;
    data?: unknown[];
};

// --- Data Visualization Renderer ---
export const ChartRenderer = ({ data }: { data: ChartData }) => {
    return (
        <div className="my-6 bg-card border border-border/60 rounded-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-500">
            <div className="bg-muted/30 px-4 py-3 border-b border-border/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-foreground/70">
                        {data.chartType || "数据可视化"}
                    </span>
                </div>
                <Badge
                    variant="outline"
                    className="text-[9px] font-mono opacity-50 uppercase"
                >
                    Live Data
                </Badge>
            </div>
            <div className="p-6 flex flex-col items-center justify-center min-h-[200px] bg-linear-to-b from-transparent to-primary/5">
                <div className="text-center space-y-2">
                    <p className="text-xs font-bold text-foreground/80">
                        {data.title || "正在渲染图表结构..."}
                    </p>
                    <div className="flex gap-1 justify-center items-end h-12">
                        {[40, 70, 45, 90, 65].map((h, i) => (
                            <div
                                key={i}
                                className="w-2 bg-primary/20 rounded-t-sm animate-in slide-in-from-bottom duration-1000"
                                style={{
                                    height: `${h}%`,
                                    transitionDelay: `${i * 100}ms`,
                                }}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export const MarkdownComponents = (compact?: boolean): Components => ({
    p: ({ children }) => (
        <p className={`${compact ? "mb-0" : "mb-3 last:mb-0"} leading-relaxed break-all whitespace-pre-wrap min-w-0`}>
            {children}
        </p>
    ),
    h1: ({ children }) => (
        <h1 className="text-xl font-black mb-4 mt-6 text-foreground tracking-tight">
            {children}
        </h1>
    ),
    h2: ({ children }) => (
        <h2 className="text-lg font-bold mb-3 mt-5 text-foreground/90 tracking-tight">
            {children}
        </h2>
    ),
    h3: ({ children }) => (
        <h3 className="text-base font-bold mb-2 mt-4 text-foreground/80">
            {children}
        </h3>
    ),
    li: ({ children }) => (
        <li className="mb-1.5 min-w-0 break-all leading-relaxed">{children}</li>
    ),
    ul: ({ children }) => (
        <ul className="mb-4 space-y-1 list-disc pl-5 marker:text-primary/40">
            {children}
        </ul>
    ),
    ol: ({ children }) => (
        <ol className="list-decimal pl-5 mb-4 space-y-1.5 marker:text-primary/50 marker:font-mono marker:text-xs">
            {children}
        </ol>
    ),
    blockquote: ({ children }) => (
        <blockquote className="flex flex-wrap gap-2 bg-linear-to-r from-primary/5 to-transparent p-3 my-4 rounded-xl border border-primary/10 items-center not-prose [&_p]:inline [&_p]:m-0 [&_code]:bg-transparent [&_code]:border-primary/30 [&_code]:text-[0.9em] [&_code]:shadow-none [&_code]:py-0 [&_code]:h-[1.4em] [&_.relative]:inline-block [&_.relative]:my-0 [&_pre]:bg-transparent [&_pre]:border-primary/30 [&_pre]:text-primary [&_pre]:p-1 [&_pre]:px-1.5 [&_pre]:leading-none">
            <div className="p-1 bg-primary/10 text-primary rounded-lg shrink-0">
                <Lightbulb size={14} />
            </div>
            <div className="text-foreground/80 text-sm font-medium italic leading-relaxed">
                {children}
            </div>
        </blockquote>
    ),
    code: (props) => {
        const { className, children, inline } = props as {
            className?: string;
            children?: React.ReactNode;
            inline?: boolean;
        };
        const match = /language-(\w+)/.exec(className || "");
        const isJson = match && match[1] === "json";
        const codeContent = String(children).replace(/\n$/, "");
        const isMultiLine = codeContent.includes("\n");

        if (!inline && isJson) {
            try {
                if (codeContent.includes("chartType") && codeContent.includes("data")) {
                    const data = JSON.parse(codeContent) as ChartData;
                    if (data.chartType && data.data)
                        return <ChartRenderer data={data} />;
                }
            } catch {
                // Ignore parsing errors
            }
        }

        if (inline) {
            return (
                <code className={`${compact ? "text-[10px] bg-transparent border-primary/30 px-1" : "bg-primary/10 border-primary/20 px-1.5"} text-primary border rounded-md font-mono font-black inline-flex items-center align-baseline leading-none mx-0.5 h-[1.5em] shadow-[0_1px_0_rgba(0,0,0,0.05)]`}>
                    {children}
                </code>
            );
        }

        // For block code in compact mode that is actually just a single line/identifier
        if (compact && !isMultiLine) {
            return (
                <code className="text-[10px] text-primary border border-primary/30 px-1.5 py-0 rounded-md font-mono font-black inline-flex items-center align-baseline leading-none mx-0.5 h-[1.5em] bg-transparent shadow-[0_1px_0_rgba(0,0,0,0.05)]">
                    {children}
                </code>
            );
        }

        return (
            <div className={`${compact ? "inline-block align-middle my-1" : "my-4 block"} relative group max-w-full`}>
                <pre className={`${compact ? "p-1.5 px-2.5 rounded-md leading-none bg-zinc-900 text-zinc-300 border-zinc-800" : "p-4 rounded-xl leading-relaxed bg-muted/50 border-border/40"} border overflow-x-auto font-mono text-xs scrollbar-thin flex items-center gap-2`}>
                    {compact && <Terminal size={10} className="text-zinc-500 shrink-0" />}
                    <code className={className}>{children}</code>
                </pre>
                {!compact && match && (
                    <div className="absolute top-2 right-3 text-[10px] font-black uppercase text-muted-foreground/40 pointer-events-none">
                        {match[1]}
                    </div>
                )}
            </div>
        );
    },
    table: ({ children }) => (
        <div className="my-6 w-full overflow-hidden rounded-xl border border-border/40 bg-muted/5 not-prose">
            <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                    {children}
                </table>
            </div>
        </div>
    ),
    thead: ({ children }) => (
        <thead className="bg-muted/50 text-muted-foreground font-bold uppercase tracking-wider border-b border-border/40">
            {children}
        </thead>
    ),
    th: ({ children }) => (
        <th className="px-4 py-3 whitespace-nowrap">{children}</th>
    ),
    tbody: ({ children }) => (
        <tbody className="divide-y divide-border/10">{children}</tbody>
    ),
    tr: ({ children }) => (
        <tr className="group transition-colors hover:bg-primary/5">
            {children}
        </tr>
    ),
    td: ({ children }) => (
        <td className="px-4 py-3 text-foreground/80 border-none group-first:font-bold group-first:text-foreground">
            {children}
        </td>
    ),
    a: ({ children, href }) => (
        <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline underline-offset-4 font-bold decoration-primary/30"
        >
            {children}
        </a>
    ),
    strong: ({ children }) => {
        const content = String(children);
        if (content.startsWith("@")) {
            return (
                <span className="inline-flex items-center gap-1 text-primary font-bold mx-0.5">
                    <AtSign size={10} strokeWidth={3} />
                    {content.substring(1)}
                </span>
            );
        }
        return (
            <strong className="font-bold text-foreground antialiased">
                {children}
            </strong>
        );
    },
    hr: () => <hr className="my-6 border-border/20" />,
});

export function MarkdownRenderer({ content, compact }: { content: string; compact?: boolean }) {
    return (
        <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={MarkdownComponents(compact)}
        >
            {content}
        </ReactMarkdown>
    );
}
