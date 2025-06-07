import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

// Icons
import { 
  LayoutDashboard, 
  LineChart, 
  Wallet, 
  History, 
  LogOut, 
  Menu, 
  X,
  Sun,
  Moon
} from 'lucide-react';

// UI Components
import { Button } from './button';
import { Avatar, AvatarFallback, AvatarImage } from './avatar';
import { useTheme } from './theme-provider';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Market', href: '/market', icon: LineChart },
    { name: 'Portfolio', href: '/portfolio', icon: Wallet },
    { name: 'Transactions', href: '/transactions', icon: History },
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile sidebar toggle */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Button
          variant="outline"
          size="icon"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="rounded-full"
        >
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {/* Sidebar for mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
          <div className="fixed inset-y-0 left-0 w-64 bg-card border-r border-border overflow-y-auto">
            <div className="flex items-center justify-between h-16 px-4 border-b border-border">
              <h1 className="text-xl font-bold">VirtualTrade</h1>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <nav className="mt-5 px-2 space-y-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-4 py-2 text-sm font-medium rounded-md ${
                    isActive(item.href)
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-muted'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-col flex-1 overflow-hidden bg-gray-100 dark:bg-neutral-900">
        {/* Top navigation */}
        <header className="bg-white dark:bg-neutral-800 border-b border-gray-200 dark:border-neutral-700">
          <div className="flex items-center justify-between h-16 px-4">
            <div className="flex items-center lg:hidden">
              <h1 className="text-xl font-bold ml-8">VirtualTrade</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="icon" onClick={toggleTheme}>
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </Button>
              <div className="flex items-center lg:hidden">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.picture} alt={user?.name} />
                  <AvatarFallback>{user?.name?.charAt(0) || 'U'}</AvatarFallback>
                </Avatar>
                <Button variant="ghost" size="icon" onClick={logout} className="ml-2">
                  <LogOut className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-5xl mx-auto w-full bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl p-6 md:p-10 min-h-[80vh] border border-gray-200 dark:border-neutral-700">
            {children}
          </div>
        </main>
      </div>

      {/* Sidebar for desktop */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <div className="flex flex-col w-64 border-r border-gray-200 dark:border-neutral-700 bg-gradient-to-b from-gray-50 to-gray-200 dark:from-neutral-900 dark:to-neutral-800 shadow-lg min-h-screen">
          <div className="flex items-center h-16 px-4 border-b border-gray-200 dark:border-neutral-700">
            <h1 className="text-xl font-bold">VirtualTrade</h1>
          </div>
          <div className="flex flex-col flex-grow">
            <nav className="flex-1 px-2 py-6 space-y-2">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-4 py-2 text-base font-medium rounded-lg transition-colors duration-150 ${
                    isActive(item.href)
                      ? 'bg-blue-600 text-white shadow'
                      : 'text-gray-700 dark:text-gray-200 hover:bg-blue-100 dark:hover:bg-blue-900'
                  }`}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              ))}
            </nav>
            <div className="flex-shrink-0 flex border-t border-gray-200 dark:border-neutral-700 p-4">
              <div className="flex items-center w-full">
                <div className="flex-shrink-0">
                  <Avatar>
                    <AvatarImage src={user?.picture} alt={user?.name} />
                    <AvatarFallback>{user?.name?.charAt(0) || 'U'}</AvatarFallback>
                  </Avatar>
                </div>
                <div className="ml-3 flex-1">
                  <p className="text-sm font-medium">{user?.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user?.email}</p>
                </div>
                <Button variant="ghost" size="icon" onClick={logout}>
                  <LogOut className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

