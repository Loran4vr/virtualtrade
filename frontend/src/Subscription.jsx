import { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { useToast } from './use-toast';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CircularProgress from '@mui/material/CircularProgress';

export default function Subscription() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [plans, setPlans] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [subscription, setSubscription] = useState(null);

  useEffect(() => {
    fetchPlans();
    fetchSubscriptionStatus();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch('/api/subscription/plans');
      const data = await response.json();
      setPlans(data);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      toast({
        title: 'Error',
        description: 'Failed to load subscription plans',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await fetch('/api/subscription/status');
      const data = await response.json();
      setSubscription(data.subscription);
    } catch (error) {
      console.error('Failed to fetch subscription status:', error);
    }
  };

  const handlePurchase = async (planId) => {
    setPurchasing(true);
    try {
      const response = await fetch('/api/subscription/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_id: planId }),
      });
      const data = await response.json();
      
      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Subscription purchased successfully',
        });
        fetchSubscriptionStatus();
      } else {
        toast({
          title: 'Error',
          description: data.error || 'Failed to purchase subscription',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Failed to purchase subscription:', error);
      toast({
        title: 'Error',
        description: 'Failed to purchase subscription',
        variant: 'destructive',
      });
    } finally {
      setPurchasing(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Subscription Plans
      </Typography>
      
      {subscription && (
        <Box sx={{ mb: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Current Subscription
              </Typography>
              <Typography variant="body1">
                Plan: {plans[subscription.plan_id]?.name}
              </Typography>
              <Typography variant="body1">
                Trading Limit: ₹{subscription.credit_limit.toLocaleString()}
              </Typography>
              <Typography variant="body1">
                Expires: {new Date(subscription.expires_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      <Grid container spacing={3}>
        {Object.entries(plans).map(([planId, plan]) => (
          <Grid item xs={12} sm={6} md={3} key={planId}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                ...(subscription?.plan_id === planId && {
                  border: '2px solid #1976d2',
                }),
              }}
            >
              {subscription?.plan_id === planId && (
                <Chip
                  icon={<CheckCircleIcon />}
                  label="Current Plan"
                  color="primary"
                  sx={{ position: 'absolute', top: 16, right: 16 }}
                />
              )}
              <CardHeader
                title={plan.name}
                subheader={`₹${plan.price} / month`}
                titleTypographyProps={{ align: 'center' }}
                subheaderTypographyProps={{ align: 'center' }}
              />
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ textAlign: 'center', mb: 2 }}>
                  <Typography variant="h4" component="div" gutterBottom>
                    ₹{plan.credit.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Trading Limit
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  • {plan.duration_days} days validity
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  • Real-time market data
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  • Advanced analytics
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Priority support
                </Typography>
              </CardContent>
              <Box sx={{ p: 2 }}>
                <Button
                  fullWidth
                  variant={subscription?.plan_id === planId ? 'outlined' : 'contained'}
                  onClick={() => handlePurchase(planId)}
                  disabled={purchasing || subscription?.plan_id === planId}
                >
                  {purchasing ? <CircularProgress size={24} /> : 'Subscribe Now'}
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
} 