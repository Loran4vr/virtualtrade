import React, { useState, useEffect } from 'react';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select
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

export default function FuturesOptions() {
  const [activeTab, setActiveTab] = useState(0);
  const [futures, setFutures] = useState([]);
  const [options, setOptions] = useState({ calls: [], puts: [] });
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [futuresChain, setFuturesChain] = useState([]);
  const [optionsChain, setOptionsChain] = useState(null);
  const [loading, setLoading] = useState(false);
  const [openOrderDialog, setOpenOrderDialog] = useState(false);
  const [orderType, setOrderType] = useState('futures');
  const [orderData, setOrderData] = useState({
    symbol: '',
    expiry: '',
    strike: '',
    option_type: 'CE',
    quantity: '',
    order_type: 'MARKET',
    price: ''
  });

  useEffect(() => {
    fetchFuturesAndOptions();
  }, []);

  const fetchFuturesAndOptions = async () => {
    setLoading(true);
    try {
      const [futuresRes, optionsRes] = await Promise.all([
        fetch('/api/futures'),
        fetch('/api/options')
      ]);
      
      if (futuresRes.ok) {
        setFutures(await futuresRes.json());
      }
      if (optionsRes.ok) {
        setOptions(await optionsRes.json());
      }
    } catch (error) {
      console.error('Error fetching F&O data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolSelect = async (symbol) => {
    setSelectedSymbol(symbol);
    setLoading(true);
    try {
      const [futuresChainRes, optionsChainRes] = await Promise.all([
        fetch(`/api/futures/chain/${symbol}`),
        fetch(`/api/options/chain/${symbol}`)
      ]);
      
      if (futuresChainRes.ok) {
        setFuturesChain(await futuresChainRes.json());
      }
      if (optionsChainRes.ok) {
        setOptionsChain(await optionsChainRes.json());
      }
    } catch (error) {
      console.error('Error fetching chains:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOrderClick = (type, data) => {
    setOrderType(type);
    setOrderData({
      ...orderData,
      symbol: selectedSymbol,
      ...data
    });
    setOpenOrderDialog(true);
  };

  const handleOrderSubmit = async () => {
    try {
      const endpoint = orderType === 'futures' ? '/api/futures/place-order' : '/api/options/place-order';
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Order placed:', result);
        setOpenOrderDialog(false);
        // Refresh data
        fetchFuturesAndOptions();
      }
    } catch (error) {
      console.error('Error placing order:', error);
    }
  };

  const renderFuturesTable = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Expiry</TableCell>
            <TableCell>Last Price</TableCell>
            <TableCell>Change</TableCell>
            <TableCell>OI</TableCell>
            <TableCell>Volume</TableCell>
            <TableCell>Action</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {futures.map((future) => (
            <TableRow key={`${future.symbol}-${future.expiry}`}>
              <TableCell>{future.symbol}</TableCell>
              <TableCell>{future.expiry}</TableCell>
              <TableCell>₹{future.last_price.toFixed(2)}</TableCell>
              <TableCell>
                <Chip
                  label={`${future.change > 0 ? '+' : ''}${future.change.toFixed(2)}%`}
                  color={future.change >= 0 ? 'success' : 'error'}
                  size="small"
                />
              </TableCell>
              <TableCell>{future.oi.toLocaleString()}</TableCell>
              <TableCell>{future.volume.toLocaleString()}</TableCell>
              <TableCell>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => handleOrderClick('futures', {
                    expiry: future.expiry,
                    price: future.last_price
                  })}
                >
                  Trade
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderOptionsTable = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Type</TableCell>
            <TableCell>Symbol</TableCell>
            <TableCell>Strike</TableCell>
            <TableCell>Expiry</TableCell>
            <TableCell>Last Price</TableCell>
            <TableCell>Change</TableCell>
            <TableCell>OI</TableCell>
            <TableCell>IV</TableCell>
            <TableCell>Action</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {[...options.calls, ...options.puts].map((option) => (
            <TableRow key={`${option.symbol}-${option.strike}-${option.expiry}`}>
              <TableCell>{option.symbol.includes('CE') ? 'Call' : 'Put'}</TableCell>
              <TableCell>{option.symbol}</TableCell>
              <TableCell>₹{option.strike.toFixed(2)}</TableCell>
              <TableCell>{option.expiry}</TableCell>
              <TableCell>₹{option.last_price.toFixed(2)}</TableCell>
              <TableCell>
                <Chip
                  label={`${option.change > 0 ? '+' : ''}${option.change.toFixed(2)}%`}
                  color={option.change >= 0 ? 'success' : 'error'}
                  size="small"
                />
              </TableCell>
              <TableCell>{option.oi.toLocaleString()}</TableCell>
              <TableCell>{(option.implied_volatility * 100).toFixed(2)}%</TableCell>
              <TableCell>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => handleOrderClick('options', {
                    expiry: option.expiry,
                    strike: option.strike,
                    option_type: option.symbol.includes('CE') ? 'CE' : 'PE',
                    price: option.last_price
                  })}
                >
                  Trade
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box sx={{ p: 2 }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="Futures" />
            <Tab label="Options" />
          </Tabs>
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box sx={{ mt: 2 }}>
              {activeTab === 0 ? renderFuturesTable() : renderOptionsTable()}
            </Box>
          )}
        </CardContent>
      </Card>

      <Dialog open={openOrderDialog} onClose={() => setOpenOrderDialog(false)}>
        <DialogTitle>
          Place {orderType === 'futures' ? 'Futures' : 'Options'} Order
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Symbol"
                value={orderData.symbol}
                disabled
              />
            </Grid>
            {orderType === 'options' && (
              <>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Strike Price"
                    value={orderData.strike}
                    disabled
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>Option Type</InputLabel>
                    <Select
                      value={orderData.option_type}
                      onChange={(e) => setOrderData({ ...orderData, option_type: e.target.value })}
                    >
                      <MenuItem value="CE">Call</MenuItem>
                      <MenuItem value="PE">Put</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </>
            )}
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Expiry"
                value={orderData.expiry}
                disabled
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Order Type</InputLabel>
                <Select
                  value={orderData.order_type}
                  onChange={(e) => setOrderData({ ...orderData, order_type: e.target.value })}
                >
                  <MenuItem value="MARKET">Market</MenuItem>
                  <MenuItem value="LIMIT">Limit</MenuItem>
                  <MenuItem value="SL">Stop Loss</MenuItem>
                  <MenuItem value="SL-M">Stop Loss Market</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={orderData.quantity}
                onChange={(e) => setOrderData({ ...orderData, quantity: e.target.value })}
              />
            </Grid>
            {orderData.order_type !== 'MARKET' && (
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Price"
                  type="number"
                  value={orderData.price}
                  onChange={(e) => setOrderData({ ...orderData, price: e.target.value })}
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenOrderDialog(false)}>Cancel</Button>
          <Button onClick={handleOrderSubmit} variant="contained">
            Place Order
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 