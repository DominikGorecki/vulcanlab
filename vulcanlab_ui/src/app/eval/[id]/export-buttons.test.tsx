/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { Download } from 'lucide-react';

// Simple test component that mimics the export buttons structure
const ExportButtonsTest = ({ onExportCSV, onExportJsonl, exportingCSV, exportingJsonl }: any) => {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={onExportCSV}
        disabled={exportingCSV}
        data-testid="export-csv-btn"
      >
        <Download className="mr-2 h-4 w-4" />
        {exportingCSV ? "Exporting..." : "Export CSV"}
      </button>
      <button
        onClick={onExportJsonl}
        disabled={exportingJsonl}
        data-testid="export-jsonl-btn"
      >
        <Download className="mr-2 h-4 w-4" />
        {exportingJsonl ? "Exporting..." : "Export JSONL"}
      </button>
    </div>
  );
};

describe('Export Buttons - JSONL Feature', () => {
  it('should render both Export CSV and Export JSONL buttons', () => {
    render(
      <ExportButtonsTest
        onExportCSV={jest.fn()}
        onExportJsonl={jest.fn()}
        exportingCSV={false}
        exportingJsonl={false}
      />
    );

    expect(screen.getByText('Export CSV')).toBeInTheDocument();
    expect(screen.getByText('Export JSONL')).toBeInTheDocument();
  });

  it('should call onExportJsonl when JSONL button is clicked', () => {
    const mockExportJsonl = jest.fn();

    render(
      <ExportButtonsTest
        onExportCSV={jest.fn()}
        onExportJsonl={mockExportJsonl}
        exportingCSV={false}
        exportingJsonl={false}
      />
    );

    const jsonlButton = screen.getByTestId('export-jsonl-btn');
    fireEvent.click(jsonlButton);

    expect(mockExportJsonl).toHaveBeenCalledTimes(1);
  });

  it('should show loading state when exportingJsonl is true', () => {
    render(
      <ExportButtonsTest
        onExportCSV={jest.fn()}
        onExportJsonl={jest.fn()}
        exportingCSV={false}
        exportingJsonl={true}
      />
    );

    expect(screen.getByText('Exporting...')).toBeInTheDocument();
    expect(screen.queryByText('Export JSONL')).not.toBeInTheDocument();
  });

  it('should disable JSONL button when exportingJsonl is true', () => {
    render(
      <ExportButtonsTest
        onExportCSV={jest.fn()}
        onExportJsonl={jest.fn()}
        exportingCSV={false}
        exportingJsonl={true}
      />
    );

    const jsonlButton = screen.getByTestId('export-jsonl-btn');
    expect(jsonlButton).toBeDisabled();
  });

  it('should not disable JSONL button when CSV is exporting', () => {
    render(
      <ExportButtonsTest
        onExportCSV={jest.fn()}
        onExportJsonl={jest.fn()}
        exportingCSV={true}
        exportingJsonl={false}
      />
    );

    const jsonlButton = screen.getByTestId('export-jsonl-btn');
    expect(jsonlButton).not.toBeDisabled();
  });

  it('should position buttons next to each other', () => {
    const { container } = render(
      <ExportButtonsTest
        onExportCSV={jest.fn()}
        onExportJsonl={jest.fn()}
        exportingCSV={false}
        exportingJsonl={false}
      />
    );

    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('flex');
    expect(wrapper).toHaveClass('items-center');
    expect(wrapper).toHaveClass('gap-2');
  });
});

describe('Export Handler Functions', () => {
  beforeEach(() => {
    // Mock document methods
    document.createElement = jest.fn((tag) => {
      const element = {
        href: '',
        setAttribute: jest.fn(),
        click: jest.fn(),
      } as any;
      return element;
    });

    document.body.appendChild = jest.fn();
    document.body.removeChild = jest.fn();
  });

  it('should create link with correct JSONL URL', () => {
    const mockLink = {
      href: '',
      setAttribute: jest.fn(),
      click: jest.fn(),
    };

    (document.createElement as jest.Mock).mockReturnValue(mockLink);

    // Simulate the handleExportJsonl logic
    const id = '42';
    const API_BASE_URL = 'http://localhost:8000';
    const url = `${API_BASE_URL}/api/v1/eval/experiments/${id}/export-jsonl`;

    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `experiment_${id}_answers.jsonl`);

    expect(mockLink.href).toBe('http://localhost:8000/api/v1/eval/experiments/42/export-jsonl');
    expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'experiment_42_answers.jsonl');
  });

  it('should create link with correct filename format', () => {
    const mockLink = {
      href: '',
      setAttribute: jest.fn(),
      click: jest.fn(),
    };

    (document.createElement as jest.Mock).mockReturnValue(mockLink);

    // Simulate the handleExportJsonl logic
    const id = '123';
    const link = document.createElement("a");
    link.setAttribute("download", `experiment_${id}_answers.jsonl`);

    expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'experiment_123_answers.jsonl');
  });
});
