import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../components/ui/use-toast';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowUpIcon, ArrowDownIcon } from 'lucide-react';

export default function Dashboard() {
  const { toast } = useToast();
  const [portfolio, setPortfolio] = useState(null);
  const [topGainers, setTopGainers] = useState([]);
  const [topLosers, setTopLosers] = useState([]);
  const [marketStatus, setMarketStatus] = useState('closed');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize portfolio if not already initialized
    async function initializePortfolio() {
      try {
        const response = await fetch('/api/portfolio/initialize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        const data = await response.json();
        setPortfolio(data.portfolio);
      } catch (error) {
        console.error('Failed to initialize portfolio:', error);
        toast({
          title: 'Error',
          description: 'Failed to initialize portfolio. Please try again.',
          variant: 'destructive',
        });
      }
    }

    // Fetch top gainers and losers
    async function fetchTopGainersLosers() {
      try {
        const response = await fetch('/api/market/top-gainers-losers');
        const data = await response.json();
        
        if (data.top_gainers) {
          setTopGainers(data.top_gainers.slice(0, 5));
        }
        
        if (data.top_losers) {
          setTopLosers(data.top_losers.slice(0, 5));
        }
      } catch (error) {
        console.error('Failed to fetch top gainers/losers:', error);
      }
    }

    // Fetch portfolio data
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
        } else {
          // If portfolio doesn't exist yet, initialize it
          await initializePortfolio();
        }
      } catch (error) {
        console.error('Failed to fetch portfolio:', error);
        // If error occurs, try to initialize portfolio
        await initializePortfolio();
      } finally {
        setLoading(false);
      }
    }

    fetchPortfolio();
    fetchTopGainersLosers();

    // Simulate market status (in a real app, this would come from an API)
    const now = new Date();
    const hour = now.getHours();
    const day = now.getDay();
    
    // Simulate Indian market hours (9:15 AM to 3:30 PM, Monday to Friday)
    if (day >= 1 && day <= 5 && hour >= 9 && hour < 16) {
      setMarketStatus('open');
    } else {
      setMarketStatus('closed');
    }
  }, [toast]);

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
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between gap-4">
        <Card className="flex-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Portfolio Value</CardTitle>
            <CardDescription>
              Total value of your portfolio
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{portfolio?.cash_balance?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              Virtual balance for paper trading
            </p>
          </CardContent>
        </Card>
        <Card className="flex-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Market Status</CardTitle>
            <CardDescription>
              Current market trading status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <div className={`h-3 w-3 rounded-full mr-2 ${
                marketStatus === 'open' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span className="text-lg font-medium capitalize">{marketStatus}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {marketStatus === 'open' 
                ? 'Market is currently trading' 
                : 'Market is currently closed'}
            </p>
          </CardContent>
        </Card>
        <Card className="flex-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Holdings</CardTitle>
            <CardDescription>
              Number of stocks in your portfolio
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(portfolio?.holdings || {}).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Different stocks currently held
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Portfolio Performance</CardTitle>
          <CardDescription>
            Track your portfolio value over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={portfolioChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => [`₹${value.toLocaleString()}`, 'Value']} />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#8884d8" 
                  strokeWidth={2} 
                  dot={{ r: 4 }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="gainers">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="gainers">Top Gainers</TabsTrigger>
          <TabsTrigger value="losers">Top Losers</TabsTrigger>
        </TabsList>
        <TabsContent value="gainers">
          <Card>
            <CardHeader>
              <CardTitle>Top Gainers</CardTitle>
              <CardDescription>
                Stocks with the highest price increase today
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topGainers.length > 0 ? (
                  topGainers.map((stock, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{stock.ticker}</p>
                        <p className="text-sm text-muted-foreground">{stock.price}</p>
                      </div>
                      <div className="flex items-center text-green-500">
                        <ArrowUpIcon className="h-4 w-4 mr-1" />
                        <span>{stock.change_percentage}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground">No data available</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="losers">
          <Card>
            <CardHeader>
              <CardTitle>Top Losers</CardTitle>
              <CardDescription>
                Stocks with the highest price decrease today
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topLosers.length > 0 ? (
                  topLosers.map((stock, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{stock.ticker}</p>
                        <p className="text-sm text-muted-foreground">{stock.price}</p>
                      </div>
                      <div className="flex items-center text-red-500">
                        <ArrowDownIcon className="h-4 w-4 mr-1" />
                        <span>{stock.change_percentage}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground">No data available</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

