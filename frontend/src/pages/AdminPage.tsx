import { useSearchParams, Navigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Header } from '@/components/layout/Header';
import { useAuthStore } from '@/store/authStore';
import { PendingApprovalsTab, AllUsersTab } from '@/components/admin';
import { DocumentUploadTab } from '@/components/admin/DocumentUploadTab';

type TabValue = 'pending' | 'users' | 'documents';

export default function AdminPage() {
  const { user } = useAuthStore();
  const [searchParams, setSearchParams] = useSearchParams();

  // Get active tab from URL params, default to 'pending'
  const activeTab = (searchParams.get('tab') as TabValue) || 'pending';

  // Check authorization
  if (!user || user.authorization_level !== 'admin') {
    return <Navigate to="/forbidden" replace />;
  }

  const handleTabChange = (value: string) => {
    setSearchParams({ tab: value });
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <div className="flex-1 p-4 md:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Admin-Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Benutzergenehmigungen und Berechtigungen verwalten
            </p>
          </div>

          <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
            <TabsList className="grid w-full grid-cols-3 md:w-auto md:inline-grid">
              <TabsTrigger value="pending">Ausstehende Genehmigungen</TabsTrigger>
              <TabsTrigger value="users">Alle Benutzer</TabsTrigger>
              <TabsTrigger value="documents">Dokumente</TabsTrigger>
            </TabsList>

            <TabsContent value="pending" className="mt-6">
              <PendingApprovalsTab />
            </TabsContent>

            <TabsContent value="users" className="mt-6">
              <AllUsersTab />
            </TabsContent>

            <TabsContent value="documents" className="mt-6">
              <DocumentUploadTab />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
