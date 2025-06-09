import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
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
  Tabs,
  Tab,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon
} from '@mui/icons-material';
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

const Portfolio = React.memo(() => {
  const [activeTab, setActiveTab] = useState(0);
  const [holdings, setHoldings] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [activeOrders, setActiveOrders] = useState([]);
  const [orderHistory, setOrderHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [openWatchlistDialog, setOpenWatchlistDialog] = useState(false);
  const [newSymbol, setNewSymbol] = useState('');

  const fetchPortfolioData = useCallback(async () => {
    setLoading(true);
    try {
      const [
        holdingsRes,
        transactionsRes,
        watchlistRes,
        activeOrdersRes,
        orderHistoryRes
      ] = await Promise.all([
        fetch('/api/portfolio/holdings'),
        fetch('/api/portfolio/transactions'),
        fetch('/api/portfolio/watchlist'),
        fetch('/api/orders/active'),
        fetch('/api/orders/history')
      ]);
      
      if (holdingsRes.ok) setHoldings(await holdingsRes.json());
      if (transactionsRes.ok) setTransactions(await transactionsRes.json());
      if (watchlistRes.ok) setWatchlist(await watchlistRes.json());
      if (activeOrdersRes.ok) setActiveOrders(await activeOrdersRes.json());
      if (orderHistoryRes.ok) setOrderHistory(await orderHistoryRes.json());
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPortfolioData();
  }, [fetchPortfolioData]);

  const handleAddToWatchlist = useCallback(async () => {
    try {
      const response = await fetch('/api/portfolio/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ symbol: newSymbol })
      });
      
      if (response.ok) {
        setOpenWatchlistDialog(false);
        setNewSymbol('');
        fetchPortfolioData();
      }
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    }
  }, [newSymbol, fetchPortfolioData]);

  const handleRemoveFromWatchlist = useCallback(async (symbol) => {
    try {
      const response = await fetch(`/api/portfolio/watchlist/${symbol}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        fetchPortfolioData();
      }
    } catch (error) {
      console.error('Error removing from watchlist:', error);
    }
  }, [fetchPortfolioData]);

  const handleModifyOrder = useCallback(async (orderId, newData) => {
    try {
      const response = await fetch(`/api/orders/${orderId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newData)
      });
      
      if (response.ok) {
        fetchPortfolioData();
      }
    } catch (error) {
      console.error('Error modifying order:', error);
    }
  }, [fetchPortfolioData]);

  const handleCancelOrder = useCallback(async (orderId) => {
    try {
      const response = await fetch(`/api/orders/${orderId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        fetchPortfolioData();
      }
    } catch (error) {
      console.error('Error cancelling order:', error);
    }
  }, [fetchPortfolioData]);

  const renderHoldingsTable = useMemo(() => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Quantity</TableCell>
            <TableCell>Avg Price</TableCell>
            <TableCell>Current Price</TableCell>
            <TableCell>Value</TableCell>
            <TableCell>P&L</TableCell>
            <TableCell>P&L %</TableCell>
            <TableCell>Type</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {holdings.map((holding) => (
            <TableRow key={`${holding.symbol}-${holding.type}`}>
              <TableCell>{holding.symbol}</TableCell>
              <TableCell>{holding.quantity}</TableCell>
              <TableCell>₹{holding.average_price.toFixed(2)}</TableCell>
              <TableCell>₹{holding.current_price.toFixed(2)}</TableCell>
              <TableCell>₹{holding.value.toFixed(2)}</TableCell>
              <TableCell>
                <Chip
                  label={`₹${holding.pnl.toFixed(2)}`}
                  color={holding.pnl >= 0 ? 'success' : 'error'}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip
                  label={`${holding.pnl_percentage.toFixed(2)}%`}
                  color={holding.pnl_percentage >= 0 ? 'success' : 'error'}
                  size="small"
                />
              </TableCell>
              <TableCell>{holding.type}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  ), [holdings]);

  const renderTransactionsTable = useMemo(() => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Quantity</TableCell>
            <TableCell>Price</TableCell>
            <TableCell>Value</TableCell>
            <TableCell>Order Type</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Timestamp</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {transactions.map((transaction) => (
            <TableRow key={transaction.id}>
              <TableCell>{transaction.symbol}</TableCell>
              <TableCell>
                <Chip
                  label={transaction.type}
                  color={transaction.type === 'BUY' ? 'success' : 'error'}
                  size="small"
                />
              </TableCell>
              <TableCell>{transaction.quantity}</TableCell>
              <TableCell>₹{transaction.price.toFixed(2)}</TableCell>
              <TableCell>₹{transaction.value.toFixed(2)}</TableCell>
              <TableCell>{transaction.order_type}</TableCell>
              <TableCell>{transaction.status}</TableCell>
              <TableCell>{new Date(transaction.timestamp).toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  ), [transactions]);

  const renderWatchlistTable = useMemo(() => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>Last Price</TableCell>
            <TableCell>Change</TableCell>
            <TableCell>Volume</TableCell>
            <TableCell>Market Cap</TableCell>
            <TableCell>Action</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {watchlist.map((item) => (
            <TableRow key={item.symbol}>
              <TableCell>{item.symbol}</TableCell>
              <TableCell>{item.name}</TableCell>
              <TableCell>₹{item.last_price.toFixed(2)}</TableCell>
              <TableCell>
                <Chip
                  label={`${item.change > 0 ? '+' : ''}${item.change.toFixed(2)}%`}
                  color={item.change >= 0 ? 'success' : 'error'}
                  size="small"
                />
              </TableCell>
              <TableCell>{item.volume.toLocaleString()}</TableCell>
              <TableCell>₹{(item.market_cap / 10000000).toFixed(2)} Cr</TableCell>
              <TableCell>
                <IconButton
                  size="small"
                  onClick={() => handleRemoveFromWatchlist(item.symbol)}
                >
                  <DeleteIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  ), [watchlist, handleRemoveFromWatchlist]);

  const renderActiveOrdersTable = useMemo(() => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Quantity</TableCell>
            <TableCell>Price</TableCell>
            <TableCell>Order Type</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Timestamp</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {activeOrders.map((order) => (
            <TableRow key={order.id}>
              <TableCell>{order.symbol}</TableCell>
              <TableCell>
                <Chip
                  label={order.type}
                  color={order.type === 'BUY' ? 'success' : 'error'}
                  size="small"
                />
              </TableCell>
              <TableCell>{order.quantity}</TableCell>
              <TableCell>₹{order.price.toFixed(2)}</TableCell>
              <TableCell>{order.order_type}</TableCell>
              <TableCell>{order.status}</TableCell>
              <TableCell>{new Date(order.timestamp).toLocaleString()}</TableCell>
              <TableCell>
                <IconButton
                  size="small"
                  onClick={() => handleModifyOrder(order.id, { price: order.price + 1 })}
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => handleCancelOrder(order.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  ), [activeOrders, handleModifyOrder, handleCancelOrder]);

  return (
    <Box sx={{ p: 2 }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="Holdings" />
            <Tab label="Transactions" />
            <Tab label="Watchlist" />
            <Tab label="Active Orders" />
          </Tabs>
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box sx={{ mt: 2 }}>
              {activeTab === 0 && renderHoldingsTable}
              {activeTab === 1 && renderTransactionsTable}
              {activeTab === 2 && (
                <>
                  <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => setOpenWatchlistDialog(true)}
                    >
                      Add to Watchlist
                    </Button>
                  </Box>
                  {renderWatchlistTable}
                </>
              )}
              {activeTab === 3 && renderActiveOrdersTable}
            </Box>
          )}
        </CardContent>
      </Card>

      <Dialog open={openWatchlistDialog} onClose={() => setOpenWatchlistDialog(false)}>
        <DialogTitle>Add to Watchlist</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Symbol"
            fullWidth
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenWatchlistDialog(false)}>Cancel</Button>
          <Button onClick={handleAddToWatchlist} variant="contained">
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
});

Portfolio.displayName = 'Portfolio';

export default Portfolio; 