export interface PlanStep {
  step: string;
  state: "not_started" | "in_progress" | "completed" | "blocked";
}

export interface ParsedProtocol {
  thought: string | null;
  plan: PlanStep[] | null;
  content: string;
  isThoughtClosed: boolean;
  isPlanClosed: boolean;
}

/**
 * Attempts to parse a potentially incomplete JSON string.
 */
export function parsePartialJson(jsonString: string): any {
  if (!jsonString.trim()) return null;

  // 1. More aggressive cleaning: find the first '[' or '{' and the last ']' or '}'
  let clean = jsonString.trim();
  const firstBracket = clean.indexOf('[');
  const firstBrace = clean.indexOf('{');
  let startIndex = -1;

  if (firstBracket !== -1 && firstBrace !== -1) {
    startIndex = Math.min(firstBracket, firstBrace);
  } else {
    startIndex = firstBracket !== -1 ? firstBracket : firstBrace;
  }

  if (startIndex === -1) return null;
  clean = clean.substring(startIndex);

  // Remove markdown code blocks if still present
  clean = clean.replace(/```json/gi, "").replace(/```/g, "").trim();

  try {
    return JSON.parse(clean);
  } catch (e) {
    // 2. Try to fix unclosed arrays of objects
    let fixed = clean;

    // Remove trailing comma before closing bracket/brace
    fixed = fixed.replace(/,\s*([\]}])/g, "$1");

    if (fixed.startsWith("[")) {
      // Find the last complete object '}'
      const lastCurly = fixed.lastIndexOf("}");
      if (lastCurly !== -1) {
        fixed = fixed.substring(0, lastCurly + 1) + "]";
      } else {
        // If it's just "[", return empty array for better UX
        return [];
      }
    } else if (fixed.startsWith("{")) {
        const lastCurly = fixed.lastIndexOf("}");
        if (lastCurly !== -1) {
            fixed = fixed.substring(0, lastCurly + 1);
        } else {
            // Can't really fix a partial object that hasn't closed a single level
            return null;
        }
    }

    try {
      return JSON.parse(fixed);
    } catch (e2) {
      return null;
    }
  }
}

export function parseProtocol(text: string): ParsedProtocol {
  const result: ParsedProtocol = {
    thought: null,
    plan: null,
    content: text,
    isThoughtClosed: false,
    isPlanClosed: false,
  };

  // 1. Extract Thought (Last one)
  const thoughtRegex = /<thought>([\s\S]*?)(?:<\/thought>|$)/gi;
  let tMatch;
  while ((tMatch = thoughtRegex.exec(text)) !== null) {
      result.thought = tMatch[1].trim();
      result.isThoughtClosed = tMatch[0].toLowerCase().includes("</thought>");
  }

  // Fallback for thought in JSON if no <thought> tag found
  if (!result.thought) {
    const jsonMatch = text.match(/```json\s*([\s\S]*?)(?:```|$)/i);
    if (jsonMatch) {
        const parsed = parsePartialJson(jsonMatch[1]);
        if (parsed && parsed.thought) {
            result.thought = parsed.thought;
            result.isThoughtClosed = text.includes('"}') || text.includes('",');
        }
    }
  }

  // 2. Extract Plan (Last one)
  const planRegex = /<plan>([\s\S]*?)(?:<\/plan>|$)/gi;
  let pMatch;
  while ((pMatch = planRegex.exec(text)) !== null) {
      const rawPlan = pMatch[1].trim();
      result.isPlanClosed = pMatch[0].toLowerCase().includes("</plan>");
      const parsed = parsePartialJson(rawPlan);
      if (parsed && Array.isArray(parsed)) {
          result.plan = parsed;
      }
  }

  // 3. Cleanup content for display
  result.content = text
    .replace(/<thought>[\s\S]*?(?:<\/thought>|$)/gi, "")
    .replace(/<plan>[\s\S]*?(?:<\/plan>|$)/gi, "")
    .replace(/<calls>[\s\S]*?(?:<\/calls>|$)/gi, "")
    .replace(/<tool_calls>[\s\S]*?(?:<\/tool_calls>|$)/gi, "")
    .replace(/<metadata>[\s\S]*?(?:<\/metadata>|$)/gi, "")
    .replace(/```json[\s\S]*?(?:```|$)/gi, "") // Also strip JSON block if used as fallback
    .trim();

  return result;
}
