import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import PrivateRoute from "./components/PrivateRoute";
import Login from "./pages/Login";
import TotpSetup from "./pages/TotpSetup";
import TotpVerify from "./pages/TotpVerify";
import Dashboard from "./pages/Dashboard";
import Portfolio from "./pages/Portfolio";
import AIAdvisor from "./pages/AIAdvisor";
import Trades from "./pages/Trades";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public auth routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/auth/setup-2fa" element={<TotpSetup />} />
        <Route path="/auth/verify-2fa" element={<TotpVerify />} />

        {/* Protected app routes */}
        <Route element={<PrivateRoute />}>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="portfolio" element={<Portfolio />} />
            <Route path="advisor" element={<AIAdvisor />} />
            <Route path="trades" element={<Trades />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
