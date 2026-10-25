import Head from 'next/head'
import Layout from '../components/layout'
import Chat from '../components/chat'

export default function Home() {
  return (
    <div>
      <Head>
        <title>BigCompany Knowledge Assistant</title>
        <meta name="description" content="BigCompany Inc. AI Knowledge Assistant" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Layout>
        <Chat />
      </Layout>
    </div>
  )
}
