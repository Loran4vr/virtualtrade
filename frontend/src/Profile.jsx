import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import Button from '@mui/material/Button';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Box from '@mui/material/Box';

export default function Profile() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState(true);

  return (
    <Box sx={{ maxWidth: 500, mx: 'auto', mt: 4 }}>
      <Card>
        <CardHeader title="User Profile & Settings" />
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar src={user?.picture} alt={user?.name} sx={{ width: 64, height: 64, mr: 2 }} />
            <Box>
              <Typography variant="h6">{user?.name}</Typography>
              <Typography color="text.secondary">{user?.email}</Typography>
            </Box>
          </Box>
          <FormControlLabel
            control={<Switch checked={notifications} onChange={e => setNotifications(e.target.checked)} />}
            label="Enable notifications"
          />
          <Box sx={{ mt: 3 }}>
            <Button variant="outlined" color="error">
              Reset All Data
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
} 