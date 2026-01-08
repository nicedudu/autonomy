export interface PlanStep {
  step: string;
  state: "no_started" | "in_progress" | "completed" | "blocked";
}

export interface Call {
  id: string;
  agent_id: string;
  instruction: string;
  mode?: "parallel" | "sync";
  artifact_refs?: string[];
}

export interface ParsedProtocol {
  thought: string | null;
  plan: PlanStep[] | null;
  calls: Call[] | null;
  content: string;
}

function extractJson(text: string): any {
  try {
    // Remove markdown code blocks if present
    let clean = text.replace(/```json/gi, "").replace(/```/g, "");
    
    // Remove standalone "json" text that might appear without backticks
    if (clean.trim().toLowerCase().startsWith("json")) {
        clean = clean.replace(/^\s*json/i, "");
    }
    
    return JSON.parse(clean.trim());
  } catch (e) {
    return null;
  }
}

export function parseMixedProtocol(text: string): ParsedProtocol {
  const result: ParsedProtocol = {
    thought: null,
    plan: null,
    calls: null,
    content: text,
  };

  // 1. Extract Thought (Last full thought + handling streaming partial)
  // We match ALL thoughts to strip them, but we only keep the last one for display logic if multiple exist
  const thoughtRegex = /<thought>([\s\S]*?)<\/thought>/gi;
  let thoughtMatch;
  while ((thoughtMatch = thoughtRegex.exec(text)) !== null) {
    result.thought = thoughtMatch[1].trim();
  }
  result.content = result.content.replace(thoughtRegex, "");
  
  // Handle open thought tag at the end (streaming)
  const openThoughtRegex = /<thought>([\s\S]*)$/i;
  const openThoughtMatch = text.match(openThoughtRegex);
  if (openThoughtMatch) {
     result.thought = openThoughtMatch[1].trim();
     result.content = result.content.replace(openThoughtRegex, "");
  }

  // 2. Extract Plan
  const planRegex = /<plan>([\s\S]*?)<\/plan>/gi;
  let planMatch;
  while ((planMatch = planRegex.exec(text)) !== null) {
      const parsed = extractJson(planMatch[1]);
      if (parsed) result.plan = parsed;
  }
  result.content = result.content.replace(planRegex, "");

  // 3. Extract Calls (Agent Delegation)
  const callsRegex = /<calls>([\s\S]*?)<\/calls>/gi;
  let callsMatch;
  while ((callsMatch = callsRegex.exec(text)) !== null) {
      let parsed = extractJson(callsMatch[1]);
      if (parsed) {
        if (!Array.isArray(parsed) && parsed.calls) {
            parsed = parsed.calls;
        }
        // Accumulate calls if multiple blocks? usually we just want the latest valid block
        result.calls = parsed;
      }
  }
  result.content = result.content.replace(callsRegex, "");

  // 4. Extract Tool Calls (Local Tools)
  const toolCallsRegex = /<tool_calls>([\s\S]*?)<\/tool_calls>/gi;
  result.content = result.content.replace(toolCallsRegex, "");
  // We don't currently visualize tool_calls details in the main chat bubble, 
  // they are handled by "observation" events usually.

  // 5. Cleanup Metadata
  const metadataRegex = /<metadata>[\s\S]*?<\/metadata>/gi;
  result.content = result.content.replace(metadataRegex, "");

  // 6. Aggressive Cleanup of Broken Tags
  // This catches things like `</thought>` that might have been orphaned or `</ "get_top_5...`
  // Be careful not to strip valid code snippets user might want to see.
  // We only strip tags that look like our protocol tags.
  result.content = result.content
      .replace(/<\/?thought>/gi, "")
      .replace(/<\/?plan>/gi, "")
      .replace(/<\/?calls>/gi, "")
      .replace(/<\/?tool_calls>/gi, "")
      .replace(/<\/?metadata>/gi, "");

  result.content = result.content.trim();

  return result;
}
