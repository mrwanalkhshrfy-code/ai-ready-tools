import { useState, useCallback, useRef, useEffect } from "react";
import type { PrologResult } from "@/lib/prolog-engine";
import { createPrologSession } from "@/lib/prolog-engine";
import { prologExamples } from "@/lib/prolog-examples";

function PlayIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  );
}

function BookIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
  );
}

function TerminalIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}

function CodeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  );
}

export default function PrologIDE() {
  const [code, setCode] = useState(prologExamples[0].code);
  const [query, setQuery] = useState(prologExamples[0].query);
  const [output, setOutput] = useState<PrologResult[]>([]);
  const [showExamples, setShowExamples] = useState(false);
  const [activeExample, setActiveExample] = useState(prologExamples[0].id);
  const [isRunning, setIsRunning] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const lineCount = code.split("\n").length;

  const runCode = useCallback(() => {
    setIsRunning(true);
    setOutput([{ type: "info", text: `?- ${query}` }]);

    // Small delay for UI feedback
    setTimeout(() => {
      try {
        const session = createPrologSession();
        const results = session.run(code, query);
        setOutput((prev) => [...prev, ...results]);
      } catch (e: any) {
        setOutput((prev) => [
          ...prev,
          { type: "error", text: `Error: ${e.message || String(e)}` },
        ]);
      } finally {
        setIsRunning(false);
      }
    }, 100);
  }, [code, query]);

  const loadExample = useCallback((id: string) => {
    const ex = prologExamples.find((e) => e.id === id);
    if (ex) {
      setCode(ex.code);
      setQuery(ex.query);
      setActiveExample(id);
      setOutput([]);
      setShowExamples(false);
    }
  }, []);

  const clearOutput = useCallback(() => setOutput([]), []);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  // Handle keyboard shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runCode();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [runCode]);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      {/* Top Toolbar */}
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-toolbar-border bg-toolbar-bg px-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <TerminalIcon className="h-5 w-5 text-primary" />
            <h1 className="text-sm font-semibold text-foreground tracking-wide">
              Prolog<span className="text-primary">Lab</span>
            </h1>
          </div>
          <span className="text-xs text-muted-foreground hidden sm:inline">|</span>
          <span className="text-xs text-muted-foreground hidden sm:inline">محرر برولوج تفاعلي</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowExamples(!showExamples)}
            className="flex items-center gap-1.5 rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground transition-colors hover:bg-muted"
          >
            <BookIcon className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">أمثلة</span>
          </button>
          <button
            onClick={runCode}
            disabled={isRunning}
            className="run-glow flex items-center gap-1.5 rounded-md bg-run-btn px-4 py-1.5 text-xs font-semibold text-run-btn-foreground transition-all hover:brightness-110 disabled:opacity-50"
          >
            <PlayIcon className="h-3.5 w-3.5" />
            {isRunning ? "جاري التنفيذ..." : "تشغيل"}
            <kbd className="ml-1 hidden rounded border border-run-btn-foreground/30 px-1 py-0.5 text-[10px] sm:inline">
              Ctrl+↵
            </kbd>
          </button>
        </div>
      </header>

      {/* Examples Dropdown */}
      {showExamples && (
        <div className="absolute right-4 top-12 z-50 mt-1 w-72 rounded-lg border border-border bg-card p-2 shadow-xl">
          <p className="mb-2 px-2 text-xs font-semibold text-muted-foreground">أمثلة جاهزة</p>
          {prologExamples.map((ex) => (
            <button
              key={ex.id}
              onClick={() => loadExample(ex.id)}
              className={`flex w-full flex-col rounded-md px-3 py-2 text-left transition-colors ${
                activeExample === ex.id
                  ? "bg-primary/15 text-primary"
                  : "hover:bg-muted text-foreground"
              }`}
            >
              <span className="text-sm font-medium">{ex.titleAr}</span>
              <span className="text-xs text-muted-foreground">{ex.description}</span>
            </button>
          ))}
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Editor Panel */}
        <div className="flex flex-1 flex-col min-w-0">
          {/* Editor Header */}
          <div className="flex h-9 items-center gap-2 border-b border-border bg-panel-header px-4">
            <CodeIcon className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">program.pl</span>
            <span className="ml-auto text-xs text-muted-foreground">{lineCount} سطر</span>
          </div>

          {/* Code Editor */}
          <div className="relative flex flex-1 overflow-auto bg-editor-bg">
            {/* Line Numbers */}
            <div className="sticky left-0 flex w-12 shrink-0 select-none flex-col items-end bg-editor-bg pr-3 pt-3 font-mono text-xs leading-[1.6] text-editor-gutter">
              {Array.from({ length: lineCount }, (_, i) => (
                <div key={i} className="h-[22.4px]">
                  {i + 1}
                </div>
              ))}
            </div>

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              spellCheck={false}
              className="editor-textarea flex-1 p-3 pl-1"
              placeholder="% اكتب كود Prolog هنا..."
            />
          </div>

          {/* Query Bar */}
          <div className="flex h-11 items-center gap-2 border-t border-border bg-toolbar-bg px-4">
            <span className="text-xs font-semibold text-primary">?-</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") runCode();
              }}
              className="flex-1 bg-transparent font-mono text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
              placeholder="اكتب الاستعلام هنا... مثال: father(X, Y)."
            />
          </div>
        </div>

        {/* Divider */}
        <div className="w-px bg-border" />

        {/* Output Panel */}
        <div className="flex w-full flex-col sm:w-[380px] lg:w-[420px]">
          {/* Output Header */}
          <div className="flex h-9 items-center justify-between border-b border-border bg-panel-header px-4">
            <div className="flex items-center gap-2">
              <TerminalIcon className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">النتائج</span>
            </div>
            {output.length > 0 && (
              <button
                onClick={clearOutput}
                className="rounded p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <TrashIcon className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Output Content */}
          <div ref={outputRef} className="flex-1 overflow-auto bg-console-bg p-4">
            {output.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <TerminalIcon className="mb-3 h-10 w-10 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">
                  اضغط <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-primary">تشغيل</span> لرؤية النتائج
                </p>
                <p className="mt-1 text-xs text-muted-foreground/60">
                  أو اضغط Ctrl + Enter
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {output.map((line, i) => (
                  <div
                    key={i}
                    className={`console-line ${
                      line.type === "success"
                        ? "text-console-success"
                        : line.type === "error"
                          ? "text-console-error"
                          : "text-console-info"
                    }`}
                  >
                    {line.type === "success" && <span className="mr-1 text-console-success/60">✓</span>}
                    {line.type === "error" && <span className="mr-1 text-console-error/60">✗</span>}
                    {line.type === "info" && <span className="mr-1 text-console-info/60">›</span>}
                    {line.text}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
