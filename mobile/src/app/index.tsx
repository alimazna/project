import { Redirect } from 'expo-router';
import { useAuth } from '../context/AuthContext';

export default function Index() {
  const { loading, accessToken } = useAuth();
  if (loading) return null;
  return <Redirect href={accessToken ? '/(tabs)' : '/login'} />;
}