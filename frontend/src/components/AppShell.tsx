import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { apiGet, apiPost } from "@/lib/api";
import type { AuthResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { BarChart3, BookOpen, Building2, ChevronDown, CircleDollarSign, ContactRound, Download, FileSearch, Gauge, Import, LayoutDashboard, ListChecks, LogOut, MailPlus, Menu, Search, Settings, Sparkles, UsersRound, X } from "lucide-react";
import { useState } from "react";

const links = [
  { label: "Home", to: "/", icon: LayoutDashboard },
  { label: "Scraper / Import Data", to: "/import", icon: Import },
  { label: "Companies", to: "/companies", icon: Building2 },
  { label: "Persons", to: "/persons", icon: UsersRound },
  { label: "Email Generator", to: "/email-generator", icon: MailPlus },
  { label: "Documentation", to: "/documentation", icon: BookOpen },
  { label: "Contact Us", to: "/contact", icon: ContactRound },
];

const operationLinks = [
  { label: "Lead search", to: "/leads", icon: Search },
  { label: "Lists", to: "/lists", icon: ListChecks },
  { label: "Scraping jobs", to: "/scraping-jobs", icon: FileSearch },
  { label: "Exports", to: "/exports", icon: Download },
  { label: "Analytics", to: "/analytics", icon: BarChart3 },
];

const navTestId = (label: string) => `nav-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}-link`;

export default function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const me = useQuery({ queryKey: ["me"], queryFn: () => apiGet<AuthResponse>("/auth/me"), retry: false });
  const logout = useMutation({ mutationFn: () => apiPost<{ message: string }>("/auth/logout"), onSuccess: () => { queryClient.clear(); navigate("/login"); toast.success("Signed out"); } });

  if (me.isLoading) return <div data-testid="app-loading-state" className="flex min-h-svh items-center justify-center bg-[#0a0d14] text-slate-400"><div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" /></div>;
  if (me.isError || !me.data || !me.data.user) return <NavigateToLogin />;
  const user = me.data.user;

  return (
    <div data-testid="app-shell" className="min-h-svh bg-[#0a0d14] text-slate-100">
      <div className={`fixed inset-0 z-40 bg-black/60 lg:hidden ${mobileOpen ? "block" : "hidden"}`} onClick={() => setMobileOpen(false)} data-testid="sidebar-overlay" />
      <aside data-testid="sidebar" className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-[#1e2b42] bg-[#0b101d] transition-transform duration-200 lg:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex h-18 items-center justify-between border-b border-[#1e2b42] px-6">
          <NavLink to="/" className="flex items-center gap-3" data-testid="brand-home-link" onClick={() => setMobileOpen(false)}>
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 shadow-lg shadow-blue-600/20"><Sparkles className="h-4 w-4 text-white" /></span>
            <span data-testid="brand-name" className="font-heading text-lg font-bold tracking-tight text-white">Lead<span className="text-blue-400">Forge</span></span>
          </NavLink>
          <Button variant="ghost" size="icon-sm" className="text-slate-400 lg:hidden" onClick={() => setMobileOpen(false)} data-testid="sidebar-close-button"><X /></Button>
        </div>
        <div className="lf-scrollbar overflow-y-auto px-4 pt-6"><p data-testid="workspace-label" className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Workspace</p><nav className="space-y-1">{links.map(({ label, to, icon: Icon }) => <NavLink key={to} to={to} end={to === "/"} onClick={() => setMobileOpen(false)} data-testid={navTestId(label)} className={({ isActive }) => `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${isActive ? "bg-blue-600/15 font-medium text-blue-300" : "text-slate-400 hover:bg-[#121a29] hover:text-slate-100"}`}><Icon className="h-4 w-4" /><span>{label}</span></NavLink>)}</nav><p data-testid="operations-label" className="mb-3 mt-7 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Operations</p><nav className="space-y-1">{operationLinks.map(({ label, to, icon: Icon }) => <NavLink key={to} to={to} onClick={() => setMobileOpen(false)} data-testid={navTestId(label)} className={({ isActive }) => `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${isActive ? "bg-blue-600/15 font-medium text-blue-300" : "text-slate-400 hover:bg-[#121a29] hover:text-slate-100"}`}><Icon className="h-4 w-4" /><span>{label}</span>{label === "Scraping jobs" && <span className="ml-auto h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />}</NavLink>)}</nav></div>
        <div className="mt-auto p-4"><div data-testid="sidebar-credit-card" className="rounded-xl border border-[#1e2b42] bg-[#121a29] p-4"><div className="mb-3 flex items-center justify-between"><span className="text-xs text-slate-400">Credits balance</span><CircleDollarSign className="h-4 w-4 text-blue-400" /></div><p data-testid="sidebar-credit-value" className="font-heading text-2xl font-bold text-white">{user.credits.toLocaleString()}</p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-800"><div className="h-full w-[28%] rounded-full bg-gradient-to-r from-blue-600 to-cyan-400" /></div><NavLink to="/credits" data-testid="manage-credits-link" className="mt-3 block text-xs font-medium text-blue-400 hover:text-blue-300">Manage credits <span aria-hidden="true">→</span></NavLink></div></div>
      </aside>
      <main className="lg:pl-64">
        <header data-testid="top-header" className="sticky top-0 z-30 flex h-18 items-center justify-between border-b border-[#1e2b42]/80 bg-[#0a0d14]/85 px-4 backdrop-blur-xl sm:px-8"><div className="flex items-center gap-3"><Button variant="ghost" size="icon" className="text-slate-300 lg:hidden" onClick={() => setMobileOpen(true)} data-testid="mobile-menu-button"><Menu /></Button><div className="hidden items-center gap-2 text-sm text-slate-500 md:flex"><Gauge className="h-4 w-4 text-blue-400" /> <span>Signal workspace</span><span className="text-slate-700">/</span><span className="text-slate-300">{location.pathname === "/" ? "Overview" : location.pathname.slice(1).replaceAll("-", " ")}</span></div></div><div className="flex items-center gap-3"><NavLink to="/leads" data-testid="header-search-link" className="hidden items-center gap-2 rounded-lg border border-[#1e2b42] bg-[#101622] px-3 py-2 text-xs text-slate-400 hover:border-blue-500/50 hover:text-slate-200 sm:flex"><Search className="h-3.5 w-3.5" /> Search leads <kbd className="rounded bg-[#1e2b42] px-1.5 py-0.5 font-mono text-[10px] text-slate-500">⌘ K</kbd></NavLink><NavLink to="/credits" data-testid="header-credits-link" className="flex items-center gap-2 rounded-full border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-300"><CircleDollarSign className="h-3.5 w-3.5" /> {user.credits.toLocaleString()}</NavLink><div className="group relative"><button data-testid="profile-menu-button" className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-[#121a29]"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 text-xs font-bold text-white">{user.full_name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</span><ChevronDown className="h-3.5 w-3.5 text-slate-500" /></button><div className="invisible absolute right-0 top-11 w-52 translate-y-1 rounded-xl border border-[#1e2b42] bg-[#121a29] p-2 opacity-0 shadow-2xl transition-all group-focus-within:visible group-focus-within:translate-y-0 group-focus-within:opacity-100"><div data-testid="profile-summary" className="border-b border-[#1e2b42] px-3 py-2"><p className="text-sm font-medium text-white">{user.full_name}</p><p className="mt-0.5 truncate text-xs text-slate-500">{user.email}</p></div><NavLink to="/settings" data-testid="settings-link" className="mt-1 flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-[#1a2538] hover:text-white"><Settings className="h-4 w-4" /> Settings</NavLink><button data-testid="logout-button" onClick={() => logout.mutate()} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-400 hover:bg-red-500/10 hover:text-red-300"><LogOut className="h-4 w-4" /> Sign out</button></div></div></div></header>
        <div className="min-h-[calc(100svh-4.5rem)] px-4 py-7 sm:px-8 lg:px-10"><Outlet /></div>
      </main>
    </div>
  );
}

function NavigateToLogin() { window.location.replace("/login"); return <div data-testid="redirecting-state" className="min-h-svh bg-[#0a0d14]" />; }