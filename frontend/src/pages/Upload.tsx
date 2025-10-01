import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBCFStore } from '@/store/bcfStore';
import { Dropzone } from '@/components/Dropzone';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import { 
  FileCheck, 
  Loader2, 
  ArrowRight, 
  Trash2,
  CheckCircle2,
  FileText
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function Upload() {
  const navigate = useNavigate();
  const { 
    uploadedFiles, 
    addUploadedFile, 
    setFileIssues, 
    isInspecting,
    setIsInspecting,
    removeFile,
    clearFiles
  } = useBCFStore();
  
  const [inspectingFiles, setInspectingFiles] = useState<Set<string>>(new Set());

  const handleFilesAccepted = async (files: File[]) => {
    files.forEach((file) => {
      addUploadedFile(file);
      inspectFile(file);
    });
  };

  const inspectFile = async (file: File) => {
    setInspectingFiles((prev) => new Set(prev).add(file.name));
    setIsInspecting(true);

    try {
      // Use mock data for demo (switch to real API call when backend is ready)
      const response = await apiClient.inspectBCFWithMock(file);
      
      setFileIssues(file.name, response.issues);
      
      toast.success(`Inspected ${file.name}`, {
        description: `Found ${response.issues.length} issue${response.issues.length !== 1 ? 's' : ''}`,
      });
    } catch (error) {
      console.error('Failed to inspect BCF:', error);
      toast.error(`Failed to inspect ${file.name}`, {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setInspectingFiles((prev) => {
        const newSet = new Set(prev);
        newSet.delete(file.name);
        return newSet;
      });
      setIsInspecting(false);
    }
  };

  const handleViewIssues = () => {
    navigate('/issues');
  };

  const handleRemoveFile = (fileName: string) => {
    removeFile(fileName);
    toast.info(`Removed ${fileName}`);
  };

  const handleClearAll = () => {
    clearFiles();
    toast.info('Cleared all files');
  };

  const filesArray = Array.from(uploadedFiles.values());
  const totalIssues = filesArray.reduce((sum, file) => sum + file.issues.length, 0);
  const allInspected = filesArray.length > 0 && filesArray.every(f => f.inspected);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Header */}
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary-glow bg-clip-text text-transparent">
                BIMFlow BCF Inspector
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Upload and inspect Building Collaboration Format files
              </p>
            </div>
            {filesArray.length > 0 && (
              <Button 
                variant="ghost" 
                size="sm"
                onClick={handleClearAll}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Clear All
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Upload Zone */}
          <Card className="p-6">
            <Dropzone 
              onFilesAccepted={handleFilesAccepted}
              disabled={isInspecting}
            />
          </Card>

          {/* Uploaded Files List */}
          {filesArray.length > 0 && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Uploaded Files</h2>
                <Badge variant="secondary">
                  {filesArray.length} file{filesArray.length !== 1 ? 's' : ''}
                </Badge>
              </div>

              <div className="space-y-3">
                {filesArray.map(({ file, issues, inspected }) => (
                  <div 
                    key={file.name}
                    className="flex items-center justify-between p-4 border rounded-lg bg-card hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <FileText className="w-5 h-5 text-primary flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">{file.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {(file.size / 1024).toFixed(2)} KB
                        </div>
                      </div>
                      
                      {inspectingFiles.has(file.name) ? (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Inspecting...
                        </div>
                      ) : inspected ? (
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-success" />
                          <Badge variant="secondary">
                            {issues.length} issue{issues.length !== 1 ? 's' : ''}
                          </Badge>
                        </div>
                      ) : null}
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveFile(file.name)}
                      disabled={inspectingFiles.has(file.name)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>

              {allInspected && totalIssues > 0 && (
                <div className="mt-6 p-4 bg-primary/10 border border-primary/20 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileCheck className="w-6 h-6 text-primary" />
                      <div>
                        <p className="font-semibold text-sm">Inspection Complete</p>
                        <p className="text-xs text-muted-foreground">
                          Found {totalIssues} total issue{totalIssues !== 1 ? 's' : ''} across all files
                        </p>
                      </div>
                    </div>
                    <Button onClick={handleViewIssues}>
                      View Issues
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Help Card */}
          <Card className="p-6 bg-muted/50">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-primary" />
              Getting Started
            </h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Upload one or more .bcf or .bcfzip files using drag & drop or file browser</li>
              <li>• Files will be automatically inspected to extract issues and metadata</li>
              <li>• View detailed issue information including comments, viewpoints, and snapshots</li>
              <li>• Merge multiple BCF files into a single file for consolidated reporting</li>
            </ul>
          </Card>
        </div>
      </main>
    </div>
  );
}