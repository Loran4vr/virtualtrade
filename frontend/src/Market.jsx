import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card';
import { Input } from './input';
import { Button } from './button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';
import { useToast } from './use-toast';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './dialog';
import { Label } from './label';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Search, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function Market() {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [stockData, setStockData] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [tradeType, setTradeType] = useState('buy');
  const [portfolio, setPortfolio] = useState(null);

  // Fetch portfolio data
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
        console.error('Failed to fetch portfolio:', error);
      }
    }

    fetchPortfolio();
  }, []);

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setSearchLoading(true);
    try {
      const response = await fetch(`/api/market/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      
      if (data.bestMatches) {
        setSearchResults(data.bestMatches);
      } else {
        setSearchResults([]);
        toast({
          title: 'No results found',
          description: 'Try a different search term',
        });
      }
    } catch (error) {
      console.error('Search failed:', error);
      toast({
        title: 'Search failed',
        description: 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setSearchLoading(false);
    }
  };

  // Handle stock selection
  const handleSelectStock = async (stock) => {
    setSelectedStock(stock);
    setLoading(true);
    
    try {
      // Fetch daily data for the selected stock
      const symbol = stock['1. symbol'];
      const response = await fetch(`/api/market/daily?symbol=${encodeURIComponent(symbol)}`);
      const data = await response.json();
      
      if (data['Time Series (Daily)']) {
        // Convert the data to a format suitable for the chart
        const timeSeriesData = data['Time Series (Daily)'];
        const chartData = Object.keys(timeSeriesData)
          .slice(0, 30) // Get last 30 days
          .reverse() // Reverse to show oldest to newest
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
        toast({
          title: 'Data not available',
          description: 'Could not fetch data for this stock',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Failed to fetch stock data:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch stock data',
        variant: 'destructive',
      });
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
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          quantity: parseInt(quantity),
          price,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        toast({
          title: 'Trade executed',
          description: `Successfully ${tradeType === 'buy' ? 'bought' : 'sold'} ${quantity} shares of ${symbol}`,
        });
        
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
      } else {
        toast({
          title: 'Trade failed',
          description: data.error || 'An error occurred',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Trade execution failed:', error);
      toast({
        title: 'Error',
        description: 'Failed to execute trade',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Market Search</CardTitle>
          <CardDescription>
            Search for stocks to trade
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-2">
            <Input
              placeholder="Search by company name or symbol..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? 'Searching...' : <Search className="h-4 w-4" />}
            </Button>
          </div>
          
          {searchResults.length > 0 && (
            <div className="mt-4 border rounded-md">
              <div className="grid grid-cols-3 gap-2 p-2 font-medium text-sm bg-muted">
                <div>Symbol</div>
                <div>Name</div>
                <div>Region</div>
              </div>
              {searchResults.map((result, index) => (
                <div
                  key={index}
                  className="grid grid-cols-3 gap-2 p-2 border-t hover:bg-muted cursor-pointer"
                  onClick={() => handleSelectStock(result)}
                >
                  <div className="font-medium">{result['1. symbol']}</div>
                  <div className="truncate">{result['2. name']}</div>
                  <div>{result['4. region']}</div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedStock && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle>{selectedStock['2. name']}</CardTitle>
                <CardDescription>
                  {selectedStock['1. symbol']} • {selectedStock['4. region']}
                </CardDescription>
              </div>
              {stockData && (
                <div className="text-right">
                  <div className="text-2xl font-bold">
                    ₹{stockData.latestPrice.toFixed(2)}
                  </div>
                  <div className={`flex items-center justify-end ${
                    stockData.change >= 0 ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {stockData.change >= 0 ? (
                      <ArrowUpRight className="h-4 w-4 mr-1" />
                    ) : (
                      <ArrowDownRight className="h-4 w-4 mr-1" />
                    )}
                    <span>
                      {stockData.change.toFixed(2)} ({stockData.changePercent.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">Loading...</div>
            ) : stockData ? (
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={stockData.chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip formatter={(value) => [`₹${value}`, 'Price']} />
                    <Line 
                      type="monotone" 
                      dataKey="close" 
                      stroke="#8884d8" 
                      strokeWidth={2} 
                      dot={false} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex justify-center py-8">Select a stock to view data</div>
            )}
          </CardContent>
          <CardFooter className="flex justify-between">
            <div className="text-sm text-muted-foreground">
              {stockData && `Last updated: ${stockData.meta?.['3. Last Refreshed']}`}
            </div>
            <Dialog>
              <DialogTrigger asChild>
                <Button>Trade</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Execute Trade</DialogTitle>
                  <DialogDescription>
                    {selectedStock['2. name']} ({selectedStock['1. symbol']})
                  </DialogDescription>
                </DialogHeader>
                
                <Tabs defaultValue="buy" onValueChange={setTradeType}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="buy">Buy</TabsTrigger>
                    <TabsTrigger value="sell">Sell</TabsTrigger>
                  </TabsList>
                  <TabsContent value="buy" className="space-y-4 pt-4">
                    <div>
                      <Label htmlFor="quantity">Quantity</Label>
                      <Input
                        id="quantity"
                        type="number"
                        min="1"
                        value={quantity}
                        onChange={(e) => setQuantity(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label>Price</Label>
                      <div className="text-lg font-medium">
                        ₹{stockData?.latestPrice.toFixed(2) || '0.00'}
                      </div>
                    </div>
                    <div>
                      <Label>Total Cost</Label>
                      <div className="text-lg font-medium">
                        ₹{((stockData?.latestPrice || 0) * quantity).toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <Label>Available Balance</Label>
                      <div className="text-lg font-medium">
                        ₹{portfolio?.cash_balance?.toLocaleString() || '0'}
                      </div>
                    </div>
                  </TabsContent>
                  <TabsContent value="sell" className="space-y-4 pt-4">
                    <div>
                      <Label htmlFor="quantity">Quantity</Label>
                      <Input
                        id="quantity"
                        type="number"
                        min="1"
                        value={quantity}
                        onChange={(e) => setQuantity(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label>Price</Label>
                      <div className="text-lg font-medium">
                        ₹{stockData?.latestPrice.toFixed(2) || '0.00'}
                      </div>
                    </div>
                    <div>
                      <Label>Total Value</Label>
                      <div className="text-lg font-medium">
                        ₹{((stockData?.latestPrice || 0) * quantity).toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <Label>Current Holdings</Label>
                      <div className="text-lg font-medium">
                        {portfolio?.holdings?.[selectedStock['1. symbol']]?.quantity || 0} shares
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
                
                <DialogFooter>
                  <Button onClick={executeTrade}>
                    {tradeType === 'buy' ? 'Buy' : 'Sell'} Shares
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardFooter>
        </Card>
      )}
    </div>
  );
}

