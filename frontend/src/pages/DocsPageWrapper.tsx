import { DocsPage } from '../components/DocsPage';
import { LightRays } from '../components/LightRays';

export function DocsPageWrapper() {
  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <DocsPage />
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    padding: '40px 20px',
    position: 'relative',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    position: 'relative',
    zIndex: 1,
  },
};
