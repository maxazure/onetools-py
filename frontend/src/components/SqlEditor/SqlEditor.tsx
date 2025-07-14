/**
 * SQL Editor Component using Monaco Editor
 */

import React, { useRef, useCallback, useMemo } from 'react';
import { Editor, OnMount } from '@monaco-editor/react';
import { Button, Space, Tooltip, Typography } from 'antd';
import { PlayCircleOutlined, SaveOutlined, FormatPainterOutlined, ClearOutlined, DatabaseOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute?: () => void;
  onSave?: () => void;
  onFormat?: () => void;
  onClear?: () => void;
  onAnalyzeSchema?: () => void;
  height?: string | number;
  readOnly?: boolean;
  loading?: boolean;
  analyzingSchema?: boolean;
  theme?: 'light' | 'dark';
  showToolbar?: boolean;
  placeholder?: string;
}

const SqlEditor: React.FC<SqlEditorProps> = ({
  value,
  onChange,
  onExecute,
  onSave,
  onFormat,
  onClear,
  onAnalyzeSchema,
  height = 300,
  readOnly = false,
  loading = false,
  analyzingSchema = false,
  theme = 'light',
  showToolbar = true,
  placeholder,
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
      provideCompletionItems: (model: any, position: any) => {
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
    if (onExecute) {
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, onExecute);
    }

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
      {showToolbar && (
        <div className="sql-editor-toolbar" style={{ marginBottom: 8 }}>
          <Space>
            {onExecute && (
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={onExecute}
                loading={loading}
                disabled={readOnly}
              >
                执行查询
              </Button>
            )}
            
            {onSave && (
              <Button
                icon={<SaveOutlined />}
                onClick={onSave}
                disabled={readOnly}
              >
                保存查询
              </Button>
            )}
            
            {onFormat && (
              <Tooltip title="验证语法">
                <Button
                  icon={<FormatPainterOutlined />}
                  onClick={handleFormat}
                  disabled={readOnly}
                >
                  验证语法
                </Button>
              </Tooltip>
            )}
            
            {onClear && (
              <Tooltip title="清空编辑器">
                <Button
                  icon={<ClearOutlined />}
                  onClick={handleClear}
                  disabled={readOnly}
                >
                  清空
                </Button>
              </Tooltip>
            )}
            
            {onAnalyzeSchema && (
              <Tooltip title="分析SQL中的表结构并生成CREATE语句">
                <Button
                  icon={<DatabaseOutlined />}
                  onClick={onAnalyzeSchema}
                  loading={analyzingSchema}
                  disabled={readOnly || !value.trim()}
                >
                  分析表结构
                </Button>
              </Tooltip>
            )}
          </Space>
          
        </div>
      )}
      
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
          renderWhitespace: 'none', // 减少渲染
          automaticLayout: true,
          wordWrap: 'on',
          folding: false, // 禁用代码折叠减少渲染开销
          selectOnLineNumbers: true,
          matchBrackets: 'never', // 禁用括号匹配减少计算
          autoIndent: 'none', // 禁用自动缩进
          formatOnPaste: false, // 禁用粘贴时格式化
          formatOnType: false, // 禁用输入时格式化
          suggestOnTriggerCharacters: false, // 禁用自动建议
          acceptSuggestionOnEnter: 'off',
          snippetSuggestions: 'none',
          quickSuggestions: false, // 完全禁用快速建议
          hover: { enabled: false }, // 禁用悬停提示
          occurrencesHighlight: 'off', // 禁用occurrence高亮
          selectionHighlight: false, // 禁用选择高亮
          renderLineHighlight: 'none', // 禁用行高亮
          smoothScrolling: false, // 禁用平滑滚动
          placeholder: placeholder,
          // 滚动条优化
          scrollbar: {
            verticalScrollbarSize: 8,
            horizontalScrollbarSize: 8,
            useShadows: false,
            alwaysConsumeMouseWheel: false
          },
        }}
      />
    </div>
  );
};

export default SqlEditor;