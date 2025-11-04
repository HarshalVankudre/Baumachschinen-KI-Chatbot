import { Navigate } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { useAuthStore } from '@/store/authStore';
import { DocumentUpload, DocumentList } from '@/components/document';
import { Separator } from '@/components/ui/separator';

export default function DocumentsPage() {
  const { user } = useAuthStore();

  // Check authorization - only superuser and admin can access
  if (!user || !['superuser', 'admin'].includes(user.authorization_level)) {
    return <Navigate to="/forbidden" replace />;
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <div className="flex-1 p-4 md:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Dokumentenverwaltung</h1>
            <p className="text-muted-foreground mt-1">
              Dokumente für die KI-Wissensdatenbank hochladen und verwalten
            </p>
          </div>

          <Separator />

          {/* Upload Section */}
          <DocumentUpload />

          <Separator />

          {/* Document List Section */}
          <DocumentList />
        </div>
      </div>
    </div>
  );
}
