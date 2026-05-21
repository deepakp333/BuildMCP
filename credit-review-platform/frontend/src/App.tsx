import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { PublicTab } from "./components/public/PublicTab";
import { PrivateTab } from "./components/private/PrivateTab";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 5000 },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen flex flex-col">
        <Header />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 p-6 overflow-auto">
            <Tabs defaultValue="public">
              <TabsList>
                <TabsTrigger value="public">Public Entities</TabsTrigger>
                <TabsTrigger value="private">Private Entities</TabsTrigger>
              </TabsList>
              <TabsContent value="public">
                <PublicTab />
              </TabsContent>
              <TabsContent value="private">
                <PrivateTab />
              </TabsContent>
            </Tabs>
          </main>
        </div>
      </div>
    </QueryClientProvider>
  );
}

export default App;
