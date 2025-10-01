import { BCFIssue } from '@/store/bcfStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface InspectResponse {
  projectMeta: {
    name: string;
    projectId: string;
  };
  issues: BCFIssue[];
}

export interface MergeResponse {
  message: string;
  fileName: string;
  downloadUrl: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async inspectBCF(file: File): Promise<InspectResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/bcf/inspect`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to inspect BCF: ${response.statusText}`);
    }

    return response.json();
  }

  async mergeBCFs(files: File[]): Promise<Blob> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch(`${this.baseUrl}/bcf/merge`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to merge BCFs: ${response.statusText}`);
    }

    return response.blob();
  }

  // Mock data generator for demo purposes
  generateMockIssues(fileName: string): BCFIssue[] {
    const statuses = ['Open', 'In Progress', 'Resolved', 'Closed'];
    const priorities = ['High', 'Medium', 'Low'];
    const authors = ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Johnson'];
    
    const issueCount = Math.floor(Math.random() * 8) + 3;
    const issues: BCFIssue[] = [];

    for (let i = 0; i < issueCount; i++) {
      const guid = `issue-${fileName}-${i}-${Date.now()}`;
      const createdDate = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000);
      
      issues.push({
        guid,
        title: `Issue ${i + 1}: ${['Structural conflict', 'MEP clash', 'Design coordination', 'Quality issue', 'Safety concern'][Math.floor(Math.random() * 5)]}`,
        status: statuses[Math.floor(Math.random() * statuses.length)],
        priority: priorities[Math.floor(Math.random() * priorities.length)],
        author: authors[Math.floor(Math.random() * authors.length)],
        createdAt: createdDate.toISOString(),
        description: `Detailed description for issue ${i + 1}. This requires attention and coordination between teams.`,
        comments: [
          {
            guid: `comment-${guid}-1`,
            comment: 'Initial observation and documentation.',
            author: authors[Math.floor(Math.random() * authors.length)],
            date: createdDate.toISOString(),
          },
          {
            guid: `comment-${guid}-2`,
            comment: 'Following up on this issue. Needs review.',
            author: authors[Math.floor(Math.random() * authors.length)],
            date: new Date(createdDate.getTime() + 2 * 24 * 60 * 60 * 1000).toISOString(),
          },
        ],
        viewpoints: [
          {
            guid: `viewpoint-${guid}-1`,
            title: 'Main View',
          },
        ],
        fileName,
      });
    }

    return issues;
  }

  async inspectBCFWithMock(file: File): Promise<InspectResponse> {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1000 + Math.random() * 1000));

    const issues = this.generateMockIssues(file.name);

    return {
      projectMeta: {
        name: file.name.replace(/\.(bcf|bcfzip)$/i, ''),
        projectId: `project-${Date.now()}`,
      },
      issues,
    };
  }

  async mergeBCFsWithMock(files: File[]): Promise<Blob> {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 2000 + Math.random() * 1000));

    // Create a dummy blob for download
    const mergedContent = `Merged BCF containing ${files.length} files: ${files.map(f => f.name).join(', ')}`;
    return new Blob([mergedContent], { type: 'application/octet-stream' });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);