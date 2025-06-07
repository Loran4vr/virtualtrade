import { useState, useEffect } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState(null);
  const [topGainers, setTopGainers] = useState([]);
  const [topLosers, setTopLosers] = useState([]);
  const [marketStatus, setMarketStatus] = useState('closed');
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [pnlData, setPnlData] = useState({
    total: 0,
    winRate: 0,
    avgPL: 0,
    best: 0,
    worst: 0,
    chart: [],
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
      } finally {
        setLoading(false);
      }
    }
    async function fetchTopGainersLosers() {
      try {
        const response = await fetch('/api/market/top-gainers-losers');
        const data = await response.json();
        if (data.top_gainers) setTopGainers(data.top_gainers.slice(0, 5));
        if (data.top_losers) setTopLosers(data.top_losers.slice(0, 5));
      } catch (error) {}
    }
    async function fetchTransactions() {
      try {
        const response = await fetch('/api/portfolio/transactions');
        const data = await response.json();
        setTransactions(data.transactions || []);
      } catch (error) {
        setTransactions([]);
      }
    }
    fetchPortfolio();
    fetchTopGainersLosers();
    fetchTransactions();
    // Simulate Indian market hours (9:15 AM to 3:30 PM, Monday to Friday)
    const now = new Date();
    const hour = now.getHours();
    const day = now.getDay();
    if (day >= 1 && day <= 5 && hour >= 9 && hour < 16) {
      setMarketStatus('open');
    } else {
      setMarketStatus('closed');
    }
  }, []);

  // Compute P&L analytics when transactions change
  useEffect(() => {
    if (!transactions.length) return;
    let realizedPL = 0;
    let wins = 0;
    let losses = 0;
    let best = -Infinity;
    let worst = Infinity;
    let tradePLs = [];
    let chart = [];
    let runningPL = 0;
    transactions.forEach((tx, idx) => {
      // Only count SELL trades for realized P&L
      if (tx.type === 'SELL') {
        // Find the matching buy (for simplicity, assume FIFO)
        const buyTx = transactions.slice(0, idx).reverse().find(b => b.symbol === tx.symbol && b.type === 'BUY');
        if (buyTx) {
          const pl = (tx.price - buyTx.price) * tx.quantity;
          realizedPL += pl;
          tradePLs.push(pl);
          runningPL += pl;
          chart.push({ date: tx.timestamp.split('T')[0], value: runningPL });
          if (pl > 0) wins++;
          if (pl < 0) losses++;
          if (pl > best) best = pl;
          if (pl < worst) worst = pl;
        }
      }
    });
    setPnlData({
      total: realizedPL,
      winRate: tradePLs.length ? (wins / tradePLs.length) * 100 : 0,
      avgPL: tradePLs.length ? (tradePLs.reduce((a, b) => a + b, 0) / tradePLs.length) : 0,
      best: tradePLs.length ? best : 0,
      worst: tradePLs.length ? worst : 0,
      chart: chart.length ? chart : [{ date: '', value: 0 }],
    });
  }, [transactions]);

  // Sample data for the portfolio value chart
  const portfolioChartData = [
    { date: '2023-01-01', value: 1000000 },
    { date: '2023-02-01', value: 1050000 },
    { date: '2023-03-01', value: 1030000 },
    { date: '2023-04-01', value: 1080000 },
    { date: '2023-05-01', value: 1120000 },
    { date: '2023-06-01', value: 1090000 },
    { date: '2023-07-01', value: 1150000 },
  ];

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
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader title="Portfolio Value" subheader="Total value of your portfolio" />
            <CardContent>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                ₹{portfolio?.cash_balance?.toLocaleString() || '0'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Virtual balance for paper trading
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader title="P&L Analytics" subheader="Your realized trading performance" />
            <CardContent>
              <Typography variant="h5" fontWeight={700} color={pnlData.total >= 0 ? 'success.main' : 'error.main'}>
                ₹{pnlData.total.toLocaleString(undefined, { maximumFractionDigits: 2 })}
              </Typography>
              <Typography variant="body2" color="text.secondary">Total Realized P&L</Typography>
              <Divider sx={{ my: 1 }} />
              <Typography variant="body2">Win Rate: {pnlData.winRate.toFixed(1)}%</Typography>
              <Typography variant="body2">Avg P&L: ₹{pnlData.avgPL.toFixed(2)}</Typography>
              <Typography variant="body2">Best Trade: ₹{pnlData.best.toFixed(2)}</Typography>
              <Typography variant="body2">Worst Trade: ₹{pnlData.worst.toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader title="Market Status" subheader="Current market trading status" />
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Chip
                  label={marketStatus === 'open' ? 'Open' : 'Closed'}
                  color={marketStatus === 'open' ? 'success' : 'error'}
                  sx={{ mr: 2 }}
                />
                <Typography variant="h6" fontWeight={500} textTransform="capitalize">
                  {marketStatus}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                {marketStatus === 'open' ? 'Market is currently trading' : 'Market is currently closed'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader title="Holdings" subheader="Number of stocks in your portfolio" />
            <CardContent>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                {Object.keys(portfolio?.holdings || {}).length}
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
            <CardHeader title="Portfolio Performance" subheader="Track your portfolio value over time" />
            <CardContent>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={portfolioChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`₹${value.toLocaleString()}`, 'Value']} />
                    <Line type="monotone" dataKey="value" stroke="#1976d2" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="P&L Over Time" subheader="Cumulative realized P&L" />
            <CardContent>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={pnlData.chart}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`₹${value.toLocaleString()}`, 'P&L']} />
                    <Line type="monotone" dataKey="value" stroke="#43a047" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Top Movers" subheader="Today's top gainers and losers" />
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>Top Gainers</Typography>
              {topGainers.length === 0 ? (
                <Typography variant="body2" color="text.secondary">No data available</Typography>
              ) : (
                topGainers.map((stock, idx) => (
                  <Box key={stock.symbol} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                    <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                    <Typography variant="body2" sx={{ flex: 1 }}>{stock.symbol}</Typography>
                    <Typography variant="body2" color="success.main">+{stock.change_percent}%</Typography>
                  </Box>
                ))
              )}
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>Top Losers</Typography>
              {topLosers.length === 0 ? (
                <Typography variant="body2" color="text.secondary">No data available</Typography>
              ) : (
                topLosers.map((stock, idx) => (
                  <Box key={stock.symbol} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                    <TrendingDownIcon color="error" sx={{ mr: 1 }} />
                    <Typography variant="body2" sx={{ flex: 1 }}>{stock.symbol}</Typography>
                    <Typography variant="body2" color="error.main">{stock.change_percent}%</Typography>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

