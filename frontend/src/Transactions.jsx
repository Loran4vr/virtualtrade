import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { Button } from './button';
import { useToast } from './use-toast';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './dialog';
import { Calendar } from './calendar';
import { Popover, PopoverContent, PopoverTrigger } from './popover';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, ArrowUpRight, ArrowDownRight, Filter } from 'lucide-react';

export default function Transactions() {
  const { toast } = useToast();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [dateRange, setDateRange] = useState({
    from: null,
    to: null,
  });
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  useEffect(() => {
    fetchTransactions();
  }, [dateRange]);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      let url = '/api/portfolio/transactions';
      
      // Add date range filters if set
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
      console.error('Failed to fetch transactions:', error);
      toast({
        title: 'Error',
        description: 'Failed to load transaction history',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setDateRange({
      from: null,
      to: null,
    });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, 'PPP p'); // Format: "Apr 29, 2023, 1:30 PM"
  };

  if (loading && transactions.length === 0) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Transaction History</CardTitle>
              <CardDescription>
                Record of all your trades
              </CardDescription>
            </div>
            <div className="flex space-x-2">
              <Popover open={isCalendarOpen} onOpenChange={setIsCalendarOpen}>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm">
                    <CalendarIcon className="h-4 w-4 mr-2" />
                    {dateRange.from ? (
                      dateRange.to ? (
                        <>
                          {format(dateRange.from, 'LLL dd, y')} - {format(dateRange.to, 'LLL dd, y')}
                        </>
                      ) : (
                        format(dateRange.from, 'LLL dd, y')
                      )
                    ) : (
                      'Date Range'
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="end">
                  <Calendar
                    initialFocus
                    mode="range"
                    defaultMonth={dateRange.from}
                    selected={dateRange}
                    onSelect={(range) => {
                      setDateRange(range);
                      if (range.to) {
                        setIsCalendarOpen(false);
                      }
                    }}
                    numberOfMonths={2}
                  />
                  <div className="flex justify-end gap-2 p-2 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        clearFilters();
                        setIsCalendarOpen(false);
                      }}
                    >
                      Clear
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => {
                        setIsCalendarOpen(false);
                      }}
                    >
                      Apply
                    </Button>
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {transactions.length > 0 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-5 gap-4 text-sm font-medium text-muted-foreground">
                <div>Date</div>
                <div>Type</div>
                <div>Symbol</div>
                <div>Quantity</div>
                <div>Price</div>
              </div>
              {transactions.map((transaction) => (
                <div 
                  key={transaction.id} 
                  className="grid grid-cols-5 gap-4 py-3 border-t cursor-pointer hover:bg-muted"
                  onClick={() => setSelectedTransaction(transaction)}
                >
                  <div>{formatDate(transaction.timestamp)}</div>
                  <div className="flex items-center">
                    {transaction.type === 'BUY' ? (
                      <span className="flex items-center text-green-500">
                        <ArrowUpRight className="h-4 w-4 mr-1" />
                        Buy
                      </span>
                    ) : (
                      <span className="flex items-center text-red-500">
                        <ArrowDownRight className="h-4 w-4 mr-1" />
                        Sell
                      </span>
                    )}
                  </div>
                  <div>{transaction.symbol}</div>
                  <div>{transaction.quantity}</div>
                  <div>₹{transaction.price.toFixed(2)}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground mb-4">No transactions found</p>
              {(dateRange.from || dateRange.to) && (
                <Button variant="outline" onClick={clearFilters}>
                  Clear Filters
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedTransaction && (
        <Dialog open={!!selectedTransaction} onOpenChange={(open) => !open && setSelectedTransaction(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Transaction Details</DialogTitle>
              <DialogDescription>
                {selectedTransaction.type === 'BUY' ? 'Purchase' : 'Sale'} of {selectedTransaction.symbol}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Transaction ID</p>
                  <p className="text-sm font-mono">{selectedTransaction.id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Date & Time</p>
                  <p className="text-sm">{formatDate(selectedTransaction.timestamp)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Type</p>
                  <p className={`text-sm ${selectedTransaction.type === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>
                    {selectedTransaction.type}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Symbol</p>
                  <p className="text-sm">{selectedTransaction.symbol}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Quantity</p>
                  <p className="text-sm">{selectedTransaction.quantity}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Price per Share</p>
                  <p className="text-sm">₹{selectedTransaction.price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Value</p>
                  <p className="text-sm">₹{selectedTransaction.total.toFixed(2)}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedTransaction(null)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

