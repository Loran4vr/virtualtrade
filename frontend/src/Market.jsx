import React, { useState } from 'react';
import { Box, Grid, Tab, Tabs } from '@mui/material';
import MarketOverview from './components/MarketOverview';
import StockSearch from './components/StockSearch';
import FuturesOptions from './components/FuturesOptions';
import Portfolio from './components/Portfolio';
import Chart from './components/Chart';
import MarketDepth from './components/MarketDepth';

export default function Market() {
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedSymbol, setSelectedSymbol] = useState(null);

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  const handleSymbolSelect = (symbol) => {
    setSelectedSymbol(symbol);
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
        <Chart symbol={selectedSymbol} />
      )}

      {selectedTab === 3 && selectedSymbol && (
        <MarketDepth symbol={selectedSymbol} />
      )}
    </Box>
  );
}

