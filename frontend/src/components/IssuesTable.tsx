import { useState, useMemo } from 'react';
import { BCFIssue } from '@/store/bcfStore';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { 
  Search, 
  Filter, 
  Eye,
  Calendar,
  User,
  FileText
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface IssuesTableProps {
  issues: BCFIssue[];
  onIssueClick: (issue: BCFIssue) => void;
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

export const IssuesTable = ({ issues, onIssueClick }: IssuesTableProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');

  const filteredIssues = useMemo(() => {
    return issues.filter((issue) => {
      const matchesSearch = 
        issue.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        issue.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
        issue.guid.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || issue.status.toLowerCase() === statusFilter.toLowerCase();
      const matchesPriority = priorityFilter === 'all' || issue.priority.toLowerCase() === priorityFilter.toLowerCase();

      return matchesSearch && matchesStatus && matchesPriority;
    });
  }, [issues, searchTerm, statusFilter, priorityFilter]);

  const statuses = useMemo(() => {
    const uniqueStatuses = Array.from(new Set(issues.map(i => i.status)));
    return ['all', ...uniqueStatuses];
  }, [issues]);

  const priorities = useMemo(() => {
    const uniquePriorities = Array.from(new Set(issues.map(i => i.priority)));
    return ['all', ...uniquePriorities];
  }, [issues]);

  if (issues.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileText className="w-16 h-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold text-foreground mb-2">No issues found</h3>
        <p className="text-sm text-muted-foreground">Upload BCF files to view issues</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search issues..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <div className="flex gap-2">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px]">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {statuses.map((status) => (
                <SelectItem key={status} value={status}>
                  {status === 'all' ? 'All Statuses' : status}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={priorityFilter} onValueChange={setPriorityFilter}>
            <SelectTrigger className="w-[140px]">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              {priorities.map((priority) => (
                <SelectItem key={priority} value={priority}>
                  {priority === 'all' ? 'All Priorities' : priority}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Results count */}
      <div className="text-sm text-muted-foreground">
        Showing {filteredIssues.length} of {issues.length} issues
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40%]">Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Author</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredIssues.map((issue) => (
              <TableRow 
                key={issue.guid}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => onIssueClick(issue)}
              >
                <TableCell className="font-medium">
                  <div className="flex flex-col gap-1">
                    <span className="text-foreground">{issue.title}</span>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      {issue.fileName}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className={cn('font-medium', getStatusColor(issue.status))}>
                    {issue.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge className={cn('font-medium', getPriorityColor(issue.priority))}>
                    {issue.priority}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2 text-sm">
                    <User className="w-4 h-4 text-muted-foreground" />
                    {issue.author}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    {new Date(issue.createdAt).toLocaleDateString()}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onIssueClick(issue);
                    }}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {filteredIssues.length === 0 && issues.length > 0 && (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <Search className="w-12 h-12 text-muted-foreground mb-3" />
          <p className="text-sm text-muted-foreground">No issues match your filters</p>
        </div>
      )}
    </div>
  );
};