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
import { format } from 'date-fns';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import TextField from '@mui/material/TextField';

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [sortBy, setSortBy] = useState('date_desc');
  const [notes, setNotes] = useState(() => {
    const saved = localStorage.getItem('tradeNotes');
    return saved ? JSON.parse(saved) : {};
  });

  useEffect(() => {
    fetchTransactions();
    // eslint-disable-next-line
  }, [dateRange]);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      let url = '/api/portfolio/transactions';
      const params = new URLSearchParams();
      if (dateRange.from) {
        params.append('start_date', format(dateRange.from, 'yyyy-MM-dd'));
      }
      if (dateRange.to) {
        params.append('end_date', format(dateRange.to, 'yyyy-MM-dd'));
      }
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      const response = await fetch(url);
      const data = await response.json();
      setTransactions(data.transactions || []);
    } catch (error) {
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setDateRange({ from: null, to: null });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, 'PPP p');
  };

  // Sorting logic
  const sortedTransactions = [...transactions].sort((a, b) => {
    switch (sortBy) {
      case 'date_asc':
        return new Date(a.timestamp) - new Date(b.timestamp);
      case 'date_desc':
        return new Date(b.timestamp) - new Date(a.timestamp);
      case 'symbol_asc':
        return a.symbol.localeCompare(b.symbol);
      case 'symbol_desc':
        return b.symbol.localeCompare(a.symbol);
      case 'type_asc':
        return a.type.localeCompare(b.type);
      case 'type_desc':
        return b.type.localeCompare(a.type);
      case 'qty_asc':
        return a.quantity - b.quantity;
      case 'qty_desc':
        return b.quantity - a.quantity;
      case 'price_asc':
        return a.price - b.price;
      case 'price_desc':
        return b.price - a.price;
      default:
        return 0;
    }
  });

  const handleNoteChange = (id, value) => {
    const updated = { ...notes, [id]: value };
    setNotes(updated);
    localStorage.setItem('tradeNotes', JSON.stringify(updated));
  };

  return (
    <Box sx={{ p: { xs: 1, md: 3 } }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="Transaction History"
              subheader="Record of all your trades"
              action={
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <FormControl size="small" sx={{ minWidth: 160 }}>
                    <InputLabel>Sort By</InputLabel>
                    <Select
                      value={sortBy}
                      label="Sort By"
                      onChange={e => setSortBy(e.target.value)}
                    >
                      <MenuItem value="date_desc">Date (Newest)</MenuItem>
                      <MenuItem value="date_asc">Date (Oldest)</MenuItem>
                      <MenuItem value="symbol_asc">Symbol (A-Z)</MenuItem>
                      <MenuItem value="symbol_desc">Symbol (Z-A)</MenuItem>
                      <MenuItem value="type_asc">Type (A-Z)</MenuItem>
                      <MenuItem value="type_desc">Type (Z-A)</MenuItem>
                      <MenuItem value="qty_asc">Quantity (Low-High)</MenuItem>
                      <MenuItem value="qty_desc">Quantity (High-Low)</MenuItem>
                      <MenuItem value="price_asc">Price (Low-High)</MenuItem>
                      <MenuItem value="price_desc">Price (High-Low)</MenuItem>
                    </Select>
                  </FormControl>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setDateRange({ from: null, to: null })}
                    disabled={!dateRange.from && !dateRange.to}
                  >
                    Clear Filters
                  </Button>
                </Box>
              }
            />
            <CardContent>
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
                  <CircularProgress />
                </Box>
              ) : sortedTransactions.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Symbol</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell align="right">Price</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {sortedTransactions.map((transaction) => (
                        <TableRow
                          key={transaction.id}
                          hover
                          onClick={() => setSelectedTransaction(transaction)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell>{formatDate(transaction.timestamp)}</TableCell>
                          <TableCell>
                            <Typography color={transaction.type === 'BUY' ? 'success.main' : 'error.main'} fontWeight={500}>
                              {transaction.type === 'BUY' ? 'Buy' : 'Sell'}
                            </Typography>
                          </TableCell>
                          <TableCell>{transaction.symbol}</TableCell>
                          <TableCell align="right">{transaction.quantity}</TableCell>
                          <TableCell align="right">₹{transaction.price.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 6 }}>
                  <Typography color="text.secondary" sx={{ mb: 2 }}>
                    No transactions found
                  </Typography>
                  {(dateRange.from || dateRange.to) && (
                    <Button variant="outlined" onClick={clearFilters}>
                      Clear Filters
                    </Button>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Transaction Details Dialog */}
      <Dialog open={!!selectedTransaction} onClose={() => setSelectedTransaction(null)}>
        <DialogTitle>Transaction Details</DialogTitle>
        <DialogContent>
          {selectedTransaction && (
            <Box sx={{ py: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                {selectedTransaction.type === 'BUY' ? 'Purchase' : 'Sale'} of {selectedTransaction.symbol}
              </Typography>
              <Typography>Date: {formatDate(selectedTransaction.timestamp)}</Typography>
              <Typography>Quantity: {selectedTransaction.quantity}</Typography>
              <Typography>Price: ₹{selectedTransaction.price.toFixed(2)}</Typography>
              <Typography>Total: ₹{(selectedTransaction.price * selectedTransaction.quantity).toFixed(2)}</Typography>
              <TextField
                label="Trade Journal / Notes"
                multiline
                minRows={2}
                fullWidth
                value={notes[selectedTransaction.id] || ''}
                onChange={e => handleNoteChange(selectedTransaction.id, e.target.value)}
                sx={{ mt: 2 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedTransaction(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

