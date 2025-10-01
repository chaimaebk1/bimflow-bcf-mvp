import { BCFIssue } from '@/store/bcfStore';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Calendar, 
  MessageSquare, 
  Eye,
  FileText,
  Image as ImageIcon
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface IssueDetailDrawerProps {
  issue: BCFIssue | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'open':
      return 'bg-accent text-accent-foreground';
    case 'in progress':
      return 'bg-primary text-primary-foreground';
    case 'resolved':
      return 'bg-success text-success-foreground';
    case 'closed':
      return 'bg-muted text-muted-foreground';
    default:
      return 'bg-secondary text-secondary-foreground';
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority.toLowerCase()) {
    case 'high':
      return 'bg-destructive text-destructive-foreground';
    case 'medium':
      return 'bg-warning text-warning-foreground';
    case 'low':
      return 'bg-success text-success-foreground';
    default:
      return 'bg-secondary text-secondary-foreground';
  }
};

export const IssueDetailDrawer = ({ issue, open, onOpenChange }: IssueDetailDrawerProps) => {
  if (!issue) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="text-xl">{issue.title}</SheetTitle>
          <SheetDescription className="flex items-center gap-2 text-xs">
            <FileText className="w-3 h-3" />
            {issue.fileName} • {issue.guid}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Status and Priority */}
          <div className="flex gap-3">
            <Badge className={cn('font-medium', getStatusColor(issue.status))}>
              {issue.status}
            </Badge>
            <Badge className={cn('font-medium', getPriorityColor(issue.priority))}>
              {issue.priority}
            </Badge>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2 text-sm">
              <User className="w-4 h-4 text-muted-foreground" />
              <div>
                <div className="text-xs text-muted-foreground">Author</div>
                <div className="font-medium">{issue.author}</div>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <div>
                <div className="text-xs text-muted-foreground">Created</div>
                <div className="font-medium">
                  {new Date(issue.createdAt).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>

          <Separator />

          {/* Description */}
          {issue.description && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Description</h3>
              <p className="text-sm text-muted-foreground">{issue.description}</p>
            </div>
          )}

          {/* Snapshot */}
          {issue.snapshotUrl && (
            <div>
              <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <ImageIcon className="w-4 h-4" />
                Snapshot
              </h3>
              <img 
                src={issue.snapshotUrl} 
                alt="Issue snapshot" 
                className="w-full rounded-lg border"
              />
            </div>
          )}

          <Separator />

          {/* Viewpoints */}
          {issue.viewpoints.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Eye className="w-4 h-4" />
                Viewpoints ({issue.viewpoints.length})
              </h3>
              <div className="space-y-2">
                {issue.viewpoints.map((viewpoint, index) => (
                  <div
                    key={`${issue.guid}-viewpoint-${index}`}
                    className="p-3 border rounded-lg bg-card hover:bg-muted/50 transition-colors"
                  >
                    <div className="text-sm font-medium break-words">
                      {viewpoint || 'Viewpoint'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Separator />

          {/* Comments */}
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Comments ({issue.comments.length})
            </h3>
            <div className="space-y-3">
              {issue.comments.map((comment, index) => {
                const formattedDate = comment.date
                  ? new Date(comment.date).toLocaleDateString()
                  : '—';
                return (
                <div
                  key={comment.guid ?? `${issue.guid}-comment-${index}`}
                  className="p-4 border rounded-lg bg-card space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{comment.author}</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="w-3 h-3" />
                      {formattedDate}
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {comment.text || 'No comment text provided.'}
                  </p>
                </div>
                );
              })}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};