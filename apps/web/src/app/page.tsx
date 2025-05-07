import Button from '@pi-monorepo/ui';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">🚧 UI coming soon</h1>
      <div className="mt-8">
        <Button onClick={() => alert('Button clicked!')}>Shared Button</Button>
      </div>
    </main>
  );
}
