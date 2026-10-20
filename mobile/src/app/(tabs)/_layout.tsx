import { Redirect, Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';
import { colors } from '../../lib/theme';

const ACTIVE = '#2563eb';
const INACTIVE = '#93a0c4';

function iconColor(color: unknown): string {
  return typeof color === 'string' ? color : String(color);
}

export default function TabsLayout() {
  const { loading, accessToken, user } = useAuth();
  if (loading) return null;
  if (!accessToken) return <Redirect href="/login" />;
  const isAdmin = user?.roles?.some((r) => r === 'admin' || r === 'super_admin') ?? false;
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg },
        headerTintColor: colors.text,
        tabBarStyle: { backgroundColor: colors.bg, borderTopColor: colors.border },
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
          title: 'Scenarios',
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
      {isAdmin && (
        <Tabs.Screen
          name="admin"
          options={{
            title: 'Symbols admin',
            tabBarIcon: ({ color, size }) => <Ionicons name="settings-outline" size={size} color={iconColor(color)} />,
          }}
        />
      )}
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