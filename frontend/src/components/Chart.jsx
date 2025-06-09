import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { Box, Typography, useTheme } from '@mui/material';

const Chart = ({ data, height = 400 }) => {
  const theme = useTheme();

  const chartData = useMemo(() => {
    if (!data || !data.length) return [];
    return data.map(item => ({
      date: new Date(item.timestamp).toLocaleDateString(),
      price: item.price,
      volume: item.volume,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close
    }));
  }, [data]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
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
            Price: ${payload[0].value.toFixed(2)}
          </Typography>
          {payload[1] && (
            <Typography variant="body2">
              Volume: {payload[1].value.toLocaleString()}
            </Typography>
          )}
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
        <AreaChart
          data={chartData}
          margin={{
            top: 10,
            right: 30,
            left: 0,
            bottom: 0,
          }}
        >
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={theme.palette.secondary.main} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={theme.palette.secondary.main} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fill: theme.palette.text.secondary }}
            stroke={theme.palette.divider}
          />
          <YAxis 
            yAxisId="left"
            tick={{ fill: theme.palette.text.secondary }}
            stroke={theme.palette.divider}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right"
            tick={{ fill: theme.palette.text.secondary }}
            stroke={theme.palette.divider}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="price"
            stroke={theme.palette.primary.main}
            fillOpacity={1}
            fill="url(#colorPrice)"
          />
          <Area
            yAxisId="right"
            type="monotone"
            dataKey="volume"
            stroke={theme.palette.secondary.main}
            fillOpacity={1}
            fill="url(#colorVolume)"
          />
          {data.map((item, index) => (
            <ReferenceLine
              key={index}
              x={new Date(item.timestamp).toLocaleDateString()}
              stroke={theme.palette.divider}
              strokeDasharray="3 3"
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default Chart; 