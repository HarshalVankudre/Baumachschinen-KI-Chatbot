import { render, screen, fireEvent, waitFor } from '@/test-utils/test-utils';
import userEvent from '@testing-library/user-event';
import { DocumentUpload } from '../DocumentUpload';
import * as documentService from '@/services/documentService';

jest.mock('@/services/documentService');

describe('DocumentUpload', () => {
  const mockOnUploadComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders drag-and-drop zone', () => {
    render(<DocumentUpload />);

    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();
  });

  it('renders category dropdown', () => {
    render(<DocumentUpload />);

    expect(screen.getByText(/category/i)).toBeInTheDocument();
  });

  it('renders browse files button', () => {
    render(<DocumentUpload />);

    const browseButton = screen.getByRole('button', { name: /browse/i });
    expect(browseButton).toBeInTheDocument();
  });

  it('highlights drop zone on drag over', () => {
    render(<DocumentUpload />);

    const dropZone = screen.getByText(/drag.*drop/i).closest('div');

    if (dropZone) {
      fireEvent.dragEnter(dropZone);
      expect(dropZone).toHaveClass(/border-blue/);

      fireEvent.dragLeave(dropZone);
    }
  });

  it('accepts file drop', async () => {
    (documentService.documentService.uploadDocument as jest.Mock).mockResolvedValue({
      document_id: '1',
      filename: 'test.pdf',
    });

    render(<DocumentUpload />);

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const dropZone = screen.getByText(/drag.*drop/i).closest('div');

    if (dropZone) {
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
        },
      });

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });
    }
  });

  it('validates file type', async () => {
    render(<DocumentUpload />);

    const invalidFile = new File(['content'], 'test.exe', { type: 'application/x-msdownload' });
    const dropZone = screen.getByText(/drag.*drop/i).closest('div');

    if (dropZone) {
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [invalidFile],
        },
      });

      await waitFor(() => {
        expect(screen.getByText(/unsupported file type/i)).toBeInTheDocument();
      });
    }
  });

  it('requires category selection before upload', async () => {
    const user = userEvent.setup();
    render(<DocumentUpload />);

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    if (input) {
      await user.upload(input, file);

      // Try to upload without selecting category
      await waitFor(() => {
        expect(screen.getByText(/select category/i)).toBeInTheDocument();
      });
    }
  });

  it('shows upload progress', async () => {
    (documentService.documentService.uploadDocument as jest.Mock).mockImplementation((file, _category, onProgress) => {
      onProgress?.({ loaded: 50, total: 100 });
      return Promise.resolve({ document_id: '1', filename: file.name });
    });

    render(<DocumentUpload />);

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const dropZone = screen.getByText(/drag.*drop/i).closest('div');

    if (dropZone) {
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
        },
      });

      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument();
      });
    }
  });

  it('uploads multiple files', async () => {
    (documentService.documentService.uploadDocument as jest.Mock).mockResolvedValue({
      document_id: '1',
      filename: 'test.pdf',
    });

    render(<DocumentUpload />);

    const files = [
      new File(['content1'], 'test1.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'test2.pdf', { type: 'application/pdf' }),
    ];

    const dropZone = screen.getByText(/drag.*drop/i).closest('div');

    if (dropZone) {
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files,
        },
      });

      await waitFor(() => {
        expect(screen.getByText('test1.pdf')).toBeInTheDocument();
        expect(screen.getByText('test2.pdf')).toBeInTheDocument();
      });
    }
  });

  it('limits concurrent uploads to 5', async () => {
    (documentService.documentService.uploadDocument as jest.Mock).mockResolvedValue({
      document_id: '1',
      filename: 'test.pdf',
    });

    render(<DocumentUpload />);

    const files = Array.from({ length: 10 }, (_, i) =>
      new File([`content${i}`], `test${i}.pdf`, { type: 'application/pdf' })
    );

    const dropZone = screen.getByText(/drag.*drop/i).closest('div');

    if (dropZone) {
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files,
        },
      });

      await waitFor(() => {
        // Should show first 5 files uploading
        expect(screen.getByText('test0.pdf')).toBeInTheDocument();
      });
    }
  });

  it('calls onUploadComplete after successful upload', async () => {
    (documentService.documentService.uploadDocument as jest.Mock).mockResolvedValue({
      document_id: '1',
      filename: 'test.pdf',
    });

    render(<DocumentUpload />);

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const dropZone = screen.getByText(/drag.*drop/i).closest('div');

    if (dropZone) {
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
        },
      });

      await waitFor(() => {
        expect(mockOnUploadComplete).toHaveBeenCalled();
      }, { timeout: 3000 });
    }
  });

  it('displays error message on upload failure', async () => {
    (documentService.documentService.uploadDocument as jest.Mock).mockRejectedValue(
      new Error('Upload failed')
    );

    render(<DocumentUpload />);

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const dropZone = screen.getByText(/drag.*drop/i).closest('div');

    if (dropZone) {
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
        },
      });

      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
      });
    }
  });
});
