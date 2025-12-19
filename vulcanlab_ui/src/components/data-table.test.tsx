import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable, DataTableColumn } from './data-table';

interface TestData {
  id: number;
  name: string;
  email: string;
  status: string;
}

const mockData: TestData[] = [
  { id: 1, name: 'Alice', email: 'alice@example.com', status: 'active' },
  { id: 2, name: 'Bob', email: 'bob@example.com', status: 'pending' },
  { id: 3, name: 'Charlie', email: 'charlie@example.com', status: 'active' },
];

const basicColumns: DataTableColumn<TestData>[] = [
  { key: 'name', header: 'Name' },
  { key: 'email', header: 'Email' },
  { key: 'status', header: 'Status' },
];

const sortableColumns: DataTableColumn<TestData>[] = [
  { key: 'name', header: 'Name', sortable: true },
  { key: 'email', header: 'Email', sortable: true },
  { key: 'status', header: 'Status' },
];

describe('DataTable', () => {
  it('should render table headers from columns', () => {
    render(<DataTable data={mockData} columns={basicColumns} />);
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('should render table rows from data', () => {
    render(<DataTable data={mockData} columns={basicColumns} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('bob@example.com')).toBeInTheDocument();
  });

  it('should call cell renderer for custom cells', () => {
    const customColumns: DataTableColumn<TestData>[] = [
      { key: 'name', header: 'Name' },
      {
        key: 'status',
        header: 'Status',
        cell: (row) => <span data-testid="custom-cell">{row.status.toUpperCase()}</span>,
      },
    ];

    render(<DataTable data={mockData} columns={customColumns} />);
    const customCells = screen.getAllByTestId('custom-cell');
    expect(customCells).toHaveLength(3);
    expect(customCells[0]).toHaveTextContent('ACTIVE');
  });

  it('should show EmptyState when data is empty', () => {
    render(<DataTable data={[]} columns={basicColumns} />);
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  it('should show custom empty state when provided', () => {
    render(
      <DataTable
        data={[]}
        columns={basicColumns}
        emptyState={{
          title: 'No users found',
          description: 'Try adding some users',
        }}
      />
    );
    expect(screen.getByText('No users found')).toBeInTheDocument();
    expect(screen.getByText('Try adding some users')).toBeInTheDocument();
  });

  it('should show PageLoadingState when loading is true', () => {
    render(<DataTable data={mockData} columns={basicColumns} loading={true} />);
    // PageLoadingState shows a spinner
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should not show data when loading is true', () => {
    render(<DataTable data={mockData} columns={basicColumns} loading={true} />);
    expect(screen.queryByText('Alice')).not.toBeInTheDocument();
  });

  it('should call onRowClick when row is clicked', () => {
    const handleRowClick = jest.fn();
    render(
      <DataTable
        data={mockData}
        columns={basicColumns}
        onRowClick={handleRowClick}
      />
    );

    const rows = screen.getAllByRole('row');
    // First row is header, click the second row (first data row)
    fireEvent.click(rows[1]);

    expect(handleRowClick).toHaveBeenCalledTimes(1);
    expect(handleRowClick).toHaveBeenCalledWith(mockData[0]);
  });

  it('should apply cursor-pointer when onRowClick is provided', () => {
    const handleRowClick = jest.fn();
    render(
      <DataTable
        data={mockData}
        columns={basicColumns}
        onRowClick={handleRowClick}
      />
    );

    const rows = screen.getAllByRole('row');
    // First data row (index 1)
    expect(rows[1]).toHaveClass('cursor-pointer');
  });

  it('should not apply cursor-pointer when onRowClick is not provided', () => {
    render(<DataTable data={mockData} columns={basicColumns} />);

    const rows = screen.getAllByRole('row');
    // First data row (index 1)
    expect(rows[1]).not.toHaveClass('cursor-pointer');
  });

  it('should apply sortable column styling', () => {
    render(<DataTable data={mockData} columns={sortableColumns} />);

    const headers = screen.getAllByRole('columnheader');
    // Name and Email columns are sortable
    expect(headers[0]).toHaveClass('cursor-pointer');
    expect(headers[1]).toHaveClass('cursor-pointer');
    expect(headers[2]).not.toHaveClass('cursor-pointer');
  });

  it('should show sort icons for sortable columns', () => {
    render(<DataTable data={mockData} columns={sortableColumns} />);

    // Should show ArrowUpDown icons for sortable columns
    const icons = document.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });

  it('should sort data when sortable column header is clicked', () => {
    render(<DataTable data={mockData} columns={sortableColumns} />);

    const nameHeader = screen.getByText('Name').closest('th');

    // Data should initially be in original order
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Alice');

    // Click to sort
    fireEvent.click(nameHeader!);

    // After sorting by name ascending, order should be Alice, Bob, Charlie
    const sortedRows = screen.getAllByRole('row');
    expect(sortedRows[1]).toHaveTextContent('Alice');
    expect(sortedRows[2]).toHaveTextContent('Bob');
    expect(sortedRows[3]).toHaveTextContent('Charlie');
  });

  it('should toggle sort direction on repeated clicks', () => {
    render(<DataTable data={mockData} columns={sortableColumns} />);

    const nameHeader = screen.getByText('Name').closest('th');

    // Click once - ascending
    fireEvent.click(nameHeader!);
    let rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Alice');

    // Click twice - descending
    fireEvent.click(nameHeader!);
    rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Charlie');
  });

  it('should apply custom className', () => {
    const { container } = render(
      <DataTable
        data={mockData}
        columns={basicColumns}
        className="custom-table-class"
      />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-table-class');
  });

  it('should apply column className to header and cells', () => {
    const columnsWithClass: DataTableColumn<TestData>[] = [
      { key: 'name', header: 'Name', className: 'custom-column-class' },
    ];

    render(<DataTable data={mockData} columns={columnsWithClass} />);

    const header = screen.getByText('Name').closest('th');
    expect(header).toHaveClass('custom-column-class');

    const cells = document.querySelectorAll('.custom-column-class');
    expect(cells.length).toBeGreaterThan(1); // Header + data cells
  });

  it('should handle null/undefined cell values gracefully', () => {
    const dataWithNull = [
      { id: 1, name: null as unknown as string, email: 'test@example.com', status: 'active' },
    ];

    render(<DataTable data={dataWithNull} columns={basicColumns} />);

    // Should not crash and should render empty string
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toBeInTheDocument();
  });

  it('should render multiple rows correctly', () => {
    render(<DataTable data={mockData} columns={basicColumns} />);

    const rows = screen.getAllByRole('row');
    // 1 header row + 3 data rows
    expect(rows).toHaveLength(4);
  });
});
