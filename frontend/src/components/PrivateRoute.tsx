import { Navigate, Outlet } from "react-router-dom";
import { useAppStore } from "../store";

export default function PrivateRoute() {
  const accessToken = useAppStore((s) => s.accessToken);
  return accessToken ? <Outlet /> : <Navigate to="/login" replace />;
}
