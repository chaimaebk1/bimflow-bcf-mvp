import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBCFStore } from '@/store/bcfStore';
import { IssuesTable } from '@/components/IssuesTable';
import { IssueDetailDrawer } from '@/components/IssueDetailDrawer';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Loader2,
  Merge,
  FileCheck
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function Issues() {
  const navigate = useNavigate();
  const { 
    allIssues, 
    uploadedFiles,
    selectedIssue,
    setSelectedIssue,
    isMerging,
    setIsMerging
  } = useBCFStore();
  
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleIssueClick = (issue: typeof allIssues[0]) => {
    setSelectedIssue(issue);
    setDrawerOpen(true);
  };

  const handleDrawerClose = (open: boolean) => {
    setDrawerOpen(open);
    if (!open) {
      setSelectedIssue(null);
    }
  };

  const handleMerge = async () => {
    const files = Array.from(uploadedFiles.values()).map(f => f.file);
    
    if (files.length < 2) {
      toast.error('Need at least 2 files to merge');
      return;
    }

    setIsMerging(true);
    
    try {
      const { blob, filename } = await apiClient.mergeBcfs(files);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `merged-${Date.now()}.bcfzip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success('BCF files merged successfully', {
        description: 'Download started automatically',
      });
    } catch (error) {
      console.error('Failed to merge BCFs:', error);
      toast.error('Failed to merge BCF files', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setIsMerging(false);
    }
  };

  const filesArray = Array.from(uploadedFiles.values());
  const canMerge = filesArray.length >= 2;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Header */}
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => navigate('/')}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-2xl font-bold">Issues Overview</h1>
                <p className="text-sm text-muted-foreground mt-1">
                  {filesArray.length} file{filesArray.length !== 1 ? 's' : ''} • {allIssues.length} issue{allIssues.length !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {canMerge && (
                <Button 
                  onClick={handleMerge}
                  disabled={isMerging}
                  variant="secondary"
                >
                  {isMerging ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Merging...
                    </>
                  ) : (
                    <>
                      <Merge className="w-4 h-4 mr-2" />
                      Merge & Download
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Issues</p>
                  <p className="text-2xl font-bold mt-1">{allIssues.length}</p>
                </div>
                <FileCheck className="w-8 h-8 text-primary" />
              </div>
            </Card>

            <Card className="p-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">By Status</p>
                <div className="flex flex-wrap gap-1">
                  {Array.from(new Set(allIssues.map(i => i.status))).map(status => {
                    const count = allIssues.filter(i => i.status === status).length;
                    return (
                      <Badge key={status} variant="secondary" className="text-xs">
                        {status}: {count}
                      </Badge>
                    );
                  })}
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">By Priority</p>
                <div className="flex flex-wrap gap-1">
                  {Array.from(new Set(allIssues.map(i => i.priority))).map(priority => {
                    const count = allIssues.filter(i => i.priority === priority).length;
                    return (
                      <Badge key={priority} variant="secondary" className="text-xs">
                        {priority}: {count}
                      </Badge>
                    );
                  })}
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Files</p>
                <div className="space-y-1">
                  {filesArray.map(({ file, issues }) => (
                    <div key={file.name} className="text-xs">
                      <span className="font-medium truncate block">{file.name}</span>
                      <span className="text-muted-foreground">{issues.length} issues</span>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>

          {/* Issues Table */}
          <Card className="p-6">
            <IssuesTable 
              issues={allIssues}
              onIssueClick={handleIssueClick}
            />
          </Card>
        </div>
      </main>

      {/* Issue Detail Drawer */}
      <IssueDetailDrawer 
        issue={selectedIssue}
        open={drawerOpen}
        onOpenChange={handleDrawerClose}
      />
    </div>
  );
}