/**
 * SQL Editor Component using Monaco Editor
 */

import React, { useRef, useCallback, useEffect } from 'react';
import { Editor, OnMount } from '@monaco-editor/react';
import { Button, Space, Tooltip, Typography } from 'antd';
import { PlayCircleOutlined, SaveOutlined, FormatPainterOutlined, ClearOutlined } from '@ant-design/icons';
// Monaco types are provided by @monaco-editor/react

const { Text } = Typography;

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute: () => void;
  onSave?: () => void;
  onFormat?: () => void;
  onClear?: () => void;
  height?: string | number;
  readOnly?: boolean;
  loading?: boolean;
  theme?: 'light' | 'dark';
}

const SqlEditor: React.FC<SqlEditorProps> = ({
  value,
  onChange,
  onExecute,
  onSave,
  onFormat,
  onClear,
  height = 300,
  readOnly = false,
  loading = false,
  theme = 'light',
}) => {
  const editorRef = useRef<any>(null);
  const handleEditorDidMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;

    // Configure SQL language features
    monaco.languages.setLanguageConfiguration('sql', {
      comments: {
        lineComment: '--',
        blockComment: ['/*', '*/'],
      },
      brackets: [
        ['{', '}'],
        ['[', ']'],
        ['(', ')'],
      ],
      autoClosingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"' },
        { open: "'", close: "'" },
      ],
      surroundingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"' },
        { open: "'", close: "'" },
      ],
    });

    // Add SQL keywords and completion
    monaco.languages.registerCompletionItemProvider('sql', {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        };

        const suggestions: any[] = [
          {
            label: 'SELECT',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'SELECT ',
            documentation: 'SQL SELECT statement',
            range: range,
          },
          {
            label: 'FROM',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'FROM ',
            documentation: 'SQL FROM clause',
            range: range,
          },
          {
            label: 'WHERE',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'WHERE ',
            documentation: 'SQL WHERE clause',
            range: range,
          },
          {
            label: 'ORDER BY',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'ORDER BY ',
            documentation: 'SQL ORDER BY clause',
            range: range,
          },
          {
            label: 'GROUP BY',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'GROUP BY ',
            documentation: 'SQL GROUP BY clause',
            range: range,
          },
          {
            label: 'Users',
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: 'Users',
            documentation: 'Users table',
            range: range,
          },
        ];

        return { suggestions };
      },
    });

    // Add keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, onExecute);

    if (onSave) {
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, onSave);
    }

    if (onFormat) {
      editor.addCommand(monaco.KeyMod.Shift | monaco.KeyMod.Alt | monaco.KeyCode.KeyF, onFormat);
    }
  }, [onExecute, onSave, onFormat]);

  const handleFormat = useCallback(() => {
    if (editorRef.current && onFormat) {
      onFormat();
      // Trigger Monaco's built-in formatter
      editorRef.current.getAction('editor.action.formatDocument')?.run();
    }
  }, [onFormat]);

  const handleClear = useCallback(() => {
    if (editorRef.current && onClear) {
      onClear();
      editorRef.current.setValue('');
    }
  }, [onClear]);

  return (
    <div className="sql-editor">
      <div className="sql-editor-toolbar" style={{ marginBottom: 8 }}>
        <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={onExecute}
            loading={loading}
            disabled={readOnly}
          >
            执行查询
          </Button>
          
          <Button
            icon={<SaveOutlined />}
            onClick={onSave}
            disabled={readOnly}
          >
            保存查询
          </Button>
          
          <Tooltip title="验证语法">
            <Button
              icon={<FormatPainterOutlined />}
              onClick={handleFormat}
              disabled={readOnly}
            >
              验证语法
            </Button>
          </Tooltip>
          
          <Tooltip title="清空编辑器">
            <Button
              icon={<ClearOutlined />}
              onClick={handleClear}
              disabled={readOnly}
            >
              清空
            </Button>
          </Tooltip>
        </Space>
        
        <div style={{ float: 'right' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Lines: {value.split('\n').length} | Characters: {value.length}
          </Text>
        </div>
      </div>
      
      <Editor
        height={height}
        language="sql"
        value={value}
        onChange={(val) => onChange(val || '')}
        onMount={handleEditorDidMount}
        theme={theme === 'dark' ? 'vs-dark' : 'vs'}
        options={{
          readOnly,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 14,
          lineNumbers: 'on',
          renderWhitespace: 'selection',
          automaticLayout: true, // Enable automatic layout
          wordWrap: 'on',
          folding: true,
          selectOnLineNumbers: true,
          matchBrackets: 'always',
          autoIndent: 'full',
          formatOnPaste: true,
          formatOnType: true,
          suggestOnTriggerCharacters: true,
          acceptSuggestionOnEnter: 'on',
          snippetSuggestions: 'inline',
          quickSuggestions: {
            other: true,
            comments: false,
            strings: false,
          },
          // Add explicit dimensions handling
          scrollbar: {
            verticalScrollbarSize: 10,
            horizontalScrollbarSize: 10,
            useShadows: false,
          },
        }}
      />
    </div>
  );
};

export default SqlEditor;