# BIMFlow BCF MVP - Frontend

Professional BCF (Building Collaboration Format) file inspection and merging tool for BIM coordination.

## 🚀 Features

- **File Upload**: Drag & drop BCF/BCFzip files with instant validation
- **Issue Inspection**: Automatic extraction of issues, comments, viewpoints, and metadata
- **Issues Table**: Searchable, filterable table with status and priority badges
- **Issue Details**: Comprehensive drawer view with comments, snapshots, and viewpoints
- **File Merging**: Combine multiple BCF files into a single consolidated file
- **State Management**: Zustand store for efficient state handling
- **Mock Data**: Built-in mock data generator for demo purposes

## 📦 Tech Stack

- **React 18** + **TypeScript**
- **Vite** for blazing fast builds
- **TailwindCSS** for styling with custom design system
- **shadcn/ui** components (Table, Button, Card, Sheet, Badge, etc.)
- **Zustand** for state management
- **React Router** for navigation
- **Sonner** for toast notifications

## 🎨 Design System

The app features a professional construction/BIM industry design:
- Deep blue primary color (#2563eb derivatives)
- Orange accents for priorities and warnings
- Status-based color coding (Open, In Progress, Resolved, Closed)
- Priority-based badges (High, Medium, Low)
- Smooth transitions and hover effects
- Responsive layouts for desktop and mobile

## 🏗️ Project Structure

```
frontend/
├─ src/
│   ├─ components/
│   │   ├─ Dropzone.tsx           # File upload component
│   │   ├─ IssuesTable.tsx        # Issues data table with filters
│   │   └─ IssueDetailDrawer.tsx  # Issue detail side panel
│   ├─ pages/
│   │   ├─ Upload.tsx              # Main upload page
│   │   └─ Issues.tsx              # Issues overview page
│   ├─ store/
│   │   └─ bcfStore.ts             # Zustand store
│   ├─ lib/
│   │   ├─ api.ts                  # API client with mock data
│   │   └─ utils.ts                # Utility functions
│   └─ index.css                   # Design system tokens
```

## 🔌 API Integration

The frontend is ready to connect to a Python FastAPI backend. Update `src/lib/api.ts` to switch from mock data to real API calls:

```typescript
// In src/lib/api.ts

// Currently using mock data:
const response = await apiClient.inspectBCFWithMock(file);

// Switch to real backend (when ready):
const response = await apiClient.inspectBCF(file);
```

Set the backend URL via environment variable:
```bash
VITE_API_URL=http://localhost:8000
```

## 🧪 Backend API Contract

### POST /bcf/inspect
**Request**: `multipart/form-data` with `file` field containing .bcf/.bcfzip
**Response**:
```json
{
  "projectMeta": {
    "name": "Project Name",
    "projectId": "uuid"
  },
  "issues": [
    {
      "guid": "issue-guid",
      "title": "Issue title",
      "status": "Open",
      "priority": "High",
      "author": "John Doe",
      "createdAt": "2025-01-01T00:00:00Z",
      "description": "Issue description",
      "comments": [
        {
          "guid": "comment-guid",
          "comment": "Comment text",
          "author": "Jane Smith",
          "date": "2025-01-02T00:00:00Z"
        }
      ],
      "viewpoints": [
        {
          "guid": "viewpoint-guid",
          "title": "View 1",
          "snapshotUrl": "optional-url"
        }
      ],
      "snapshotUrl": "optional-url",
      "fileName": "original-file.bcf"
    }
  ]
}
```

### POST /bcf/merge
**Request**: `multipart/form-data` with multiple `files` fields
**Response**: Binary `.bcfzip` file download

## 🚀 Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📝 Next Steps for Full Monorepo

To complete the full-stack monorepo:

1. **Backend Development** (outside Lovable):
   - Implement FastAPI server in `backend/` directory
   - Add BCF parsing logic (XML, ZIP handling)
   - Add merge functionality
   - Write pytest tests
   - Create Dockerfile

2. **CI/CD Setup** (outside Lovable):
   - Create `.github/workflows/ci.yml`
   - Add backend tests (pytest, ruff, black)
   - Add frontend tests (eslint, vitest)
   - Configure linting and formatting

3. **Deployment**:
   - Deploy frontend to Lovable hosting or Vercel/Netlify
   - Deploy backend to Docker container (AWS, GCP, Azure)
   - Configure CORS for cross-origin requests

## 🔐 Environment Variables

Create a `.env` file for local development:

```env
VITE_API_URL=http://localhost:8000
```

## 📄 License

MIT

## 🤝 Contributing

This is an MVP project scaffold. Extend backend functionality and add more BCF features as needed.