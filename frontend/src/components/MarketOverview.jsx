import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

export default function MarketOverview() {
  const [indices, setIndices] = useState({});
  const [sectors, setSectors] = useState({});
  const [mostActive, setMostActive] = useState({ gainers: [], losers: [], most_active: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [indicesRes, sectorsRes, mostActiveRes] = await Promise.all([
          fetch('/api/market/indices'),
          fetch('/api/market/sectors'),
          fetch('/api/market/most-active')
        ]);

        if (indicesRes.ok) setIndices(await indicesRes.json());
        if (sectorsRes.ok) setSectors(await sectorsRes.json());
        if (mostActiveRes.ok) setMostActive(await mostActiveRes.json());
      } catch (error) {
        console.error('Error fetching market data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, []);

  const renderChange = (change, percent) => {
    const isPositive = change >= 0;
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', color: isPositive ? 'success.main' : 'error.main' }}>
        {isPositive ? <TrendingUpIcon /> : <TrendingDownIcon />}
        <Typography variant="body2" sx={{ ml: 0.5 }}>
          {change.toFixed(2)} ({percent}%)
        </Typography>
      </Box>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Grid container spacing={3}>
        {/* Market Indices */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Market Indices" />
            <CardContent>
              <Grid container spacing={2}>
                {Object.entries(indices).map(([name, data]) => (
                  <Grid item xs={12} sm={6} md={4} key={name}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {name}
                        </Typography>
                        <Typography variant="h5" gutterBottom>
                          {data.price.toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}
                        </Typography>
                        {renderChange(data.change, data.change_percent)}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Sector Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Sector Performance" />
            <CardContent>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Sector</TableCell>
                      <TableCell align="right">Change</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(sectors).map(([sector, data]) => (
                      <TableRow key={sector}>
                        <TableCell>{sector}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`${data.change_percent}%`}
                            color={data.change_percent >= 0 ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Most Active Stocks */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Most Active Stocks" />
            <CardContent>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell align="right">Change</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mostActive.most_active.map((stock) => (
                      <TableRow key={stock.symbol}>
                        <TableCell>{stock.symbol}</TableCell>
                        <TableCell align="right">
                          {parseFloat(stock.price).toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}
                        </TableCell>
                        <TableCell align="right">
                          {renderChange(parseFloat(stock.change), stock.change_percent)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
} 