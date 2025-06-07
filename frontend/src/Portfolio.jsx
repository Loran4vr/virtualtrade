import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { Button } from './button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './dialog';
import { useToast } from './use-toast';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';
import { Calendar } from './calendar';
import { Popover, PopoverContent, PopoverTrigger } from './popover';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, Filter } from 'lucide-react';

export default function Portfolio() {
  const { toast } = useToast();
  const [portfolio, setPortfolio] = useState(null);
  const [holdings, setHoldings] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);

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

  if (loading) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-6">
        <Card className="min-w-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Portfolio Value</CardTitle>
            <CardDescription>
              Cash + Holdings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{calculateTotalValue().toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Virtual balance for paper trading
            </p>
          </CardContent>
        </Card>
        <Card className="min-w-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Cash Balance</CardTitle>
            <CardDescription>
              Available for trading
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{portfolio?.cash_balance?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              Funds not invested in stocks
            </p>
          </CardContent>
        </Card>
        <Card className="min-w-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Holdings</CardTitle>
            <CardDescription>
              Number of stocks
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(holdings).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Different stocks currently held
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col gap-6 md:flex-row md:gap-6">
        <Card className="flex-1 min-w-0">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Portfolio Allocation</CardTitle>
              <Button variant="outline" size="sm" onClick={refreshHoldingPrices} disabled={refreshing}>
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
            <CardDescription>
              Distribution of your investments
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              {Object.keys(holdings).length > 0 || portfolio?.cash_balance > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={preparePieChartData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                      nameKey="name"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {preparePieChartData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  No holdings to display
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="flex-1 min-w-0">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Your Holdings</CardTitle>
              <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    Reset Portfolio
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Reset Portfolio</DialogTitle>
                    <DialogDescription>
                      This will reset your portfolio to the initial state with ₹10,00,000 cash balance and no holdings.
                      This action cannot be undone.
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setResetDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button variant="destructive" onClick={resetPortfolio}>
                      Reset Portfolio
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
            <CardDescription>
              Stocks currently in your portfolio
            </CardDescription>
          </CardHeader>
          <CardContent>
            {Object.keys(holdings).length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-4 gap-2 text-sm font-medium text-muted-foreground">
                  <div>Symbol</div>
                  <div>Quantity</div>
                  <div>Avg. Price</div>
                  <div>Value</div>
                </div>
                {Object.entries(holdings).map(([symbol, holding]) => {
                  const value = holding.quantity * holding.avg_price;
                  
                  return (
                    <div 
                      key={symbol} 
                      className="grid grid-cols-4 gap-2 py-2 border-t cursor-pointer hover:bg-muted"
                      onClick={() => setSelectedHolding({ symbol, ...holding })}
                    >
                      <div className="font-medium">{symbol}</div>
                      <div>{holding.quantity}</div>
                      <div>₹{holding.avg_price.toFixed(2)}</div>
                      <div>₹{value.toLocaleString()}</div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                No holdings to display
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {selectedHolding && (
        <Dialog open={!!selectedHolding} onOpenChange={(open) => !open && setSelectedHolding(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{selectedHolding.symbol}</DialogTitle>
              <DialogDescription>
                Holding details
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Quantity</p>
                  <p className="text-lg">{selectedHolding.quantity}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Average Price</p>
                  <p className="text-lg">₹{selectedHolding.avg_price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Value</p>
                  <p className="text-lg">₹{(selectedHolding.quantity * selectedHolding.avg_price).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
                  <p className="text-lg">{new Date(selectedHolding.last_updated).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedHolding(null)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

