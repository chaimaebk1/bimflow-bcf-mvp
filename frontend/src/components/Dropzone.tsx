import { useCallback, useState } from 'react';
import { Upload, FileCheck, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DropzoneProps {
  onFilesAccepted: (files: File[]) => void;
  accept?: string;
  maxFiles?: number;
  disabled?: boolean;
}

export const Dropzone = ({ 
  onFilesAccepted, 
  accept = '.bcf,.bcfzip',
  maxFiles = 10,
  disabled = false 
}: DropzoneProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFiles = (files: File[]): { valid: File[], errors: string[] } => {
    const errors: string[] = [];
    const valid: File[] = [];

    if (files.length > maxFiles) {
      errors.push(`Maximum ${maxFiles} files allowed`);
      return { valid: [], errors };
    }

    files.forEach((file) => {
      const extension = file.name.toLowerCase().split('.').pop();
      if (!['bcf', 'bcfzip'].includes(extension || '')) {
        errors.push(`${file.name}: Invalid file type. Only .bcf and .bcfzip files are accepted.`);
      } else if (file.size > 100 * 1024 * 1024) { // 100MB limit
        errors.push(`${file.name}: File too large. Maximum size is 100MB.`);
      } else {
        valid.push(file);
      }
    });

    return { valid, errors };
  };

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0 || disabled) return;

    const fileArray = Array.from(files);
    const { valid, errors } = validateFiles(fileArray);

    if (errors.length > 0) {
      setError(errors.join(' '));
      setTimeout(() => setError(null), 5000);
    }

    if (valid.length > 0) {
      setError(null);
      onFilesAccepted(valid);
    }
  }, [onFilesAccepted, disabled, maxFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
  }, [handleFiles]);

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative border-2 border-dashed rounded-lg transition-all duration-300",
          "flex flex-col items-center justify-center p-12 cursor-pointer",
          "hover:border-primary hover:bg-primary/5",
          isDragging && "border-primary bg-primary/10 scale-[1.02]",
          disabled && "opacity-50 cursor-not-allowed",
          !isDragging && !disabled && "border-border bg-card",
          error && "border-destructive"
        )}
      >
        <input
          type="file"
          accept={accept}
          multiple
          onChange={handleFileInput}
          disabled={disabled}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          id="file-upload"
        />
        
        <div className="flex flex-col items-center gap-4 pointer-events-none">
          {error ? (
            <AlertCircle className="w-16 h-16 text-destructive" />
          ) : isDragging ? (
            <FileCheck className="w-16 h-16 text-primary animate-pulse" />
          ) : (
            <Upload className="w-16 h-16 text-muted-foreground" />
          )}
          
          <div className="text-center space-y-2">
            <p className="text-lg font-semibold text-foreground">
              {error ? 'Invalid files detected' : isDragging ? 'Drop files here' : 'Upload BCF Files'}
            </p>
            <p className="text-sm text-muted-foreground max-w-sm">
              {error ? error : `Drag and drop your .bcf or .bcfzip files here, or click to browse (max ${maxFiles} files)`}
            </p>
          </div>
          
          {!error && !isDragging && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2">
              <FileCheck className="w-4 h-4" />
              <span>Accepts: .bcf, .bcfzip (max 100MB each)</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};