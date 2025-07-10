/**
 * Virtual Table Component - 处理大数据量的高性能表格
 */

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Typography } from 'antd';

const { Text } = Typography;

interface VirtualTableProps {
  data: any[];
  columns: string[];
  height?: number;
  rowHeight?: number;
  loading?: boolean;
}

const VirtualTable: React.FC<VirtualTableProps> = ({
  data,
  columns,
  height = 400,
  rowHeight = 32,
  loading = false,
}) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(height);
  const [columnWidths, setColumnWidths] = useState<number[]>(
    () => columns.map(() => 120) // 初始宽度120px
  );
  const [isResizing, setIsResizing] = useState(false);
  const [resizingIndex, setResizingIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);

  // 计算可视区域内需要渲染的行
  const visibleRange = useMemo(() => {
    const start = Math.floor(scrollTop / rowHeight);
    const visibleCount = Math.ceil(containerHeight / rowHeight);
    const end = Math.min(start + visibleCount + 5, data.length); // 多渲染5行作为缓冲
    
    return {
      start: Math.max(0, start - 5), // 向前缓冲5行
      end,
      visibleCount
    };
  }, [scrollTop, containerHeight, rowHeight, data.length]);

  // 获取要渲染的数据
  const visibleData = useMemo(() => {
    return data.slice(visibleRange.start, visibleRange.end);
  }, [data, visibleRange.start, visibleRange.end]);

  // 处理滚动事件
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = e.currentTarget.scrollTop;
    setScrollTop(scrollTop);
  }, []);

  // 处理列宽调整
  const handleMouseDown = useCallback((e: React.MouseEvent, columnIndex: number) => {
    e.preventDefault();
    setIsResizing(true);
    setResizingIndex(columnIndex);
    
    const startX = e.clientX;
    const startWidth = columnWidths[columnIndex];
    
    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(60, startWidth + (e.clientX - startX)); // 最小宽度60px
      const newWidths = [...columnWidths];
      newWidths[columnIndex] = newWidth;
      setColumnWidths(newWidths);
    };
    
    const handleMouseUp = () => {
      setIsResizing(false);
      setResizingIndex(-1);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [columnWidths]);

  // 当列数变化时重置列宽
  useEffect(() => {
    if (columns.length !== columnWidths.length) {
      setColumnWidths(columns.map(() => 120));
    }
  }, [columns.length, columnWidths.length]);

  // 总高度
  const totalHeight = data.length * rowHeight;

  // 当前可视区域的偏移量
  const offsetY = visibleRange.start * rowHeight;

  if (loading) {
    return (
      <div style={{ 
        height, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        border: '1px solid #d9d9d9',
        borderRadius: '6px'
      }}>
        <Text>加载中...</Text>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div style={{ 
        height, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        border: '1px solid #d9d9d9',
        borderRadius: '6px'
      }}>
        <Text type="secondary">暂无数据</Text>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      style={{
        height,
        overflow: 'auto',
        border: '1px solid #d9d9d9',
        borderRadius: '6px',
        position: 'relative',
        userSelect: isResizing ? 'none' : 'auto'
      }}
      onScroll={handleScroll}
    >
      {/* 虚拟滚动容器 */}
      <div style={{ height: totalHeight, position: 'relative' }}>
        {/* 表头 */}
        <div style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          backgroundColor: '#fafafa',
          borderBottom: '2px solid #d9d9d9',
          display: 'flex',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          height: '41px'
        }}>
          {columns.map((column, index) => (
            <div
              key={index}
              style={{
                width: columnWidths[index],
                minWidth: '60px',
                padding: '8px 12px',
                fontWeight: 600,
                fontSize: '12px',
                borderRight: index < columns.length - 1 ? '1px solid #f0f0f0' : 'none',
                textAlign: 'left',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                position: 'relative'
              }}
            >
              {column}
              {/* 拖拽手柄 */}
              {index < columns.length - 1 && (
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    right: '-2px',
                    width: '4px',
                    height: '100%',
                    cursor: 'col-resize',
                    backgroundColor: isResizing && resizingIndex === index ? '#1890ff' : 'transparent',
                    zIndex: 10
                  }}
                  onMouseDown={(e) => handleMouseDown(e, index)}
                />
              )}
            </div>
          ))}
        </div>

        {/* 可视区域数据行 */}
        <div style={{
          position: 'absolute',
          top: offsetY + 43, // 表头高度 + 边框
          left: 0,
          right: 0
        }}>
          {visibleData.map((row, rowIndex) => {
            const actualRowIndex = visibleRange.start + rowIndex;
            return (
              <div
                key={actualRowIndex}
                style={{
                  height: rowHeight,
                  display: 'flex',
                  backgroundColor: actualRowIndex % 2 === 0 ? '#ffffff' : '#fafafa',
                  borderBottom: '1px solid #f0f0f0'
                }}
              >
                {columns.map((column, colIndex) => (
                  <div
                    key={colIndex}
                    style={{
                      width: columnWidths[colIndex],
                      minWidth: '60px',
                      padding: '6px 12px',
                      fontSize: '12px',
                      borderRight: colIndex < columns.length - 1 ? '1px solid #f0f0f0' : 'none',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    {String(row[column] || '')}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>

      {/* 滚动指示器 */}
      <div style={{
        position: 'absolute',
        bottom: '8px',
        right: '8px',
        background: 'rgba(0,0,0,0.6)',
        color: 'white',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '11px',
        pointerEvents: 'none'
      }}>
        {visibleRange.start + 1}-{Math.min(visibleRange.end, data.length)} / {data.length}
      </div>
    </div>
  );
};

export default VirtualTable;