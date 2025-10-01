import { create } from 'zustand';

export interface BCFComment {
  guid?: string;
  author: string;
  date: string;
  text: string;
}

export type BCFViewpoint = string;

export interface BCFIssue {
  guid: string;
  title: string;
  status: string;
  priority: string;
  author: string;
  createdAt: string;
  description?: string;
  comments: BCFComment[];
  viewpoints: BCFViewpoint[];
  snapshotUrl?: string;
  fileName: string;
}

export interface UploadedFile {
  file: File;
  issues: BCFIssue[];
  inspected: boolean;
}

interface BCFState {
  uploadedFiles: Map<string, UploadedFile>;
  allIssues: BCFIssue[];
  selectedIssue: BCFIssue | null;
  isInspecting: boolean;
  isMerging: boolean;
  
  addUploadedFile: (file: File) => void;
  setFileIssues: (fileName: string, issues: BCFIssue[]) => void;
  setSelectedIssue: (issue: BCFIssue | null) => void;
  setIsInspecting: (isInspecting: boolean) => void;
  setIsMerging: (isMerging: boolean) => void;
  clearFiles: () => void;
  removeFile: (fileName: string) => void;
}

export const useBCFStore = create<BCFState>((set, get) => ({
  uploadedFiles: new Map(),
  allIssues: [],
  selectedIssue: null,
  isInspecting: false,
  isMerging: false,

  addUploadedFile: (file: File) => {
    set((state) => {
      const newFiles = new Map(state.uploadedFiles);
      newFiles.set(file.name, {
        file,
        issues: [],
        inspected: false,
      });
      return { uploadedFiles: newFiles };
    });
  },

  setFileIssues: (fileName: string, issues: BCFIssue[]) => {
    set((state) => {
      const newFiles = new Map(state.uploadedFiles);
      const fileData = newFiles.get(fileName);
      if (fileData) {
        newFiles.set(fileName, {
          ...fileData,
          issues,
          inspected: true,
        });
      }
      
      // Aggregate all issues from all files
      const allIssues: BCFIssue[] = [];
      newFiles.forEach((fileData) => {
        allIssues.push(...fileData.issues);
      });
      
      return { uploadedFiles: newFiles, allIssues };
    });
  },

  setSelectedIssue: (issue: BCFIssue | null) => {
    set({ selectedIssue: issue });
  },

  setIsInspecting: (isInspecting: boolean) => {
    set({ isInspecting });
  },

  setIsMerging: (isMerging: boolean) => {
    set({ isMerging });
  },

  clearFiles: () => {
    set({ uploadedFiles: new Map(), allIssues: [], selectedIssue: null });
  },

  removeFile: (fileName: string) => {
    set((state) => {
      const newFiles = new Map(state.uploadedFiles);
      newFiles.delete(fileName);
      
      // Recalculate all issues
      const allIssues: BCFIssue[] = [];
      newFiles.forEach((fileData) => {
        allIssues.push(...fileData.issues);
      });
      
      return { uploadedFiles: newFiles, allIssues };
    });
  },
}));