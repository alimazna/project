import { Redirect, Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';

const ACTIVE = '#58a6ff';
const INACTIVE = '#8b949e';

function iconColor(color: unknown): string {
  return typeof color === 'string' ? color : String(color);
}

export default function TabsLayout() {
  const { loading, accessToken } = useAuth();
  if (loading) return null;
  if (!accessToken) return <Redirect href="/login" />;
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: '#0d1117' },
        headerTintColor: '#e6edf3',
        tabBarStyle: { backgroundColor: '#0d1117', borderTopColor: '#30363d' },
        tabBarActiveTintColor: ACTIVE,
        tabBarInactiveTintColor: INACTIVE,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color, size }) => <Ionicons name="stats-chart" size={size} color={iconColor(color)} />,
        }}
      />
      <Tabs.Screen
        name="watchlist"
        options={{
          title: 'Watchlist',
          tabBarIcon: ({ color, size }) => <Ionicons name="star-outline" size={size} color={iconColor(color)} />,
        }}
      />
      <Tabs.Screen
        name="scenarios"
        options={{
          title: 'Analyses',
          tabBarIcon: ({ color, size }) => <Ionicons name="scan" size={size} color={iconColor(color)} />,
        }}
      />
      <Tabs.Screen
        name="alerts"
        options={{
          title: 'Alerts',
          tabBarIcon: ({ color, size }) => <Ionicons name="notifications-outline" size={size} color={iconColor(color)} />,
        }}
      />
      <Tabs.Screen
        name="account"
        options={{
          title: 'Account',
          tabBarIcon: ({ color, size }) => <Ionicons name="person-outline" size={size} color={iconColor(color)} />,
        }}
      />
    </Tabs>
  );
}