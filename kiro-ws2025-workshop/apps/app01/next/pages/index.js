export default function Home({ host, generatedAt }) {
  return (
    <main data-testid="next-workshop" style={{fontFamily: 'system-ui', maxWidth: 720, margin: '4rem auto'}}>
      <h1>Next.js on APP01</h1>
      <p id="compatibility-marker">NEXT_OK_V1</p>
      <p>Server-rendered by {host} at {generatedAt}.</p>
    </main>
  );
}

export async function getServerSideProps() {
  return {
    props: {
      host: process.env.COMPUTERNAME || 'unknown',
      generatedAt: new Date().toISOString()
    }
  };
}
