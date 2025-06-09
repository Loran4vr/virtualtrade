import React, { useState, useEffect } from 'react';
import { Box, Grid, Tab, Tabs } from '@mui/material';
import MarketOverview from './components/MarketOverview';
import StockSearch from './components/StockSearch';
import FuturesOptions from './components/FuturesOptions';
import Portfolio from './components/Portfolio';
import Chart from './components/Chart';
import MarketDepth from './components/MarketDepth';
import {
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress
} from '@mui/material';

export default function Market() {
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [timeframe, setTimeframe] = useState('1D');
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedSymbol) {
      fetchChartData();
    }
  }, [selectedSymbol, timeframe]);

  const fetchChartData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/market/chart/${selectedSymbol}?timeframe=${timeframe}`);
      if (response.ok) {
        const data = await response.json();
        setChartData(data.candles);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  const handleSymbolSelect = (symbol) => {
    setSelectedSymbol(symbol);
  };

  const handleTimeframeChange = (event) => {
    setTimeframe(event.target.value);
  };

  return (
    <Box sx={{ p: { xs: 1, md: 3 } }}>
      <MarketOverview />
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={selectedTab} onChange={handleTabChange}>
          <Tab label="F&O Trading" />
          <Tab label="Portfolio" />
          <Tab label="Charts" />
          <Tab label="Market Depth" />
        </Tabs>
      </Box>

      {selectedTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <FuturesOptions />
          </Grid>
          <Grid item xs={12}>
            <StockSearch onSymbolSelect={handleSymbolSelect} />
          </Grid>
        </Grid>
      )}

      {selectedTab === 1 && (
        <Portfolio />
      )}

      {selectedTab === 2 && selectedSymbol && (
        <Card>
          <CardContent>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">
                {selectedSymbol} Chart
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
              <Chart data={chartData} height={400} />
            )}
          </CardContent>
        </Card>
      )}

      {selectedTab === 3 && selectedSymbol && (
        <MarketDepth symbol={selectedSymbol} />
      )}
    </Box>
  );
}

