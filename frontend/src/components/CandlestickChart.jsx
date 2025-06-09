import React, { useMemo } from 'react';
import {
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Rectangle
} from 'recharts';
import { Box, Typography, useTheme } from '@mui/material';

const CustomCandlestick = (props) => {
  const { x, y, width, height, low, high, open, close } = props;
  const isGrowing = open < close;
  const color = isGrowing ? '#26a69a' : '#ef5350';
  const wickHeight = high - low;
  const bodyHeight = Math.abs(close - open);
  const bodyY = isGrowing ? y + (high - close) : y + (high - open);

  return (
    <g>
      {/* Wick */}
      <line
        x1={x + width / 2}
        y1={y}
        x2={x + width / 2}
        y2={y + wickHeight}
        stroke={color}
        strokeWidth={1}
      />
      {/* Body */}
      <Rectangle
        x={x}
        y={bodyY}
        width={width}
        height={bodyHeight}
        fill={color}
        stroke={color}
      />
    </g>
  );
};

const CandlestickChart = ({ data, height = 400 }) => {
  const theme = useTheme();

  const chartData = useMemo(() => {
    if (!data || !data.length) return [];
    return data.map(item => ({
      date: new Date(item.timestamp).toLocaleDateString(),
      timestamp: item.timestamp,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
      volume: item.volume
    }));
  }, [data]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box sx={{ 
          backgroundColor: 'background.paper',
          p: 1,
          border: 1,
          borderColor: 'divider',
          borderRadius: 1
        }}>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="body2">
            Open: ${data.open.toFixed(2)}
          </Typography>
          <Typography variant="body2">
            High: ${data.high.toFixed(2)}
          </Typography>
          <Typography variant="body2">
            Low: ${data.low.toFixed(2)}
          </Typography>
          <Typography variant="body2">
            Close: ${data.close.toFixed(2)}
          </Typography>
          <Typography variant="body2">
            Volume: {data.volume.toLocaleString()}
          </Typography>
        </Box>
      );
    }
    return null;
  };

  if (!data || data.length === 0) {
    return (
      <Box sx={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', height }}>
      <ResponsiveContainer>
        <ComposedChart
          data={chartData}
          margin={{
            top: 10,
            right: 30,
            left: 0,
            bottom: 0,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fill: theme.palette.text.secondary }}
            stroke={theme.palette.divider}
          />
          <YAxis 
            domain={['dataMin', 'dataMax']}
            tick={{ fill: theme.palette.text.secondary }}
            stroke={theme.palette.divider}
          />
          <Tooltip content={<CustomTooltip />} />
          <CustomCandlestick
            dataKey="price"
            fill="#8884d8"
            stroke="#8884d8"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default CandlestickChart; 