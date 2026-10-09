import { Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import AppShell from "@/components/AppShell";
import Dashboard from "@/pages/Dashboard";
import Leads from "@/pages/Leads";
import Lists from "@/pages/Lists";
import Jobs from "@/pages/Jobs";
import Analytics from "@/pages/Analytics";
import Companies from "@/pages/Companies";
import Credits from "@/pages/Credits";
import Exports from "@/pages/Exports";
import Persons from "@/pages/Persons";
import ImportData from "@/pages/ImportData";
import EmailGenerator from "@/pages/EmailGenerator";
import Documentation from "@/pages/Documentation";
import Contact from "@/pages/Contact";

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/leads" element={<Leads />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/persons" element={<Persons />} />
          <Route path="/import" element={<ImportData />} />
          <Route path="/email-generator" element={<EmailGenerator />} />
          <Route path="/documentation" element={<Documentation />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/lists" element={<Lists />} />
          <Route path="/scraping-jobs" element={<Jobs />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/credits" element={<Credits />} />
          <Route path="/exports" element={<Exports />} />
          <Route path="/settings" element={<Credits settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster richColors />
    </>
  );
}
