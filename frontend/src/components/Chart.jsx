import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  CandlestickChart,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  ShowChart as ShowChartIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';

export default function Chart({ symbol }) {
  const [timeframe, setTimeframe] = useState('1D');
  const [chartData, setChartData] = useState([]);
  const [indicators, setIndicators] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedIndicators, setSelectedIndicators] = useState(['sma_20', 'sma_50']);

  useEffect(() => {
    if (symbol) {
      fetchChartData();
    }
  }, [symbol, timeframe]);

  const fetchChartData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/market/chart/${symbol}?timeframe=${timeframe}`);
      if (response.ok) {
        const data = await response.json();
        setChartData(data.candles);
        setIndicators(data.indicators);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTimeframeChange = (event) => {
    setTimeframe(event.target.value);
  };

  const toggleIndicator = (indicator) => {
    setSelectedIndicators(prev => 
      prev.includes(indicator)
        ? prev.filter(i => i !== indicator)
        : [...prev, indicator]
    );
  };

  const renderCandlestickChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <CandlestickChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis domain={['dataMin', 'dataMax']} />
        <RechartsTooltip />
        <Legend />
        {selectedIndicators.includes('sma_20') && (
          <Line
            type="monotone"
            dataKey="sma_20"
            stroke="#2196f3"
            dot={false}
            name="SMA 20"
          />
        )}
        {selectedIndicators.includes('sma_50') && (
          <Line
            type="monotone"
            dataKey="sma_50"
            stroke="#f50057"
            dot={false}
            name="SMA 50"
          />
        )}
      </CandlestickChart>
    </ResponsiveContainer>
  );

  const renderVolumeChart = () => (
    <ResponsiveContainer width="100%" height={100}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis />
        <RechartsTooltip />
        <Line
          type="monotone"
          dataKey="volume"
          stroke="#4caf50"
          fill="#4caf50"
          name="Volume"
        />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderIndicators = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" gutterBottom>
        Technical Indicators
      </Typography>
      <Grid container spacing={2}>
        <Grid item>
          <Tooltip title="SMA 20">
            <IconButton
              color={selectedIndicators.includes('sma_20') ? 'primary' : 'default'}
              onClick={() => toggleIndicator('sma_20')}
            >
              <ShowChartIcon />
            </IconButton>
          </Tooltip>
        </Grid>
        <Grid item>
          <Tooltip title="SMA 50">
            <IconButton
              color={selectedIndicators.includes('sma_50') ? 'primary' : 'default'}
              onClick={() => toggleIndicator('sma_50')}
            >
              <TimelineIcon />
            </IconButton>
          </Tooltip>
        </Grid>
        <Grid item>
          <Tooltip title="RSI">
            <IconButton
              color={selectedIndicators.includes('rsi') ? 'primary' : 'default'}
              onClick={() => toggleIndicator('rsi')}
            >
              <TrendingUpIcon />
            </IconButton>
          </Tooltip>
        </Grid>
        <Grid item>
          <Tooltip title="MACD">
            <IconButton
              color={selectedIndicators.includes('macd') ? 'primary' : 'default'}
              onClick={() => toggleIndicator('macd')}
            >
              <TrendingDownIcon />
            </IconButton>
          </Tooltip>
        </Grid>
      </Grid>
    </Box>
  );

  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            {symbol} Chart
          </Typography>
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Timeframe</InputLabel>
            <Select
              value={timeframe}
              label="Timeframe"
              onChange={handleTimeframeChange}
            >
              <MenuItem value="1m">1 Minute</MenuItem>
              <MenuItem value="5m">5 Minutes</MenuItem>
              <MenuItem value="15m">15 Minutes</MenuItem>
              <MenuItem value="30m">30 Minutes</MenuItem>
              <MenuItem value="1h">1 Hour</MenuItem>
              <MenuItem value="1D">1 Day</MenuItem>
              <MenuItem value="1W">1 Week</MenuItem>
              <MenuItem value="1M">1 Month</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {renderCandlestickChart()}
            {renderVolumeChart()}
            {renderIndicators()}
          </>
        )}
      </CardContent>
    </Card>
  );
} 