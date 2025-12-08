"use client";

import { Editor } from "@monaco-editor/react";
import { useEffect, useRef } from "react";

interface CodeEditorProps {
    value: string;
    onChange: (value: string) => void;
    readOnly?: boolean;
}

export default function CodeEditor({ value, onChange, readOnly = false }: CodeEditorProps) {
    const editorRef = useRef<any>(null);

    function handleEditorDidMount(editor: any) {
        editorRef.current = editor;
    }

    function handleEditorChange(value: string | undefined) {
        onChange(value || "");
    }

    return (
        <div className="h-full w-full rounded-lg border overflow-hidden">
            <Editor
                height="100%"
                defaultLanguage="yaml"
                value={value}
                onChange={handleEditorChange}
                onMount={handleEditorDidMount}
                theme="vs-dark"
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: "on",
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    readOnly,
                    wordWrap: "on",
                }}
            />
        </div>
    );
}
