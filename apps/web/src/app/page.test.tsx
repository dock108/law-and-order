import { render, screen } from '@testing-library/react';
import HomePage from './page';

describe('HomePage', () => {
  it('renders the heading', () => {
    render(<HomePage />);
    const heading = screen.getByRole('heading', {
      name: /🚧 UI coming soon/i,
    });
    expect(heading).toBeInTheDocument();
  });

  it('renders the shared button', () => {
    render(<HomePage />);
    const button = screen.getByRole('button', { name: /Shared Button/i });
    expect(button).toBeInTheDocument();
  });
});
