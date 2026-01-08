# Plan: Mixed-Format Protocol & Interactive UI Implementation

## Objective
Refactor the system to support a "Mixed-Format Protocol" (XML-structured streams) for better user interaction and structured control. This enables the Agent to "think", "speak" (interact), "plan", and "act" in a way that the UI can render distinctively.

## 1. Backend: Protocol & Parsing (Engine)
**Goal:** Enable the Engine to produce and parse a stream containing Thoughts, User Messages, Plans, and Tool Calls.

- [ ] **Define Protocol Schema**
    - Structure:
      ```xml
      <metadata>...</metadata> (Optional)
      <thought>...</thought> (Streaming reasoning)
      User Interaction Text (Streaming natural language)
      <plan>JSON Array</plan> (Structured task list)
      <calls>JSON Array</calls> (Structured tool execution)
      ```
- [ ] **Update `parser.py`**
    - Implement a stateful parser/splitter in `apps/engine/core/protocol/parser.py`.
    - It should identify XML tags and separate them from plain text.
    - Validate JSON content within `<plan>` and `<calls>` tags.
- [ ] **Update System Prompt (`prompts/system.py`)**
    - Enforce the Mixed-Format output in the `SYSTEM_PROMPT_TEMPLATE`.
    - Add explicit examples for the `<plan>` and `<calls>` JSON structures.

## 2. Frontend: Chat Interface & Visualization (Admin)
**Goal:** Create a functional Chat UI that visualizes the new protocol elements.

- [ ] **Scaffold Chat Interface**
    - Replace the default `apps/admin/app/(dashboard)/page.tsx` with a Chat Layout.
    - Create `ChatInput` and `MessageList` components.
- [ ] **Implement Stream Parser (Frontend)**
    - Create a utility to parse the incoming stream on the client-side (or handle SSE events if backend splits them).
    - Separate `<thought>` (collapsible), `text` (bubble), and `<plan>` (sidebar/widget).
- [ ] **Create Visualization Components**
    - **ThoughtWidget:** A collapsible component to show the agent's internal monologue.
    - **PlanWidget:** A visual list/timeline of tasks showing `no_started`, `in_progress`, `completed`.
    - **ChatBubble:** Standard message display for the "Interaction" text.

## 3. Verification
- [ ] **Unit Test Parser:** Ensure `parser.py` correctly extracts all segments from a mixed string.
- [ ] **End-to-End Test:** Run a simple query ("Research OpenAI") and verify:
    - Thoughts appear.
    - Plan updates in the UI.
    - Search tool is called.
    - Final response is rendered.