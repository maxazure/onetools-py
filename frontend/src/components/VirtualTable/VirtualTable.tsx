/**
 * Virtual Table Component - 处理大数据量的高性能表格
 */

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Typography } from 'antd';

const { Text } = Typography;

// 性能优化：行组件使用 memo 避免不必要的重新渲染
const TableRow = React.memo<{
  row: any;
  columns: string[];
  columnWidths: number[];
  rowHeight: number;
  actualRowIndex: number;
}>(({ row, columns, columnWidths, rowHeight, actualRowIndex }) => (
  <div
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
));

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
  const [containerHeight, setContainerHeight] = useState(height - 43); // 减去表头高度
  const [columnWidths, setColumnWidths] = useState<number[]>(
    () => columns.map(() => 120) // 初始宽度120px
  );
  const [isResizing, setIsResizing] = useState(false);
  const [resizingIndex, setResizingIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tableWidth, setTableWidth] = useState<number | undefined>(undefined);

  // 计算总列宽
  const totalColumnWidth = useMemo(() => {
    return columnWidths.reduce((sum, width) => sum + width, 0);
  }, [columnWidths]);

  // 计算可视区域内需要渲染的行 - 优化大数据性能
  const visibleRange = useMemo(() => {
    const start = Math.floor(scrollTop / rowHeight);
    const visibleCount = Math.ceil(Math.max(containerHeight, 0) / rowHeight);
    // 对于大数据集，使用固定的小缓冲区以保持性能
    const bufferSize = Math.min(3, Math.max(1, Math.floor(visibleCount / 4))); 
    const end = Math.min(start + visibleCount + bufferSize, data.length);
    
    return {
      start: Math.max(0, start - bufferSize),
      end,
      visibleCount
    };
  }, [scrollTop, containerHeight, rowHeight, data.length]);

  // 获取要渲染的数据
  const visibleData = useMemo(() => {
    return data.slice(visibleRange.start, visibleRange.end);
  }, [data, visibleRange.start, visibleRange.end]);

  // 处理滚动事件 - 使用节流优化性能
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
    const containerWidth = containerRef.current?.clientWidth || 0;
    
    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(60, startWidth + (e.clientX - startX)); // 最小宽度60px
      const newWidths = [...columnWidths];
      const oldWidth = newWidths[columnIndex];
      newWidths[columnIndex] = newWidth;
      
      // 计算新的总宽度
      const newTotalWidth = newWidths.reduce((sum, width) => sum + width, 0);
      
      // 如果新的总宽度超过容器宽度，则调整表格宽度
      if (newTotalWidth > containerWidth) {
        setTableWidth(newTotalWidth);
      } else {
        // 如果总宽度小于容器宽度，则使用容器宽度
        setTableWidth(undefined);
      }
      
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

  // 监听容器高度变化
  useEffect(() => {
    setContainerHeight(height - 43); // 43px = 表头高度(41px) + 边框(2px)
  }, [height]);

  // 监听容器尺寸变化
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { height: newHeight } = entry.contentRect;
        setContainerHeight(newHeight - 43); // 减去表头高度
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // 当列数变化时重置列宽和表格宽度
  useEffect(() => {
    if (columns.length !== columnWidths.length) {
      setColumnWidths(columns.map(() => 120));
      setTableWidth(undefined);
    }
  }, [columns.length, columnWidths.length]);

  // 初始化表格宽度
  useEffect(() => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.clientWidth;
      if (totalColumnWidth > containerWidth) {
        setTableWidth(totalColumnWidth);
      } else {
        setTableWidth(undefined);
      }
    }
  }, [totalColumnWidth]);

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
      <div style={{ 
        height: totalHeight, 
        position: 'relative',
        width: tableWidth || '100%',
        minWidth: '100%'
      }}>
        {/* 表头 */}
        <div style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          backgroundColor: '#fafafa',
          borderBottom: '2px solid #d9d9d9',
          display: 'flex',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          height: '41px',
          width: tableWidth || '100%',
          minWidth: '100%'
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
            </div>
          ))}
        </div>

        {/* 可视区域数据行 */}
        <div style={{
          position: 'absolute',
          top: offsetY + 43, // 表头高度 + 边框
          left: 0,
          right: 0,
          width: tableWidth || '100%',
          minWidth: '100%'
        }}>
          {visibleData.map((row, rowIndex) => {
            const actualRowIndex = visibleRange.start + rowIndex;
            return (
              <TableRow
                key={actualRowIndex}
                row={row}
                columns={columns}
                columnWidths={columnWidths}
                rowHeight={rowHeight}
                actualRowIndex={actualRowIndex}
              />
            );
          })}
        </div>
      </div>

      {/* 滚动指示器 - 简化以提高性能 */}
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