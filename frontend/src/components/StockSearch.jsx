import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const sectors = [
  'IT',
  'BANKING',
  'PHARMA',
  'AUTO',
  'FMCG',
  'METAL',
  'REALTY',
  'ENERGY',
  'TELECOM'
];

export default function StockSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState('');
  const [minMarketCap, setMinMarketCap] = useState('');
  const [maxMarketCap, setMaxMarketCap] = useState('');
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [technicalData, setTechnicalData] = useState(null);
  const [fundamentalData, setFundamentalData] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        query: searchQuery,
        sector: selectedSector,
        min_market_cap: minMarketCap,
        max_market_cap: maxMarketCap
      });
      
      const response = await fetch(`/api/stock/search?${params}`);
      if (response.ok) {
        const data = await response.json();
        setStocks(data);
      }
    } catch (error) {
      console.error('Error searching stocks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStockSelect = async (stock) => {
    setSelectedStock(stock);
    setOpenDialog(true);
    setLoading(true);
    
    try {
      const [technicalRes, fundamentalRes] = await Promise.all([
        fetch(`/api/stock/technical/${stock.symbol}`),
        fetch(`/api/stock/fundamentals/${stock.symbol}`)
      ]);
      
      if (technicalRes.ok) {
        setTechnicalData(await technicalRes.json());
      }
      if (fundamentalRes.ok) {
        setFundamentalData(await fundamentalRes.json());
      }
    } catch (error) {
      console.error('Error fetching stock details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                label="Search Stocks"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Symbol or Company Name"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                select
                label="Sector"
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
              >
                <MenuItem value="">All Sectors</MenuItem>
                {sectors.map((sector) => (
                  <MenuItem key={sector} value={sector}>
                    {sector}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                label="Min Market Cap (Cr)"
                type="number"
                value={minMarketCap}
                onChange={(e) => setMinMarketCap(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                label="Max Market Cap (Cr)"
                type="number"
                value={maxMarketCap}
                onChange={(e) => setMaxMarketCap(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleSearch}
                disabled={loading}
              >
                Search
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Sector</TableCell>
                <TableCell>Market Cap (Cr)</TableCell>
                <TableCell>Last Price</TableCell>
                <TableCell>Change</TableCell>
                <TableCell>Volume</TableCell>
                <TableCell>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {stocks.map((stock) => (
                <TableRow key={stock.symbol}>
                  <TableCell>{stock.symbol}</TableCell>
                  <TableCell>{stock.name}</TableCell>
                  <TableCell>{stock.sector}</TableCell>
                  <TableCell>₹{(stock.market_cap / 10000000).toFixed(2)}</TableCell>
                  <TableCell>₹{stock.last_price.toFixed(2)}</TableCell>
                  <TableCell>
                    <Chip
                      label={`${stock.change > 0 ? '+' : ''}${stock.change.toFixed(2)}%`}
                      color={stock.change >= 0 ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{stock.volume.toLocaleString()}</TableCell>
                  <TableCell>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleStockSelect(stock)}
                    >
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedStock && (
          <>
            <DialogTitle>
              {selectedStock.name} ({selectedStock.symbol})
            </DialogTitle>
            <DialogContent>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="Technical Analysis" />
                <Tab label="Fundamentals" />
              </Tabs>

              {activeTab === 0 && technicalData && (
                <Box sx={{ mt: 2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="h6">Technical Indicators</Typography>
                      <Grid container spacing={2} sx={{ mt: 1 }}>
                        <Grid item xs={3}>
                          <Typography variant="subtitle2">SMA (20)</Typography>
                          <Typography>{technicalData.indicators.sma_20?.toFixed(2) || 'N/A'}</Typography>
                        </Grid>
                        <Grid item xs={3}>
                          <Typography variant="subtitle2">SMA (50)</Typography>
                          <Typography>{technicalData.indicators.sma_50?.toFixed(2) || 'N/A'}</Typography>
                        </Grid>
                        <Grid item xs={3}>
                          <Typography variant="subtitle2">RSI</Typography>
                          <Typography>{technicalData.indicators.rsi?.toFixed(2) || 'N/A'}</Typography>
                        </Grid>
                        <Grid item xs={3}>
                          <Typography variant="subtitle2">MACD</Typography>
                          <Typography>{technicalData.indicators.macd?.macd?.toFixed(2) || 'N/A'}</Typography>
                        </Grid>
                      </Grid>
                    </Grid>
                  </Grid>
                </Box>
              )}

              {activeTab === 1 && fundamentalData && (
                <Box sx={{ mt: 2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2">Sector</Typography>
                      <Typography>{fundamentalData.sector}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2">Industry</Typography>
                      <Typography>{fundamentalData.industry}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2">Market Cap</Typography>
                      <Typography>₹{(fundamentalData.market_cap / 10000000).toFixed(2)} Cr</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2">P/E Ratio</Typography>
                      <Typography>{fundamentalData.pe_ratio?.toFixed(2) || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2">EPS</Typography>
                      <Typography>₹{fundamentalData.eps?.toFixed(2) || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2">Dividend Yield</Typography>
                      <Typography>{fundamentalData.dividend_yield?.toFixed(2)}%</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2">52 Week High</Typography>
                      <Typography>₹{fundamentalData['52_week_high']?.toFixed(2) || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2">52 Week Low</Typography>
                      <Typography>₹{fundamentalData['52_week_low']?.toFixed(2) || 'N/A'}</Typography>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setOpenDialog(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
} 