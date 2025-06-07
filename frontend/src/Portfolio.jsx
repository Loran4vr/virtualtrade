import { useState, useEffect } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { useToast } from './use-toast';
import { ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';
import { Calendar } from './calendar';
import { Popover, PopoverContent, PopoverTrigger } from './popover';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, Filter } from 'lucide-react';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';

export default function Portfolio() {
  const { toast } = useToast();
  const [portfolio, setPortfolio] = useState(null);
  const [holdings, setHoldings] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [sortBy, setSortBy] = useState('symbol_asc');

  // Colors for the pie chart
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#8dd1e1'];

  useEffect(() => {
    fetchPortfolioData();
  }, []);

  const fetchPortfolioData = async () => {
    setLoading(true);
    try {
      // Fetch balance
      const balanceResponse = await fetch('/api/portfolio/balance');
      const balanceData = await balanceResponse.json();
      
      // Fetch holdings
      const holdingsResponse = await fetch('/api/portfolio/holdings');
      const holdingsData = await holdingsResponse.json();
      
      setPortfolio({
        cash_balance: balanceData.cash_balance,
      });
      
      setHoldings(holdingsData.holdings || {});
      
      // If no portfolio exists, initialize one
      if (!balanceData.cash_balance) {
        const initResponse = await fetch('/api/portfolio/initialize', {
          method: 'POST',
        });
        const initData = await initResponse.json();
        setPortfolio({
          cash_balance: initData.portfolio.cash_balance,
        });
      }
    } catch (error) {
      console.error('Failed to fetch portfolio data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load portfolio data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const refreshHoldingPrices = async () => {
    setRefreshing(true);
    try {
      // In a real app, this would update the current market prices of all holdings
      // For this demo, we'll just show a success message
      toast({
        title: 'Prices refreshed',
        description: 'Latest market prices have been fetched',
      });
    } catch (error) {
      console.error('Failed to refresh prices:', error);
      toast({
        title: 'Error',
        description: 'Failed to refresh prices',
        variant: 'destructive',
      });
    } finally {
      setRefreshing(false);
    }
  };

  const resetPortfolio = async () => {
    try {
      const response = await fetch('/api/portfolio/reset', {
        method: 'POST',
      });
      const data = await response.json();
      
      if (response.ok) {
        setPortfolio({
          cash_balance: data.portfolio.cash_balance,
        });
        setHoldings({});
        toast({
          title: 'Portfolio reset',
          description: 'Your portfolio has been reset to initial state',
        });
        setResetDialogOpen(false);
      } else {
        toast({
          title: 'Reset failed',
          description: data.error || 'An error occurred',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Failed to reset portfolio:', error);
      toast({
        title: 'Error',
        description: 'Failed to reset portfolio',
        variant: 'destructive',
      });
    }
  };

  // Calculate total portfolio value
  const calculateTotalValue = () => {
    let totalHoldingsValue = 0;
    
    Object.entries(holdings).forEach(([symbol, holding]) => {
      totalHoldingsValue += holding.quantity * holding.avg_price;
    });
    
    return (portfolio?.cash_balance || 0) + totalHoldingsValue;
  };

  // Prepare data for pie chart
  const preparePieChartData = () => {
    const data = [];
    
    // Add cash
    data.push({
      name: 'Cash',
      value: portfolio?.cash_balance || 0,
    });
    
    // Add holdings
    Object.entries(holdings).forEach(([symbol, holding]) => {
      data.push({
        name: symbol,
        value: holding.quantity * holding.avg_price,
      });
    });
    
    return data;
  };

  // Sorting logic for holdings
  const sortedHoldings = Object.entries(holdings).sort((a, b) => {
    const [symbolA, holdingA] = a;
    const [symbolB, holdingB] = b;
    switch (sortBy) {
      case 'symbol_asc':
        return symbolA.localeCompare(symbolB);
      case 'symbol_desc':
        return symbolB.localeCompare(symbolA);
      case 'qty_asc':
        return holdingA.quantity - holdingB.quantity;
      case 'qty_desc':
        return holdingB.quantity - holdingA.quantity;
      case 'avg_asc':
        return holdingA.avg_price - holdingB.avg_price;
      case 'avg_desc':
        return holdingB.avg_price - holdingA.avg_price;
      case 'val_asc':
        return (holdingA.quantity * holdingA.avg_price) - (holdingB.quantity * holdingB.avg_price);
      case 'val_desc':
        return (holdingB.quantity * holdingB.avg_price) - (holdingA.quantity * holdingA.avg_price);
      default:
        return 0;
    }
  });

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 1, md: 3 } }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Total Portfolio Value" subheader="Cash + Holdings" />
            <CardContent>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                ₹{calculateTotalValue().toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Virtual balance for paper trading
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Cash Balance" subheader="Available for trading" />
            <CardContent>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                ₹{portfolio?.cash_balance?.toLocaleString() || '0'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Funds not invested in stocks
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Holdings" subheader="Number of stocks" />
            <CardContent>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                {Object.keys(holdings).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Different stocks currently held
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader
              title="Holdings Breakdown"
              subheader="Your current stock holdings"
              action={
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel>Sort By</InputLabel>
                  <Select
                    value={sortBy}
                    label="Sort By"
                    onChange={e => setSortBy(e.target.value)}
                  >
                    <MenuItem value="symbol_asc">Symbol (A-Z)</MenuItem>
                    <MenuItem value="symbol_desc">Symbol (Z-A)</MenuItem>
                    <MenuItem value="qty_asc">Quantity (Low-High)</MenuItem>
                    <MenuItem value="qty_desc">Quantity (High-Low)</MenuItem>
                    <MenuItem value="avg_asc">Avg Price (Low-High)</MenuItem>
                    <MenuItem value="avg_desc">Avg Price (High-Low)</MenuItem>
                    <MenuItem value="val_asc">Value (Low-High)</MenuItem>
                    <MenuItem value="val_desc">Value (High-Low)</MenuItem>
                  </Select>
                </FormControl>
              }
            />
            <CardContent>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell align="right">Avg. Price</TableCell>
                      <TableCell align="right">Total Value</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sortedHoldings.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center">No holdings</TableCell>
                      </TableRow>
                    ) : (
                      sortedHoldings.map(([symbol, holding], idx) => (
                        <TableRow key={symbol}>
                          <TableCell>{symbol}</TableCell>
                          <TableCell align="right">{holding.quantity}</TableCell>
                          <TableCell align="right">₹{holding.avg_price.toLocaleString()}</TableCell>
                          <TableCell align="right">₹{(holding.quantity * holding.avg_price).toLocaleString()}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Portfolio Allocation" subheader="Cash vs Stocks" />
            <CardContent>
              <Box sx={{ height: 250 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={preparePieChartData()}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      label
                    >
                      {preparePieChartData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button variant="contained" color="primary" onClick={fetchPortfolioData}>
          Refresh
        </Button>
        <Button variant="outlined" color="error" onClick={() => setResetDialogOpen(true)}>
          Reset Portfolio
        </Button>
      </Box>

      <Dialog open={resetDialogOpen} onClose={() => setResetDialogOpen(false)}>
        <DialogTitle>Reset Portfolio</DialogTitle>
        <DialogContent>
          <Typography>Are you sure you want to reset your portfolio? This action cannot be undone.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>Cancel</Button>
          <Button color="error" onClick={resetPortfolio}>Reset</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

