import { useState, useEffect } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import IconButton from '@mui/material/IconButton';

export default function Market() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [stockData, setStockData] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [tradeType, setTradeType] = useState('buy');
  const [portfolio, setPortfolio] = useState(null);
  const [tradeDialogOpen, setTradeDialogOpen] = useState(false);
  const [watchlist, setWatchlist] = useState(() => {
    const saved = localStorage.getItem('watchlist');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    async function fetchPortfolio() {
      try {
        const balanceResponse = await fetch('/api/portfolio/balance');
        const holdingsResponse = await fetch('/api/portfolio/holdings');
        if (balanceResponse.ok && holdingsResponse.ok) {
          const balanceData = await balanceResponse.json();
          const holdingsData = await holdingsResponse.json();
          setPortfolio({
            cash_balance: balanceData.cash_balance,
            holdings: holdingsData.holdings,
          });
        }
      } catch (error) {
        // Handle error
      }
    }
    fetchPortfolio();
  }, []);

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      console.log('Searching for:', searchQuery);
      const response = await fetch(`/api/market/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      console.log('Search results:', data);
      if (Array.isArray(data)) {
        setSearchResults(data);
      } else {
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Error searching stocks:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // Handle stock selection
  const handleSelectStock = async (stock) => {
    setSelectedStock(stock);
    setLoading(true);
    setTradeDialogOpen(true);
    try {
      const symbol = stock['1. symbol'];
      const response = await fetch(`/api/market/daily?symbol=${encodeURIComponent(symbol)}`);
      const data = await response.json();
      if (data['Time Series (Daily)']) {
        const timeSeriesData = data['Time Series (Daily)'];
        const chartData = Object.keys(timeSeriesData)
          .slice(0, 30)
          .reverse()
          .map(date => ({
            date,
            close: parseFloat(timeSeriesData[date]['4. close']),
            open: parseFloat(timeSeriesData[date]['1. open']),
            high: parseFloat(timeSeriesData[date]['2. high']),
            low: parseFloat(timeSeriesData[date]['3. low']),
            volume: parseFloat(timeSeriesData[date]['5. volume']),
          }));
        setStockData({
          meta: data['Meta Data'],
          chartData,
          latestPrice: chartData[chartData.length - 1].close,
          change: chartData[chartData.length - 1].close - chartData[chartData.length - 2].close,
          changePercent: ((chartData[chartData.length - 1].close - chartData[chartData.length - 2].close) / chartData[chartData.length - 2].close) * 100,
        });
      } else {
        setStockData(null);
      }
    } catch (error) {
      setStockData(null);
    } finally {
      setLoading(false);
    }
  };

  // Handle trade execution
  const executeTrade = async () => {
    if (!selectedStock || !stockData) return;
    const symbol = selectedStock['1. symbol'];
    const price = stockData.latestPrice;
    try {
      const endpoint = tradeType === 'buy' ? '/api/portfolio/buy' : '/api/portfolio/sell';
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, quantity: parseInt(quantity), price }),
      });
      const data = await response.json();
      if (response.ok) {
        // Update portfolio data
        const balanceResponse = await fetch('/api/portfolio/balance');
        const holdingsResponse = await fetch('/api/portfolio/holdings');
        if (balanceResponse.ok && holdingsResponse.ok) {
          const balanceData = await balanceResponse.json();
          const holdingsData = await holdingsResponse.json();
          setPortfolio({
            cash_balance: balanceData.cash_balance,
            holdings: holdingsData.holdings,
          });
        }
        setTradeDialogOpen(false);
      }
    } catch (error) {}
  };

  // Watchlist handlers
  const addToWatchlist = (symbol) => {
    if (!watchlist.includes(symbol)) {
      const updated = [...watchlist, symbol];
      setWatchlist(updated);
      localStorage.setItem('watchlist', JSON.stringify(updated));
    }
  };
  const removeFromWatchlist = (symbol) => {
    const updated = watchlist.filter((s) => s !== symbol);
    setWatchlist(updated);
    localStorage.setItem('watchlist', JSON.stringify(updated));
  };
  const isInWatchlist = (symbol) => watchlist.includes(symbol);

  const handleViewStock = async (stock) => {
    setSelectedStock(stock);
    setLoading(true);
    try {
      const response = await fetch(`/api/market/stock/${stock['1. symbol']}`);
      const data = await response.json();
      setStockData(data);
    } catch (error) {
      console.error('Error fetching stock data:', error);
      setStockData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: { xs: 1, md: 3 } }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader title="Market Search" subheader="Search for stocks to trade" />
            <CardContent>
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                  label="Search Stocks"
                  variant="outlined"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  fullWidth
                  onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
                />
                <Button variant="contained" onClick={handleSearch} disabled={searchLoading}>
                  {searchLoading ? <CircularProgress size={24} /> : 'Search'}
                </Button>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Region</TableCell>
                      <TableCell align="right">Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.map((stock) => (
                      <TableRow key={stock['1. symbol']} hover>
                        <TableCell>{stock['1. symbol']}</TableCell>
                        <TableCell>{stock['2. name']}</TableCell>
                        <TableCell>{stock['3. type']}</TableCell>
                        <TableCell>{stock['4. region']}</TableCell>
                        <TableCell align="right">
                          <Button variant="outlined" size="small" onClick={() => handleSelectStock(stock)}>
                            View
                          </Button>
                          <IconButton onClick={() => isInWatchlist(stock['1. symbol']) ? removeFromWatchlist(stock['1. symbol']) : addToWatchlist(stock['1. symbol'])}>
                            {isInWatchlist(stock['1. symbol']) ? <StarIcon color="warning" /> : <StarBorderIcon />}
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Portfolio Snapshot" subheader="Your current balance and holdings" />
            <CardContent>
              <Typography variant="h6">Balance: ₹{portfolio?.cash_balance?.toLocaleString() || '0'}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Holdings: {Object.keys(portfolio?.holdings || {}).length}
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell align="right">Qty</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(portfolio?.holdings || {}).map(([symbol, qty]) => (
                    <TableRow key={symbol}>
                      <TableCell>{symbol}</TableCell>
                      <TableCell align="right">{qty}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
          <Card sx={{ mt: 3 }}>
            <CardHeader title="Watchlist" subheader="Your favorite stocks" />
            <CardContent>
              {watchlist.length === 0 ? (
                <Typography color="text.secondary">No stocks in watchlist</Typography>
              ) : (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell align="right">Remove</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {watchlist.map((symbol) => (
                      <TableRow key={symbol}>
                        <TableCell>{symbol}</TableCell>
                        <TableCell align="right">
                          <Button size="small" onClick={() => removeFromWatchlist(symbol)}>
                            Remove
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Stock Details Dialog */}
      <Dialog open={tradeDialogOpen} onClose={() => setTradeDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Stock Details</DialogTitle>
        <DialogContent>
          {loading || !stockData ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box>
              <Typography variant="h6" gutterBottom>{selectedStock['2. name']} ({selectedStock['1. symbol']})</Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Latest Price: ₹{stockData.latestPrice} &nbsp;
                {stockData.change >= 0 ? (
                  <Chip icon={<TrendingUpIcon />} label={`+${stockData.change.toFixed(2)} (${stockData.changePercent.toFixed(2)}%)`} color="success" size="small" />
                ) : (
                  <Chip icon={<TrendingDownIcon />} label={`${stockData.change.toFixed(2)} (${stockData.changePercent.toFixed(2)}%)`} color="error" size="small" />
                )}
              </Typography>
              <Box sx={{ height: 200, my: 2 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={stockData.chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" hide />
                    <YAxis />
                    <Tooltip formatter={(value) => [`₹${value.toLocaleString()}`, 'Close']} />
                    <Line type="monotone" dataKey="close" stroke="#1976d2" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2 }}>
                <TextField
                  label="Quantity"
                  type="number"
                  value={quantity}
                  onChange={e => setQuantity(e.target.value)}
                  size="small"
                  sx={{ width: 120 }}
                  inputProps={{ min: 1 }}
                />
                <Button variant={tradeType === 'buy' ? 'contained' : 'outlined'} color="primary" onClick={() => { setTradeType('buy'); executeTrade(); }}>
                  Buy
                </Button>
                <Button variant={tradeType === 'sell' ? 'contained' : 'outlined'} color="secondary" onClick={() => { setTradeType('sell'); executeTrade(); }}>
                  Sell
                </Button>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTradeDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

