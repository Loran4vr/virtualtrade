import { Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { Button } from './components/ui/button';

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center text-center px-4">
      <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text">
        Virtual Trade
      </h1>
      <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-2xl">
        Experience the thrill of stock trading with virtual money. Learn, practice, and master the art of trading without risking real capital.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12 max-w-4xl">
        <div className="p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Virtual Trading</h3>
          <p className="text-gray-600">
            Trade with virtual money in real market conditions. Perfect for beginners and experienced traders alike.
          </p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Real Market Data</h3>
          <p className="text-gray-600">
            Access real-time market data and make informed decisions based on actual market conditions.
          </p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Learn & Grow</h3>
          <p className="text-gray-600">
            Track your performance, learn from your trades, and improve your trading strategy over time.
          </p>
        </div>
      </div>

      {user ? (
        <div className="space-x-4">
          <Link to="/market">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
              Start Trading
            </Button>
          </Link>
          <Link to="/portfolio">
            <Button size="lg" variant="outline">
              View Portfolio
            </Button>
          </Link>
        </div>
      ) : (
        <div className="space-x-4">
          <Link to="/login">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
              Get Started
            </Button>
          </Link>
          <a href="#features">
            <Button size="lg" variant="outline">
              Learn More
            </Button>
          </a>
        </div>
      )}

      <div id="features" className="mt-24 w-full max-w-6xl">
        <h2 className="text-3xl font-bold mb-12">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">Real-time Market Data</h3>
            <p className="text-gray-600">
              Access live market data and make informed trading decisions.
            </p>
          </div>
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">Portfolio Tracking</h3>
            <p className="text-gray-600">
              Monitor your investments and track your performance over time.
            </p>
          </div>
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">Trading Limits</h3>
            <p className="text-gray-600">
              Start with ₹10 lakhs virtual money and upgrade your limits as you grow.
            </p>
          </div>
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">Market Analysis</h3>
            <p className="text-gray-600">
              Access detailed stock information and market trends.
            </p>
          </div>
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">Secure Platform</h3>
            <p className="text-gray-600">
              Trade with confidence on our secure and reliable platform.
            </p>
          </div>
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">Subscription Plans</h3>
            <p className="text-gray-600">
              Choose from various subscription plans to enhance your trading experience.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 