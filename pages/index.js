import Dashboard from '../components/Dashboard';
import Head from 'next/head';

export default function Home() {
  return (
    <>
      <Head>
        <title>NeuroFlow Dashboard</title>
        <meta name="description" content="AI-powered tutoring dashboard with image and audio processing" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Dashboard />
    </>
  );
} 