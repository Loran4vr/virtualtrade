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
  CircularProgress
} from '@mui/material';

export default function MarketDepth({ symbol }) {
  const [marketDepth, setMarketDepth] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (symbol) {
      fetchMarketDepth();
      const interval = setInterval(fetchMarketDepth, 5000); // Update every 5 seconds
      return () => clearInterval(interval);
    }
  }, [symbol]);

  const fetchMarketDepth = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/market/depth/${symbol}`);
      if (response.ok) {
        const data = await response.json();
        setMarketDepth(data);
      }
    } catch (error) {
      console.error('Error fetching market depth:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderOrderBook = () => {
    if (!marketDepth) return null;

    const { bids, asks, last_price } = marketDepth;

    return (
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6" color="error" gutterBottom>
            Sell Orders
          </Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Price</TableCell>
                  <TableCell>Quantity</TableCell>
                  <TableCell>Total</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {asks.map((ask, index) => {
                  const total = asks
                    .slice(0, index + 1)
                    .reduce((sum, a) => sum + a.quantity, 0);
                  return (
                    <TableRow key={ask.price}>
                      <TableCell sx={{ color: 'error.main' }}>
                        ₹{ask.price.toFixed(2)}
                      </TableCell>
                      <TableCell>{ask.quantity}</TableCell>
                      <TableCell>{total}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        <Grid item xs={12} md={6}>
          <Typography variant="h6" color="success.main" gutterBottom>
            Buy Orders
          </Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Price</TableCell>
                  <TableCell>Quantity</TableCell>
                  <TableCell>Total</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {bids.map((bid, index) => {
                  const total = bids
                    .slice(0, index + 1)
                    .reduce((sum, b) => sum + b.quantity, 0);
                  return (
                    <TableRow key={bid.price}>
                      <TableCell sx={{ color: 'success.main' }}>
                        ₹{bid.price.toFixed(2)}
                      </TableCell>
                      <TableCell>{bid.quantity}</TableCell>
                      <TableCell>{total}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        <Grid item xs={12}>
          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Typography variant="h6">
              Last Price: ₹{last_price.toFixed(2)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Spread: ₹{(asks[0].price - bids[0].price).toFixed(2)}
            </Typography>
          </Box>
        </Grid>
      </Grid>
    );
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Market Depth - {symbol}
        </Typography>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          renderOrderBook()
        )}
      </CardContent>
    </Card>
  );
} 