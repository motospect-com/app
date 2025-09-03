import { render, screen } from '@testing-library/react';
import { jest } from '@jest/globals';
import App from './App';

// Mock the VehicleVisualization component
jest.mock('./VehicleVisualization', () => () => <div>VehicleVisualization Mock</div>);

test('renders Motospect header', () => {
  render(<App />);
  const headerElement = screen.getByText(/Motospect 3D Vehicle Scanner/i);
  expect(headerElement).toBeInTheDocument();
});

